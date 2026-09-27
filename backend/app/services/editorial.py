"""Immutable technical decisions, separate from rights and applicability reviews."""
import hashlib
from sqlalchemy.orm import object_session
from ..models import EditorialReview, Audit, now
from ..sec_core.core import canonical, digest
from ..errors import fail
from . import rights


def revision(source):
    policy = source.policy or {}
    # Applicability and rights decisions have their own gates. Technical review
    # binds identity, prose, references and exact citation/provenance metadata.
    sec = policy.get('sec_core', {})
    return digest(canonical({'title': source.title, 'publisher': source.publisher,
        'url': source.canonical_url, 'version': source.version_label, 'kind': source.kind,
        'framework': source.framework, 'text_sha256': hashlib.sha256((source.text or '').encode()).hexdigest(),
        'references': policy.get('content_reference_ids', []),
        'reference_snapshot': policy.get('content_reference_snapshot'),
        'provenance': {k: policy.get(k) for k in ('content_item_id','content_version','content_sha256',
            'intake_locator','intake_extraction_id','intake_artifact_id','content_references_sha256')},
        'sec_provenance': {k: v for k, v in sec.items() if not k.startswith('applicability_')
            and k not in {'effective_from','effective_to','public_available_at'}}}))


def references_current(source):
    """Original-library citation metadata must be captured; links are not evidence."""
    policy = source.policy or {}
    if not policy.get('content_item_id'):
        return True  # SEC/intake provenance is bound separately by revision().
    refs = policy.get('content_reference_snapshot')
    ids = policy.get('content_reference_ids', [])
    return bool(isinstance(refs, list) and refs and all(isinstance(r, dict) for r in refs)
                and len(ids) == len(set(ids))
                and [r.get('id') for r in refs] == sorted(ids)
                and policy.get('content_references_sha256') == digest(canonical(refs)))


def current(source):
    db = object_session(source)
    record_id = (source.policy or {}).get('technical_review_record_id')
    if not db or not record_id:
        return False
    row = db.get(EditorialReview, record_id)
    return bool(references_current(source) and row and row.source_id == source.id and row.reviewer_id and row.decision == 'approved'
                and row.expires_at > now() and row.review_revision == revision(source)
                and row.payload_sha256 == digest(canonical(row.payload))
                and row.payload.get('reviewer_id') == row.reviewer_id
                and row.payload.get('decision') == row.decision
                and row.payload.get('expires_at') == row.expires_at
                and row.payload.get('expected_review_revision') == row.review_revision)


def record(db, source, payload, reviewer_id):
    if source.created_by == reviewer_id:
        fail('SEPARATION_OF_DUTIES', 'You cannot technically review your own submission.', 403)
    if not source.enabled or not source.reviewed:
        fail('RIGHTS_REVIEW_REQUIRED', 'The source requires independent rights approval first.', 409)
    actual = hashlib.sha256((source.text or '').encode()).hexdigest()
    if (payload.expected_policy_version != source.policy_version or payload.content_sha256 != actual
            or payload.expected_review_revision != revision(source)):
        fail('REVISION_CONFLICT', 'Reload the source: its review revision changed.', 409)
    # A rejected/revoked decision must remain possible after body access expires.
    if payload.decision == 'approved' and (not source.text or not rights.allowed(source, 'display_full')):
        fail('SOURCE_POLICY_BLOCK', 'Current permission to inspect the source body is required.', 403)
    if payload.decision == 'approved' and not references_current(source):
        fail('REFERENCE_REVISION_REQUIRED', 'Publish a new version with verified reference metadata before approval.', 409)
    if payload.expires_at <= now():
        fail('REVIEW_EXPIRED', 'Choose an explicit future review expiry.', 422)
    refs = set(source.policy.get('content_reference_ids', []))
    checked = set(payload.checked_reference_ids)
    if len(checked) != len(payload.checked_reference_ids) or not checked.issubset(refs):
        fail('UNKNOWN_REFERENCE', 'Check only distinct references listed for this revision.', 422)
    if payload.decision == 'approved' and checked != refs:
        fail('INCOMPLETE_REVIEW', 'Address every listed reference and its limitations.', 422)
    terms = {**payload.model_dump(mode='json'), 'reviewer_id': reviewer_id}
    row = EditorialReview(source_id=source.id, reviewer_id=reviewer_id, decision=payload.decision,
        review_revision=payload.expected_review_revision, payload=terms,
        payload_sha256=digest(canonical(terms)), expires_at=payload.expires_at)
    db.add(row); db.flush()
    policy = {**source.policy, 'technical_review_status': payload.decision,
        'technical_reviewer_id': reviewer_id, 'technical_reviewed_at': row.created_at,
        'technical_reviewed_sha256': actual, 'technical_review_record_id': row.id,
        'checked_reference_ids': payload.checked_reference_ids}
    policy.pop('technical_review_note', None)  # Private findings live only in immutable records.
    source.policy = policy
    source.policy_version += 1
    db.add(Audit(actor_id=reviewer_id, action='content.technical_review', target_id=source.id,
        detail={'decision': payload.decision, 'review_id': row.id, 'review_revision': row.review_revision,
                'payload_sha256': row.payload_sha256, 'policy_version': source.policy_version}))
    db.commit()
    return row


def packet(db, source):
    """A portable review input, never a professional decision or upstream acquisition."""
    from . import output_rights
    for operation in ('display_full', 'export'):
        rights.require(source, operation)
    policy = source.policy or {}
    references = policy.get('content_reference_snapshot')
    captured = references_current(source) and isinstance(references, list)
    content = {
        'schema_version': 1, 'packet_kind': 'technical_review_input',
        'source': {'id': source.id, 'title': source.title, 'publisher': source.publisher,
                   'url': source.canonical_url, 'edition': source.version_label, 'kind': source.kind,
                   'framework': source.framework, 'body': source.text or '',
                   'body_sha256': hashlib.sha256((source.text or '').encode()).hexdigest(),
                   'policy_version': source.policy_version, 'review_revision': revision(source)},
        'references': {'ids': policy.get('content_reference_ids', []),
                       'metadata_snapshot': references if captured else None,
                       'metadata_sha256': policy.get('content_references_sha256') if captured else None,
                       'status': 'captured_metadata_only' if captured else 'not_captured',
                       'primary_text_verified_by_packet': False},
        'provenance': {k: policy.get(k) for k in ('content_item_id', 'content_version', 'content_license',
            'intake_locator', 'intake_extraction_id', 'intake_artifact_id')},
        'sec_provenance': {k: policy.get('sec_core', {}).get(k) for k in (
            'passage_id', 'source_id', 'locator', 'snapshot_id', 'source_as_of', 'retrieved_at',
            'effective_from', 'effective_to', 'public_available_at', 'authority_type',
            'acquisition_method', 'raw_artifact_included', 'coverage', 'context_note')},
        'gates': {'display_full': True, 'export': True,
                  'technical_review_current': current(source),
                  'technical_review_record_id': policy.get('technical_review_record_id'),
                  'applicability_status': policy.get('applicability_review_status',
                      policy.get('sec_core', {}).get('applicability_review_status', 'not_recorded')),
                  'agent_admission_granted_by_packet': False},
        'source_attributions': output_rights.notices(db, [source]),
        'limitations': [
            'This packet is a review input, not an approval, license or authoritative accounting conclusion.',
            'Reference metadata and URLs do not prove acquisition, permission, primary-text verification or historical applicability.',
            'No remote references are fetched. Private prior findings and supporting records are not included.',
            'An exported copy can become stale; recheck the live revision and permissions before use.'],
        'review_checklist': [
            'Verify independent reviewer identity, competence, scope and actual supporting records.',
            'Verify source-operation permissions and notices separately from subscription or workspace access.',
            'Inspect exact primary-source editions, locators, exceptions and missing context where authorized.',
            'Check accounting claims, original examples, calculations, assumptions and contradictions.',
            'Validate issued, publicly available and effective dates for the requested period separately.',
            'Record findings, every reference limitation, supporting-record hash and explicit review expiry.'],
    }
    result = {'packet_sha256': digest(canonical(content)), 'packet': content}
    output_rights.release(db, [source], result)
    return result
