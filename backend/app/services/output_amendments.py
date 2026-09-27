"""Atomic output-term amendments. A transition never grants source-body rights."""
import hashlib
from sqlalchemy import select
from ..models import Source, OutputBudget, OutputAmendment, Audit, now
from ..schemas import OutputControl
from ..output_amendment_schemas import OutputAmendmentSubmission
from ..errors import fail
from . import rights, output_rights, counsel


def digest(value):
    return hashlib.sha256(output_rights.canonical(value).encode()).hexdigest()


def fingerprint(group, actor, proposal):
    return digest({'group_id': group, 'submitted_by': actor, 'proposal': proposal})


def sources(db, group, *, lock=False):
    query = select(Source).where(Source.policy['output_control']['group_id'].as_string() == group).order_by(Source.id)
    rows = db.scalars(query).all()
    if not rows: fail('NOT_FOUND', 'No registered sources belong to this work group.', 404)
    if lock:
        rows = [counsel.lock_source(db, source.id) for source in rows]
        if any((row.policy.get('output_control') or {}).get('group_id') != group for row in rows):
            fail('REVISION_CONFLICT', 'Work-group membership changed.', 409)
    return rows


def snapshot(rows):
    return [{'source_id': row.id, 'policy_version': row.policy_version, 'rights_revision': rights.revision(row),
             'title': row.title, 'publisher': row.publisher, 'version': row.version_label,
             'created_by': row.created_by, 'enabled': row.enabled, 'reviewed': row.reviewed,
             'output_control': row.policy.get('output_control')} for row in rows]


def budget_state(db, group, rows, *, lock=False):
    budget = db.get(OutputBudget, group)
    if budget is None:
        try: controls = [OutputControl.model_validate(row.policy['output_control']).model_dump(mode='json') for row in rows]
        except (ValueError, TypeError, KeyError): fail('OUTPUT_POLICY_REQUIRED', 'Review valid initial source output terms first.', 409)
        hashes = {digest(control) for control in controls}
        if len(hashes) != 1: fail('OUTPUT_POLICY_CONFLICT', 'Initial source terms disagree.', 409)
        current_hash = hashes.pop()
        if not lock:
            return {'limits_sha256': current_hash, 'terms_revision': 1, 'released_chars': 0}
        if db.bind.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        db.execute(insert(OutputBudget).values(group_id=group, limits_sha256=current_hash, released_chars=0,
                    terms_revision=1).on_conflict_do_nothing(index_elements=['group_id']))
    if lock:
        budget = db.scalar(select(OutputBudget).where(OutputBudget.group_id == group).with_for_update()
                           .execution_options(populate_existing=True))
    return budget


def preview(db, group):
    rows = sources(db, group)
    items = snapshot(rows)
    budget = budget_state(db, group, rows)
    state = budget if isinstance(budget, dict) else {key: getattr(budget, key) for key in (
        'limits_sha256', 'terms_revision', 'released_chars')}
    return {**state, 'group_id': group, 'sources_sha256': digest(items), 'sources': items}


def submit(db, group, payload, actor_id):
    if payload.new_control.group_id != group:
        fail('OUTPUT_GROUP_IMMUTABLE', 'An amendment cannot move a work to a new counter.', 422)
    if payload.review_expires_at <= now(): fail('REVIEW_EXPIRED', 'The review deadline has passed.', 422)
    rows = sources(db, group, lock=True)
    items = snapshot(rows)
    budget = budget_state(db, group, rows, lock=True)
    if (payload.expected_limits_sha256 != budget.limits_sha256
            or payload.expected_terms_revision != budget.terms_revision
            or payload.expected_sources_sha256 != digest(items)):
        fail('REVISION_CONFLICT', 'Reload the work group before proposing new terms.', 409)
    if digest(payload.new_control.model_dump(mode='json')) == budget.limits_sha256:
        fail('OUTPUT_TERMS_UNCHANGED', 'The proposed terms are unchanged.', 422)
    proposal = {**payload.model_dump(mode='json'), 'sources': items, 'released_chars_at_submission': budget.released_chars}
    row = OutputAmendment(group_id=group, proposal=proposal, submitted_by=actor_id,
                          record_sha256=fingerprint(group, actor_id, proposal))
    db.add(row); db.flush()
    db.add(Audit(actor_id=actor_id, action='output_amendment.submitted', target_id=row.id,
                 detail={'group_id': group, 'record_sha256': row.record_sha256}))
    return row


def review(db, group, record_id, payload, actor_id):
    rows = sources(db, group, lock=True)
    budget = budget_state(db, group, rows, lock=True)
    row = db.scalar(select(OutputAmendment).where(OutputAmendment.id == record_id,
        OutputAmendment.group_id == group).with_for_update().execution_options(populate_existing=True))
    if not row: fail('NOT_FOUND', 'Amendment not found.', 404)
    if actor_id == row.submitted_by or any(source.created_by == actor_id for source in rows):
        fail('SEPARATION_OF_DUTIES', 'A different authorized reviewer must review these terms.', 403)
    if (row.status != 'pending' or row.record_sha256 != payload.expected_record_sha256
            or row.record_sha256 != fingerprint(group, row.submitted_by, row.proposal)):
        fail('REVISION_CONFLICT', 'The amendment changed or has already been decided.', 409)
    data = {key: value for key, value in row.proposal.items() if key not in {'sources', 'released_chars_at_submission'}}
    proposal = OutputAmendmentSubmission.model_validate(data)
    if payload.decision == 'reject':
        row.status, row.reviewed_by, row.reviewed_at = 'rejected', actor_id, now()
        db.add(Audit(actor_id=actor_id, action='output_amendment.rejected', target_id=row.id))
        return row
    if (proposal.new_control.group_id != group or proposal.review_expires_at <= now()
            or proposal.expected_limits_sha256 != budget.limits_sha256
            or proposal.expected_terms_revision != budget.terms_revision
            or proposal.expected_sources_sha256 != digest(snapshot(rows))
            or payload.expected_released_chars != budget.released_chars):
        fail('REVISION_CONFLICT', 'Source revisions, terms, usage or review deadline changed. Reload before applying.', 409)
    new_control = proposal.new_control.model_dump(mode='json')
    budget.limits_sha256 = digest(new_control)
    budget.terms_revision += 1
    # Deliberately do not update released_chars or any OutputRelease row.
    for source in rows:
        source.policy = {**source.policy, 'output_control': new_control}
        source.policy_version += 1
        source.reviewed = False
    row.status, row.reviewed_by, row.reviewed_at = 'applied', actor_id, now()
    row.released_chars_at_apply, row.applied_terms_revision = budget.released_chars, budget.terms_revision
    db.add(Audit(actor_id=actor_id, action='output_amendment.applied', target_id=row.id, detail={
        'group_id': group, 'terms_revision': budget.terms_revision, 'released_chars': budget.released_chars,
        'source_count': len(rows)}))
    return row


def serialize(row):
    return {key: getattr(row, key) for key in ('id', 'group_id', 'proposal', 'record_sha256', 'submitted_by',
        'submitted_at', 'status', 'reviewed_by', 'reviewed_at', 'released_chars_at_apply', 'applied_terms_revision')}
