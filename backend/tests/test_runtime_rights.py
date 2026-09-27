"""Synthetic provider/reviewer contracts; no real license or model validation."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Source, Run, Evidence, Membership, Document, Memo
from app.providers.gemini import MockGemini
from app.schemas import Verification
from app.services import rights, retrieval
from app.worker import tick
from conftest import activate, create_run, key, complete_run, upload


def approve_policy(db, source, **policy):
    source.policy = {**source.policy, **policy}
    rights.record_approval(source, 'synthetic-reviewer')
    db.commit()


def start(client, **kwargs):
    activate(client)
    run = create_run(client, **kwargs)
    response = client.post('/api/v1/runs/'+run['id']+'/start',
                           json={'expected_revision': 1, 'confirm_scope': True}, headers=key())
    assert response.status_code == 202, response.text
    return run


class ProbeModel(MockGemini):
    def __init__(self, callback=None, correction=True):
        self.calls, self.callback, self.correction = [], callback, correction
    def structured(self, schema, system, data, **kwargs):
        self.calls.append((schema.__name__, data))
        result = super().structured(schema, system, data, **kwargs)
        if schema is Verification and self.correction and len(self.calls) == 3:
            result = Verification(findings=[{'claim_id': 'demo-inference', 'severity': 'block', 'reason': 'Synthetic correction trigger.'}], limitations=[])
        if self.callback: self.callback(len(self.calls), data)
        return result


def test_trusted_context_ignores_user_inputs_and_unverified_entitlements(client):
    run = create_run(client)
    with client.app.state.db.Session() as db:
        row = db.get(Run, run['id'])
        row.context = {'workspace_id': 'forged', 'provider': 'forged', 'region': 'forged',
                       'seat_id': 'fake-seat', 'retention': 'none', 'jurisdiction': 'US'}
        row.inputs = dict(row.context)
        context = rights.runtime_context(db, row, client.app.state.settings)
        assert context == {'workspace_id': 'demo-workspace', 'route': 'hosted_agent',
                           'audience': 'workspace', 'provider': 'mock', 'region': 'us'}
        source = db.get(Source, 'sample-research')
        approve_policy(db, source, scope={'workspace_id': ['demo-workspace'], 'provider': ['mock'], 'region': ['us']})
        assert rights.allowed(source, 'model_input', context=context)
        for field in ('seat_id', 'jurisdiction', 'retention'):
            approve_policy(db, source, scope={field: ['fake-seat', 'none', 'US']})
            assert not rights.allowed(source, 'model_input', context=context)


def test_scoped_source_retrieval_and_saved_export_use_server_context(client):
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research')
        approve_policy(db, source, scope={'workspace_id': ['demo-workspace'], 'provider': ['mock'],
                       'region': ['us'], 'route': ['hosted_agent'], 'audience': ['workspace']})
    run = complete_run(client)
    evidence = client.get('/api/v1/runs/'+run['id']+'/evidence').json()['items']
    item = next(e for e in evidence if e['source_id'] == 'sample-research')
    assert client.get('/api/v1/evidence/'+item['id']).json()['text']
    memo = client.post('/api/v1/runs/'+run['id']+'/memo').json()
    assert client.get('/api/v1/memos/'+memo['id']+'/export').status_code == 200
    # A configured region change does not inherit approval for the old context.
    client.app.state.settings.model_location = 'eu'
    assert client.get('/api/v1/evidence/'+item['id']).json()['text'] is None
    assert client.get('/api/v1/runs/'+run['id']).json()['access_blocked']
    assert client.get('/api/v1/memos/'+memo['id']+'/export').status_code == 409


@pytest.mark.parametrize('scope', [{'workspace_id': ['reviewer-private']}, {'provider': ['google_cloud']},
                                  {'region': ['eu']}, {'seat_id': ['demo']}])
def test_mismatched_scope_never_enters_model_evidence(client, scope):
    with client.app.state.db.Session() as db:
        source = db.get(Source, 'sample-research'); approve_policy(db, source, scope=scope)
        row = Run(workspace_id='demo-workspace', user_id='demo', question='implementation subscription research',
                  workflow='deep_research', context={}, document_ids=[], inputs={})
        db.add(row); db.flush()
        hits = retrieval.search(db, row, row.question, rights_context=rights.runtime_context(db, row, client.app.state.settings))
        assert all(not hit['text'] for hit in hits if hit['source_id'] == source.id)


@pytest.mark.parametrize('after_call', [2, 3, 4, 5])
@pytest.mark.parametrize('change', ['disable', 'expire'])
def test_revocation_stops_each_remaining_provider_call_and_release(client, monkeypatch, after_call, change):
    run = start(client)
    def revoke(count, payload):
        if count != after_call: return
        sid = next(e['source_id'] for e in payload['evidence'] if e['source_id'] and e['text'])
        with client.app.state.db.Session() as db:
            source = db.get(Source, sid)
            if change == 'disable': source.enabled = False
            else: approve_policy(db, source, expires_at=1)
            db.commit()
    model = ProbeModel(revoke)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    with client.app.state.db.Session() as db:
        row = db.get(Run, run['id'])
        assert row.state == 'blocked' and row.error_code == 'SOURCE_CHANGED' and row.result is None
    assert len(model.calls) == after_call


@pytest.mark.parametrize('after_call', [0, 1, 2, 3, 4, 5])
def test_membership_revocation_stops_worker_at_every_boundary(client, monkeypatch, after_call):
    run = start(client)
    def revoke(count, _):
        if count != after_call: return
        with client.app.state.db.Session() as db:
            db.delete(db.get(Membership, ('demo-workspace', 'demo'))); db.commit()
    if after_call == 0: revoke(0, {})
    model = ProbeModel(revoke)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    with client.app.state.db.Session() as db:
        row = db.get(Run, run['id'])
        assert row.state == 'blocked' and row.error_code == 'WORKSPACE_ACCESS_REVOKED' and row.result is None
    assert len(model.calls) == after_call


def test_downgraded_membership_cannot_execute_paid_run(client, monkeypatch):
    run = start(client)
    with client.app.state.db.Session() as db:
        db.get(Membership, ('demo-workspace', 'demo')).role = 'viewer'; db.commit()
    model = ProbeModel()
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    assert not model.calls
    assert client.get('/api/v1/runs/'+run['id']).json()['error_code'] == 'WORKSPACE_ACCESS_REVOKED'


def test_changed_preprocessed_document_stops_before_analysis(client, monkeypatch):
    activate(client)
    doc = upload(client)
    run = start(client, docs=[doc['id']])
    def mutate(count, _):
        if count != 1: return
        with client.app.state.db.Session() as db:
            db.get(Document, doc['id']).chunks = [{'locator': 'Changed', 'text': 'Changed bytes'}]; db.commit()
    model = ProbeModel(mutate)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    assert len(model.calls) == 1
    assert client.get('/api/v1/runs/'+run['id']).json()['error_code'] == 'SOURCE_CHANGED'


def test_saved_memo_change_stops_correction_call(client, monkeypatch):
    parent = complete_run(client)
    memo = client.post('/api/v1/runs/'+parent['id']+'/memo').json()
    run = start(client, workflow='memo_review', inputs={'memo_id': memo['id']})
    def mutate(count, _):
        if count != 3: return
        with client.app.state.db.Session() as db:
            db.get(Memo, memo['id']).body += '\nUser edit during processing'; db.commit()
    model = ProbeModel(mutate)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    assert len(model.calls) == 3
    assert client.get('/api/v1/runs/'+run['id']).json()['error_code'] == 'SOURCE_CHANGED'


def test_reference_label_cannot_smuggle_body(client):
    run = complete_run(client)
    with client.app.state.db.Session() as db:
        e = db.scalar(select(Evidence).where(Evidence.run_id == run['id']))
        e.access = 'reference_only'; e.text = 'Unauthorized body hidden under metadata label'
        assert not rights.evidence_allowed(db, e)


def test_cross_workspace_document_cannot_back_evidence(client):
    activate(client)
    doc = upload(client); run = complete_run(client, docs=[doc['id']])
    with client.app.state.db.Session() as db:
        db.get(Document, doc['id']).workspace_id = 'reviewer-private'; db.commit()
        row = db.get(Run, run['id'])
        with pytest.raises(HTTPException): rights.run_artifact_access(db, row)


def test_authorized_correction_sequence_completes(client, monkeypatch):
    run = start(client); model = ProbeModel()
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    assert [name for name, _ in model.calls] == ['Plan', 'Analysis', 'Verification', 'Analysis', 'Verification']
    assert client.get('/api/v1/runs/'+run['id']).json()['state'] == 'completed_with_limitations'


def test_current_collaborator_can_read_after_execution_owner_leaves(client):
    run = complete_run(client)
    memo = client.post('/api/v1/runs/'+run['id']+'/memo').json()
    with client.app.state.db.Session() as db:
        db.delete(db.get(Membership, ('demo-workspace', 'demo'))); db.commit()
    # Source access follows the authenticated viewer; it is not the creator's subscription.
    headers = {'X-Dev-User': 'reviewer'}
    assert client.get('/api/v1/runs/'+run['id']).status_code == 404
    response = client.get('/api/v1/runs/'+run['id'], headers=headers)
    assert response.status_code == 200 and response.json()['result'] and not response.json()['access_blocked']
    assert client.get('/api/v1/memos/'+memo['id']+'/export', headers=headers).status_code == 200


def test_revocation_before_retrieval_sends_no_source_body(client, monkeypatch):
    run = start(client)
    def revoke(count, _):
        if count == 1:
            with client.app.state.db.Session() as db:
                db.get(Source, 'sample-research').enabled = False; db.commit()
    model = ProbeModel(revoke)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    tick(client.app.state.db, client.app.state.settings)
    assert client.get('/api/v1/runs/'+run['id']).json()['state'] == 'completed_with_limitations'
    assert all(e['source_id'] != 'sample-research' for _, data in model.calls for e in data.get('evidence', []))


def test_selected_file_outside_retrieval_subset_still_revokes_result(client):
    activate(client)
    doc = upload(client)
    run = complete_run(client, docs=[doc['id']])
    with client.app.state.db.Session() as db:
        # Model-independent preprocessing can use a selected file without a retained excerpt.
        from sqlalchemy import delete
        db.execute(delete(Evidence).where(Evidence.run_id == run['id'], Evidence.document_id == doc['id']))
        db.get(Document, doc['id']).status = 'deleted'; db.commit()
    assert client.get('/api/v1/runs/'+run['id']).json()['access_blocked']
