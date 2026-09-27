"""Revision-bound independent counsel decisions, never an automatic fair-use exception."""
import hashlib
import json
from sqlalchemy import select
from sqlalchemy.orm import object_session
from ..models import CounselRecord, Source, Audit, now
from ..counsel_schemas import CounselSubmission
from ..errors import fail
from . import rights


def fingerprint(source_id, submitted_by, proposal):
    return hashlib.sha256(json.dumps({'source_id': source_id, 'submitted_by': submitted_by,
        'proposal': proposal}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_record(row, source, *, active):
    """Revalidate storage, binding, interval and separation at every protected operation."""
    if row.record_sha256 != fingerprint(row.source_id, row.submitted_by, row.proposal):
        return False
    try: proposal = CounselSubmission.model_validate(row.proposal)
    except (ValueError, TypeError): return False
    if (row.status != 'approved' or not row.reviewed_by or row.reviewed_at is None
            or row.reviewed_by in {row.submitted_by, source.created_by, source.approved_by}
            or row.source_id != source.id or row.revoked_at is not None
            or proposal.expected_rights_revision != rights.revision(source)
            or not proposal.effective_at <= now() < proposal.expires_at):
        return False
    expected = row.activated_policy_version if active else proposal.expected_policy_version
    if expected != source.policy_version:
        return False
    if active and row.activated_policy_version != proposal.expected_policy_version + 1:
        return False
    return proposal


def permitted(source, action):
    db = object_session(source)
    if db is None: return False
    # Refresh records even in a long-lived worker session: revocation must not use a cached row.
    rows = db.scalars(select(CounselRecord).where(CounselRecord.source_id == source.id,
        CounselRecord.status == 'approved').execution_options(populate_existing=True)).all()
    for row in rows:
        proposal = validate_record(row, source, active=True)
        if proposal and action in proposal.operations:
            return True
    return False


def lock_source(db, source_id):
    # All review/activation/revocation paths acquire source then record, in that order.
    from sqlalchemy import update
    if db.bind.dialect.name == 'sqlite':
        db.execute(update(Source).where(Source.id == source_id).values(policy_version=Source.policy_version))
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update()
                       .execution_options(populate_existing=True))
    if not source: fail('NOT_FOUND', 'Source not found.', 404)
    return source


def submit(db, source, payload, actor_id):
    if (source.policy.get('basis') != 'reviewed_use' or not source.enabled):
        fail('COUNSEL_SCOPE', 'Counsel records require an enabled reviewed-use source.', 409)
    if (payload.expected_policy_version != source.policy_version
            or payload.expected_rights_revision != rights.revision(source)):
        fail('REVISION_CONFLICT', 'Reload the exact source revision.', 409)
    grants = {op for op in rights.OPERATIONS if source.policy.get(op) is True}
    if set(payload.operations) != grants:
        fail('COUNSEL_SCOPE', 'Review every requested operation; change the source policy for a narrower request.', 422)
    scope = source.policy.get('scope', {})
    if not all(scope.get(key) for key in ('route', 'audience', 'jurisdiction')):
        fail('COUNSEL_SCOPE', 'Explicit route, audience and jurisdiction scope is required.', 422)
    if payload.evidence_ref != source.policy.get('license_evidence_ref'):
        fail('COUNSEL_SCOPE', 'The restricted evidence reference must match the source policy.', 422)
    if payload.expires_at <= now():
        fail('COUNSEL_EXPIRED', 'Submit a current or future review interval.', 422)
    proposal = payload.model_dump(mode='json')
    row = CounselRecord(source_id=source.id, submitted_by=actor_id, proposal=proposal,
                        record_sha256=fingerprint(source.id, actor_id, proposal))
    db.add(row); db.flush()
    db.add(Audit(actor_id=actor_id, action='counsel.submitted', target_id=row.id,
                 detail={'source_id': source.id, 'record_sha256': row.record_sha256}))
    return row


def activate(db, source, actor_id):
    """A rights approver activates an independently approved record in the same transaction."""
    candidates = db.scalars(select(CounselRecord).where(CounselRecord.source_id == source.id)
                           .with_for_update().execution_options(populate_existing=True)).all()
    grants = {op for op in rights.OPERATIONS if source.policy.get(op) is True}
    for row in candidates:
        proposal = validate_record(row, source, active=False)
        if (proposal and set(proposal.operations) == grants and row.reviewed_by != actor_id
                and row.activated_policy_version is None):
            row.activated_policy_version = source.policy_version + 1
            db.add(Audit(actor_id=actor_id, action='counsel.activated', target_id=row.id,
                         detail={'source_id': source.id, 'policy_version': row.activated_policy_version}))
            return
    fail('COUNSEL_REQUIRED', 'A current independent counsel decision for this exact revision is required.', 403)


def serialize(row):
    return {name: getattr(row, name) for name in ('id', 'source_id', 'proposal', 'record_sha256',
        'submitted_by', 'submitted_at', 'status', 'reviewed_by', 'reviewed_at',
        'activated_policy_version', 'revoked_by', 'revoked_at', 'revocation_reason')}
