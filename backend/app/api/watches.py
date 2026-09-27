from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from ..auth import current_user, session, workspace_access
from ..models import Watch, now
from ..schemas import WatchCreate
from ..services.entitlements import require_agent
from ..agents.catalog import get_workflow
from ..errors import fail

router = APIRouter(tags=['watches'])


@router.get('/watches')
def list_watches(user=Depends(current_user), db=Depends(session)):
    rows = db.scalars(select(Watch).where(Watch.user_id == user.id)).all()
    return {'items': [{'id': r.id, 'topic': r.topic, 'enabled': r.enabled, 'cadence_days': r.cadence_days,
                       'next_at': r.next_at, 'workspace_id': r.workspace_id} for r in rows]}


@router.post('/watches', status_code=201)
def create_watch(payload: WatchCreate, request: Request, user=Depends(current_user), db=Depends(session)):
    config = request.app.state.settings
    get_workflow('standards_watch', config)
    workspace_access(db, user, payload.workspace_id, 'edit')
    require_agent(db, user, config)
    existing = db.scalars(select(Watch).where(Watch.user_id == user.id)).all()
    if len(existing) >= 10:
        fail('WATCH_LIMIT', 'At most ten saved watches are supported.', 429)
    row = Watch(user_id=user.id, workspace_id=payload.workspace_id, topic=payload.topic,
                cadence_days=payload.cadence_days, next_at=now()+payload.cadence_days*86400,
                last_source_at=now(), consent_at=now())
    db.add(row)
    db.commit()
    return {'id': row.id, 'scope': 'New approved platform source records only; inbox notifications, no email.'}


@router.delete('/watches/{watch_id}', status_code=204)
def remove_watch(watch_id: str, user=Depends(current_user), db=Depends(session)):
    row = db.get(Watch, watch_id)
    if not row or row.user_id != user.id:
        fail('NOT_FOUND', 'Watch not found.', 404)
    # Deletion does not require an active subscription.
    row.enabled = False
    db.commit()
    return Response(status_code=204)
