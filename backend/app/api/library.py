"""Public educational drafts. This router does not charge, crawl, or call a model."""
import hashlib
from typing import Literal
from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy import select
from ..auth import fresh_user, settings, session, current_user
from ..content import Library, ContentError
from ..schemas import Strict
from ..models import Source, Audit, now
from ..errors import fail
from ..services import rights, output_rights

router = APIRouter(tags=['open library'])


def get_library(config=Depends(settings)):
    try:
        return Library(config.content_dir)
    except (ValueError, OSError, ContentError):
        fail('CONTENT_LIBRARY_UNAVAILABLE', 'The content library is missing or failed its integrity check.', 503)


@router.get('/library')
def library(q: str = Query('', max_length=200), topic: str = Query('', max_length=60),
            kind: str = Query('', max_length=40), offset: int = Query(0, ge=0),
            limit: int = Query(24, ge=1, le=100), pack=Depends(get_library)):
    return pack.search(q, topic, kind, offset, limit)


@router.get('/library/{item_id}')
def library_item(item_id: str, pack=Depends(get_library)):
    result = pack.get(item_id)
    if result is None:
        fail('NOT_FOUND', 'Library item not found.', 404)
    return result


def require_editor(user):
    if user.role != 'technical_reviewer':
        fail('FORBIDDEN', 'An assigned technical reviewer is required.', 403)


class EditorialDecision(Strict):
    expected_policy_version: int = Field(ge=1)
    content_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['approved', 'changes_requested']
    review_note: str = Field(min_length=20, max_length=4000)
    checked_reference_ids: list[str] = Field(min_length=1, max_length=100)
    confirm_actual_review_performed: Literal[True]


@router.get('/editorial/sources')
def editorial_sources(user=Depends(current_user), db=Depends(session)):
    require_editor(user)
    rows = db.scalars(select(Source).where(Source.enabled.is_(True)).order_by(Source.created_at.desc()).limit(2000))
    items, releases = [], []
    for s in rows:
        if not (s.policy or {}).get('requires_technical_review'): continue
        text = s.text if rights.allowed(s, 'display_full') else None
        notes = output_rights.notices(db, [s])
        if text: releases.append(([s], {'text': text, 'source_attributions': notes}))
        items.append({**rights.metadata(s), 'policy': s.policy, 'text': text,
                      'source_attributions': notes, 'created_by': s.created_by})
    output_rights.release_batch(db, releases)
    db.commit()
    return {'items': items}


@router.post('/editorial/sources/{source_id}/review')
def editorial_review(source_id: str, payload: EditorialDecision,
                     user=Depends(fresh_user), db=Depends(session)):
    require_editor(user)
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if not source or not (source.policy or {}).get('requires_technical_review'):
        fail('NOT_FOUND', 'Reviewable library source not found.', 404)
    if source.created_by == user.id:
        fail('SEPARATION_OF_DUTIES', 'You cannot technically approve your own submission.', 403)
    if not source.enabled or not source.reviewed:
        fail('RIGHTS_REVIEW_REQUIRED', 'The source must first receive independent rights approval.', 409)
    digest = hashlib.sha256((source.text or '').encode()).hexdigest()
    if payload.expected_policy_version != source.policy_version or payload.content_sha256 != digest:
        fail('REVISION_CONFLICT', 'Reload the source: the version or content changed.', 409)
    refs = set(source.policy.get('content_reference_ids', []))
    if not set(payload.checked_reference_ids).issubset(refs):
        fail('UNKNOWN_REFERENCE', 'The review contains a reference absent from this article.', 422)
    if payload.decision == 'approved' and set(payload.checked_reference_ids) != refs:
        fail('INCOMPLETE_REVIEW', 'Address every listed reference, including its limitations, before approval.', 422)
    source.policy = {**source.policy, 'technical_review_status': payload.decision,
                     'technical_reviewer_id': user.id, 'technical_reviewed_at': now(),
                     'technical_review_note': payload.review_note,
                     'technical_reviewed_sha256': digest,
                     'checked_reference_ids': payload.checked_reference_ids}
    source.policy_version += 1
    db.add(Audit(actor_id=user.id, action='content.technical_review', target_id=source.id,
                 detail={'decision': payload.decision, 'sha256': digest,
                         'policy_version': source.policy_version}))
    db.commit()
    return rights.metadata(source)
