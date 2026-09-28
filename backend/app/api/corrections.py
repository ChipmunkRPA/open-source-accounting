"""Private administrative triage. Resolution never grants rights or restores evidence."""
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select, func
from ..auth import current_user, fresh_user, session, require_admin, settings
from ..models import CorrectionCase, CorrectionEvent, Source, Audit
from ..correction_schemas import CorrectionCreate, CorrectionAction
from ..services import counsel, editorial, idempotency, dependency_report
from ..errors import fail

router=APIRouter(tags=['corrections'])


def serialize(row):
    return {k:getattr(row,k) for k in ('id','source_id','kind','status','version','policy_version','review_revision','created_at')}


def event(db,row,source,user,action,note):
    db.add(CorrectionEvent(case_id=row.id,version=row.version,actor_id=user.id,action=action,note=note,
                           source_policy_version=source.policy_version))
    db.add(Audit(actor_id=user.id,action='correction.'+action,target_id=row.id,
                 detail={'source_id':source.id,'case_version':row.version,'policy_version':source.policy_version}))


@router.get('/admin/corrections')
def listing(status: Literal['open','triaged','resolved','dismissed'] | None=None,
            offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),
            user=Depends(current_user),db=Depends(session)):
    require_admin(user)
    q=select(CorrectionCase)
    if status:q=q.where(CorrectionCase.status==status)
    total=db.scalar(select(func.count()).select_from(q.subquery()))
    return {'total':total,'items':[serialize(r) for r in db.scalars(q.order_by(CorrectionCase.created_at.desc(),CorrectionCase.id).offset(offset).limit(limit))]}


@router.get('/admin/corrections/{case_id}')
def detail(case_id:str,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100),user=Depends(current_user),db=Depends(session)):
    require_admin(user)
    row=db.get(CorrectionCase,case_id)
    if not row:fail('NOT_FOUND','Correction case not found.',404)
    source=db.get(Source,row.source_id)
    records=db.scalars(select(CorrectionEvent).where(CorrectionEvent.case_id==row.id).order_by(CorrectionEvent.version.desc()).offset(offset).limit(limit))
    return {**serialize(row),'source_enabled':source.enabled,'current_policy_version':source.policy_version,
            'source_changed':source.policy_version!=row.policy_version or editorial.revision(source)!=row.review_revision,
            'events':[{'version':r.version,'actor_id':r.actor_id,'action':r.action,'note':r.note,'source_policy_version':r.source_policy_version,'created_at':r.created_at} for r in records]}


@router.post('/admin/corrections',status_code=201)
def create(payload:CorrectionCreate,user=Depends(fresh_user),db=Depends(session),key:str|None=Header(None,alias='Idempotency-Key')):
    require_admin(user)
    source=counsel.lock_source(db,payload.source_id)
    if not source:fail('NOT_FOUND','Source not found.',404)
    receipt,replayed=idempotency.begin(db,user.id,'correction.create',key,payload.model_dump())
    if replayed:return receipt.response
    if source.policy_version!=payload.expected_policy_version or editorial.revision(source)!=payload.expected_review_revision:
        fail('REVISION_CONFLICT','Reload the source before opening the case.',409)
    row=CorrectionCase(source_id=source.id,kind=payload.kind,policy_version=source.policy_version,review_revision=editorial.revision(source))
    db.add(row);db.flush();event(db,row,source,user,'open',payload.note)
    receipt.response=serialize(row);db.commit();return receipt.response


@router.post('/admin/corrections/{case_id}/actions')
def action(case_id:str,payload:CorrectionAction,user=Depends(fresh_user),db=Depends(session)):
    require_admin(user)
    row=db.get(CorrectionCase,case_id)
    if not row:fail('NOT_FOUND','Correction case not found.',404)
    # Same source-first locking order as rights/review/disable writers.
    source=counsel.lock_source(db,row.source_id)
    row=db.scalar(select(CorrectionCase).where(CorrectionCase.id==case_id).with_for_update().execution_options(populate_existing=True))
    if row.version!=payload.expected_version:fail('REVISION_CONFLICT','Reload the case before acting.',409)
    allowed={'triage':{'open'},'resolve':{'triaged'},'dismiss':{'open','triaged'},'reopen':{'resolved','dismissed'},'disable':{'open','triaged'}}
    if row.status not in allowed[payload.action]:fail('INVALID_TRANSITION','This action is not available in the current case state.',409)
    if payload.action=='disable':
        if source.enabled:
            source.enabled=False;source.policy_version+=1
            db.add(Audit(actor_id=user.id,action='source.disabled',target_id=source.id,detail={'case_id':row.id}))
        row.status='triaged'
    else:row.status={'triage':'triaged','resolve':'resolved','dismiss':'dismissed','reopen':'open'}[payload.action]
    row.version+=1;event(db,row,source,user,payload.action,payload.note);db.commit()
    return {**serialize(row),'source_enabled':source.enabled,'current_policy_version':source.policy_version}


@router.get('/admin/corrections/{case_id}/impact')
def impact(case_id:str,user=Depends(current_user),db=Depends(session),config=Depends(settings)):
    require_admin(user)
    row=db.get(CorrectionCase,case_id)
    if not row:fail('NOT_FOUND','Correction case not found.',404)
    return dependency_report.report(db,config,affected_by=row.source_id)
