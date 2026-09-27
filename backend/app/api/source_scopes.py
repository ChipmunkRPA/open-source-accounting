"""Operator-controlled source entitlement verification; ordinary accounts cannot self-assign."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from ..auth import current_user, fresh_user, session, require_admin
from ..models import Source, SourceScopeGrant, Audit, now
from ..scope_schemas import ScopeSubmission, ScopeApproval, ScopeRevocation
from ..services import source_scopes as scopes, counsel, rights
from ..errors import fail

router = APIRouter(tags=['source entitlements'])


@router.get('/admin/sources/{source_id}/scope-grants')
def grants(source_id: str, user=Depends(current_user), db=Depends(session)):
    require_admin(user)
    source = db.get(Source, source_id)
    if not source: fail('NOT_FOUND', 'Source not found.', 404)
    rows = db.scalars(select(SourceScopeGrant).where(SourceScopeGrant.source_id == source_id)
        .order_by(SourceScopeGrant.submitted_at.desc(), SourceScopeGrant.id).limit(200)).all()
    return {'source': {**rights.metadata(source), 'policy': source.policy, 'rights_revision': rights.revision(source)},
            'items': [scopes.serialize(row) for row in rows]}


@router.post('/admin/sources/{source_id}/scope-grants', status_code=201)
def submit(source_id: str, payload: ScopeSubmission, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    source = counsel.lock_source(db, source_id)
    row = scopes.submit(db, source, payload, user.id)
    db.commit()
    return scopes.serialize(row)


def locked_record(db, source_id, record_id, expected):
    row = db.scalar(select(SourceScopeGrant).where(SourceScopeGrant.id == record_id,
        SourceScopeGrant.source_id == source_id).with_for_update().execution_options(populate_existing=True))
    if not row: fail('NOT_FOUND', 'Scope grant not found.', 404)
    if row.record_sha256 != expected:
        fail('REVISION_CONFLICT', 'Reload the exact scope record.', 409)
    return row


@router.post('/admin/sources/{source_id}/scope-grants/{record_id}/approve')
def approve(source_id: str, record_id: str, payload: ScopeApproval, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user, approve=True)
    source = counsel.lock_source(db, source_id)
    row = locked_record(db, source_id, record_id, payload.expected_record_sha256)
    if user.id in {row.submitted_by, row.subject_user_id, source.created_by}:
        fail('SEPARATION_OF_DUTIES', 'An independent authorized reviewer must verify this assignment.', 403)
    if (row.status != 'pending'
            or row.record_sha256 != scopes.fingerprint(source.id, row.submitted_by, row.proposal)):
        fail('REVISION_CONFLICT', 'The grant changed or has already been decided.', 409)
    proposal = ScopeSubmission.model_validate(row.proposal)
    scopes.validate_proposal(source, proposal)
    if (proposal.subject_user_id != row.subject_user_id or proposal.workspace_id != row.workspace_id
            or not scopes.member(db, row.workspace_id, row.subject_user_id) or proposal.expires_at <= now()):
        fail('REVISION_CONFLICT', 'The member or verification interval changed.', 409)
    old = db.scalars(select(SourceScopeGrant).where(SourceScopeGrant.source_id == source_id,
        SourceScopeGrant.subject_user_id == row.subject_user_id, SourceScopeGrant.workspace_id == row.workspace_id,
        SourceScopeGrant.status == 'approved').with_for_update()).all()
    for prior in old:
        prior.status = 'superseded'
        db.add(Audit(actor_id=user.id, action='source_scope.superseded', target_id=prior.id,
                     detail={'replacement_id': row.id}))
    db.flush()  # Release partial unique index before activating the replacement.
    row.status, row.approved_by, row.approved_at = 'approved', user.id, now()
    db.add(Audit(actor_id=user.id, action='source_scope.approved', target_id=row.id,
                 detail={'source_id': source.id, 'record_sha256': row.record_sha256}))
    db.commit()
    return scopes.serialize(row)


@router.post('/admin/sources/{source_id}/scope-grants/{record_id}/revoke')
def revoke(source_id: str, record_id: str, payload: ScopeRevocation, user=Depends(fresh_user), db=Depends(session)):
    require_admin(user)
    counsel.lock_source(db, source_id)
    row = locked_record(db, source_id, record_id, payload.expected_record_sha256)
    if row.status != 'revoked':
        row.status, row.revoked_by, row.revoked_at = 'revoked', user.id, now()
        row.revocation_reason = payload.reason
        db.add(Audit(actor_id=user.id, action='source_scope.revoked', target_id=row.id,
                     detail={'source_id': source_id, 'reason': payload.reason}))
    db.commit()
    return scopes.serialize(row)
