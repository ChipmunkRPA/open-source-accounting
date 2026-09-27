import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.worker import tick


@pytest.fixture
def client(tmp_path):
    config = Settings(app_env='test', database_url=f'sqlite:///{tmp_path}/test.db', data_dir=str(tmp_path),
                      auth_mode='dev', model_provider='mock', demo_billing_enabled=True,
                      auto_seed=True, auto_create_schema=True, _env_file=None)
    with TestClient(create_app(config)) as c:
        yield c


def key(value=None):
    return {'Idempotency-Key': value or str(uuid.uuid4())}


def activate(client):
    r = client.post('/api/v1/dev/subscription', json={'state': 'active'})
    assert r.status_code == 200


def create_run(client, workflow='deep_research', docs=None, inputs=None, **changes):
    body = {'workspace_id': 'demo-workspace', 'workflow': workflow,
            'question': 'How should we research implementation fees in a subscription contract?',
            'facts': [{'text': 'The fictional agreement has an implementation fee.', 'status': 'confirmed'}],
            'document_ids': docs or [], 'inputs': inputs or {}}
    body.update(changes)
    response = client.post('/api/v1/runs', json=body, headers=key())
    assert response.status_code == 201, response.text
    return response.json()


def complete_run(client, workflow='deep_research', **kwargs):
    activate(client)
    run = create_run(client, workflow, **kwargs)
    response = client.post(f'/api/v1/runs/{run["id"]}/start', json={'expected_revision': 1, 'confirm_scope': True}, headers=key())
    assert response.status_code == 202, response.text
    assert tick(client.app.state.db, client.app.state.settings)
    result = client.get('/api/v1/runs/'+run['id']).json()
    assert result['state'] == 'completed_with_limitations', result
    return result


def upload(client, text='Fictional contract: annual subscription fee is 12000. Implementation fee is 2000.', name='contract.txt'):
    response = client.post('/api/v1/workspaces/demo-workspace/documents',
                files={'file': (name, text.encode(), 'text/plain')},
                data={'authorization_basis': 'own_original'})
    assert response.status_code == 201, response.text
    return response.json()


def rights_approval(client, source_id):
    """Synthetic test attestation only; never professional or legal approval."""
    from app.models import Source
    from app.services.rights import revision
    with client.app.state.db.Session() as db:
        source = db.get(Source, source_id)
        return {'expected_policy_version': source.policy_version,
                'expected_rights_revision': revision(source),
                'confirm_actual_rights_review': True}


def scope_grant(client, source_id='sample-research', user_id='demo', workspace_id='demo-workspace', **changes):
    """Synthetic independent verification only, never an actual publisher entitlement."""
    from app.models import Source, now
    from app.services import rights
    with client.app.state.db.Session() as db:
        source = db.get(Source, source_id)
        settings = client.app.state.settings
        payload = {'expected_policy_version': source.policy_version,
            'expected_rights_revision': rights.revision(source), 'subject_user_id': user_id,
            'workspace_id': workspace_id, 'operations': sorted(op for op in rights.OPERATIONS if source.policy.get(op) is True),
            'values': {k: v[0] for k, v in source.policy.get('scope', {}).items() if k in {'seat_id', 'jurisdiction', 'retention'}},
            'provider': settings.model_provider, 'project': settings.google_cloud_project,
            'region': settings.model_location, 'model_id': settings.model_id,
            'evidence_ref': 'ev_synthetic_entitlement', 'evidence_sha256': 'b'*64,
            'effective_at': now()-10, 'expires_at': now()+3600, **changes}
    endpoint = '/api/v1/admin/sources/' + source_id + '/scope-grants'
    result = client.post(endpoint, headers={'X-Dev-User': 'admin'}, json=payload)
    assert result.status_code == 201, result.text
    row = result.json()
    result = client.post(endpoint + '/' + row['id'] + '/approve', headers={'X-Dev-User': 'approver'}, json={
        'expected_record_sha256': row['record_sha256'], 'confirm_actual_entitlement_verification': True})
    assert result.status_code == 200, result.text
    return result.json()
