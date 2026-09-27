"""Privileged, explicit intake steps; listing family recipes never performs network I/O."""
import asyncio
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select, func
from starlette.concurrency import run_in_threadpool
from ..auth import current_user, fresh_user, session, require_admin
from ..intake_schemas import IntakeCreate
from ..models import IntakeWork, SourceArtifact, SourceExtraction, IntakeAttempt, Source, SourceDiscovery
from ..services import intake, rights, discovery
from ..errors import fail

router = APIRouter(tags=['source-intake'])


@router.get('/admin/intake/families')
def families(request: Request, user=Depends(current_user)):
    require_admin(user)
    return {'items': list(intake.families(request.app.state.settings).values()), 'network_requests': 0}


def work_metadata(db, work):
    source = db.get(Source, work.source_id)
    return {'id': work.id, 'source_id': source.id, 'manifest': work.manifest,
            'manifest_sha256': work.manifest_sha256, 'policy_version': source.policy_version,
            'rights_revision': rights.revision(source), 'rights_reviewed': source.reviewed,
            'enabled': source.enabled, 'agent_eligible': False}


@router.post('/admin/intake/works', status_code=201)
def register(payload: IntakeCreate, request: Request, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    return work_metadata(db, intake.register(db, request.app.state.settings, payload, user.id))


@router.get('/admin/intake/works')
def works(user=Depends(current_user), db=Depends(session), offset: int = 0):
    require_admin(user)
    if offset < 0:
        fail('OFFSET', 'Offset must be nonnegative.', 422)
    rows = db.scalars(select(IntakeWork).order_by(IntakeWork.id).offset(offset).limit(100)).all()
    return {'items': [work_metadata(db, row) for row in rows], 'next_offset': offset+100 if len(rows)==100 else None}


@router.get('/admin/intake/works/{work_id}')
def preview(work_id: str, user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    work = db.get(IntakeWork, work_id)
    if not work:
        fail('NOT_FOUND', 'Work not found.', 404)
    source = db.get(Source, work.source_id)
    context = {'route': work.manifest['route'], 'audience': 'internal_ingestion'}
    return {**work_metadata(db, work), 'operations': {op: rights.allowed(source, op, context=context) for op in rights.OPERATIONS},
            'artifacts': [intake.artifact_metadata(a) for a in db.scalars(select(SourceArtifact).where(SourceArtifact.work_id == work_id))],
            'attempts': [{'id': a.id, 'state': a.state, 'lease_until': a.lease_until, 'error_code': a.error_code}
                         for a in db.scalars(select(IntakeAttempt).where(IntakeAttempt.work_id == work_id))],
            'network_requests': 0}


@router.post('/admin/intake/works/{work_id}/acquire')
def acquire(work_id: str, request: Request, idempotency_key: str = Header(alias='Idempotency-Key'), user=Depends(fresh_user)):
    require_admin(user)
    return intake.acquire(request.app.state.db, request.app.state.settings, work_id, user.id, idempotency_key)


@router.post('/admin/intake/artifacts/{artifact_id}/parse')
def parse(artifact_id: str, request: Request, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    return intake.parse(db, request.app.state.settings, artifact_id, user.id)


@router.post('/admin/intake/works/{work_id}/import')
async def manual_import(work_id: str, request: Request,
                        request_key: str = Header(default='', alias='Idempotency-Key'), user=Depends(fresh_user)):
    require_admin(user)
    database = request.app.state.db
    preflight = await run_in_threadpool(intake.manual_preflight, database, work_id, request_key)
    delivery = preflight['manifest']['manual_delivery']
    mime = request.headers.get('content-type', '')
    if mime != delivery['mime'] or request.headers.get('content-encoding'):
        fail('ARTIFACT_INTEGRITY', 'Send the exact reviewed MIME and unencoded file bytes.', 422)
    raw = bytearray()
    try:
        async with asyncio.timeout(120):
            async for chunk in request.stream():
                if len(raw) + len(chunk) > delivery['byte_count']:
                    fail('BODY_TOO_LARGE', 'Import exceeds the reviewed file size.', 413)
                raw.extend(chunk)
    except TimeoutError:
        fail('IMPORT_TIMEOUT', 'Import exceeded the body-receive deadline.', 408)
    return await run_in_threadpool(intake.import_manual, database, request.app.state.settings,
                                  work_id, user.id, request_key, bytes(raw), mime, preflight)


@router.post('/admin/intake/extractions/{extraction_id}/stage')
def stage(extraction_id: str, request: Request, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    return intake.stage(db, request.app.state.settings, extraction_id, user.id)


@router.post('/admin/intake/artifacts/{artifact_id}/discover')
def discover(artifact_id: str, request: Request, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    return discovery.discover(db, request.app.state.settings, artifact_id, user.id)


@router.get('/admin/intake/discoveries/{discovery_id}')
def read_discovery(discovery_id: str, request: Request, user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    return discovery.read(db, request.app.state.settings, discovery_id)


@router.get('/admin/intake/coverage')
def coverage(user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    # Counts use separate units, without claiming overlapping work editions are percent coverage.
    return {'registered_work_editions': db.scalar(select(func.count()).select_from(IntakeWork)),
            'discovery_snapshots': db.scalar(select(func.count()).select_from(SourceDiscovery)),
            'acquired_raw_artifacts': db.scalar(select(func.count()).select_from(SourceArtifact)),
            'parsed_artifact_versions': db.scalar(select(func.count()).select_from(SourceExtraction)),
            'parsed_passages': db.scalar(select(func.coalesce(func.sum(SourceExtraction.passage_count), 0))),
            'review_and_index_status': 'separate_workflows_not_inferred_from_acquisition'}
