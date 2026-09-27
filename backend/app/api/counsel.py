"""Restricted counsel workflow; no public route exposes private evidence references."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from ..auth import current_user, fresh_user, session, require_admin
from ..counsel_schemas import CounselSubmission, CounselReview, CounselRevocation
from ..models import CounselRecord, Audit, now
from ..services import counsel, rights
from ..errors import fail

router = APIRouter(tags=['counsel'])


def reader(user):
    if user.role not in {'admin', 'rights_approver', 'counsel_reviewer'}:
        fail('FORBIDDEN', 'An authorized rights or counsel role is required.', 403)


@router.get('/admin/sources/{source_id}/counsel-records')
def records(source_id: str, user=Depends(current_user), db=Depends(session)):
    reader(user)
    from ..models import Source
    source = db.get(Source, source_id)
    if not source: fail('NOT_FOUND', 'Source not found.', 404)
    rows = db.scalars(select(CounselRecord).where(CounselRecord.source_id == source_id)
                      .order_by(CounselRecord.submitted_at.desc(), CounselRecord.id).limit(200)).all()
    return {'source': {**rights.metadata(source), 'policy': source.policy,
                       'rights_revision': rights.revision(source)},
            'items': [counsel.serialize(row) for row in rows]}


@router.post('/admin/sources/{source_id}/counsel-records', status_code=201)
def submit(source_id: str, payload: CounselSubmission, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    source = counsel.lock_source(db, source_id)
    row = counsel.submit(db, source, payload, user.id)
    db.commit()
    return counsel.serialize(row)


@router.post('/admin/sources/{source_id}/counsel-records/{record_id}/review')
def review(source_id: str, record_id: str, payload: CounselReview, user=Depends(fresh_user), db=Depends(session)):
    if user.role != 'counsel_reviewer':
        fail('FORBIDDEN', 'A designated independent counsel reviewer is required.', 403)
    source = counsel.lock_source(db, source_id)
    row = db.scalar(select(CounselRecord).where(CounselRecord.id == record_id,
        CounselRecord.source_id == source_id).with_for_update())
    if not row: fail('NOT_FOUND', 'Counsel record not found.', 404)
    if user.id in {row.submitted_by, source.created_by, source.approved_by}:
        fail('SEPARATION_OF_DUTIES', 'Another authorized counsel reviewer must perform this review.', 403)
    if (row.status != 'pending' or row.record_sha256 != payload.expected_record_sha256
            or row.record_sha256 != counsel.fingerprint(source.id, row.submitted_by, row.proposal)):
        fail('REVISION_CONFLICT', 'The review record changed or has already been decided.', 409)
    proposal = CounselSubmission.model_validate(row.proposal)
    if (proposal.expected_rights_revision != rights.revision(source)
            or proposal.expected_policy_version != source.policy_version or not source.enabled
            or proposal.expires_at <= now()):
        fail('REVISION_CONFLICT', 'The source changed or the decision interval expired.', 409)
    row.status, row.reviewed_by, row.reviewed_at = payload.decision, user.id, now()
    db.add(Audit(actor_id=user.id, action='counsel.' + payload.decision, target_id=row.id,
                 detail={'source_id': source.id, 'record_sha256': row.record_sha256}))
    db.commit()
    return counsel.serialize(row)


@router.post('/admin/sources/{source_id}/counsel-records/{record_id}/revoke')
def revoke(source_id: str, record_id: str, payload: CounselRevocation, user=Depends(fresh_user), db=Depends(session)):
    reader(user)
    source = counsel.lock_source(db, source_id)
    row = db.scalar(select(CounselRecord).where(CounselRecord.id == record_id,
        CounselRecord.source_id == source_id).with_for_update())
    if not row: fail('NOT_FOUND', 'Counsel record not found.', 404)
    if row.record_sha256 != payload.expected_record_sha256:
        fail('REVISION_CONFLICT', 'Reload the counsel record.', 409)
    if row.status != 'revoked':
        row.status, row.revoked_by, row.revoked_at = 'revoked', user.id, now()
        row.revocation_reason = payload.reason
        if row.activated_policy_version == source.policy_version:
            source.policy_version += 1
            source.reviewed = False
        db.add(Audit(actor_id=user.id, action='counsel.revoked', target_id=row.id,
                     detail={'source_id': source.id, 'reason': payload.reason}))
    db.commit()
    return counsel.serialize(row)
