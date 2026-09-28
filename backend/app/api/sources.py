from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, or_
from ..auth import fresh_user, current_user, session, require_admin
from ..schemas import SourceCreate, RightsApproval
from ..models import Source, Audit
from ..services import rights, output_rights, counsel, editorial
from ..errors import fail

router = APIRouter(tags=['sources'])


@router.get('/sources')
def sources(q: str = '', framework: str = '', db=Depends(session)):
    query = select(Source).where(Source.enabled.is_(True), Source.reviewed.is_(True))
    if q:
        q = q[:200]
        query = query.where(or_(Source.title.ilike('%'+q+'%'), Source.publisher.ilike('%'+q+'%')))
    if framework:
        query = query.where(Source.framework == framework)
    return {'items': [rights.metadata(s) for s in db.scalars(query.order_by(Source.title).limit(200))]}


@router.get('/sources/{source_id}')
def source(source_id: str, db=Depends(session)):
    row = db.get(Source, source_id)
    if not row or not row.enabled or not row.reviewed:
        fail('NOT_FOUND', 'Source not found.', 404)
    text = row.text if rights.allowed(row, 'display_full') else None
    rows = output_rights.notices(db, [row])
    if text:
        output_rights.release(db, [row], {'text': text, 'source_attributions': rows})
        db.commit()
    return {**rights.metadata(row), 'text': text, 'source_attributions': rows}


@router.get('/topics')
def topics(db=Depends(session)):
    rows = db.scalars(select(Source).where(Source.kind == 'original_commentary', Source.enabled.is_(True),
                                           Source.reviewed.is_(True))).all()
    items, releases = [], []
    for source in rows:
        summary = (source.text or '')[:200] if rights.allowed(source, 'display_full') else ''
        notes = output_rights.notices(db, [source])
        if summary: releases.append(([source], {'text': summary, 'source_attributions': notes}))
        items.append({**rights.metadata(source), 'summary': summary, 'source_attributions': notes})
    output_rights.release_batch(db, releases)
    db.commit()
    return {'items': items}


@router.get('/admin/sources')
def admin_sources(user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    return {'items': [{**rights.metadata(s), 'policy': s.policy, 'rights_revision': rights.revision(s), 'created_by': s.created_by,
                       'approved_by': s.approved_by, 'review_revision': editorial.revision(s)} for s in db.scalars(select(Source).order_by(Source.created_at.desc()).limit(500))]}


@router.post('/admin/sources', status_code=201)
def submit_source(payload: SourceCreate, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    # References are never silently turned into a license. Legal evidence belongs in a restricted system.
    data = payload.model_dump(mode='json')
    if payload.text:
        # An independent rights decision does not professionally approve the new prose.
        data['policy']['requires_technical_review'] = True
        data['policy']['technical_review_status'] = 'unreviewed'
    row = Source(**data, created_by=user.id, reviewed=False)
    db.add(row)
    db.flush()
    db.add(Audit(actor_id=user.id, action='source.submitted', target_id=row.id))
    db.commit()
    return {**rights.metadata(row), 'status': 'awaiting_independent_approval'}


@router.post('/admin/sources/{source_id}/approve')
def approve_source(source_id: str, payload: RightsApproval, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user, approve=True)
    row = counsel.lock_source(db, source_id)
    if not row:
        fail('NOT_FOUND', 'Source not found.', 404)
    if row.created_by == user.id:
        fail('SEPARATION_OF_DUTIES', 'Another authorized reviewer must approve this source.', 403)
    if (payload.expected_policy_version != row.policy_version
            or payload.expected_rights_revision != rights.revision(row)):
        fail('REVISION_CONFLICT', 'Reload the source: the rights revision changed.', 409)
    if row.policy.get('basis') == 'reviewed_use':
        counsel.activate(db, row, user.id)
    row.reviewed, row.approved_by = True, user.id
    row.policy_version += 1  # Previously saved evidence must not revive after a new approval.
    rights.record_approval(row, user.id)
    db.add(Audit(actor_id=user.id, action='source.approved', target_id=row.id,
                 detail={'policy_version': row.policy_version, 'rights_revision': rights.revision(row)}))
    db.commit()
    return rights.metadata(row)


@router.post('/admin/sources/{source_id}/disable')
def disable_source(source_id: str, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    row = counsel.lock_source(db, source_id)
    if not row:
        fail('NOT_FOUND', 'Source not found.', 404)
    row.enabled, row.policy_version = False, row.policy_version+1
    from ..services import source_search
    source_search.remove(db,row,user.id)
    db.add(Audit(actor_id=user.id, action='source.disabled', target_id=row.id))
    db.commit()
    return {'disabled': True, 'dependent_outputs_require_review': True}


@router.get('/admin/audit')
def audit(user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    rows = db.scalars(select(Audit).order_by(Audit.id.desc()).limit(200)).all()
    return {'items': [{'id': x.id, 'actor_id': x.actor_id, 'action': x.action, 'target_id': x.target_id,
                       'detail': x.detail, 'created_at': x.created_at} for x in rows]}


@router.get('/admin/sources/{source_id}/search-index')
def search_index_status(source_id: str,user=Depends(current_user),db=Depends(session)):
    from ..models import SourceSearchIndex
    from ..services import source_search
    require_admin(user)
    row=db.get(Source,source_id)
    if not row:fail('NOT_FOUND','Source not found.',404)
    entry=db.get(SourceSearchIndex,source_id)
    return {'source_id':source_id,'expected_revision':source_search.revision(row),
        'stored':entry is not None,'current':source_search.current(row,entry),
        'index_version':entry.index_version if entry else None,
        'global_index_allowed':source_search.index_allowed(row)}


class IndexBuild(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision:str=Field(pattern=r'^[0-9a-f]{64}$')


@router.post('/admin/sources/{source_id}/search-index')
def build_search_index(source_id:str,payload:IndexBuild,user=Depends(fresh_user),db=Depends(session)):
    from ..services import source_search
    require_admin(user)
    row=counsel.lock_source(db,source_id)
    if not row:fail('NOT_FOUND','Source not found.',404)
    entry=source_search.rebuild(db,row,payload.expected_revision,user.id)
    db.commit()
    return {'source_id':source_id,'revision':entry.revision,'index_version':entry.index_version,'indexed':True}


@router.delete('/admin/sources/{source_id}/search-index')
def delete_search_index(source_id:str,user=Depends(fresh_user),db=Depends(session)):
    from ..services import source_search
    require_admin(user)
    row=counsel.lock_source(db,source_id)
    if not row:fail('NOT_FOUND','Source not found.',404)
    source_search.remove(db,row,user.id);db.commit()
    return {'removed':True,'source_id':source_id}


class CleanupAdvance(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_sequence:int=Field(strict=True,ge=0)


@router.post('/admin/search-index/sweeps')
def start_index_cleanup(request_key:str=Header(alias='Idempotency-Key',min_length=16,max_length=200),
                        user=Depends(fresh_user),db=Depends(session)):
    from ..services import index_cleanup
    require_admin(user)
    sweep=index_cleanup.start(db,user.id,request_key);db.commit()
    return index_cleanup.status(sweep)


@router.get('/admin/search-index/sweeps/{sweep_id}')
def index_cleanup_status(sweep_id:str,user=Depends(current_user),db=Depends(session)):
    from ..models import SearchIndexSweep
    from ..services import index_cleanup
    require_admin(user)
    sweep=db.get(SearchIndexSweep,sweep_id)
    if not sweep:fail('NOT_FOUND','Index cleanup sweep not found.',404)
    return index_cleanup.status(sweep)


@router.post('/admin/search-index/sweeps/{sweep_id}/advance')
def advance_index_cleanup(sweep_id:str,payload:CleanupAdvance,user=Depends(fresh_user),db=Depends(session)):
    from ..services import index_cleanup
    require_admin(user)
    sweep=index_cleanup.advance(db,sweep_id,payload.expected_sequence,user.id);db.commit()
    return index_cleanup.status(sweep)


@router.get('/admin/search-index/sweeps/{sweep_id}/receipts')
def index_cleanup_receipts(sweep_id:str,after:int=Query(default=0,ge=0),user=Depends(current_user),db=Depends(session)):
    from ..models import SearchIndexSweep
    from ..sec_core.core import canonical,digest
    require_admin(user)
    if not db.get(SearchIndexSweep,sweep_id):fail('NOT_FOUND','Index cleanup sweep not found.',404)
    rows=list(db.scalars(select(Audit).where(Audit.target_id==sweep_id,
        Audit.action=='source.index_cleanup_batch',Audit.id>after).order_by(Audit.id).limit(50)))
    for row in rows:
        if row.detail.get('receipt_sha256')!=digest(canonical(row.detail.get('receipt'))):
            fail('CLEANUP_RECEIPT_INTEGRITY','Cleanup receipt integrity check failed.',409)
    return {'items':[{'audit_id':row.id,**row.detail} for row in rows],
            'next_after':rows[-1].id if len(rows)==50 else None}


@router.get('/admin/search-index/inventory')
def search_index_inventory(user=Depends(current_user),db=Depends(session)):
    from sqlalchemy import func
    from ..models import SourceSearchIndex
    require_admin(user)
    return {'stored_entries':db.scalar(select(func.count()).select_from(SourceSearchIndex)),
        'current_entries':None,'approval_granted':False,
        'notice':'Stored entries can be stale or revoked. Current eligibility is checked per source and during cleanup; this count does not establish corpus completeness.'}


@router.get('/admin/search-index/sweeps')
def list_index_cleanup(before:str=Query(default='',max_length=36),user=Depends(current_user),db=Depends(session)):
    from sqlalchemy import and_
    from ..models import SearchIndexSweep
    from ..services import index_cleanup
    require_admin(user)
    query=select(SearchIndexSweep)
    if before:
        cursor=db.get(SearchIndexSweep,before)
        if not cursor:fail('NOT_FOUND','Cleanup history cursor not found. Reload the list.',404)
        query=query.where(or_(SearchIndexSweep.started_at<cursor.started_at,
            and_(SearchIndexSweep.started_at==cursor.started_at,SearchIndexSweep.id<cursor.id)))
    rows=list(db.scalars(query.order_by(SearchIndexSweep.started_at.desc(),SearchIndexSweep.id.desc()).limit(21)))
    return {'items':[index_cleanup.status(row) for row in rows[:20]],
            'next_before':rows[19].id if len(rows)>20 else None}
