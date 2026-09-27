from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from ..auth import fresh_user, current_user, session, require_admin
from ..schemas import SourceCreate, RightsApproval
from ..models import Source, Audit
from ..services import rights, output_rights, counsel
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
                       'approved_by': s.approved_by} for s in db.scalars(select(Source).order_by(Source.created_at.desc()).limit(500))]}


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
    db.add(Audit(actor_id=user.id, action='source.disabled', target_id=row.id))
    db.commit()
    return {'disabled': True, 'dependent_outputs_require_review': True}


@router.get('/admin/audit')
def audit(user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    rows = db.scalars(select(Audit).order_by(Audit.id.desc()).limit(200)).all()
    return {'items': [{'id': x.id, 'actor_id': x.actor_id, 'action': x.action, 'target_id': x.target_id,
                       'detail': x.detail, 'created_at': x.created_at} for x in rows]}
