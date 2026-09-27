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
