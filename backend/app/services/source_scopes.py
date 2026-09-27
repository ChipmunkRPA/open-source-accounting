"""Rechecked source-specific entitlements. No client value becomes a verified scope."""
import hashlib
import json
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import object_session
from ..models import SourceScopeGrant, Membership, Audit, now
from ..scope_schemas import ScopeSubmission
from ..errors import fail

PROTECTED = frozenset({'seat_id', 'jurisdiction', 'retention'})


class RuntimeContext(dict):
    """Internal request/worker context; never deserialize this from user JSON."""
    def __init__(self, values, db, actor_id, settings, require_edit=False):
        super().__init__(values)
        self.db, self.actor_id, self.settings, self.require_edit = db, actor_id, settings, require_edit


def fingerprint(source_id, actor_id, proposal):
    return hashlib.sha256(json.dumps({'source_id': source_id, 'submitted_by': actor_id,
        'proposal': proposal}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def member(db, workspace_id, user_id):
    return db.scalar(select(Membership).where(Membership.workspace_id == workspace_id,
        Membership.user_id == user_id).execution_options(populate_existing=True))


def validate_proposal(source, payload):
    from .rights import revision
    if (not source.enabled or not source.reviewed
            or payload.expected_policy_version != source.policy_version
            or payload.expected_rights_revision != revision(source)
            or source.policy.get('rights_reviewed_revision') != revision(source)):
        fail('REVISION_CONFLICT', 'An approved exact source revision is required.', 409)
    values = payload.values.model_dump(exclude_none=True)
    scope = source.policy.get('scope', {})
    if set(values) != (set(scope) & PROTECTED):
        fail('SCOPE_MISMATCH', 'Verify every protected scope required by this source.', 422)
    if any(value not in scope[key] for key, value in values.items()):
        fail('SCOPE_MISMATCH', 'The verified value is outside the approved source policy.', 422)
    if any(source.policy.get(op) is not True for op in payload.operations):
        fail('SCOPE_MISMATCH', 'An entitlement cannot grant a prohibited source operation.', 422)
    context = {'workspace_id': payload.workspace_id, 'route': 'hosted_agent', 'audience': 'workspace',
               'provider': payload.provider, 'region': payload.region, **values}
    if any(context.get(key) not in allowed for key, allowed in scope.items()):
        fail('SCOPE_MISMATCH', 'The assignment does not match the approved runtime scope.', 422)


def submit(db, source, payload, actor_id):
    validate_proposal(source, payload)
    if not member(db, payload.workspace_id, payload.subject_user_id):
        fail('SCOPE_MEMBER_REQUIRED', 'An existing workspace member is required.', 422)
    if payload.expires_at <= now():
        fail('SCOPE_EXPIRED', 'The verification interval has expired.', 422)
    proposal = payload.model_dump(mode='json')
    row = SourceScopeGrant(source_id=source.id, subject_user_id=payload.subject_user_id,
        workspace_id=payload.workspace_id, proposal=proposal, submitted_by=actor_id,
        record_sha256=fingerprint(source.id, actor_id, proposal))
    db.add(row); db.flush()
    db.add(Audit(actor_id=actor_id, action='source_scope.submitted', target_id=row.id,
                 detail={'source_id': source.id, 'record_sha256': row.record_sha256}))
    return row


def resolve(source, action, context):
    """Resolve all protected values from one fresh assignment; never union partial grants."""
    db = object_session(source)
    if not isinstance(context, RuntimeContext) or context.db is not db or context.settings is None:
        return None
    if context.get('route') != 'hosted_agent' or context.get('audience') != 'workspace':
        return None
    membership = member(db, context.get('workspace_id'), context.actor_id)
    if not membership or (context.require_edit and membership.role not in {'owner', 'editor'}):
        return None
    rows = db.scalars(select(SourceScopeGrant).where(SourceScopeGrant.source_id == source.id,
        SourceScopeGrant.subject_user_id == context.actor_id,
        SourceScopeGrant.workspace_id == context.get('workspace_id'), SourceScopeGrant.status == 'approved')
        .execution_options(populate_existing=True)).all()
    if len(rows) != 1: return None
    row = rows[0]
    if row.record_sha256 != fingerprint(source.id, row.submitted_by, row.proposal): return None
    try:
        proposal = ScopeSubmission.model_validate(row.proposal)
        validate_proposal(source, proposal)
    except (ValueError, TypeError): return None
    except HTTPException: return None
    if (not row.approved_by or row.approved_by in {row.submitted_by, row.subject_user_id, source.created_by}
            or row.approved_at is None or row.revoked_at is not None
            or proposal.subject_user_id != row.subject_user_id or proposal.workspace_id != row.workspace_id
            or action not in proposal.operations or not proposal.effective_at <= now() < proposal.expires_at):
        return None
    settings = context.settings
    if ((proposal.provider, proposal.project, proposal.region, proposal.model_id) !=
            (settings.model_provider, settings.google_cloud_project, settings.model_location, settings.model_id)
            or context.get('provider') != settings.model_provider or context.get('region') != settings.model_location):
        return None
    return {**context, **proposal.values.model_dump(exclude_none=True)}


def serialize(row):
    return {name: getattr(row, name) for name in ('id', 'source_id', 'subject_user_id', 'workspace_id',
        'proposal', 'record_sha256', 'submitted_by', 'submitted_at', 'status', 'approved_by',
        'approved_at', 'revoked_by', 'revoked_at', 'revocation_reason')}
