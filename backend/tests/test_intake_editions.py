"""Synthetic edition manifests/receipts only; no real source acquisition or approval."""
from copy import deepcopy
import pytest
from sqlalchemy import select, func
from app.models import IntakeEdition, SourceArtifact, Source, Audit, IntakeAttempt
from app.services.storage import Storage
from app.sec_core.fetch import Gateway
from app.sec_core.core import digest
from test_source_intake import registered, payload, fetch, parse, FakeGateway, RAW, ADMIN

BASE = '/api/v1/admin/intake/editions'


def body(work=None, raw=None, **changes):
    part = {'key': 'part-1', 'label': 'Synthetic first component', 'required': True}
    if work:
        part.update(intake_work_id=work['id'], manifest_sha256=work['manifest_sha256'],
                    expected_raw_sha256=raw)
    result = dict(family_id='SEC_RULES', collection_key='synthetic-edition', edition='2026-fixture',
                  expected_revision=0, coverage_unit='Two synthetic sections, not real government content',
                  inventory_note='Synthetic declared inventory; not independent publisher completeness review.', parts=[part])
    result.update(changes)
    return result


def create(client, request):
    r = client.post(BASE, headers=ADMIN, json=request)
    assert r.status_code == 201, r.text
    return r.json()


def report(client, row):
    r = client.get(BASE+'/'+row['id'], headers=ADMIN)
    assert r.status_code == 200, r.text
    return r.json()


def test_missing_required_and_optional_denominators(client):
    work = registered(client)
    fetch(client, work)
    b = body(work, digest(RAW))
    b['parts'] += [{'key': 'required-appendix', 'label': 'Missing appendix'},
                   {'key': 'optional-index', 'label': 'Optional index', 'required': False}]
    r = report(client, create(client, b))
    assert (r['declared_parts'], r['required_parts'], r['optional_parts'], r['required_matching_receipts']) == (3, 2, 1, 1)
    assert not r['required_receipts_complete']
    assert [x['receipt_state'] for x in r['items']] == ['matched', 'unbound', 'unbound']
    assert r['content_completeness'] == 'not_established_by_receipt_counts'
    assert r['publisher_inventory_completeness'] == 'not_independently_reviewed'


def test_expected_hash_arrival_not_arbitrary_artifact(client):
    work = registered(client)
    row = create(client, body(work, digest(RAW)))
    assert report(client, row)['items'][0]['receipt_state'] == 'missing_artifact'
    fetch(client, work)
    r = report(client, row)
    assert r['required_receipts_complete'] and not r['approval_granted'] and not r['agent_eligible']
    assert not r['items'][0]['raw_bytes_verified_now']


def test_unexpected_delivery_requires_explicit_revision(client):
    work = registered(client)
    fetch(client, work)
    original = create(client, body(work, digest(RAW)))
    new_raw = RAW.replace(b'original', b'changed')
    fetch(client, work, FakeGateway(new_raw), key='changed')
    old = report(client, original)
    assert old['items'][0]['receipt_state'] == 'unreconciled_delivery'
    assert not old['required_receipts_complete']
    revised = create(client, body(work, digest(new_raw), expected_revision=1))
    assert report(client, revised)['required_receipts_complete']
    old = report(client, original)
    assert not old['current_revision'] and not old['required_receipts_complete'] and old['latest_id'] == revised['id']
    assert original['manifest']['parts'][0]['expected_raw_sha256'] == digest(RAW)
    assert len(revised['manifest']['parts'][0]['known_raw_sha256']) == 2


def test_replacing_manifest_revision_does_not_mutate_old_complete_snapshot(client):
    work = registered(client); fetch(client, work)
    old = create(client, body(work, digest(RAW)))
    new_body = body(work, digest(RAW), expected_revision=1)
    new_body['parts'].append({'key': 'appendix', 'label': 'Newly discovered required appendix'})
    new = create(client, new_body)
    assert not report(client, new)['required_receipts_complete']
    old_report = report(client, old)
    assert old_report['required_matching_receipts'] == 1 and not old_report['required_receipts_complete']
    assert old_report['manifest_sha256'] == old['manifest_sha256']


def test_retry_idempotency_stale_conflict_and_history(client):
    request = body()
    row = create(client, request)
    assert create(client, request)['id'] == row['id']
    changed = deepcopy(request); changed['inventory_note'] = 'A distinct concurrent inventory proposal.'
    assert client.post(BASE, headers=ADMIN, json=changed).status_code == 409
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(IntakeEdition)) == 1
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == 'intake.edition_declared')) == 1
    assert len(client.get(BASE+'?collection_key=synthetic-edition&edition=2026-fixture', headers=ADMIN).json()['items']) == 1
    assert client.get(BASE+'?family_id=FASB', headers=ADMIN).json()['items'] == []


@pytest.mark.parametrize('mutation', ['duplicate-key', 'duplicate-work', 'all-optional', 'truthy-required', 'missing-manifest', 'hash-without-work', 'too-many'])
def test_invalid_inventory_contract(client, mutation):
    work = registered(client)
    b = body(work, digest(RAW))
    if mutation == 'duplicate-key': b['parts'].append(deepcopy(b['parts'][0]))
    if mutation == 'duplicate-work': b['parts'].append({**b['parts'][0], 'key': 'other'})
    if mutation == 'all-optional': b['parts'][0]['required'] = False
    if mutation == 'truthy-required': b['parts'][0]['required'] = 'true'
    if mutation == 'missing-manifest': b['parts'][0]['manifest_sha256'] = None
    if mutation == 'hash-without-work': b['parts'][0].update(intake_work_id=None, manifest_sha256=None)
    if mutation == 'too-many': b['parts'] = [{'key': 'p'+str(i), 'label': 'Part'} for i in range(251)]
    assert client.post(BASE, headers=ADMIN, json=b).status_code == 422


def test_foreign_family_unknown_work_stale_binding_and_private_denied(client):
    work = registered(client)
    assert client.post(BASE, headers=ADMIN, json=body(work, family_id='FASB')).status_code == 422
    assert client.post(BASE, headers=ADMIN, json=body(family_id='PRIVATE_UPLOADS')).status_code == 422
    b = body(work); b['parts'][0]['intake_work_id'] = 'missing'
    assert client.post(BASE, headers=ADMIN, json=b).status_code == 422
    b = body(work); b['parts'][0]['manifest_sha256'] = '0'*64
    assert client.post(BASE, headers=ADMIN, json=b).status_code == 409


def test_auth_and_offline_metadata_report(client, monkeypatch):
    work = registered(client); artifact = fetch(client, work); parse(client, artifact)
    monkeypatch.setattr(Storage, 'get', lambda *_: pytest.fail('No body reads in inventory report'))
    monkeypatch.setattr(Storage, 'get_bounded', lambda *_: pytest.fail('No body reads in inventory report'))
    monkeypatch.setattr(Gateway, 'get', lambda *_: pytest.fail('No network in inventory report'))
    assert client.post(BASE, json=body(work)).status_code == 403
    assert client.get(BASE).status_code == 403
    row = create(client, body(work, digest(RAW)))
    assert client.get(BASE+'/'+row['id']).status_code == 403
    r = report(client, row)
    assert r['items'][0]['extractions'][0]['parser_review'] == 'pending'
    assert r['items'][0]['technical_applicability_index_status'] == 'not_assessed_by_edition_report'
    assert client.get(BASE+'/missing', headers=ADMIN).status_code == 404


def test_receipt_hash_provenance_and_integrity_hold(client):
    work = registered(client); artifact = fetch(client, work)
    row = create(client, body(work, digest(RAW)))
    with client.app.state.db.Session() as db:
        a = db.get(SourceArtifact, artifact['id']); a.receipt = {**a.receipt, 'manifest_sha256': '0'*64}; db.commit()
    assert report(client, row)['items'][0]['receipt_state'] == 'receipt_mismatch'
    with client.app.state.db.Session() as db:
        a = db.get(SourceArtifact, artifact['id']); a.receipt = {**a.receipt, 'manifest_sha256': work['manifest_sha256']}
        s = db.get(Source, work['source_id']); s.policy = {**s.policy, 'integrity_holds': {artifact['id']: {'fixture': True}}}; db.commit()
    assert report(client, row)['items'][0]['receipt_state'] == 'integrity_hold'


def test_missing_artifact_and_undeclared_hash_remain_incomplete(client):
    work = registered(client); artifact = fetch(client, work)
    unpinned = create(client, body(work))
    assert report(client, unpinned)['items'][0]['receipt_state'] == 'hash_not_declared'
    pinned = create(client, body(work, digest(RAW), expected_revision=1))
    with client.app.state.db.Session() as db:
        for attempt in db.scalars(select(IntakeAttempt).where(IntakeAttempt.artifact_id == artifact['id'])):
            attempt.artifact_id = None
        db.flush()
        db.delete(db.get(SourceArtifact, artifact['id'])); db.commit()
    assert report(client, pinned)['items'][0]['receipt_state'] == 'missing_artifact'


def test_edition_tamper_is_not_reported_as_complete(client):
    row = create(client, body())
    with client.app.state.db.Session() as db:
        r = db.get(IntakeEdition, row['id']); r.manifest = {**r.manifest, 'parts': []}; db.commit()
    assert client.get(BASE+'/'+row['id'], headers=ADMIN).status_code == 409


def test_historical_receipt_does_not_regrant_revoked_rights(client):
    work = registered(client); fetch(client, work)
    row = create(client, body(work, digest(RAW)))
    with client.app.state.db.Session() as db:
        s = db.get(Source, work['source_id']); s.enabled = False; s.policy_version += 1; db.commit()
    r = report(client, row)
    assert r['required_receipts_complete']  # Historical receipt inventory, not permission/byte integrity.
    assert not any(r['items'][0]['rights_operations'].values())
    assert not r['agent_eligible']


def test_distinct_component_editions_and_optional_missing_part(client):
    first = registered(client)
    second = registered(client, body=payload(work_id='another-work', edition='different-component-edition'))
    fetch(client, first); fetch(client, second, key='second')
    b = body(first, digest(RAW)); p = body(second, digest(RAW))['parts'][0]; p['key'] = 'part-2'
    b['parts'] += [p, {'key': 'optional', 'label': 'Optional component', 'required': False}]
    r = report(client, create(client, b))
    assert r['required_receipts_complete'] and r['required_matching_receipts'] == 2
    assert r['optional_matching_receipts'] == 0
    assert r['items'][1]['component_edition'] == 'different-component-edition'


def test_combined_representation_never_fills_missing_component(client):
    combined = registered(client); fetch(client, combined)
    b = body(); b['combined'] = body(combined, digest(RAW))['parts'][0]
    r = report(client, create(client, b))
    assert r['combined_receipt']['receipt_state'] == 'matched'
    assert r['declared_parts'] == r['required_parts'] == 1
    assert r['required_matching_receipts'] == 0 and not r['required_receipts_complete']
    b = body(combined, digest(RAW)); b['combined'] = b['parts'][0]
    assert client.post(BASE, headers=ADMIN, json=b).status_code == 422


def test_changed_component_manifest_cannot_keep_receipt_complete(client):
    from app.models import IntakeWork
    work = registered(client); fetch(client, work)
    row = create(client, body(work, digest(RAW)))
    with client.app.state.db.Session() as db:
        w = db.get(IntakeWork, work['id']); w.manifest = {**w.manifest, 'edition': 'tampered'}; db.commit()
    r = report(client, row)
    assert r['items'][0]['receipt_state'] == 'manifest_changed' and not r['required_receipts_complete']


def test_artifact_limit_never_silently_hides_changed_delivery(client):
    work = registered(client)
    row = create(client, body(work))
    with client.app.state.db.Session() as db:
        for i in range(101):
            db.add(SourceArtifact(work_id=work['id'], raw_sha256=digest(str(i).encode()),
                object_key='synthetic-no-body-'+str(i), byte_count=1, mime='text/plain', receipt={}))
        db.commit()
    assert client.get(BASE+'/'+row['id'], headers=ADMIN).status_code == 409
    assert client.post(BASE, headers=ADMIN, json=body(work, expected_revision=1)).status_code == 409


def test_parser_ledger_expiry_and_parent_revision_are_separate(client, monkeypatch):
    from app.models import SourceExtraction, ParserReview, now
    from app.services import parser_review
    from app.sec_core.core import canonical
    work = registered(client); artifact = fetch(client, work); ex = parse(client, artifact)
    row = create(client, body(work, digest(RAW)))
    with client.app.state.db.Session() as db:
        e = db.get(SourceExtraction, ex['id'])
        _, _, _, identity, revision = parser_review.identity(db, e)
        terms = dict(reviewer_id='approver', expected_revision=revision, identity=identity,
                     expires_at=now()+3600, decision='approved')
        db.add(ParserReview(extraction_id=e.id, sequence=1, reviewer_id='approver', payload=terms,
                            payload_sha256=digest(canonical(terms))))
        db.commit()
    assert report(client, row)['items'][0]['extractions'][0]['parser_review'] == 'approved'
    with monkeypatch.context() as clock:
        clock.setattr('app.services.editions.now', lambda: terms['expires_at']+1)
        assert report(client, row)['items'][0]['extractions'][0]['parser_review'] == 'stale_or_invalid'
    with client.app.state.db.Session() as db:
        s = db.get(Source, work['source_id']); s.policy_version += 1; db.commit()
    r = report(client, row)
    assert r['required_receipts_complete']
    assert r['items'][0]['extractions'][0]['parser_review'] == 'stale_or_invalid'
    assert not r['agent_eligible']
