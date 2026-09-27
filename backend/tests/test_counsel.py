"""Synthetic counsel attestations only; these fixtures are not real legal decisions."""
import pytest
from sqlalchemy import select
from app.models import Source, User, CounselRecord, Audit, Run, Evidence, now
from app.services import rights, counsel
from conftest import rights_approval

ADMIN = {'X-Dev-User': 'admin'}
APPROVER = {'X-Dev-User': 'approver'}
COUNSEL = {'X-Dev-User': 'editor'}
CONTEXT = {'route': 'hosted_agent', 'audience': 'workspace', 'jurisdiction': 'synthetic-jurisdiction'}


@pytest.fixture
def scoped(client):
    with client.app.state.db.Session() as db:
        db.get(User, 'editor').role = 'counsel_reviewer'  # Test-only role assignment.
        source = db.get(Source, 'sample-research')
        source.policy = {**source.policy, 'basis': 'reviewed_use',
            'license_evidence_ref': 'ev_synthetic_bundle',
            'output_control': {'mode': 'bounded', 'group_id': 'synthetic',
                               'max_chars_per_response': 10000, 'max_chars_total': 100000},
            'scope': {k: [v] for k, v in CONTEXT.items()}}
        source.reviewed = False
        source.approved_by = None
        rights.record_approval(source, 'approver')  # A Boolean approval must not bypass counsel.
        source.reviewed = True
        db.commit()
        payload = {'expected_policy_version': source.policy_version,
                   'expected_rights_revision': rights.revision(source),
                   'operations': sorted(op for op in rights.OPERATIONS if source.policy.get(op) is True),
                   'evidence_ref': 'ev_synthetic_bundle', 'evidence_sha256': 'a' * 64,
                   'assessments': {k: 'ev_synthetic_' + k for k in (
                       'purpose', 'nature', 'amount_and_substantiality', 'output_and_reconstruction',
                       'market_effect', 'access_route_and_terms', 'jurisdiction')},
                   'effective_at': now() - 10, 'expires_at': now() + 3600}
    return client, payload


def path(suffix=''):
    return '/api/v1/admin/sources/sample-research/counsel-records' + suffix


def submit(scoped):
    client, payload = scoped
    result = client.post(path(), json=payload, headers=ADMIN)
    assert result.status_code == 201, result.text
    return result.json()


def review(client, row, headers=COUNSEL, decision='approved'):
    return client.post(path('/' + row['id'] + '/review'), headers=headers, json={
        'expected_record_sha256': row['record_sha256'], 'decision': decision,
        'confirm_actual_independent_counsel_review': True})


def activate(client):
    return client.post('/api/v1/admin/sources/sample-research/approve',
                       headers=APPROVER, json=rights_approval(client, 'sample-research'))


def approved(scoped):
    client, _ = scoped
    row = submit(scoped)
    assert review(client, row).status_code == 200
    response = activate(client)
    assert response.status_code == 200, response.text
    return row


def allowed(client):
    with client.app.state.db.Session() as db:
        return rights.allowed(db.get(Source, 'sample-research'), 'model_input', context=CONTEXT)


def revoke(client, row):
    return client.post(path('/' + row['id'] + '/revoke'), headers=ADMIN, json={
        'expected_record_sha256': row['record_sha256'], 'reason': 'operator_hold'})


def test_requires_counsel_and_separate_rights_activation(scoped):
    client, _ = scoped
    assert not allowed(client)
    assert activate(client).status_code == 403
    row = submit(scoped)
    assert not allowed(client)
    assert activate(client).status_code == 403
    assert review(client, row).status_code == 200
    assert not allowed(client)
    assert activate(client).status_code == 200
    assert allowed(client)
    assert activate(client).status_code == 403  # Re-review needed, no reuse for a new policy version.
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        for context in ({}, {**CONTEXT, 'route': 'mirror'}, {**CONTEXT, 'jurisdiction': 'other'}):
            assert not rights.allowed(source, 'model_input', context=context)
        assert not rights.allowed(source, 'train', context=CONTEXT)


@pytest.mark.parametrize('who', ['demo', 'reviewer', 'admin', 'approver'])
def test_only_designated_counsel_can_review(scoped, who):
    client, _ = scoped
    row = submit(scoped)
    assert review(client, row, {'X-Dev-User': who}).status_code == 403


def test_creator_cannot_review_even_after_role_change(scoped):
    client, _ = scoped
    row = submit(scoped)
    with client.app.state.db.Session() as db:
        db.get(User, 'admin').role = 'counsel_reviewer'; db.commit()
    assert review(client, row, ADMIN).status_code == 403


def test_counsel_cannot_also_activate_by_changing_role(scoped):
    client, _ = scoped
    row = submit(scoped)
    assert review(client, row).status_code == 200
    with client.app.state.db.Session() as db:
        db.get(User, 'editor').role = 'rights_approver'; db.commit()
    response = client.post('/api/v1/admin/sources/sample-research/approve', headers=COUNSEL,
                           json=rights_approval(client, 'sample-research'))
    assert response.status_code == 403


@pytest.mark.parametrize('field', ['version_label', 'text', 'canonical_url'])
def test_changed_work_cannot_receive_stale_review(scoped, field):
    client, _ = scoped
    row = submit(scoped)
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        setattr(source, field, 'changed fixture')
        db.commit()
    assert review(client, row).status_code == 409
    assert activate(client).status_code == 403


def test_rejected_or_revoked_decision_cannot_be_reapproved(scoped):
    client, _ = scoped
    row = submit(scoped)
    assert review(client, row, decision='rejected').status_code == 200
    assert review(client, row).status_code == 409
    assert activate(client).status_code == 403
    assert revoke(client, row).status_code == 200
    assert review(client, row).status_code == 409


def test_record_revocation_invalidates_dependent_outputs_and_is_idempotent(scoped):
    client, _ = scoped
    row = approved(scoped)
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        version = source.policy_version
        run = Run(workspace_id='demo-workspace', user_id='demo', workflow='deep_research',
                  question='Synthetic research', document_ids=[], inputs={})
        db.add(run); db.flush()
        db.add(Evidence(run_id=run.id, source_id=source.id, title=source.title,
                        locator='fixture', text=source.text, access='licensed_text',
                        policy_version=version, source_kind=source.kind))
        db.commit()
        context = {**CONTEXT, 'workspace_id': run.workspace_id}
        rights.run_artifact_access(db, run, context=context)
        assert revoke(client, row).status_code == 200
        # A separate API session revoked it; the already-loaded worker row must not revive it.
        assert not rights.allowed(source, 'model_input', context=CONTEXT)
        from fastapi import HTTPException
        with pytest.raises(HTTPException): rights.run_artifact_access(db, run, context=context)
    assert revoke(client, row).status_code == 200
    with client.app.state.db.Session() as db:
        assert db.get(Source, 'sample-research').policy_version == version + 1
        assert not db.get(Source, 'sample-research').reviewed
        assert len(db.scalars(select(Audit).where(Audit.action == 'counsel.revoked')).all()) == 1
    assert not allowed(client)


def test_expiry_and_future_effective_time_are_enforced(scoped, monkeypatch):
    client, payload = scoped
    approved(scoped)
    monkeypatch.setattr(counsel, 'now', lambda: payload['expires_at'])
    assert not allowed(client)
    monkeypatch.setattr(counsel, 'now', lambda: payload['effective_at'] - 1)
    assert not allowed(client)
    monkeypatch.setattr(counsel, 'now', lambda: payload['effective_at'])
    assert allowed(client)


def test_payload_tampering_fails_closed(scoped):
    client, _ = scoped
    row = approved(scoped)
    with client.app.state.db.Session() as db:
        record = db.get(CounselRecord, row['id'])
        record.proposal = {**record.proposal, 'expires_at': now() + 999999}
        db.commit()
    assert not allowed(client)


@pytest.mark.parametrize('change', [
    {'operations': ['model_input', 'model_input']}, {'operations': ['silent_training']},
    {'evidence_ref': 'Private legal analysis pasted here'}, {'effective_at': True},
    {'expires_at': 0}, {'assessments': {}}, {'unreviewed_override': True}])
def test_strict_proposal_rejects_advice_or_missing_assessments(scoped, change):
    client, payload = scoped
    assert client.post(path(), headers=ADMIN, json={**payload, **change}).status_code == 422


def test_no_automatic_jurisdiction_or_broad_operation_grant(scoped):
    client, payload = scoped
    assert client.post(path(), headers=ADMIN, json={**payload, 'operations': ['model_input']}).status_code == 422
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        source.policy = {**source.policy, 'scope': {'route': ['hosted_agent']}}
        db.commit()
        payload['expected_rights_revision'] = rights.revision(source)
    assert client.post(path(), headers=ADMIN, json=payload).status_code == 422


def test_private_references_not_public_or_audit_detail(scoped):
    client, _ = scoped
    row = approved(scoped)
    assert client.get(path()).status_code == 403
    assert client.post(path(), json=scoped[1]).status_code == 403
    data = client.get(path(), headers=COUNSEL).json()
    assert data['items'][0]['record_sha256'] == row['record_sha256']
    assert 'text' not in data['source']
    public = client.get('/api/v1/sources/sample-research').json()
    assert public['text'] is None  # Public audience lacks the reviewed context.
    assert 'ev_synthetic' not in str(public)
    audits = client.get('/api/v1/admin/audit', headers=ADMIN).json()
    assert 'ev_synthetic' not in str(audits)


def test_review_requires_attestation_and_exact_record_digest(scoped):
    client, _ = scoped
    row = submit(scoped)
    endpoint = path('/' + row['id'] + '/review')
    body = {'decision': 'approved', 'expected_record_sha256': row['record_sha256']}
    assert client.post(endpoint, headers=COUNSEL, json=body).status_code == 422
    body.update(expected_record_sha256='0'*64, confirm_actual_independent_counsel_review=True)
    assert client.post(endpoint, headers=COUNSEL, json=body).status_code == 409
