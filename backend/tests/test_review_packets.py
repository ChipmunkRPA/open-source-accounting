"""Synthetic review inputs only: exporting a packet never approves its content."""
import copy
import pytest
from app.content import stage_library, ContentError
from app.models import Source, EditorialReview, OutputBudget
from app.sec_core.core import canonical, digest
from app.services import editorial, rights
from test_content_library import pack as pack, stage, decision
from test_editorial_ledger import prepared, review, EDITOR
from test_output_rights import fixture


def download(client, sid, **overrides):
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        params = {'expected_review_revision': editorial.revision(source),
                  'expected_policy_version': source.policy_version, **overrides}
    return client.get('/api/v1/editorial/sources/'+sid+'/packet', headers=EDITOR, params=params)


def test_packet_contains_exact_original_revision_references_and_no_approval(client, pack):
    sid, _ = prepared(client, pack)
    response = download(client, sid)
    assert response.status_code == 200, response.text
    result = response.json(); packet = result['packet']
    assert result['packet_sha256'] == digest(canonical(packet))
    assert packet['source']['body_sha256'] == digest(packet['source']['body'])
    refs = packet['references']
    assert refs['metadata_sha256'] == digest(canonical(refs['metadata_snapshot']))
    assert refs['status'] == 'captured_metadata_only'
    assert all(r == pack.references[r['id']] for r in refs['metadata_snapshot'])
    assert not refs['primary_text_verified_by_packet']
    assert not packet['gates']['technical_review_current']
    assert not packet['gates']['agent_admission_granted_by_packet']
    assert len(packet['review_checklist']) == 6
    assert download(client, sid).json() == result
    with client.app.state.db.Session() as db:
        assert db.query(EditorialReview).count() == 0
        assert not rights.allowed(db.get(Source, sid), 'model_input')


def test_packet_omits_private_findings_and_supporting_records(client, pack):
    sid, payload = prepared(client, pack)
    payload['review_note'] = 'PRIVATE_SYNTHETIC_FINDING not for export into reviewer input packets'
    assert review(client, sid, payload).status_code == 200
    result = download(client, sid)
    assert result.status_code == 200
    assert 'PRIVATE_SYNTHETIC_FINDING' not in result.text
    assert 'ev_synthetic_technical' not in result.text


@pytest.mark.parametrize('operation', ['display_full', 'export'])
def test_packet_requires_each_distinct_operation(client, pack, operation):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        source.policy = {**source.policy, operation: False}
        rights.record_approval(source, 'approver'); db.commit()
    assert download(client, sid).status_code == 403


def test_packet_requires_reviewer_and_live_source(client, pack):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        params = {'expected_review_revision': editorial.revision(source), 'expected_policy_version':source.policy_version}
    assert client.get('/api/v1/editorial/sources/'+sid+'/packet',params=params).status_code == 403
    client.post('/api/v1/admin/sources/'+sid+'/disable',headers={'X-Dev-User':'admin'})
    assert download(client, sid).status_code == 403


@pytest.mark.parametrize('change', [{'expected_review_revision':'0'*64}, {'expected_policy_version':999}])
def test_packet_rejects_stale_request(client, pack, change):
    sid, _ = prepared(client, pack)
    assert download(client, sid, **change).status_code == 409


def test_packet_preserves_notices_and_accounts_export_once(client, pack):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        _, group = fixture(db, source_id=sid, per=100000, total=1000000)
    first = download(client, sid); assert first.status_code == 200
    assert 'Required synthetic notice' in first.text
    with client.app.state.db.Session() as db:
        count = db.get(OutputBudget, group).released_chars
    assert download(client, sid).json() == first.json()
    with client.app.state.db.Session() as db:
        assert db.get(OutputBudget, group).released_chars == count > 0


def test_packet_obeys_output_limit_without_consuming_failed_release(client, pack):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        _, group = fixture(db, source_id=sid, per=100, total=100)
    assert download(client, sid).status_code == 403
    with client.app.state.db.Session() as db:
        row = db.get(OutputBudget, group)
        assert row is None or row.released_chars == 0


def test_changed_reference_metadata_requires_new_item_version(client, pack):
    stage(client, pack)
    item = next(iter(pack.items.values()))
    pack.references[item.source_ids[0]]['review_scope'] = 'Changed synthetic metadata, same article prose.'
    with client.app.state.db.Session() as db:
        with pytest.raises(ContentError, match='Reference metadata changed'):
            stage_library(db, pack, 'admin')


def test_reference_snapshot_is_detached_from_mutable_library(client, pack):
    sid, _ = prepared(client, pack)
    before = download(client, sid).json()['packet']['references']
    item = next(iter(pack.items.values()))
    pack.references[item.source_ids[0]]['title'] = 'Changed local pack title'
    assert download(client, sid).json()['packet']['references'] == before


def test_changed_snapshot_cannot_retain_technical_approval(client, pack):
    sid, payload = prepared(client, pack)
    assert review(client, sid, payload).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); policy = copy.deepcopy(source.policy)
        policy['content_reference_snapshot'][0]['url'] = 'https://example.test/changed'
        source.policy = policy
        assert not editorial.current(source)
        assert not rights.allowed(source, 'model_input')


def test_legacy_missing_snapshot_requires_new_version_and_review(client, pack):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); policy = dict(source.policy)
        policy.pop('content_reference_snapshot'); policy.pop('content_references_sha256')
        source.policy = policy; db.commit(); payload = decision(source)
    assert review(client, sid, payload).status_code == 409
    result = download(client, sid)
    assert result.status_code == 200
    assert result.json()['packet']['references']['status'] == 'not_captured'
    with client.app.state.db.Session() as db:
        with pytest.raises(ContentError): stage_library(db, pack, 'admin')


def test_packet_excludes_private_sec_applicability_findings(client, pack):
    sid, _ = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        source.policy = {**source.policy, 'sec_core': {'locator': 'Synthetic section 1',
            'applicability_review_note': 'PRIVATE_APPLICABILITY_NOTE', 'unknown_private_field': 'SECRET_FIXTURE'}}
        db.commit()
    result = download(client, sid)
    assert result.status_code == 200
    assert 'Synthetic section 1' in result.text
    assert 'PRIVATE_APPLICABILITY_NOTE' not in result.text
    assert 'SECRET_FIXTURE' not in result.text
