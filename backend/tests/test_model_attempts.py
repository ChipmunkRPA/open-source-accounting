"""Synthetic costs and failures only; no Cloud credentials, requests or actual bills."""
import json
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from app.config import Settings
from app.errors import ProviderError
from app.models import ModelAttempt, Run, Job, now
from app.providers.gemini import Gemini, MockGemini
from app.schemas import Plan
from app.services import model_attempts as ledger
from app.worker import tick
from conftest import activate, create_run, key, complete_run
from test_gemini_contract import response, fake_http


def metadata(token='one'):
    return dict(key=ledger.operation_key('synthetic', token), phase='planning', user_id='demo',
        workspace_id='demo-workspace', thinking='MEDIUM', output_limit=2500, prompt_version='synthetic-1')


def settings():
    return Settings(model_provider='google_cloud', google_cloud_project='test-project', _env_file=None)


def rows(client):
    with client.app.state.db.Session() as db:
        return db.scalars(select(ModelAttempt).order_by(ModelAttempt.started_at, ModelAttempt.id)).all()


def invoke(client, model, token='one', **kw):
    return ledger.invoke(client.app.state.db.Session, settings(), model,
        lambda: model.structured(Plan, 'Synthetic private prompt', {}), **{**metadata(token), **kw})


def plan_response():
    return response('{"issues":[],"missing_questions":[],"proposed_queries":[],"scope":"synthetic"}')


def test_receipt_is_committed_before_dispatch_and_contains_no_prompt(client):
    def transport(*_):
        receipt = rows(client)[0]
        assert receipt.outcome == 'pending' and receipt.cost_state == 'unknown'
        assert receipt.usage is None and receipt.finished_at is None
        return plan_response()
    result = invoke(client, Gemini(settings(), transport))
    assert result.scope == 'synthetic'
    row = rows(client)[0]
    assert row.outcome == 'succeeded' and row.cost_state == 'estimated' and row.http_status == 200
    assert row.usage['thoughtsTokenCount'] == 2
    assert Decimal(row.cost_estimate['estimated_usd']) > 0
    payload = {c.name: getattr(row, c.name) for c in ModelAttempt.__table__.columns}
    assert 'Synthetic private prompt' not in json.dumps(payload)
    assert '"scope"' not in json.dumps(payload)


def test_billed_schema_failure_keeps_exact_usage_and_estimate(client):
    with pytest.raises(ProviderError, match='SCHEMA_INVALID'):
        invoke(client, Gemini(settings(), lambda *_: response('invalid JSON private body')))
    row = rows(client)[0]
    assert row.outcome == 'failed' and row.cost_state == 'estimated'
    assert row.usage['totalTokenCount'] == 15 and row.error_code == 'MODEL_SCHEMA_INVALID'


@pytest.mark.parametrize('status,cost_state', [(429, 'not_incurred'), (403, 'not_incurred'), (503, 'not_incurred')])
def test_known_non_200_is_distinct_from_unknown_cost(client, monkeypatch, status, cost_state):
    session, _ = fake_http(monkeypatch, status=status)
    with pytest.raises(ProviderError):
        invoke(client, Gemini(settings()))
    row = rows(client)[0]
    assert row.http_status == status and row.cost_state == cost_state and row.usage is None
    session.post.assert_called_once()


def test_ambiguous_timeout_never_becomes_zero_cost(client):
    def timeout(*_):
        raise TimeoutError('Synthetic private timeout detail')
    with pytest.raises(ProviderError, match='^MODEL_REQUEST_FAILED$'):
        invoke(client, Gemini(settings(), timeout))
    row = rows(client)[0]
    assert row.cost_state == 'unknown' and row.cost_estimate is None and row.usage is None
    assert row.error_code == 'MODEL_REQUEST_FAILED'


def test_invalid_usage_after_http_200_stays_unknown(client):
    data = plan_response()
    data.pop('usageMetadata')
    with pytest.raises(ProviderError, match='USAGE_INVALID'):
        invoke(client, Gemini(settings(), lambda *_: data))
    assert rows(client)[0].cost_state == 'unknown'
    assert rows(client)[0].http_status == 200


def test_unusable_output_token_counts_are_not_estimated_as_zero(client):
    data = plan_response()
    data['usageMetadata'].update(candidatesTokenCount=0, totalTokenCount=12)
    with pytest.raises(ProviderError, match='USAGE_INVALID'):
        invoke(client, Gemini(settings(), lambda *_: data))
    assert rows(client)[0].cost_state == 'unknown' and rows(client)[0].usage is None


def test_pre_dispatch_rejection_is_not_incurred(client):
    model = Gemini(settings(), Mock())
    with pytest.raises(ProviderError, match='INPUT_LIMIT'):
        ledger.invoke(client.app.state.db.Session, settings(), model,
            lambda: model.structured(Plan, 'x'*180000, {}), **metadata())
    assert rows(client)[0].cost_state == 'not_incurred'
    model.transport.assert_not_called()


@pytest.mark.parametrize('finished', [False, True])
def test_duplicate_operation_does_not_repeat_inference(client, finished):
    transport = Mock(return_value=plan_response())
    model = Gemini(settings(), transport)
    if finished:
        invoke(client, model)
    else:
        ledger.prepare(client.app.state.db.Session, settings(), **metadata())
    before = transport.call_count
    with pytest.raises(ProviderError, match='ATTEMPT_ALREADY_RECORDED'):
        invoke(client, model)
    assert transport.call_count == before and len(rows(client)) == 1


def test_process_death_leaves_pending_unknown_receipt(client):
    def die():
        raise SystemExit('synthetic process termination')
    with pytest.raises(SystemExit):
        ledger.invoke(client.app.state.db.Session, settings(), Mock(), die, **metadata())
    row = rows(client)[0]
    assert row.outcome == 'pending' and row.cost_state == 'unknown' and row.finished_at is None


def test_settlement_failure_withholds_result_and_preserves_pending(client, monkeypatch):
    def cannot_settle(*args, **kwargs):
        raise ProviderError('MODEL_LEDGER_UNAVAILABLE')
    monkeypatch.setattr(ledger, 'settle', cannot_settle)
    with pytest.raises(ProviderError, match='LEDGER_UNAVAILABLE'):
        invoke(client, Gemini(settings(), lambda *_: plan_response()))
    assert rows(client)[0].outcome == 'pending'


def test_receipt_cannot_be_rewritten(client):
    model = Gemini(settings(), lambda *_: plan_response())
    invoke(client, model)
    receipt = rows(client)[0]
    with pytest.raises(ProviderError, match='ALREADY_SETTLED'):
        ledger.settle(client.app.state.db.Session, receipt.id, model, succeeded=False, error_code='MODEL_TIMEOUT')
    assert rows(client)[0].outcome == 'succeeded'


def test_chat_records_mock_and_deduplicates_then_survives_chat_deletion(client):
    chat = client.post('/api/v1/chats', json={'title': 'Synthetic'}).json()
    route = '/api/v1/chats/'+chat['id']+'/messages'
    headers = key()
    for _ in range(2):
        assert client.post(route, json={'message': 'Hello synthetic example'}, headers=headers).status_code == 200
    assert len(rows(client)) == 1
    assert rows(client)[0].phase == 'chat' and rows(client)[0].cost_state == 'mock'
    assert client.delete('/api/v1/chats/'+chat['id']).status_code == 204
    assert rows(client)[0].chat_id is None


def test_mock_worker_records_every_step_separately(client):
    run = complete_run(client)
    receipts = rows(client)
    assert {r.phase for r in receipts} == {'planning', 'synthesis', 'verification'}
    assert all(r.run_id == run['id'] and r.cost_state == 'mock' for r in receipts)
    assert len({r.execution_id for r in receipts}) == 1


def test_correction_and_reverification_have_distinct_receipts(client, monkeypatch):
    from test_runtime_rights import ProbeModel
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: ProbeModel())
    complete_run(client)
    assert {r.phase for r in rows(client)} == {'planning', 'synthesis', 'verification', 'correction', 'reverification'}
    assert len({r.operation_key for r in rows(client)}) == 5


def test_worker_failure_preserves_prior_steps_and_explicit_restart_gets_new_execution(client, monkeypatch):
    activate(client)
    run = create_run(client)
    class FailingModel(MockGemini):
        count = 0
        def structured(self, *args, **kwargs):
            self.count += 1
            if self.count == 2:
                raise ProviderError('MODEL_TIMEOUT')
            return super().structured(*args, **kwargs)
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: FailingModel())
    route = '/api/v1/runs/'+run['id']+'/start'
    for _ in range(2):
        assert client.post(route, json={'expected_revision': 1, 'confirm_scope': True}, headers=key()).status_code == 202
        tick(client.app.state.db, client.app.state.settings)
    receipts = rows(client)
    assert len(receipts) == 4 and sum(r.outcome == 'failed' for r in receipts) == 2
    assert len({r.execution_id for r in receipts}) == 2
    assert client.get('/api/v1/runs/'+run['id']).json()['state'] == 'failed'


def test_lease_recovery_cannot_blindly_repeat_a_recorded_step(client, monkeypatch):
    activate(client)
    run = create_run(client)
    assert client.post('/api/v1/runs/'+run['id']+'/start',
        json={'expected_revision': 1, 'confirm_scope': True}, headers=key()).status_code == 202
    class Dies(MockGemini):
        def structured(self, *args, **kwargs):
            raise SystemExit('synthetic crash during dispatch')
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: Dies())
    with pytest.raises(SystemExit):
        tick(client.app.state.db, client.app.state.settings)
    with client.app.state.db.Session() as db:
        job = db.scalar(select(Job).where(Job.run_id == run['id']))
        job.lease_until = 1
        db.commit()
    model = MockGemini()
    model.structured = Mock(side_effect=AssertionError('must not dispatch again'))
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: model)
    assert tick(client.app.state.db, client.app.state.settings)
    assert len(rows(client)) == 1 and rows(client)[0].outcome == 'pending'
    model.structured.assert_not_called()
    assert client.get('/api/v1/runs/'+run['id']).json()['error_code'] == 'MODEL_ATTEMPT_ALREADY_RECORDED'


def test_report_is_admin_only_and_unknown_liability_prevents_total(client):
    ledger.prepare(client.app.state.db.Session, settings(), **metadata())
    invoke(client, Gemini(settings(), lambda *_: plan_response()), token='two')
    url = f'/api/v1/admin/model-usage?start_at={now()-100}&end_at={now()+100}'
    assert client.get(url).status_code == 403
    assert client.get(url, headers={'X-Dev-User': 'approver'}).status_code == 403
    result = client.get(url, headers={'X-Dev-User': 'admin'}).json()
    assert result['attempts'] == 2 and result['unknown_cost_attempts'] == 1
    assert result['complete_estimate_usd'] is None and Decimal(result['known_estimate_subtotal_usd']) > 0
    assert result['agent_cohort']['estimated_model_usd_per_completed_run'] is None
    assert 'user_id' not in json.dumps(result)


def test_failed_task_cost_is_in_successful_task_denominator_cohort(client):
    first, second = create_run(client), create_run(client)
    with client.app.state.db.Session() as db:
        db.get(Run, first['id']).state = 'completed_with_limitations'
        db.get(Run, second['id']).state = 'failed'
        db.commit()
    invoke(client, Gemini(settings(), lambda *_: plan_response()), 'first', run_id=first['id'])
    with pytest.raises(ProviderError):
        invoke(client, Gemini(settings(), lambda *_: response('bad JSON')), 'second', run_id=second['id'])
    with client.app.state.db.Session() as db:
        result = ledger.report(db, start_at=now()-100, end_at=now()+100)
    cohort = result['agent_cohort']
    assert cohort['completed_runs'] == 1 and cohort['tracked_runs'] == 2
    assert Decimal(cohort['estimated_model_usd_per_completed_run']) == Decimal(result['known_estimate_subtotal_usd'])


def test_complete_cohort_includes_later_attempts_and_does_not_count_active_as_success(client):
    run = create_run(client)
    invoke(client, Gemini(settings(), lambda *_: plan_response()), 'first', run_id=run['id'])
    invoke(client, Gemini(settings(), lambda *_: plan_response()), 'second', run_id=run['id'])
    with client.app.state.db.Session() as db:
        receipts = db.scalars(select(ModelAttempt).order_by(ModelAttempt.operation_key)).all()
        receipts[0].started_at, receipts[1].started_at = 100, 300
        db.commit()
        result = ledger.report(db, start_at=90, end_at=200)
    assert result['attempts'] == 1
    cohort = result['agent_cohort']
    assert cohort['active_runs'] == 1 and cohort['estimated_model_usd_per_completed_run'] is None
    assert Decimal(cohort['known_estimate_subtotal_usd']) == Decimal(result['known_estimate_subtotal_usd'])*2


def test_report_rejects_invalid_window(client):
    assert client.get('/api/v1/admin/model-usage?start_at=2&end_at=1', headers={'X-Dev-User': 'admin'}).status_code == 422


def test_unavailable_ledger_prevents_any_provider_call():
    factory, call = Mock(side_effect=RuntimeError('synthetic db unavailable')), Mock()
    with pytest.raises(ProviderError, match='LEDGER_UNAVAILABLE'):
        ledger.invoke(factory, settings(), Mock(), call, **metadata())
    call.assert_not_called()


def test_deleted_run_cost_is_retained_and_cannot_silently_improve_ratio(client):
    first, second = create_run(client), create_run(client)
    for index, run in enumerate([first, second]):
        invoke(client, Gemini(settings(), lambda *_: plan_response()), str(index), run_id=run['id'])
    with client.app.state.db.Session() as db:
        db.get(Run, first['id']).state = 'completed_with_limitations'
        db.delete(db.get(Run, second['id']))
        db.commit()
        result = ledger.report(db, start_at=now()-100, end_at=now()+100)
    assert len(rows(client)) == 2
    assert result['agent_cohort']['orphaned_agent_attempts_in_window'] == 1
    assert result['agent_cohort']['estimated_model_usd_per_completed_run'] is None


def test_cost_survives_cancellation_after_provider_return(client, monkeypatch):
    activate(client)
    run = create_run(client)
    assert client.post('/api/v1/runs/'+run['id']+'/start',
        json={'expected_revision': 1, 'confirm_scope': True}, headers=key()).status_code == 202
    class CancelAfterReturn(MockGemini):
        def structured(self, *args, **kwargs):
            result = super().structured(*args, **kwargs)
            with client.app.state.db.Session() as db:
                db.get(Run, run['id']).cancel_requested = True
                db.commit()
            return result
    monkeypatch.setattr('app.agents.orchestrator.get_model', lambda _: CancelAfterReturn())
    tick(client.app.state.db, client.app.state.settings)
    assert len(rows(client)) == 1 and rows(client)[0].outcome == 'succeeded'
    assert client.get('/api/v1/runs/'+run['id']).json()['state'] == 'cancelled'
