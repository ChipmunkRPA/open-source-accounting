"""Restricted group-term review. There is intentionally no ledger reset endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from ..auth import current_user, fresh_user, session, require_admin
from ..models import OutputAmendment
from ..output_amendment_schemas import OutputAmendmentSubmission, OutputAmendmentReview
from ..services import output_amendments as amendments

router = APIRouter(tags=['output amendments'])


@router.get('/admin/output-groups/{group_id}/amendments')
def records(group_id: str, user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    state = amendments.preview(db, group_id)
    rows = db.scalars(select(OutputAmendment).where(OutputAmendment.group_id == group_id)
        .order_by(OutputAmendment.submitted_at.desc(), OutputAmendment.id).limit(200)).all()
    return {**state, 'items': [amendments.serialize(row) for row in rows]}


@router.post('/admin/output-groups/{group_id}/amendments', status_code=201)
def submit(group_id: str, payload: OutputAmendmentSubmission, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    row = amendments.submit(db, group_id, payload, user.id)
    db.commit()
    return amendments.serialize(row)


@router.post('/admin/output-groups/{group_id}/amendments/{record_id}/review')
def review(group_id: str, record_id: str, payload: OutputAmendmentReview, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user, approve=True)
    row = amendments.review(db, group_id, record_id, payload, user.id)
    db.commit()
    return amendments.serialize(row)
