"""Synthetic technical reviews only; no professional approval of the content pack."""
import copy
import pytest
from sqlalchemy import select, func
from app.models import Source, EditorialReview, now
from app.services import rights, editorial
from conftest import rights_approval
from test_content_library import pack as pack, stage, decision

EDITOR = {'X-Dev-User':'editor'}


def prepared(client, pack):
    sid = stage(client, pack)['created'][0]
    response = client.post('/api/v1/admin/sources/'+sid+'/approve', headers={'X-Dev-User':'approver'},
                           json=rights_approval(client, sid))
    assert response.status_code == 200
    with client.app.state.db.Session() as db:
        payload = decision(db.get(Source, sid))
    return sid, payload


def review(client, sid, payload):
    return client.post('/api/v1/editorial/sources/'+sid+'/review', headers=EDITOR, json=payload)


def test_append_only_decisions_revoke_without_erasing_prior_review(client, pack):
    sid, payload = prepared(client, pack)
    first = review(client, sid, payload)
    assert first.status_code == 200 and first.json()['technical_review_current']
    first_id = first.json()['review_record_id']
    with client.app.state.db.Session() as db:
        original = copy.deepcopy(db.get(EditorialReview, first_id).payload)
        source = db.get(Source, sid)
        later = decision(source, decision='revoked', checked_reference_ids=[])
    assert review(client, sid, later).status_code == 200
    with client.app.state.db.Session() as db:
        assert db.get(EditorialReview, first_id).payload == original
        assert db.scalar(select(func.count()).select_from(EditorialReview)) == 2
        assert not rights.allowed(db.get(Source, sid), 'model_input')
    history = client.get('/api/v1/editorial/sources/'+sid+'/reviews', headers=EDITOR)
    assert history.status_code == 200 and not history.json()['current']
    assert len(history.json()['items']) == 2
    assert 'technical_review_note' not in client.get('/api/v1/editorial/sources', headers=EDITOR).json()['items'][0]['policy']


def test_expiry_withholds_model_input_without_mutating_record(client, pack, monkeypatch):
    sid, payload = prepared(client, pack)
    assert review(client, sid, payload).status_code == 200
    monkeypatch.setattr(editorial, 'now', lambda: payload['expires_at'])
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        assert not rights.allowed(source, 'model_input') and rights.allowed(source, 'display_full')
        assert db.scalar(select(EditorialReview)).decision == 'approved'


@pytest.mark.parametrize('field,value', [('framework','IFRS'), ('kind','changed'), ('title','Changed title')])
def test_metadata_changes_invalidate_technical_review(client, pack, field, value):
    sid, payload = prepared(client, pack)
    assert review(client, sid, payload).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); setattr(source, field, value)
        assert not editorial.current(source)


def test_reference_change_invalidates_even_without_prose_change(client, pack):
    sid, payload = prepared(client, pack)
    assert review(client, sid, payload).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        source.policy = {**source.policy, 'content_reference_ids':['different-reference']}
        assert not editorial.current(source)


def test_legacy_policy_flags_cannot_substitute_for_record(client, pack):
    sid, payload = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        source.policy = {**source.policy, 'technical_review_status':'approved',
                         'technical_reviewed_sha256':payload['content_sha256']}
        assert not rights.allowed(source, 'model_input')


def test_changed_record_payload_cannot_authorize(client, pack):
    sid, payload = prepared(client, pack)
    result = review(client, sid, payload)
    with client.app.state.db.Session() as db:
        row = db.get(EditorialReview, result.json()['review_record_id'])
        row.payload = {**row.payload, 'review_scope':'Changed after review'}
        assert not editorial.current(db.get(Source, sid))


@pytest.mark.parametrize('change,status', [({'expires_at':1},422),({'expected_review_revision':'0'*64},409),
    ({'evidence_ref':'https://private.example/credential'},422),({'review_scope':''},422),
    ({'decision':'rejected','checked_reference_ids':[]},200)])
def test_review_contract_requires_evidence_scope_revision_and_expiry(client, pack, change, status):
    sid, payload = prepared(client, pack)
    assert review(client, sid, {**payload, **change}).status_code == status


def test_approval_needs_current_display_rights(client, pack):
    sid, payload = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); source.policy = {**source.policy, 'expires_at':now()-1}
        rights.record_approval(source, 'approver'); db.commit()
    assert review(client, sid, payload).status_code == 403


def test_stale_policy_version_cannot_append_second_decision(client, pack):
    sid, payload = prepared(client, pack)
    assert review(client, sid, payload).status_code == 200
    assert review(client, sid, payload).status_code == 409
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(EditorialReview)) == 1


def test_history_is_private_and_source_permission_gated(client, pack):
    sid, payload = prepared(client, pack); assert review(client, sid, payload).status_code == 200
    assert client.get('/api/v1/editorial/sources/'+sid+'/reviews', headers={'X-Dev-User':'demo'}).status_code == 403
    client.post('/api/v1/admin/sources/'+sid+'/disable', headers={'X-Dev-User':'admin'})
    assert client.get('/api/v1/editorial/sources/'+sid+'/reviews', headers=EDITOR).status_code == 403


def test_own_submission_cannot_be_reviewed(client, pack):
    sid, payload = prepared(client, pack)
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); source.created_by = 'editor'; db.commit()
    assert review(client, sid, payload).status_code == 403
