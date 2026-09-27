"""Durable, bounded research execution. Server controls tools and source eligibility."""
import json
from sqlalchemy import select, delete
from ..models import Run, Job, Evidence, RunEvent, User, now
from ..schemas import Plan, Analysis, Verification
from ..providers.gemini import get_model
from ..services import retrieval, rights, memos
from ..services.entitlements import require_agent, settle, TERMINAL_STATES
from ..errors import ProviderError, RunStopped
from .catalog import get_workflow
from .workflows import preprocess
from .verification import structural_verify
from . import prompts


def emit(db, run, state, **payload):
    run.state = state
    run.updated_at = now()
    db.add(RunEvent(run_id=run.id, kind='stage', payload={'state': state, **payload}))


def checkpoint(db, run_id, job_id, owner, settings):
    db.expire_all()
    run = db.scalar(select(Run).where(Run.id == run_id).with_for_update())
    job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if not job or job.lease_owner != owner or run.cancel_requested:
        raise RunStopped('CANCELLED_OR_LEASE_LOST')
    require_agent(db, db.get(User, run.user_id), settings)
    job.lease_until = now() + settings.worker_lease_seconds
    return run


def execute(db_factory, job_id, owner, config):
    model = get_model(config)
    with db_factory() as db:
        job = db.get(Job, job_id)
        if not job or job.lease_owner != owner:
            return
        run_id = job.run_id
    try:
        with db_factory() as db:
            run = checkpoint(db, run_id, job_id, owner, config)
            task = get_workflow(run.workflow, config)
            deterministic = preprocess(db, run, task)
            emit(db, run, 'planning')
            request_data = {'question': run.question, 'context': run.context, 'facts': run.facts,
                            'task': task, 'inputs': run.inputs}
            db.commit()
        plan = model.structured(Plan, prompts.PLAN, request_data, thinking='MEDIUM', cap=2500)
        usage = dict(model.last_usage)
        with db_factory() as db:
            run = checkpoint(db, run_id, job_id, owner, config)
            run.plan = plan.model_dump()
            emit(db, run, 'retrieving', query_count=min(len(plan.proposed_queries), task['max_queries']))
            db.execute(delete(Evidence).where(Evidence.run_id == run.id))
            selected, seen = [], set()
            queries = [run.question] + plan.proposed_queries[:task['max_queries'] - 1]
            for query in queries:
                for row in retrieval.search(db, run, query, task['max_evidence']):
                    key = (row['source_id'], row['document_id'], row['locator'])
                    if key not in seen:
                        seen.add(key)
                        selected.append(row)
            # Guarantee each explicitly selected document has at least one evidence packet.
            # A retrieval subset is disclosed; it is NOT a full-document completeness audit.
            rows = []
            doc_first = []
            for doc_id in run.document_ids:
                hit = next((x for x in selected if x['document_id'] == doc_id), None)
                if hit:
                    doc_first.append(hit)
            pool = doc_first + [x for x in selected if x not in doc_first]
            for row in pool[:task['max_evidence']]:
                evidence = Evidence(run_id=run.id, **row)
                db.add(evidence)
                db.flush()
                rows.append({'id': evidence.id, **row})
            emit(db, run, 'analyzing', evidence_count=len(rows))
            data = {**request_data, 'plan': plan.model_dump(), 'evidence': rows,
                    'deterministic_calculations': deterministic}
            # Keep large deterministic schedules out of the model. Full schedule remains in deliverable.
            if deterministic.get('lease'):
                data['deterministic_calculations'] = {**deterministic,
                    'lease': {**deterministic['lease'], 'rows': deterministic['lease']['rows'][:12],
                              'model_preview_only': True}}
            db.commit()
        analysis = model.structured(Analysis, prompts.ANALYZE, data, thinking='HIGH', cap=7500)
        usage = merge_usage(usage, model.last_usage)
        findings = structural_verify(analysis, rows)
        with db_factory() as db:
            run = checkpoint(db, run_id, job_id, owner, config)
            rights.run_artifact_access(db, run, 'model_input')
            emit(db, run, 'verifying', check='citations_and_applicability')
            db.commit()
        verification = model.structured(Verification, prompts.VERIFY,
                    {'draft': analysis.model_dump(), 'evidence': rows, 'context': data['context']},
                    thinking='HIGH', cap=3500)
        usage = merge_usage(usage, model.last_usage)
        findings += [x.model_dump() for x in verification.findings]
        blocked = any(x['severity'] == 'block' for x in findings)
        if blocked:
            # One bounded correction round. Never silently release the original unsupported draft.
            correction = {**data, 'draft': analysis.model_dump(), 'required_corrections': findings}
            analysis = model.structured(Analysis, prompts.ANALYZE + '\nCorrect or remove every flagged claim.',
                                        correction, thinking='HIGH', cap=7500)
            usage = merge_usage(usage, model.last_usage)
            verification = model.structured(Verification, prompts.VERIFY,
                    {'draft': analysis.model_dump(), 'evidence': rows, 'context': data['context']},
                    thinking='HIGH', cap=3500)
            usage = merge_usage(usage, model.last_usage)
            findings = structural_verify(analysis, rows) + [x.model_dump() for x in verification.findings]
        if any(x['severity'] == 'block' for x in findings):
            raise ProviderError('VERIFICATION_BLOCKED')
        with db_factory() as db:
            run = checkpoint(db, run_id, job_id, owner, config)
            rights.run_artifact_access(db, run, 'quote')
            result = analysis.model_dump()
            result['limitations'] = list(dict.fromkeys(result['limitations'] + verification.limitations + [
                'AI checks are not professional review or certification.',
                'Research uses a bounded evidence subset, not an exhaustive reading of every source or uploaded page.',
            ]))
            if any(e['access'] == 'reference_only' for e in rows):
                result['limitations'].append('One or more references were identified but their primary text was not accessed.')
            result.update({'verification': findings, 'deterministic': deterministic,
                           'provider': config.model_provider, 'model_id': config.model_id,
                           'prompt_version': prompts.PROMPT_VERSION, 'evidence_count': len(rows)})
            run.result = result
            run.token_usage = usage
            run.error_code = None
            emit(db, run, 'completed_with_limitations')
            # Every generated result is a draft with limits; never label it GAAP-certified.
            if run.workflow in {'memo', 'policy_draft', 'sec_response'}:
                memos.from_result(db, run)
            settle(db, run, released=True)
            job = db.get(Job, job_id)
            job.state, job.lease_until = 'done', 0
            db.add(RunEvent(run_id=run.id, kind='answer.released', payload={'revision': run.revision}))
            db.commit()
    except Exception as error:
        from fastapi import HTTPException
        code = str(error) if isinstance(error, (ProviderError, RunStopped)) else 'TASK_FAILED'
        if isinstance(error, HTTPException):
            code = error.detail.get('code', 'TASK_BLOCKED') if isinstance(error.detail, dict) else 'TASK_BLOCKED'
        with db_factory() as db:
            run = db.get(Run, run_id)
            job = db.get(Job, job_id)
            if not run or not job or job.lease_owner != owner:
                return
            state = 'cancelled' if run.cancel_requested else ('blocked' if code in {
                'SUBSCRIPTION_REQUIRED', 'SOURCE_CHANGED', 'SOURCE_POLICY_BLOCK', 'FEATURE_NOT_ENABLED',
                'DOCUMENT_UNAVAILABLE'} else 'failed')
            emit(db, run, state, error_code=code)
            run.error_code = code
            settle(db, run, released=False)
            job.state, job.lease_until = 'done', 0
            db.commit()
        # No raw exceptions/prompts/documents in logs. UI gets the safe category.


def merge_usage(first, second):
    result = dict(first)
    for key, value in second.items():
        if isinstance(value, int) and not isinstance(value, bool):
            result[key] = int(result.get(key, 0)) + value
        else:
            result[key] = value
    return result
