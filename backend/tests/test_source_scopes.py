"""Synthetic entitlement evidence and attestations; no real publisher seats are granted."""
import pytest
from types import SimpleNamespace
from app.models import Source, SourceScopeGrant, Run, Membership, now
from app.services import rights, source_scopes
from app.worker import tick
from conftest import scope_grant, complete_run, create_run
from test_runtime_rights import start, ProbeModel

ADMIN = {'X-Dev-User': 'admin'}
APPROVER = {'X-Dev-User': 'approver'}
VALUES = {'seat_id': 'synthetic-seat', 'jurisdiction': 'synthetic-country', 'retention': 'synthetic-retention'}


@pytest.fixture
def scoped(client):
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        source.policy = {**source.policy, 'scope': {k: [v] for k, v in VALUES.items()}}
        rights.record_approval(source, 'approver'); db.commit()
    return client


def path(record=None, action=''):
    base = '/api/v1/admin/sources/sample-research/scope-grants'
    return base + ('/' + record['id'] + '/' + action if record else '')


def revoke(client, row):
    response = client.post(path(row, 'revoke'), headers=ADMIN, json={
        'expected_record_sha256': row['record_sha256'], 'reason': 'seat_removed'})
    assert response.status_code == 200, response.text
    return response.json()


def permitted(client, actor='demo', workspace='demo-workspace', action='model_input'):
    with client.app.state.db.Session() as db:
        context = rights.runtime_context(db, SimpleNamespace(workspace_id=workspace, user_id=actor), client.app.state.settings)
        return rights.allowed(db.get(Source, 'sample-research'), action, context=context)


def test_client_context_and_subscription_cannot_manufacture_scopes(scoped):
    run = create_run(scoped)
    with scoped.app.state.db.Session() as db:
        db.get(Run, run['id']).context = VALUES
        db.commit()
    assert not permitted(scoped)
    with scoped.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        forged = {**VALUES, 'workspace_id': 'demo-workspace', 'actor_id': 'demo', 'subscription': 'paid'}
        assert not rights.allowed(source, 'model_input', context=forged)
        context = rights.runtime_context(db, db.get(Run, run['id']), scoped.app.state.settings)
        context.update(VALUES)
        assert not rights.allowed(source, 'model_input', context=context)
    grant = scope_grant(scoped)
    assert permitted(scoped)
    revoke(scoped, grant)
    assert not permitted(scoped)


def test_verified_scopes_reach_worker_evidence_and_saved_exports(scoped):
    grant = scope_grant(scoped)
    run = complete_run(scoped)
    evidence = scoped.get('/api/v1/runs/' + run['id'] + '/evidence').json()['items']
    item = next(e for e in evidence if e['source_id'] == 'sample-research')
    assert scoped.get('/api/v1/evidence/' + item['id']).json()['text']
    memo = scoped.post('/api/v1/runs/' + run['id'] + '/memo').json()
    assert scoped.get('/api/v1/memos/' + memo['id'] + '/export').status_code == 200
    revoke(scoped, grant)
    assert scoped.get('/api/v1/runs/' + run['id']).json()['access_blocked']
    assert scoped.get('/api/v1/evidence/' + item['id']).json()['text'] is None
    assert scoped.get('/api/v1/memos/' + memo['id'] + '/export').status_code == 409


@pytest.mark.parametrize('after_call', [2, 3, 4, 5])
def test_seat_revocation_blocks_every_remaining_model_call(scoped, monkeypatch, after_call):
    grant = scope_grant(scoped)
    run = start(scoped)
    def callback(count, _):
        if count == after_call: revoke(scoped, grant)
    model = ProbeModel(callback)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(scoped.app.state.db, scoped.app.state.settings)
    with scoped.app.state.db.Session() as db:
        result = db.get(Run, run['id'])
        assert result.state == 'blocked' and result.result is None
    assert len(model.calls) == after_call


def test_viewer_needs_their_own_grant_and_expiry_does_not_revoke_colleague(scoped, monkeypatch):
    first = scope_grant(scoped)
    assert not permitted(scoped, actor='reviewer')
    second = scope_grant(scoped, user_id='reviewer', expires_at=now()+7200)
    assert permitted(scoped, actor='reviewer')
    run = complete_run(scoped)
    memo = scoped.post('/api/v1/runs/' + run['id'] + '/memo').json()
    headers = {'X-Dev-User': 'reviewer'}
    assert scoped.get('/api/v1/memos/'+memo['id']+'/export', headers=headers).status_code == 200
    monkeypatch.setattr(source_scopes, 'now', lambda: first['proposal']['expires_at'])
    assert not permitted(scoped)
    assert permitted(scoped, actor='reviewer')
    revoke(scoped, first)
    assert scoped.get('/api/v1/memos/'+memo['id']+'/export', headers=headers).status_code == 200
    revoke(scoped, second)
    assert scoped.get('/api/v1/memos/'+memo['id']+'/export', headers=headers).status_code == 409


@pytest.mark.parametrize('field,value', [('model_provider','google_cloud'), ('model_location','eu'),
                                       ('google_cloud_project','another-project'), ('model_id','different-model')])
def test_provider_binding_requires_fresh_verification(scoped, field, value):
    scope_grant(scoped)
    assert permitted(scoped)
    setattr(scoped.app.state.settings, field, value)
    assert not permitted(scoped)


def test_loaded_context_rechecks_grant_and_membership(scoped):
    grant = scope_grant(scoped)
    with scoped.app.state.db.Session() as db:
        context = rights.runtime_context(db, SimpleNamespace(workspace_id='demo-workspace', user_id='demo'), scoped.app.state.settings)
        source = db.get(Source, 'sample-research')
        assert rights.allowed(source, 'model_input', context=context)
        with scoped.app.state.db.Session() as other:
            other.delete(other.get(Membership, ('demo-workspace', 'demo'))); other.commit()
        assert not rights.allowed(source, 'model_input', context=context)
        revoke(scoped, grant)
        assert not rights.allowed(source, 'model_input', context=context)


def test_replacement_is_atomic_and_old_grant_cannot_return(scoped):
    old = scope_grant(scoped)
    new = scope_grant(scoped, operations=['quote'])
    assert not permitted(scoped, action='model_input')
    assert permitted(scoped, action='quote')
    with scoped.app.state.db.Session() as db:
        assert db.get(SourceScopeGrant, old['id']).status == 'superseded'
    response = scoped.post(path(old, 'approve'), headers=APPROVER, json={
        'expected_record_sha256': old['record_sha256'], 'confirm_actual_entitlement_verification': True})
    assert response.status_code == 409
    revoke(scoped, new)
    assert not permitted(scoped, action='quote')
    # Revocation does not change global source version or silently activate an earlier grant.
    with scoped.app.state.db.Session() as db:
        assert db.get(Source, 'sample-research').policy_version == old['proposal']['expected_policy_version']


def test_work_revision_and_record_integrity_are_both_required(scoped):
    grant = scope_grant(scoped)
    with scoped.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        source.version_label = 'Changed'
        rights.record_approval(source, 'approver'); db.commit()
    assert not permitted(scoped)
    current = scope_grant(scoped)
    assert permitted(scoped)
    with scoped.app.state.db.Session() as db:
        row = db.get(SourceScopeGrant, current['id'])
        row.proposal = {**row.proposal, 'expires_at': now()+999999}; db.commit()
    assert not permitted(scoped)
    assert grant['record_sha256'] != current['record_sha256']


def test_protected_record_routes_and_public_metadata(scoped):
    grant = scope_grant(scoped)
    assert scoped.get(path()).status_code == 403
    assert scoped.post(path(), json=grant['proposal']).status_code == 403
    assert scoped.post(path(grant, 'revoke'), json={'expected_record_sha256': grant['record_sha256'],
        'reason': 'operator_hold'}).status_code == 403
    public = scoped.get('/api/v1/sources/sample-research').json()
    assert public['text'] is None and 'synthetic-seat' not in str(public)
    assert 'ev_synthetic' not in str(scoped.get('/api/v1/admin/audit', headers=ADMIN).json())


def test_workspace_and_runtime_context_identity_are_not_transferable(scoped):
    scope_grant(scoped)
    other = scoped.post('/api/v1/workspaces', json={'name': 'Synthetic other workspace'}).json()
    assert not permitted(scoped, workspace=other['id'])
    with scoped.app.state.db.Session() as db:
        context = rights.runtime_context(db, SimpleNamespace(workspace_id='demo-workspace', user_id='demo'), scoped.app.state.settings)
        source = db.get(Source, 'sample-research')
        assert rights.allowed(source, 'model_input', context=context)
        assert not rights.allowed(source, 'model_input', context=dict(context))
        with scoped.app.state.db.Session() as other_db:
            assert not rights.allowed(other_db.get(Source, 'sample-research'), 'model_input', context=context)


def test_future_and_expired_grants_do_not_supply_scope(scoped, monkeypatch):
    grant = scope_grant(scoped, effective_at=now()+100, expires_at=now()+200)
    assert not permitted(scoped)
    monkeypatch.setattr(source_scopes, 'now', lambda: grant['proposal']['effective_at'])
    assert permitted(scoped)
    monkeypatch.setattr(source_scopes, 'now', lambda: grant['proposal']['expires_at'])
    assert not permitted(scoped)


@pytest.mark.parametrize('change', [
    {'operations': ['unknown']}, {'operations': ['quote', 'quote']}, {'operations': ['train']},
    {'values': {'seat_id': 'synthetic-seat'}}, {'values': {**VALUES, 'jurisdiction': 'other'}},
    {'provider': 'unauthorized'}, {'evidence_ref': 'Pasted private agreement'}, {'evidence_sha256': 'bad'},
    {'effective_at': True}, {'expires_at': 0}, {'subject_user_id': 'missing'},
    {'unknown_override': True}])
def test_unknown_partial_unreviewed_scope_rejected(scoped, change):
    grant = scope_grant(scoped)
    response = scoped.post(path(), headers=ADMIN, json={**grant['proposal'], **change})
    assert response.status_code == 422, response.text


def pending(scoped, **changes):
    base = scope_grant(scoped)
    response = scoped.post(path(), headers=ADMIN, json={**base['proposal'], **changes})
    assert response.status_code == 201, response.text
    return response.json()


def approve(scoped, row, actor='approver', **changes):
    return scoped.post(path(row, 'approve'), headers={'X-Dev-User': actor}, json={
        'expected_record_sha256': row['record_sha256'], 'confirm_actual_entitlement_verification': True, **changes})


def test_independent_approval_required_even_after_role_change(scoped):
    from app.models import User
    grant = pending(scoped)
    assert approve(scoped, grant, actor='demo').status_code == 403
    assert approve(scoped, grant, actor='admin').status_code == 403
    with scoped.app.state.db.Session() as db:
        db.get(User, 'admin').role = 'rights_approver'; db.commit()
    assert approve(scoped, grant, actor='admin').status_code == 403
    with scoped.app.state.db.Session() as db:
        db.get(User, 'demo').role = 'rights_approver'; db.commit()
    assert approve(scoped, grant, actor='demo').status_code == 403


def test_pending_record_cannot_skip_review_or_change_under_approval(scoped):
    grant = pending(scoped, operations=['quote'])
    assert approve(scoped, grant, confirm_actual_entitlement_verification=False).status_code == 422
    assert approve(scoped, grant, expected_record_sha256='0'*64).status_code == 409
    with scoped.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research'); source.version_label = 'new'; db.commit()
    assert approve(scoped, grant).status_code == 409


def test_revocation_is_idempotent_and_cannot_be_reapproved(scoped):
    from sqlalchemy import select
    from app.models import Audit
    grant = scope_grant(scoped)
    revoke(scoped, grant); revoke(scoped, grant)
    assert approve(scoped, grant).status_code == 409
    with scoped.app.state.db.Session() as db:
        assert len(db.scalars(select(Audit).where(Audit.action == 'source_scope.revoked', Audit.target_id == grant['id'])).all()) == 1
