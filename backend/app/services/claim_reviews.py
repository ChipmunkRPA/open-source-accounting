"""Exact, independently attested claim review. Never an automated accounting approval."""
from fastapi import HTTPException
from sqlalchemy import select, update
from ..models import Run, Evidence, Source, Document, User, Membership, RunClaimReview, Audit, now
from ..errors import fail
from ..schemas import Claim
from ..claim_review_schemas import ClaimDecision
from ..sec_core.core import canonical, digest
from . import rights, output_rights, authority_evidence, editorial

VERSION = 'claim-review-1'
MAX_EXPORT_BYTES = 2 * 1024 * 1024


def locked_run(db, run):
    # Same run-before-source order used by worker checkpoints; serialize sequences.
    if db.bind.dialect.name == 'sqlite':
        db.execute(update(Run).where(Run.id == run.id).values(revision=Run.revision))
    return db.scalar(select(Run).where(Run.id == run.id).with_for_update().execution_options(populate_existing=True))


def latest(db, run_id, claim_id):
    return db.scalar(select(RunClaimReview).where(RunClaimReview.run_id == run_id,
        RunClaimReview.claim_id == claim_id).order_by(RunClaimReview.sequence.desc()).limit(1))


def binding(db, run, claim_id):
    if run.state != 'completed_with_limitations' or not run.result:
        fail('NO_RESULT', 'Claim review requires a completed retained draft.', 409)
    claims = [c for c in run.result.get('claims', []) if c.get('id') == claim_id]
    if len(claims) != 1:
        fail('CLAIM_UNAVAILABLE', 'Choose one uniquely identified claim in the current result.', 404)
    claim = Claim.model_validate(claims[0]).model_dump(mode='json')
    if len(set(claim['evidence_ids'])) != len(claim['evidence_ids']):
        fail('CLAIM_EVIDENCE', 'Duplicate evidence bindings require correction.', 409)
    rights.run_artifact_access(db, run, 'quote')
    passages = []
    authors = {run.user_id}
    for eid in claim['evidence_ids']:
        e = db.get(Evidence, eid, populate_existing=True)
        if not e or e.run_id != run.id or not e.text or e.access == 'reference_only':
            fail('CLAIM_EVIDENCE', 'Each cited passage must contain available retained evidence.', 409)
        context = rights.runtime_context(db, run)
        if not rights.evidence_allowed(db, e, 'quote', context=context):
            fail('SOURCE_CHANGED', 'A cited passage is no longer available.', 409)
        s = db.get(Source, e.source_id, populate_existing=True) if e.source_id else None
        d = db.get(Document, e.document_id, populate_existing=True) if e.document_id else None
        if s:authors.add(s.created_by)
        if d:authors.add(d.uploaded_by)
        passages.append({'evidence_id': e.id, 'source_id': e.source_id, 'document_id': e.document_id,
            'title': e.title, 'locator': e.locator, 'text': e.text, 'text_sha256': digest(e.text),
            'access': e.access, 'source_kind': e.source_kind, 'policy_version': e.policy_version,
            'extraction_context': e.extraction_context,
            'source_revision': editorial.revision(s) if s else None,
            'source_version': s.version_label if s else None,
            'document_checksum': d.checksum if d else None})
    body = {'version': VERSION, 'run_id': run.id, 'workspace_id': run.workspace_id, 'claim': claim,
        'run_revision': run.revision, 'execution_id': run.execution_id, 'result_sha256': digest(canonical(run.result)),
        'context_sha256': digest(canonical({'context': run.context, 'facts': run.facts, 'inputs': run.inputs,
                                           'documents': run.document_ids, 'question': run.question})),
        'model_id': run.model_id, 'prompt_version': run.result.get('prompt_version'),
        'passages': passages, 'relationship_snapshots': authority_evidence.packets(db, run, 'quote')}
    return body, digest(canonical(body)), authors - {None}


def retained_binding(body):
    """Preserve immutable locators/versions/hashes without duplicating passage text."""
    return {**{k: v for k, v in body.items() if k not in {'claim', 'passages'}},
        'claim_sha256': digest(canonical(body['claim'])),
        'passages': [{k: v for k, v in p.items() if k != 'text'} for p in body['passages']]}


def valid_record(db, row):
    if not row or not row.reviewer_id or digest(canonical(row.payload)) != row.payload_sha256:
        return False
    p = row.payload
    try:decision = ClaimDecision.model_validate(p['decision'])
    except (KeyError, TypeError, ValueError):return False
    reviewer = db.get(User, row.reviewer_id, populate_existing=True)
    run = db.get(Run, row.run_id)
    member = db.get(Membership, (run.workspace_id, row.reviewer_id), populate_existing=True) if run else None
    return bool(reviewer and reviewer.role == 'technical_reviewer' and p.get('version') == VERSION
        and member and member.role in {'owner', 'editor', 'reviewer'}
        and p.get('reviewer_id') == row.reviewer_id and p.get('run_id') == row.run_id
        and p.get('claim_id') == row.claim_id and decision.expected_revision == row.revision
        and decision.expected_sequence == row.sequence-1)


def summary(db, run, claim_id):
    row = latest(db, run.id, claim_id)
    valid = valid_record(db, row)
    current, revision = False, None
    try:
        body, revision, authors = binding(db, run, claim_id)
        current = bool(valid and row.revision == revision and row.reviewer_id not in authors
            and row.payload.get('binding') == retained_binding(body)
            and row.payload['decision']['decision'] != 'revoked'
            and row.payload['decision']['expires_at'] > now())
    except HTTPException:
        pass
    return {'claim_id': claim_id, 'revision': revision, 'sequence': row.sequence if row else 0,
        'record_id': row.id if row else None, 'record_revision': row.revision if row else None,
        'decision': row.payload['decision']['decision'] if valid else 'unreviewed_or_invalid',
        'current': current, 'reviewer_id': row.reviewer_id if valid else None,
        'created_at': row.created_at if row else None, 'source_rights_granted': False,
        'deliverable_approval_granted': False, 'qualification_basis': 'assigned_role_and_reviewer_attestation'}


def packet(db, run, claim_id, *, export_revision=None, export_sequence=None):
    run = locked_run(db, run)
    exporting = export_revision is not None
    if exporting:
        rights.run_artifact_access(db, run, 'export')
    body, revision, _ = binding(db, run, claim_id)
    status = summary(db, run, claim_id)
    if exporting and (export_revision != revision or export_sequence != status['sequence']):
        fail('REVISION_CONFLICT', 'Reload the exact claim packet and review sequence before exporting.', 409)
    row = latest(db, run.id, claim_id)
    result = {'version': VERSION, 'revision': revision, 'binding': body, 'status': status,
        'review': row.payload['decision'] if row and status['current'] else None,
        'notice': 'Human claim assessment only. No source rights, professional credential verification or whole-deliverable approval is granted.'}
    sources = output_rights.run_sources(db, run)
    result['source_attributions'] = output_rights.notices(db, sources)
    if exporting:
        result['export'] = {'version': 'claim-review-export-1', 'format': 'json',
            'permission_checked': 'export', 'current_at_release_only': True,
            'notice': 'Recheck the live record before relying on this file. Downloaded copies cannot reflect later revocation.'}
        if len(canonical(result)) > MAX_EXPORT_BYTES:
            fail('EXPORT_LIMIT', 'The claim packet exceeds the bounded export size.', 413)
    output_rights.release(db, sources, result)
    authority_evidence.release_check(db, run)
    if exporting:
        rights.run_artifact_access(db, run, 'export')
    if binding(db, run, claim_id)[1] != revision or summary(db, run, claim_id) != status:
        fail('SOURCE_CHANGED', 'Claim, evidence or review status changed before packet release.', 409)
    return result


def decide(db, run, claim_id, payload, reviewer_id):
    run = locked_run(db, run)
    row = latest(db, run.id, claim_id)
    sequence = row.sequence if row else 0
    if payload.expected_sequence != sequence:
        fail('REVISION_CONFLICT', 'Reload the current claim review sequence.', 409)
    if run.user_id == reviewer_id:
        fail('SEPARATION_OF_DUTIES', 'An independent reviewer must assess the claim.', 403)
    if payload.decision == 'revoked':
        if not row or payload.expected_revision != row.revision:
            fail('REVISION_CONFLICT', 'Revocation must identify the last reviewed revision.', 409)
        saved_binding = row.payload.get('binding')
    else:
        body, revision, authors = binding(db, run, claim_id)
        if reviewer_id in authors:
            fail('SEPARATION_OF_DUTIES', 'The reviewer must be independent of the run and cited input authors.', 403)
        if revision != payload.expected_revision:
            fail('REVISION_CONFLICT', 'Reload the exact claim and evidence packet.', 409)
        if {p.evidence_id for p in payload.passages} != {p['evidence_id'] for p in body['passages']}:
            fail('CLAIM_EVIDENCE', 'Assess every cited passage in the exact packet.', 422)
        if payload.expires_at <= now():
            fail('REVIEW_EXPIRED', 'Choose a future review expiry.', 422)
        # Retain hash bindings, not additional copies of source text in the ledger.
        sources = output_rights.run_sources(db, run)
        for source in sources:
            if not rights.allowed(source, 'store_text', context=rights.runtime_context(db, run)):
                fail('SOURCE_POLICY_BLOCK', 'Current source storage permission is required for review findings.', 403)
        saved_binding = retained_binding(body)
        output_rights.release(db, sources, {'review': payload.model_dump(mode='json'),
                                         'source_attributions': output_rights.notices(db, sources)})
        authority_evidence.release_check(db, run)
        if binding(db, run, claim_id)[1] != revision:
            fail('SOURCE_CHANGED', 'Claim or evidence changed before the decision was recorded.', 409)
    body = {'version': VERSION, 'run_id': run.id, 'claim_id': claim_id,
            'reviewer_id': reviewer_id, 'decision': payload.model_dump(mode='json'), 'binding': saved_binding}
    row = RunClaimReview(run_id=run.id, claim_id=claim_id, sequence=sequence+1,
        revision=payload.expected_revision, reviewer_id=reviewer_id, payload=body, payload_sha256=digest(canonical(body)))
    db.add(row);db.flush()
    db.add(Audit(actor_id=reviewer_id, action='claim.reviewed', target_id=run.id,
        detail={'record_id': row.id, 'claim_id': claim_id, 'sequence': row.sequence, 'decision': payload.decision}))
    return summary(db, run, claim_id)
