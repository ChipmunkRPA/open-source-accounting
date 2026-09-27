"""Commit before inference; settle independently of result publication. Never persist content."""
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import ProviderError, fail
from ..models import ModelAttempt, Run, now
from ..providers.gemini_contract import usage_counts
from ..providers.gemini_costs import estimate_usd
from . import model_budgets

PHASES = {'chat', 'planning', 'synthesis', 'verification', 'correction', 'reverification'}
SAFE_ERRORS = {
    'MODEL_REQUEST_FAILED', 'MODEL_TIMEOUT', 'MODEL_AUTH_REQUIRED', 'MODEL_ACCESS_DENIED',
    'MODEL_UNAVAILABLE', 'MODEL_RATE_LIMITED', 'MODEL_INPUT_LIMIT', 'MODEL_INPUT_INVALID',
    'MODEL_CONFIG_INVALID', 'MODEL_RESPONSE_INVALID', 'MODEL_USAGE_INVALID',
    'MODEL_UNEXPECTED_TOOL', 'MODEL_OUTPUT_INCOMPLETE', 'MODEL_OUTPUT_BLOCKED',
    'MODEL_EMPTY_OUTPUT', 'MODEL_OUTPUT_LIMIT', 'MODEL_SCHEMA_INVALID',
    'MODEL_BUDGET_EXHAUSTED_OR_INACTIVE', 'MODEL_BUDGET_SCOPE',
}


def operation_key(*parts):
    # Includes no prompt/document hash and never stores a caller's raw retry key.
    return hashlib.sha256(json.dumps(parts, separators=(',', ':')).encode()).hexdigest()


def prepare(db_factory, config, *, key, phase, user_id, thinking, output_limit,
            prompt_version, run_id=None, run_revision=None, execution_id=None, workspace_id=None, chat_id=None):
    if phase not in PHASES or not re.fullmatch('[a-f0-9]{64}', key):
        raise ProviderError('MODEL_ATTEMPT_INVALID')
    row = ModelAttempt(operation_key=key, phase=phase, user_id=user_id,
        workspace_id=workspace_id, run_id=run_id, run_revision=run_revision, execution_id=execution_id, chat_id=chat_id,
        provider=config.model_provider, project=config.google_cloud_project,
        location=config.model_location, model_id=config.model_id,
        prompt_version=prompt_version, thinking=thinking, output_limit=output_limit)
    try:
        with db_factory() as db:
            if db.scalar(select(ModelAttempt.id).where(ModelAttempt.operation_key == key)):
                raise ProviderError('MODEL_ATTEMPT_ALREADY_RECORDED')
            model_budgets.reserve(db, config, row)
            db.add(row)
            db.commit()
            return row.id
    except ProviderError:
        raise
    except IntegrityError:
        # A unique operation key is the network ownership boundary on both DBs.
        # A pending/finished receipt never licenses another request or stores a reply.
        try:
            with db_factory() as db:
                duplicate = db.scalar(select(ModelAttempt.id).where(ModelAttempt.operation_key == key))
        except Exception:
            duplicate = None
        raise ProviderError('MODEL_ATTEMPT_ALREADY_RECORDED' if duplicate else 'MODEL_LEDGER_UNAVAILABLE') from None
    except Exception:
        raise ProviderError('MODEL_LEDGER_UNAVAILABLE') from None


def settle(db_factory, attempt_id, model, *, succeeded, error_code):
    try:
        with db_factory() as db:
            row = db.get(ModelAttempt, attempt_id)
            if row is None or row.outcome != 'pending':
                raise ProviderError('MODEL_ATTEMPT_ALREADY_SETTLED')
            usage, estimate, cost_state = None, None, 'unknown'
            http = getattr(model, 'last_http_status', None)
            http = http if type(http) is int and 100 <= http <= 599 else None
            if row.provider == 'mock':
                usage, cost_state = {'mock': True, 'totalTokenCount': 0}, 'mock'
            else:
                raw = getattr(model, 'last_usage', {})
                try:
                    usage = usage_counts(raw)
                except ValueError:
                    pass
                if error_code == 'MODEL_USAGE_INVALID':
                    usage = None
                # Only explicit pre-dispatch/non-200 knowledge proves no model charge.
                # Missing headers, HTTP 200 without usable usage, and crashes stay unknown.
                if getattr(model, 'last_dispatch_state', None) == 'not_sent' or (http is not None and http != 200):
                    cost_state = 'not_incurred'
                elif http == 200 and usage is not None:
                    try:
                        estimate = estimate_usd(usage, provider=row.provider, model=row.model_id,
                            location=row.location, incurred_on=datetime.fromtimestamp(row.started_at, timezone.utc).date())
                        cost_state = 'estimated'
                    except ValueError:
                        pass
            version = getattr(model, 'last_model_version', None)
            if not isinstance(version, str) or not re.fullmatch(r'[a-zA-Z0-9._-]{1,128}', version):
                version = None
            changed = db.execute(update(ModelAttempt).where(ModelAttempt.id == attempt_id,
                ModelAttempt.outcome == 'pending').values(
                    outcome='succeeded' if succeeded else 'failed', finished_at=now(),
                    error_code=None if succeeded else error_code if error_code in SAFE_ERRORS else 'MODEL_REQUEST_FAILED',
                    http_status=http, usage=usage, cost_state=cost_state,
                    cost_estimate=estimate, model_version=version))
            if changed.rowcount != 1:
                raise ProviderError('MODEL_ATTEMPT_ALREADY_SETTLED')
            overrun = model_budgets.settle(db, row, cost_state, estimate)
            db.commit()
            if overrun:
                raise ProviderError('MODEL_BUDGET_OVERRUN')
    except ProviderError:
        raise
    except Exception:
        # The pending receipt survives. Do not release an unaccounted answer.
        raise ProviderError('MODEL_LEDGER_UNAVAILABLE') from None


def invoke(db_factory, config, model, call, **metadata):
    attempt_id = prepare(db_factory, config, **metadata)
    if config.model_provider != 'mock':
        # Defensive reset for any adapter. Gemini sets dispatch state explicitly.
        model.last_usage, model.last_model_version = {}, None
        model.last_http_status, model.last_dispatch_state = None, 'not_sent'
    try:
        model_budgets.dispatch_allowed(db_factory, config, attempt_id)
        if config.model_provider != 'mock':
            model.last_dispatch_state = 'unknown'
        result = call()
    except Exception as exc:
        settle(db_factory, attempt_id, model, succeeded=False, error_code=str(exc) if isinstance(exc, ProviderError) else '')
        raise ProviderError(str(exc) if isinstance(exc, ProviderError) and str(exc) in SAFE_ERRORS else 'MODEL_REQUEST_FAILED') from None
    # A process death (BaseException) deliberately leaves pending/unknown, never zero.
    settle(db_factory, attempt_id, model, succeeded=True, error_code=None)
    return result


def report(db, *, start_at, end_at):
    """Attempt-window subtotal, plus complete tracked-run cohorts. No content returned."""
    rows = db.scalars(select(ModelAttempt).where(ModelAttempt.started_at >= start_at,
        ModelAttempt.started_at < end_at).order_by(ModelAttempt.started_at, ModelAttempt.id).limit(10001)).all()
    if len(rows) > 10000:
        fail('REPORT_TOO_LARGE', 'Use a smaller report window.', 422)
    live = [r for r in rows if r.provider != 'mock']
    orphaned = sum(r.phase != 'chat' and r.run_id is None for r in live)
    unknown = sum(r.cost_state == 'unknown' for r in live)
    subtotal = sum((Decimal(r.cost_estimate['estimated_usd']) for r in live if r.cost_state == 'estimated'), Decimal(0))
    # Run cohort: first-ever recorded attempt starts within the window; include
    # every attempt for those runs, even if a later stage crossed the window end.
    run_ids = select(ModelAttempt.run_id).where(ModelAttempt.run_id.is_not(None),
        ModelAttempt.provider != 'mock').group_by(ModelAttempt.run_id).having(
            func.min(ModelAttempt.started_at) >= start_at, func.min(ModelAttempt.started_at) < end_at)
    all_agent = db.scalars(select(ModelAttempt).where(ModelAttempt.run_id.in_(run_ids),
        ModelAttempt.provider != 'mock').limit(10001)).all()
    if len(all_agent) > 10000:
        fail('REPORT_TOO_LARGE', 'Use a smaller report cohort.', 422)
    by_run = {}
    for row in all_agent:
        by_run.setdefault(row.run_id, []).append(row)
    cohort = {rid: attempts for rid, attempts in by_run.items()
              if start_at <= min(r.started_at for r in attempts) < end_at}
    cohort_rows = [r for attempts in cohort.values() for r in attempts]
    states = dict(db.execute(select(Run.id, Run.state).where(Run.id.in_(cohort))).all())
    completed = sum(states.get(rid) == 'completed_with_limitations' for rid in cohort)
    active = sum(states.get(rid) not in {'completed_with_limitations', 'failed', 'blocked', 'cancelled'} for rid in cohort)
    unresolved = sum(r.cost_state == 'unknown' for r in cohort_rows)
    agent_subtotal = sum((Decimal(r.cost_estimate['estimated_usd']) for r in cohort_rows if r.cost_state == 'estimated'), Decimal(0))
    return {'start_at': start_at, 'end_at': end_at, 'attempts': len(rows), 'mock_attempts': len(rows)-len(live),
        'pending_attempts': sum(r.outcome == 'pending' for r in rows), 'unknown_cost_attempts': unknown,
        'known_estimate_subtotal_usd': str(subtotal), 'complete_estimate_usd': str(subtotal) if not unknown else None,
        'agent_cohort': {'tracked_runs': len(cohort), 'completed_runs': completed, 'active_runs': active,
            'orphaned_agent_attempts_in_window': orphaned,
            'unknown_cost_attempts': unresolved, 'known_estimate_subtotal_usd': str(agent_subtotal),
            'estimated_model_usd_per_completed_run': str(agent_subtotal / completed) if completed and not unresolved and not active and not orphaned else None},
        'basis': 'dated_standard_text_estimate_not_invoice; mock excluded; legacy untracked runs excluded; infrastructure excluded'}


def report_snapshot(database, *, start_at, end_at):
    # A completion observed after a new call must not be paired with an older
    # cost snapshot. Auth uses its own session; this connection starts fresh.
    with database.engine.connect() as connection:
        if connection.dialect.name == 'postgresql':
            connection = connection.execution_options(isolation_level='REPEATABLE READ')
        else:
            connection.exec_driver_sql('BEGIN')  # SQLite SELECT alone uses legacy transaction behavior.
        with Session(bind=connection) as db:
            return report(db, start_at=start_at, end_at=end_at)
