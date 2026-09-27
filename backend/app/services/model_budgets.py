"""Conservative spend reservations. Unknown and estimated liabilities are never auto-refunded."""
import hashlib
import json
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal, ROUND_CEILING
from sqlalchemy import select, update
from ..models import ModelBudget, ModelAttempt, User, now
from ..errors import ProviderError, fail
from ..providers.gemini_costs import CATALOG_VERSION, OBSERVED_ON, estimate_usd

NANOS = Decimal(1000000000)
REVIEW_DEADLINE = int(datetime.combine(OBSERVED_ON + timedelta(days=30), datetime.min.time(), timezone.utc).timestamp())


def nanos(value):
    return int((Decimal(value) * NANOS).to_integral_value(rounding=ROUND_CEILING))


def minimum_reservation(location):
    # Entire documented context and TWO output ceilings (response + thinking),
    # using the higher published post-intro rate. An admission estimate, not an invoice guarantee.
    return nanos(estimate_usd({'promptTokenCount': 1048576, 'candidatesTokenCount': 65536,
        'thoughtsTokenCount': 65536, 'totalTokenCount': 1179648}, location=location,
        incurred_on=date(2027, 1, 1))['estimated_usd'])


def digest(terms):
    return hashlib.sha256(json.dumps(terms, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def authorize(db, payload, actor_id):
    actor = db.get(User, actor_id)
    if not actor or actor.role != 'admin':
        fail('FORBIDDEN', 'Spending authorization requires an operations administrator.', 403)
    limit, per_call = nanos(payload.limit_usd), nanos(payload.per_call_usd)
    if not minimum_reservation(payload.location) <= per_call <= limit <= nanos('1000000'):
        fail('INVALID_BUDGET', 'Amounts must cover the documented conservative per-call reserve and stay within USD 1,000,000.', 422)
    if not now() < payload.expires_at <= min(now()+30*86400, REVIEW_DEADLINE):
        fail('INVALID_BUDGET_EXPIRY', 'Reverify prices before authorizing a budget beyond the current review window.', 422)
    terms = payload.model_dump()
    existing = db.scalar(select(ModelBudget).where(ModelBudget.terms_sha256 == digest(terms)))
    if existing:
        return existing  # Retrying authorization never creates additional money or reactivates it.
    row = ModelBudget(terms=terms, terms_sha256=digest(terms), authorized_by=actor_id,
        expires_at=payload.expires_at, limit_nanos=limit, per_call_nanos=per_call)
    db.add(row)
    db.flush()
    return row


def reserve(db, config, attempt):
    if config.model_provider == 'mock':
        return
    if not config.model_budget_id:
        raise ProviderError('MODEL_BUDGET_REQUIRED')
    row = db.get(ModelBudget, config.model_budget_id)
    if not row or row.terms_sha256 != digest(row.terms):
        raise ProviderError('MODEL_BUDGET_INVALID')
    if (row.limit_nanos != nanos(row.terms['limit_usd']) or row.per_call_nanos != nanos(row.terms['per_call_usd'])
            or row.expires_at != row.terms['expires_at'] or row.per_call_nanos < minimum_reservation(row.terms['location'])):
        raise ProviderError('MODEL_BUDGET_INVALID')
    expected = {'provider': config.model_provider, 'project': config.google_cloud_project,
                'location': config.model_location, 'model_id': config.model_id, 'catalog_version': CATALOG_VERSION}
    if any(row.terms.get(k) != v for k, v in expected.items()):
        raise ProviderError('MODEL_BUDGET_SCOPE')
    # Unbudgeted legacy uncertainty must be reconciled, never washed away by a new envelope.
    legacy = db.scalar(select(ModelAttempt.id).where(ModelAttempt.budget_id.is_(None),
        ModelAttempt.provider == config.model_provider, ModelAttempt.project == config.google_cloud_project,
        ModelAttempt.location == config.model_location, ModelAttempt.model_id == config.model_id,
        ModelAttempt.cost_state == 'unknown').limit(1))
    if legacy:
        raise ProviderError('MODEL_BUDGET_LEGACY_UNKNOWN')
    changed = db.execute(update(ModelBudget).where(ModelBudget.id == row.id,
        ModelBudget.active.is_(True), ModelBudget.expires_at > now(),
        ModelBudget.expires_at <= REVIEW_DEADLINE,
        ModelBudget.held_nanos + ModelBudget.committed_nanos + ModelBudget.per_call_nanos <= ModelBudget.limit_nanos
        ).values(held_nanos=ModelBudget.held_nanos+ModelBudget.per_call_nanos))
    if changed.rowcount != 1:
        raise ProviderError('MODEL_BUDGET_EXHAUSTED_OR_INACTIVE')
    attempt.budget_id, attempt.reserved_nanos, attempt.budget_state = row.id, row.per_call_nanos, 'held'


def settle(db, attempt, cost_state, estimate):
    if not attempt.budget_id:
        return
    if cost_state == 'unknown':
        return  # No timeout/expiry/retry releases uncertain money.
    reserved = attempt.reserved_nanos
    committed = 0 if cost_state == 'not_incurred' else max(reserved, nanos(estimate['estimated_usd']))
    changed = db.execute(update(ModelBudget).where(ModelBudget.id == attempt.budget_id,
        ModelBudget.held_nanos >= reserved).values(
            held_nanos=ModelBudget.held_nanos-reserved,
            committed_nanos=ModelBudget.committed_nanos+committed,
            **({'active': False} if committed > reserved else {})))
    if changed.rowcount != 1:
        raise ProviderError('MODEL_BUDGET_LEDGER_CONFLICT')
    attempt.budget_state = 'overrun' if committed > reserved else 'released' if committed == 0 else 'committed'
    return committed > reserved


def dispatch_allowed(db_factory, config, attempt_id):
    if config.model_provider == 'mock':
        return
    with db_factory() as db:
        attempt = db.get(ModelAttempt, attempt_id)
        row = db.get(ModelBudget, attempt.budget_id)
        if not row.active or row.expires_at <= now():
            raise ProviderError('MODEL_BUDGET_EXHAUSTED_OR_INACTIVE')
        if any(row.terms.get(k) != v for k, v in {'provider': config.model_provider,
            'project': config.google_cloud_project, 'location': config.model_location, 'model_id': config.model_id}.items()):
            raise ProviderError('MODEL_BUDGET_SCOPE')


def serialize(row):
    return {'id': row.id, 'terms': row.terms, 'terms_sha256': row.terms_sha256,
        'active': row.active, 'expires_at': row.expires_at,
        'limit_usd': str(Decimal(row.limit_nanos)/NANOS),
        'per_call_usd': str(Decimal(row.per_call_nanos)/NANOS),
        'held_usd': str(Decimal(row.held_nanos)/NANOS),
        'committed_usd': str(Decimal(row.committed_nanos)/NANOS),
        'available_usd': str(Decimal(max(0, row.limit_nanos-row.held_nanos-row.committed_nanos))/NANOS)}
