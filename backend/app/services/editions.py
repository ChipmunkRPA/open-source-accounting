"""Declared edition inventories and exact receipt accounting, never content admission."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..models import IntakeEdition, IntakeWork, Source, SourceArtifact, SourceExtraction, Audit, now
from ..errors import fail
from ..sec_core.core import canonical, digest
from . import intake, rights, parser_review


def latest(db, scope):
    return db.scalar(select(IntakeEdition).where(
        IntakeEdition.family_id == scope.family_id,
        IntakeEdition.collection_key == scope.collection_key,
        IntakeEdition.edition == scope.edition).order_by(IntakeEdition.revision.desc()).limit(1))


def checked(row):
    if (digest(canonical(row.manifest)) != row.manifest_sha256
            or any(row.manifest.get(k) != getattr(row, k) for k in
                   ('family_id', 'collection_key', 'edition', 'revision'))):
        fail('EDITION_INTEGRITY', 'Edition inventory changed; inspect immutable revision history.', 409)
    return row


def metadata(row):
    checked(row)
    return {'id': row.id, 'revision': row.revision, 'manifest': row.manifest,
            'manifest_sha256': row.manifest_sha256, 'created_at': row.created_at,
            'approval_granted': False, 'agent_eligible': False}


def artifacts(db, work_id):
    rows = db.scalars(select(SourceArtifact).where(SourceArtifact.work_id == work_id)
                      .order_by(SourceArtifact.id).limit(101)).all()
    if len(rows) > 100:
        fail('EDITION_ARTIFACT_LIMIT', 'More than 100 artifacts for one component; reconcile its scope explicitly.', 409)
    return rows


def create(db, settings, payload, actor_id):
    if payload.family_id not in intake.families(settings) or payload.family_id == 'PRIVATE_UPLOADS':
        fail('EDITION_FAMILY', 'Choose a registered public/reference source family; private files use workspaces.', 422)
    request = payload.model_dump(mode='json')
    request_hash = digest(canonical(request))
    previous = latest(db, payload)
    if previous:
        checked(previous)
        if previous.request_sha256 == request_hash:
            return previous
    if payload.expected_revision != (previous.revision if previous else 0):
        fail('REVISION_CONFLICT', 'Reload the latest inventory revision.', 409)
    # Use the acquisition lock order: Source before artifact inventory. No network or bytes.
    works = {}
    all_parts = [*payload.parts, *([payload.combined] if payload.combined else [])]
    for part in all_parts:
        if part.intake_work_id:
            work = db.get(IntakeWork, part.intake_work_id)
            if not work or work.family_id != payload.family_id:
                fail('EDITION_COMPONENT', 'Component must bind an existing work in this family.', 422)
            works[work.id] = work
    parents = {}
    for source_id in sorted({w.source_id for w in works.values()}):
        parents[source_id] = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    parts = []
    for part in all_parts:
        record = part.model_dump(mode='json')
        record['known_raw_sha256'] = []
        if part.intake_work_id:
            work = works[part.intake_work_id]
            parent = parents[work.source_id]
            if (work.manifest_sha256 != part.manifest_sha256
                    or digest(canonical(work.manifest)) != part.manifest_sha256
                    or not parent or parent.policy.get('intake_manifest_sha256') != part.manifest_sha256):
                fail('EDITION_COMPONENT_REVISION', 'Component intake manifest is stale or changed.', 409)
            record['known_raw_sha256'] = sorted(a.raw_sha256 for a in artifacts(db, work.id))
        parts.append(record)
    manifest = {k: request[k] for k in ('family_id', 'collection_key', 'edition', 'coverage_unit', 'inventory_note')}
    manifest.update(revision=payload.expected_revision+1, parts=parts[:len(payload.parts)],
                    combined=parts[-1] if payload.combined else None,
                    previous_id=previous.id if previous else None)
    row = IntakeEdition(family_id=payload.family_id, collection_key=payload.collection_key,
        edition=payload.edition, revision=manifest['revision'], request_sha256=request_hash,
        manifest=manifest, manifest_sha256=digest(canonical(manifest)), created_by=actor_id)
    db.add(row)
    try:
        db.flush()
        db.add(Audit(actor_id=actor_id, action='intake.edition_declared', target_id=row.id,
                     detail={'revision': row.revision, 'manifest_sha256': row.manifest_sha256}))
        db.commit()
    except IntegrityError:
        db.rollback()
        winner = latest(db, payload)
        if winner and checked(winner).request_sha256 == request_hash:
            return winner
        fail('REVISION_CONFLICT', 'Another operator registered this inventory revision; reload.', 409)
    return row


def parser_status(db, ex):
    decision = parser_review.latest(db, ex.id)
    if not decision:
        return 'pending'
    _, _, _, identity, revision = parser_review.identity(db, ex)
    p = decision.payload
    if (not decision.reviewer_id or digest(canonical(p)) != decision.payload_sha256
            or p.get('reviewer_id') != decision.reviewer_id or p.get('expected_revision') != revision
            or p.get('identity') != identity or p.get('expires_at', 0) <= now()):
        return 'stale_or_invalid'
    return p.get('decision') if p.get('decision') in {'approved', 'rejected', 'revoked'} else 'pending'


def component(db, part):
    out = {**part, 'receipt_state': 'unbound', 'artifact_id': None,
           'rights_operations': {}, 'extractions': [], 'unreconciled_raw_sha256': [],
           'raw_bytes_verified_now': False,
           'technical_applicability_index_status': 'not_assessed_by_edition_report'}
    if not part['intake_work_id']:
        return out
    work = db.get(IntakeWork, part['intake_work_id'])
    if not work:
        out['receipt_state'] = 'missing_work'
        return out
    parent = db.get(Source, work.source_id)
    out['component_edition'] = work.edition
    if (work.manifest_sha256 != part['manifest_sha256']
            or digest(canonical(work.manifest)) != part['manifest_sha256']
            or not parent or parent.policy.get('intake_manifest_sha256') != part['manifest_sha256']):
        out['receipt_state'] = 'manifest_changed'
        return out
    context = {'route': work.manifest['route'], 'audience': 'internal_ingestion'}
    out['rights_operations'] = {op: rights.allowed(parent, op, context=context) for op in rights.OPERATIONS}
    rows = artifacts(db, work.id)
    expected = part['expected_raw_sha256']
    # The expected future hash may arrive after registration; other new hashes need a new revision.
    known = set(part['known_raw_sha256']) | {expected}
    out['unreconciled_raw_sha256'] = sorted(a.raw_sha256 for a in rows if a.raw_sha256 not in known)
    selected = next((a for a in rows if a.raw_sha256 == expected), None)
    out['receipt_state'] = 'hash_not_declared' if not expected else 'missing_artifact'
    if selected:
        out['artifact_id'] = selected.id
        receipt = selected.receipt
        out['receipt_state'] = ('matched' if receipt.get('raw_sha256') == expected
            and receipt.get('manifest_sha256') == part['manifest_sha256'] else 'receipt_mismatch')
        extractions = db.scalars(select(SourceExtraction).where(SourceExtraction.artifact_id == selected.id)
                                .order_by(SourceExtraction.id).limit(11)).all()
        out['extractions_truncated'] = len(extractions) > 10
        out['extractions'] = [{'id': e.id, 'normalized_sha256': e.normalized_sha256,
                              'parser_version': e.parser_version, 'passage_count': e.passage_count,
                              'parser_review': parser_status(db, e)} for e in extractions[:10]]
    if parent.policy.get('integrity_holds'):
        out['receipt_state'] = 'integrity_hold'
    elif out['unreconciled_raw_sha256']:
        out['receipt_state'] = 'unreconciled_delivery'
    return out


def report(db, edition_id):
    row = db.get(IntakeEdition, edition_id)
    if not row:
        fail('NOT_FOUND', 'Edition inventory not found.', 404)
    checked(row)
    items = [component(db, part) for part in row.manifest['parts']]
    head = latest(db, row)
    checked(head)
    current = head.id == row.id
    required = [p for p in items if p['required']]
    return {**metadata(row), 'current_revision': current, 'latest_id': head.id,
            'observed_at': now(), 'observation': 'metadata_only_non_atomic_no_storage_or_network_reads',
            'declared_parts': len(items), 'required_parts': len(required),
            'optional_parts': len(items)-len(required),
            'required_matching_receipts': sum(p['receipt_state'] == 'matched' for p in required),
            'optional_matching_receipts': sum(p['receipt_state'] == 'matched' for p in items if not p['required']),
            'required_receipts_complete': current and all(p['receipt_state'] == 'matched' for p in required),
            'publisher_inventory_completeness': 'not_independently_reviewed',
            'content_completeness': 'not_established_by_receipt_counts',
            'items': items,
            'combined_receipt': component(db, row.manifest['combined']) if row.manifest.get('combined') else None,
            'notice': 'Counts concern the declared component inventory, not a whole-document artifact or approved corpus. '
                      'No rights, parser, technical, applicability or index approval is granted. '
                      'Reconcile unexpected deliveries in a new immutable inventory revision.'}
