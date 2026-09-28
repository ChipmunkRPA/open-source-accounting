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


def comparison(db, edition_id):
    """Compare frozen declarations only; never reconstruct historical live receipt state."""
    row = db.get(IntakeEdition, edition_id)
    if not row:
        fail('NOT_FOUND', 'Edition inventory not found.', 404)
    checked(row)
    previous_id = row.manifest.get('previous_id')
    previous = db.get(IntakeEdition, previous_id) if previous_id else None
    if row.revision == 1:
        valid_chain = previous_id is None
    else:
        valid_chain = previous is not None and previous.revision == row.revision-1 and all(
            getattr(previous, k) == getattr(row, k) for k in ('family_id', 'collection_key', 'edition'))
    if not valid_chain:
        fail('EDITION_HISTORY', 'Inventory predecessor is missing or inconsistent; inspect revision history.', 409)
    if previous:
        checked(previous)
    before = previous.manifest if previous else {}
    after = row.manifest

    def identity(item):
        return {'id': item.id, 'revision': item.revision, 'manifest_sha256': item.manifest_sha256} if item else None

    def changes(old, new):
        # Include every persisted field, including frozen known-delivery hashes.
        return [{'field': key, 'before': old.get(key), 'after': new.get(key)}
                for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]

    old_parts = {p['key']: p for p in before.get('parts', [])}
    new_parts = {p['key']: p for p in after['parts']}
    shared = sorted(old_parts.keys() & new_parts.keys())
    changed = [{'key': key, 'fields': changes(old_parts[key], new_parts[key])} for key in shared
               if old_parts[key] != new_parts[key]]
    old_combined, new_combined = before.get('combined'), after.get('combined')
    combined_status = ('unchanged' if old_combined == new_combined else
                       'added' if old_combined is None else 'removed' if new_combined is None else 'changed')

    def counts(manifest):
        parts = manifest.get('parts', [])
        return {'required': sum(p['required'] for p in parts),
                'optional': sum(not p['required'] for p in parts), 'total': len(parts)}

    return {'before': identity(previous), 'after': identity(row),
            'family_id': row.family_id, 'collection_key': row.collection_key, 'edition': row.edition,
            'comparison_basis': 'immutable_predecessor_declarations_only',
            'initial_inventory': previous is None,
            'scope_changes': changes({k: before.get(k) for k in ('coverage_unit', 'inventory_note')},
                                     {k: after[k] for k in ('coverage_unit', 'inventory_note')}),
            'parts': {'added': [new_parts[k] for k in sorted(new_parts.keys()-old_parts.keys())],
                      'removed': [old_parts[k] for k in sorted(old_parts.keys()-new_parts.keys())],
                      'changed': changed, 'unchanged_count': len(shared)-len(changed),
                      'order_before': list(old_parts), 'order_after': list(new_parts),
                      'order_changed': list(old_parts) != list(new_parts)},
            'declared_counts': {'before': counts(before), 'after': counts(after)},
            'required_components_removed': sorted(k for k in old_parts.keys()-new_parts.keys() if old_parts[k]['required']),
            'required_components_made_optional': [k for k in shared if old_parts[k]['required'] and not new_parts[k]['required']],
            'combined': {'status': combined_status, 'before': old_combined, 'after': new_combined,
                         'fields': changes(old_combined or {}, new_combined or {})},
            'approval_granted': False, 'agent_eligible': False,
            'notice': 'This compares declared scope and identities, not source text or historical receipt/review state. '
                      'Removing required parts or making them optional reduces the denominator; it is not new acquisition. '
                      'Combined representations remain separate. No completeness or professional approval is granted.'}
