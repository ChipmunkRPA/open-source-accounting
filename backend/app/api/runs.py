import asyncio
import json
from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from ..auth import current_user, session, workspace_access, lock_user
from ..models import Run, Job, RunEvent, Evidence, Document, Source, Membership, now
from ..schemas import RunCreate, RunUpdate, RunStart, FollowUp
from ..agents.catalog import get_workflow
from ..agents.workflows import validate_inputs
from ..services.entitlements import reserve, settle, ACTIVE_STATES, TERMINAL_STATES
from ..services.idempotency import begin
from ..services import rights, memos, output_rights
from ..errors import fail
from .common import get_run, run_json

router = APIRouter(tags=['research'])


@router.get('/runs')
def list_runs(workspace_id: str | None = None, user=Depends(current_user), db=Depends(session)):
    query = select(Run).join(Membership, Membership.workspace_id == Run.workspace_id).where(Membership.user_id == user.id)
    if workspace_id:
        workspace_access(db, user, workspace_id)
        query = query.where(Run.workspace_id == workspace_id)
    rows = db.scalars(query.order_by(Run.created_at.desc()).limit(100)).all()
    return {'items': [{'id': r.id, 'workflow': r.workflow, 'question': r.question[:180], 'state': r.state,
                       'workspace_id': r.workspace_id, 'created_at': r.created_at} for r in rows]}


@router.post('/runs', status_code=201)
def create_run(payload: RunCreate, request: Request, idempotency_key: str = Header(default=''),
               user=Depends(current_user), db=Depends(session)):
    # Free users may prepare a draft. Nothing invokes a model or processes files here.
    workspace_access(db, user, payload.workspace_id, 'edit')
    get_workflow(payload.workflow, request.app.state.settings)
    if payload.workflow == 'standards_watch':
        fail('USE_WATCH_SETUP', 'Use watch setup for this workflow.', 422)
    lock_user(db, user.id)
    record, repeat = begin(db, user.id, 'runs.create', idempotency_key, payload.model_dump(mode='json'))
    if repeat:
        return run_json(db, get_run(db, user, record.resource_id))
    for doc_id in payload.document_ids:
        doc = db.get(Document, doc_id)
        if not doc or doc.workspace_id != payload.workspace_id or doc.status != 'ready':
            fail('DOCUMENT_UNAVAILABLE', 'Selected document is not available in this workspace.', 422)
    row = Run(user_id=user.id, **payload.model_dump(mode='json'), model_id=request.app.state.settings.model_id)
    db.add(row)
    db.flush()
    record.resource_id = row.id
    db.commit()
    return run_json(db, row)


@router.get('/runs/{run_id}')
def read_run(run_id: str, user=Depends(current_user), db=Depends(session)):
    return run_json(db, get_run(db, user, run_id))


@router.put('/runs/{run_id}/facts')
def update_facts(run_id: str, payload: RunUpdate, user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id, 'edit')
    if run.revision != payload.expected_revision:
        fail('REVISION_CONFLICT', 'This run has changed. Reload before saving.', 409)
    if run.state not in {'draft', 'planned'}:
        fail('IMMUTABLE_RUN', 'Completed or active runs are immutable. Use a follow-up revision.', 409)
    run.facts = [x.model_dump() for x in payload.facts]
    run.context = payload.context.model_dump(mode='json')
    run.revision += 1
    run.plan = None
    run.state = 'draft'
    db.commit()
    return run_json(db, run)


@router.post('/runs/{run_id}/scope')
def preview_scope(run_id: str, request: Request, user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id)
    task = get_workflow(run.workflow, request.app.state.settings)
    return {'kind': 'static_preview', 'no_model_call': True, 'workflow': task['title'],
            'sections': task['sections'], 'guardrail': task['guardrail'],
            'documents_selected': len(run.document_ids), 'min_documents': task['min_documents'],
            'requires_confirmation': True,
            'notice': 'Starting an Agent task requires your annual subscription and reserves one task.'}


@router.post('/runs/{run_id}/start', status_code=202)
def start_run(run_id: str, payload: RunStart, request: Request,
              idempotency_key: str = Header(default=''), user=Depends(current_user), db=Depends(session)):
    config = request.app.state.settings
    run = get_run(db, user, run_id, 'edit')
    # Only the owner of this execution pays for it; collaborators create their own child run.
    if run.user_id != user.id:
        fail('RUN_OWNER_REQUIRED', 'Create a follow-up under your own subscription to execute this work.', 403)
    lock_user(db, user.id)
    record, repeat = begin(db, user.id, f'runs.start:{run_id}', idempotency_key, payload.model_dump())
    if repeat:
        return run_json(db, run)
    if run.revision != payload.expected_revision:
        fail('REVISION_CONFLICT', 'Reload the latest confirmed facts.', 409)
    if run.state not in {'draft', 'planned', 'failed', 'cancelled', 'blocked'}:
        fail('INVALID_STATE', 'This run is already active or completed.', 409)
    if run.error_code == 'DOCUMENT_DELETED':
        fail('DOCUMENT_DELETED', 'Create a fresh task without the deleted document.', 409)
    task = get_workflow(run.workflow, config)
    validate_inputs(db, run, task)
    reserve(db, user, run, config)
    from ..models import uid
    run.execution_id = uid()  # Explicitly confirmed restart; lease recovery keeps this ID.
    run.state, run.cancel_requested, run.error_code = 'queued', False, None
    job = db.scalar(select(Job).where(Job.run_id == run.id))
    if job:
        job.state, job.attempts, job.lease_until, job.available_at = 'queued', 0, 0, now()
        job.lease_owner = None
    else:
        db.add(Job(run_id=run.id))
    db.add(RunEvent(run_id=run.id, kind='stage', payload={'state': 'queued'}))
    record.resource_id = run.id
    db.commit()
    return run_json(db, run)


@router.post('/runs/{run_id}/cancel')
def cancel(run_id: str, user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id, 'edit')
    if run.state not in ACTIVE_STATES:
        fail('INVALID_STATE', 'Only active tasks may be cancelled.', 409)
    run.cancel_requested = True
    job = db.scalar(select(Job).where(Job.run_id == run.id))
    if run.state == 'queued':
        run.state = 'cancelled'
        if job:
            job.state = 'done'
        settle(db, run, False)
    db.add(RunEvent(run_id=run.id, kind='cancellation.requested', payload={}))
    db.commit()
    return {'state': run.state, 'cancel_requested': True,
            'notice': 'An in-flight provider request may finish before cancellation is applied.'}


@router.post('/runs/{run_id}/follow-ups', status_code=201)
def follow_up(run_id: str, payload: FollowUp, request: Request, idempotency_key: str = Header(default=''),
              user=Depends(current_user), db=Depends(session)):
    parent = get_run(db, user, run_id, 'edit')
    lock_user(db, user.id)
    record, repeat = begin(db, user.id, f'followup:{run_id}', idempotency_key, payload.model_dump())
    if repeat:
        return run_json(db, get_run(db, user, record.resource_id))
    row = Run(workspace_id=parent.workspace_id, user_id=user.id, workflow=parent.workflow,
              question=payload.question, context=parent.context, facts=parent.facts,
              document_ids=parent.document_ids, inputs=parent.inputs,
              parent_id=parent.id, model_id=request.app.state.settings.model_id)
    db.add(row)
    db.flush()
    record.resource_id = row.id
    db.commit()
    return run_json(db, row)


def evidence_json(db, evidence, include_text=False):
    usable = rights.evidence_allowed(db, evidence, 'quote')
    source = db.get(Source, evidence.source_id) if evidence.source_id else None
    rows = output_rights.notices(db, [source]) if source and usable else []
    if include_text and usable and source and evidence.text:
        output_rights.release(db, [source], {'text': evidence.text, 'source_attributions': rows})
        db.commit()
    return {'id': evidence.id, 'title': evidence.title, 'locator': evidence.locator,
            'source_attributions': rows,
            'access': evidence.access if usable else 'unavailable', 'source_kind': evidence.source_kind,
            'source_id': evidence.source_id, 'document_id': evidence.document_id,
            'text': evidence.text if include_text and usable else None,
            'url': source.canonical_url if source else None,
            'version': source.version_label if source else None}


@router.get('/runs/{run_id}/evidence')
def evidence_list(run_id: str, user=Depends(current_user), db=Depends(session)):
    get_run(db, user, run_id)
    return {'items': [evidence_json(db, e) for e in db.scalars(select(Evidence).where(Evidence.run_id == run_id))]}


@router.get('/evidence/{evidence_id}')
def evidence_detail(evidence_id: str, user=Depends(current_user), db=Depends(session)):
    e = db.get(Evidence, evidence_id)
    if not e:
        fail('NOT_FOUND', 'Evidence not found.', 404)
    get_run(db, user, e.run_id)
    return evidence_json(db, e, include_text=True)


@router.get('/runs/{run_id}/events')
def events(run_id: str, after: int = 0, user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id)
    rows = db.scalars(select(RunEvent).where(RunEvent.run_id == run_id, RunEvent.id > after)
                       .order_by(RunEvent.id).limit(100)).all()
    return {'items': [{'id': e.id, 'kind': e.kind, 'payload': e.payload, 'created_at': e.created_at} for e in rows],
            'cursor': rows[-1].id if rows else after, 'state': run.state}


@router.get('/runs/{run_id}/stream')
async def event_stream(run_id: str, request: Request, after: int = 0,
                       user=Depends(current_user), db=Depends(session)):
    get_run(db, user, run_id)
    actor_id = user.id
    async def stream():
        from ..models import User
        cursor = after
        for _ in range(60):  # Bounded connection; client reconnects with last cursor.
            if await request.is_disconnected():
                return
            with request.app.state.db.Session() as fresh:
                actor = fresh.get(User, actor_id)
                run = get_run(fresh, actor, run_id)  # Membership checked on every iteration.
                batch = fresh.scalars(select(RunEvent).where(RunEvent.run_id == run_id,
                                      RunEvent.id > cursor).order_by(RunEvent.id).limit(100)).all()
                for e in batch:
                    cursor = e.id
                    yield f'id: {e.id}\nevent: {e.kind}\ndata: {json.dumps(e.payload)}\n\n'
                if run.state in TERMINAL_STATES:
                    return
            yield ': keepalive\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-store'})


@router.post('/runs/{run_id}/memo', status_code=201)
def memo_from_run(run_id: str, user=Depends(current_user), db=Depends(session)):
    # Deterministic conversion of an existing deliverable; no new model work or paid gate.
    run = get_run(db, user, run_id, 'edit')
    if not run.result:
        fail('NO_RESULT', 'Complete a task before creating a memo from it.', 409)
    rights.run_artifact_access(db, run, 'export')
    row = memos.from_result(db, run)
    db.commit()
    return memos.serial(db, row)
