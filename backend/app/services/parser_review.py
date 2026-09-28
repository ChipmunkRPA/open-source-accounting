"""Independent parser/citation decisions; synthetic fixtures are never real reviews."""
import base64
import json
from sqlalchemy import select
from sqlalchemy.orm import object_session
from ..models import Source, SourceExtraction, SourceArtifact, IntakeWork, ParserReview, Audit, now
from ..errors import fail
from ..sec_core.core import canonical, digest
from . import intake, rights, output_rights
from .storage import Storage


def identity(db, extraction):
    artifact = db.get(SourceArtifact, extraction.artifact_id)
    work = db.get(IntakeWork, artifact.work_id)
    parent = db.get(Source, work.source_id)
    data = {'extraction_id': extraction.id, 'artifact_id': artifact.id,
            'raw_sha256': artifact.raw_sha256, 'byte_count': artifact.byte_count,
            'receipt_sha256': digest(canonical(artifact.receipt)),
            'normalized_sha256': extraction.normalized_sha256,
            'parser_version': extraction.parser_version, 'passage_count': extraction.passage_count,
            'manifest_sha256': work.manifest_sha256,
            'parent_policy_version': parent.policy_version, 'parent_rights_revision': rights.revision(parent)}
    return artifact, work, parent, data, digest(canonical(data))


def latest(db, extraction_id):
    return db.scalar(select(ParserReview).where(ParserReview.extraction_id == extraction_id)
                     .order_by(ParserReview.sequence.desc()).limit(1))


def load(db, settings, extraction_id, operations):
    extraction = db.get(SourceExtraction, extraction_id)
    if not extraction: fail('NOT_FOUND', 'Extraction not found.', 404)
    artifact = db.get(SourceArtifact, extraction.artifact_id)
    intake.authorize(db, artifact.work_id, operations, lock=True)
    artifact, work, parent, data, revision = identity(db, extraction)
    raw = Storage(settings).get(artifact.object_key)
    normalized = Storage(settings).get(extraction.object_key)
    if (len(raw) != artifact.byte_count or digest(raw) != artifact.raw_sha256
            or digest(normalized) != extraction.normalized_sha256):
        fail('ARTIFACT_INTEGRITY', 'Raw or parsed artifact changed; no review was granted.', 409)
    try:
        passages = json.loads(normalized)
        if (not isinstance(passages, list) or len(passages) != extraction.passage_count or not passages
                or len(passages) > 10000 or any(not p['locator'] or digest(p['text']) != p['sha256'] for p in passages)):
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        fail('ARTIFACT_INTEGRITY', 'Parsed passages failed integrity validation.', 409)
    return extraction, artifact, parent, data, revision, raw, passages


def packet(db, settings, extraction_id):
    ex, artifact, parent, data, revision, raw, passages = load(db, settings, extraction_id,
        ['store_raw', 'store_text', 'display_full', 'export'])
    previous = latest(db, ex.id)
    manifest = db.get(IntakeWork, artifact.work_id).manifest
    body = {'schema_version': 1, 'kind': 'parser_citation_review_input', 'identity': data,
            'review_revision': revision, 'review_sequence': previous.sequence if previous else 0,
            'source': {'title': parent.title, 'publisher': parent.publisher, 'url': parent.canonical_url,
                       'edition': parent.version_label},
            'publication_metadata': {k: manifest.get(k) for k in ('family_id', 'work_id', 'edition',
                'language', 'jurisdiction', 'authority_type', 'coverage_unit', 'issued_at',
                'publicly_available_at', 'effective_from', 'effective_to', 'date_notes',
                'effective_conditions', 'notices')},
            'raw_base64': base64.b64encode(raw).decode('ascii'), 'raw_mime': artifact.mime,
            'passages': passages, 'source_attributions': output_rights.notices(db, [parent]),
            'notice': 'Original bytes are encoded, not executed. Inspect them safely. Parsing is not accounting or applicability approval.',
            'checklist': ['Compare every normalized passage with the original bytes.',
                          'Check section/page locators, tables, footnotes, omitted context and reading order.',
                          'Record limits, exceptions, supporting evidence and explicit expiry.'],
            'approval_granted': False}
    result = {'packet_sha256': digest(canonical(body)), 'packet': body}
    output_rights.release(db, [parent], result)
    db.commit()
    return result


def record(db, settings, extraction_id, payload, actor_id):
    ex, artifact, parent, data, revision, raw, passages = load(db, settings, extraction_id,
        ['store_raw', 'store_text', 'display_full'])
    previous = latest(db, ex.id)
    sequence = previous.sequence if previous else 0
    if payload.expected_revision != revision or payload.expected_sequence != sequence:
        fail('REVISION_CONFLICT', 'Reload the extraction and latest parser decision.', 409)
    contributors = set(db.scalars(select(Audit.actor_id).where(Audit.target_id == ex.id,
                       Audit.action == 'intake.parsed_unreviewed')))
    contributors.update([parent.created_by, artifact.receipt.get('operator_id')])
    if actor_id in contributors:
        fail('SEPARATION_OF_DUTIES', 'An independent reviewer must inspect this extraction.', 403)
    if payload.expires_at <= now(): fail('REVIEW_EXPIRED', 'Choose a future review expiry.', 422)
    indices = payload.checked_passage_indices
    if len(set(indices)) != len(indices) or any(i < 0 or i >= len(passages) for i in indices):
        fail('PASSAGE_SCOPE', 'Choose distinct passage indices from this exact extraction.', 422)
    if payload.decision == 'approved' and set(indices) != set(range(len(passages))):
        fail('INCOMPLETE_REVIEW', 'Approval requires inspecting every passage and locator.', 422)
    terms = {**payload.model_dump(mode='json'), 'reviewer_id': actor_id, 'identity': data,
             'passage_bindings': [{'sha256': p['sha256'], 'locator': p['locator']} for p in passages]}
    row = ParserReview(extraction_id=ex.id, sequence=sequence+1, reviewer_id=actor_id,
                       payload=terms, payload_sha256=digest(canonical(terms)))
    db.add(row); db.flush()
    # Invalidate already saved evidence/export dependencies without changing source bodies.
    for source in db.scalars(select(Source).where(Source.policy['intake_extraction_id'].as_string() == ex.id)
                             .order_by(Source.id).with_for_update()):
        source.policy_version += 1
    db.add(Audit(actor_id=actor_id, action='intake.parser_review', target_id=ex.id,
                 detail={'record_id': row.id, 'sequence': row.sequence, 'payload_sha256': row.payload_sha256,
                         'decision': payload.decision}))
    db.commit()
    return {'record_id': row.id, 'sequence': row.sequence, 'decision': payload.decision,
            'revision': revision, 'technical_or_applicability_approval_granted': False}


def current(source):
    db = object_session(source)
    policy = source.policy or {}
    if not db: return False
    ex = db.get(SourceExtraction, policy.get('intake_extraction_id'))
    if not ex: return False
    row = latest(db, ex.id)
    if not row or not row.reviewer_id or row.payload_sha256 != digest(canonical(row.payload)): return False
    terms = row.payload
    _, work, parent, data, revision = identity(db, ex)
    if (terms.get('decision') != 'approved' or terms.get('expires_at', 0) <= now()
            or terms.get('expected_revision') != revision or terms.get('reviewer_id') != row.reviewer_id
            or terms.get('identity') != data or policy.get('intake_parent_id') != parent.id
            or policy.get('intake_artifact_id') != ex.artifact_id
            or policy.get('intake_extraction_sha256') != ex.normalized_sha256
            or policy.get('intake_parser_version') != ex.parser_version):
        return False
    index = policy.get('intake_passage_index')
    bindings = terms.get('passage_bindings', [])
    return bool(type(index) is int and 0 <= index < len(bindings)
                and bindings[index] == {'sha256': digest(source.text or ''), 'locator': policy.get('intake_locator')})


def history(db, settings, extraction_id):
    ex, artifact, parent, data, revision, raw, passages = load(db, settings, extraction_id,
        ['store_raw', 'store_text', 'display_full'])
    rows = db.scalars(select(ParserReview).where(ParserReview.extraction_id == ex.id)
                      .order_by(ParserReview.sequence.desc()).limit(100)).all()
    supporting = output_rights.history_sources(db,parent)
    result = {'source_attributions': output_rights.notices(db,supporting), 'extraction_id': ex.id, 'revision': revision,
              'items': [{'id': r.id, 'sequence': r.sequence, 'created_at': r.created_at,
                         'payload': r.payload, 'payload_sha256': r.payload_sha256} for r in rows]}
    output_rights.release(db, supporting, result)
    db.commit()
    return result
