"""Synthetic rights contracts: no publisher permission or human approval is asserted."""
import pytest
from pydantic import ValidationError
from app.models import Source
from app.schemas import SourcePolicy
from app.services import rights
from conftest import activate, complete_run, rights_approval


def source(**policy):
    row = Source(id='fixture', title='Synthetic work', publisher='Test only', canonical_url='',
                 version_label='1', text='Synthetic rights test text.', enabled=True, reviewed=True,
                 policy={'basis': 'original', 'commercial_use': True, **{op: True for op in rights.OPERATIONS}, **policy})
    rights.record_approval(row, 'synthetic-test-reviewer')
    return row


@pytest.mark.parametrize('action', sorted(rights.OPERATIONS))
def test_each_operation_is_independent(action):
    row = source(**{action: False})
    assert not rights.allowed(row, action)
    for other in rights.OPERATIONS - {action}:
        assert rights.allowed(row, other)


@pytest.mark.parametrize('action', ['commercial_use', 'basis', 'review_note', 'subscription', 'temporary_cache', 'unknown'])
def test_metadata_and_product_entitlements_are_not_operations(action):
    row = source(**{action: True})
    assert not rights.allowed(row, action)


@pytest.mark.parametrize('value', ['true', 'false', 1, 0, None, [], {}])
def test_truthy_non_boolean_grants_never_authorize(value):
    assert not rights.allowed(source(model_input=value), 'model_input')
    if value is not None:  # HTTP contract rejects all nonboolean values, including null.
        with pytest.raises(ValidationError):
            SourcePolicy(basis='original', review_note='Synthetic fixture only.', model_input=value)


@pytest.mark.parametrize('expiry', [0, 100, '100', True, -1])
def test_expired_or_malformed_expiry_denies(expiry, monkeypatch):
    monkeypatch.setattr(rights, 'now', lambda: 100)
    assert not rights.allowed(source(expires_at=expiry), 'export')


def test_license_interval_boundaries(monkeypatch):
    monkeypatch.setattr(rights, 'now', lambda: 100)
    assert rights.allowed(source(effective_at=100, expires_at=101), 'export')
    assert not rights.allowed(source(effective_at=101), 'export')


@pytest.mark.parametrize('field,value', [('text', 'changed'), ('version_label', '2'), ('publisher', 'other')])
def test_exact_work_revision_invalidates_approval(field, value):
    row = source()
    setattr(row, field, value)
    assert not rights.allowed(row, 'display_full')


def test_changed_operation_or_removed_review_denies():
    row = source(export=False)
    row.policy = {**row.policy, 'export': True}
    assert not rights.allowed(row, 'export')
    row = source()
    row.policy.pop('rights_reviewed_revision')
    assert not rights.allowed(row, 'model_input')


@pytest.mark.parametrize('key', ['route', 'workspace_id', 'seat_id', 'audience', 'provider', 'region', 'retention', 'jurisdiction'])
def test_missing_or_wrong_context_denies_scoped_grant(key):
    row = source(scope={key: ['approved']})
    assert not rights.allowed(row, 'model_input')
    assert not rights.allowed(row, 'model_input', context={key: 'other', 'subscription': 'paid'})
    assert rights.allowed(row, 'model_input', context={key: 'approved'}) == (key not in {'seat_id', 'jurisdiction', 'retention'})


@pytest.mark.parametrize('scope', [{'unknown': ['yes']}, {'route': []}, {'route': 'mirror'}, [], None])
def test_invalid_scope_denies(scope):
    assert not rights.allowed(source(scope=scope), 'acquire')


@pytest.mark.parametrize('basis', ['license', 'reviewed_use'])
def test_label_without_evidence_is_not_permission(basis):
    assert not rights.allowed(source(basis=basis), 'model_input')
    with pytest.raises(ValidationError):
        SourcePolicy(basis=basis, store_text=True, review_note='Synthetic fixture only.')


def test_reference_only_never_grants_body_operations():
    row = source(basis='reference_only')
    assert all(not rights.allowed(row, op) for op in rights.OPERATIONS)


def test_stale_rights_approval_request_rejected(client):
    from app.content import Library, stage_library
    with client.app.state.db.Session() as db:
        sid = stage_library(db, Library(client.app.state.settings.content_dir), 'admin')['created'][0]
        db.commit()
    payload = rights_approval(client, sid)
    with client.app.state.db.Session() as db:
        row = db.get(Source, sid)
        row.text += '\nChanged fixture revision.'
        db.commit()
    response = client.post(f'/api/v1/admin/sources/{sid}/approve', json=payload, headers={'X-Dev-User': 'approver'})
    assert response.status_code == 409
    with client.app.state.db.Session() as db:
        assert not db.get(Source, sid).reviewed


def test_approval_requires_explicit_attestation(client):
    response = client.post('/api/v1/admin/sources/sample-research/approve',
                           headers={'X-Dev-User': 'approver'}, json={})
    assert response.status_code == 422


def test_paid_subscription_does_not_reenable_source(client):
    activate(client)
    with client.app.state.db.Session() as db:
        row = db.get(Source, 'ref-asc606')
        assert not rights.allowed(row, 'model_input')
    assert client.get('/api/v1/sources/ref-asc606').json()['text'] is None


def test_stale_rights_block_saved_output(client):
    run = complete_run(client, 'memo')
    with client.app.state.db.Session() as db:
        row = db.get(Source, 'sample-research')
        row.text += '\nUnapproved mutation.'
        db.commit()
    response = client.get('/api/v1/memos/' + run['memo_id'])
    assert response.status_code == 409


@pytest.mark.parametrize('basis', ['license', 'reviewed_use'])
def test_restricted_body_cannot_be_stored_by_claiming_a_license(client, basis):
    response = client.post('/api/v1/admin/sources', headers={'X-Dev-User': 'admin'}, json={
        'title': 'Synthetic restricted work', 'publisher': 'Fixture', 'kind': 'standard',
        'text': 'Synthetic text only, not a real publisher passage.',
        'policy': {'basis': basis, 'store_text': True, 'license_evidence_ref': 'fixture-not-real',
                   'review_note': 'Synthetic claimed license is not authorization.'}})
    assert response.status_code == 422


def test_new_original_rights_approval_does_not_grant_technical_approval(client):
    response = client.post('/api/v1/admin/sources', headers={'X-Dev-User': 'admin'}, json={
        'title': 'Synthetic original', 'publisher': 'Fixture', 'kind': 'original_commentary',
        'text': 'Synthetic original with no accounting review.',
        'policy': {'basis': 'original', 'commercial_use': True, 'store_text': True, 'model_input': True,
                   'review_note': 'Synthetic original for independent gate testing.'}})
    assert response.status_code == 201
    sid = response.json()['id']
    assert client.post(f'/api/v1/admin/sources/{sid}/approve', headers={'X-Dev-User': 'approver'},
                       json=rights_approval(client, sid)).status_code == 200
    with client.app.state.db.Session() as db:
        assert not rights.allowed(db.get(Source, sid), 'model_input')


def test_editorial_role_cannot_display_unapproved_body(client):
    from app.content import Library, stage_library
    with client.app.state.db.Session() as db:
        stage_library(db, Library(client.app.state.settings.content_dir), 'admin')
        db.commit()
    response = client.get('/api/v1/editorial/sources', headers={'X-Dev-User': 'editor'})
    assert response.status_code == 200
    assert response.json()['items']
    assert all(row['text'] is None for row in response.json()['items'])


def test_reapproval_cannot_revive_old_evidence(client):
    from sqlalchemy import select
    from app.models import Evidence
    run = complete_run(client, 'memo')
    with client.app.state.db.Session() as db:
        evidence = db.scalar(select(Evidence).where(Evidence.run_id == run['id'], Evidence.source_id.is_not(None), Evidence.access != 'reference_only'))
        sid = evidence.source_id
        old_version = evidence.policy_version
    payload = rights_approval(client, sid)
    response = client.post(f'/api/v1/admin/sources/{sid}/approve', headers={'X-Dev-User': 'approver'}, json=payload)
    assert response.status_code == 200
    assert response.json()['policy_version'] > old_version
    assert client.post(f'/api/v1/admin/sources/{sid}/approve', headers={'X-Dev-User': 'approver'}, json=payload).status_code == 409
    assert client.get('/api/v1/memos/' + run['memo_id']).status_code == 409
