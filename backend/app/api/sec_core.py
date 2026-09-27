"""Public SEC source-excerpt reading and MFA-protected applicability review."""
from pathlib import Path
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from ..auth import settings, session, fresh_user
from ..applicability_schemas import ApplicabilityDecision
from ..models import Source
from ..errors import fail
from ..sec_core.core import CorePack, CoreError
from .library import require_editor

router = APIRouter(tags=['SEC Core'])


def pack(config=Depends(settings)):
    try:
        return CorePack(Path(config.content_dir) / 'sec_core')
    except (ValueError, OSError, KeyError):
        fail('SEC_PACK_UNAVAILABLE', 'SEC source pack is unavailable or failed integrity validation.', 503)


@router.get('/sec-core')
def inventory(data=Depends(pack)):
    return {**data.report(), 'sources': list(data.entries.values())}


@router.get('/sec-core/search')
def preview(q: str = Query('', max_length=500), family: str | None = None,
            limit: int = Query(12, ge=1, le=100), data=Depends(pack)):
    try:
        return {'items': data.preview(q, limit, family), 'notice': data.report()['notice'],
                'agent_approved': False}
    except CoreError:
        fail('INVALID_SEARCH', 'Choose a listed SEC collection.', 422)


@router.get('/sec-core/sources/{source_id}')
def source(source_id: str, data=Depends(pack)):
    result = data.public_source(source_id)
    if result is None:
        fail('NOT_FOUND', 'SEC source not found.', 404)
    return result


@router.get('/sec-core/passages/{passage_id}')
def passage(passage_id: str, data=Depends(pack)):
    result = data.passage(passage_id)
    if result is None:
        fail('NOT_FOUND', 'SEC excerpt not found.', 404)
    return result


@router.post('/editorial/sec-core/{source_id}/applicability')
def applicability(source_id: str, payload: ApplicabilityDecision,
                  user=Depends(fresh_user), db=Depends(session)):
    """SEC-specific route uses the same exact-revision ledger and private history."""
    from ..services import applicability as reviews
    require_editor(user)
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if not source or not (source.policy or {}).get('sec_core'):
        fail('NOT_FOUND', 'Staged SEC source not found.', 404)
    return reviews.record(db, source, payload, user.id)
