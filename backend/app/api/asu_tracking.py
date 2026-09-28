"""Anonymous ASU reading; only a freshly authenticated admin can advance refresh."""
from fastapi import APIRouter, Depends, Query
from ..auth import session, fresh_user, require_admin
from ..errors import fail
from ..services import asu_tracking as service
from ..asu_schemas import Status

router = APIRouter(tags=['ASU tracking'])


@router.get('/asu-tracking')
def listing(q: str = Query('', max_length=200), topic: str = Query('', max_length=80), db=Depends(session)):
    return service.listing(db, q, topic)


@router.get('/asu-tracking/{asu_id}/filings')
def filings(asu_id: str, company: str = Query('', max_length=200), status: Status | None = None,
            offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), db=Depends(session)):
    if asu_id not in {a.id for a in service.catalog().asus}:
        fail('NOT_FOUND', 'ASU is not registered.', 404)
    return service.materials(db, asu_id, company, status or '', offset, limit)


@router.post('/admin/asu-tracking/refresh')
def refresh(user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    service.refresh(db, force=True)
    return service.refresh_status(db)
