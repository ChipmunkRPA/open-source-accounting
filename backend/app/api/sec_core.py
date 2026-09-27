"""Public SEC source-excerpt reading and MFA-protected applicability review."""
from pathlib import Path
from ..services.editorial import current as technical_current
from datetime import date
from typing import Literal
import hashlib
from fastapi import APIRouter, Depends, Query
from pydantic import Field, model_validator
from sqlalchemy import select
from ..auth import settings, session, fresh_user
from ..schemas import Strict
from ..models import Source, Audit, now
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


class ApplicabilityReview(Strict):
    expected_policy_version: int = Field(ge=1)
    content_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    effective_from: date
    effective_to: date | None = None
    public_available_at: date
    review_note: str = Field(min_length=30, max_length=4000)
    confirm_source_history_checked: Literal[True]

    @model_validator(mode='after')
    def interval(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError('Applicability interval is reversed')
        return self


@router.post('/editorial/sec-core/{source_id}/applicability')
def applicability(source_id: str, payload: ApplicabilityReview,
                  user=Depends(fresh_user), db=Depends(session)):
    require_editor(user)
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if not source or not (source.policy or {}).get('sec_core'):
        fail('NOT_FOUND', 'Staged SEC source not found.', 404)
    if source.created_by == user.id:
        fail('SEPARATION_OF_DUTIES', 'A different reviewer must validate applicability.', 403)
    if (not source.enabled or not source.reviewed or
            source.policy.get('technical_review_status') != 'approved' or not technical_current(source)):
        fail('REVIEW_REQUIRED', 'Rights and technical reviews must be completed first.', 409)
    actual = hashlib.sha256((source.text or '').encode()).hexdigest()
    if (payload.content_sha256 != actual or payload.expected_policy_version != source.policy_version or
            source.policy.get('technical_reviewed_sha256') != actual):
        fail('REVISION_CONFLICT', 'Content or policy changed; reload and review again.', 409)
    values = {'effective_from': payload.effective_from.isoformat(),
              'effective_to': payload.effective_to.isoformat() if payload.effective_to else None,
              'public_available_at': payload.public_available_at.isoformat(),
              'applicability_review_status': 'approved', 'applicability_reviewer': user.id,
              'applicability_reviewed_at': now(), 'applicability_review_note': payload.review_note}
    source.policy = {**source.policy, 'sec_core': {**source.policy['sec_core'], **values}}
    source.effective_from, source.effective_to = values['effective_from'], values['effective_to']
    source.policy_version += 1
    db.add(Audit(actor_id=user.id, action='sec_core.applicability_review', target_id=source_id,
                 detail={'policy_version': source.policy_version, 'sha256': actual}))
    db.commit()
    return {'source_id': source_id, 'policy_version': source.policy_version, **values}
