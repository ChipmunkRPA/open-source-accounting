"""Synthetic operator approvals and transport responses only; no paid resource use."""
from unittest.mock import Mock
import pytest
from sqlalchemy import select
from app.config import Settings
from app.errors import ProviderError
from app.models import ModelBudget, ModelAttempt, now
from app.providers.gemini import Gemini
from app.schemas import Plan
from app.services import model_attempts as ledger, model_budgets as budgets
from conftest import synthetic_model_budget
from test_model_attempts import metadata, plan_response
from test_gemini_contract import fake_http


def config(budget='synthetic-budget', **kw):
    return Settings(model_provider='google_cloud', google_cloud_project='test-project',
        model_budget_id=budget, _env_file=None, **kw)


def fund(client, **kw):
    synthetic_model_budget(client.app.state.db, **kw)


def budget(client, budget_id='synthetic-budget'):
    with client.app.state.db.Session() as db:
        return db.get(ModelBudget, budget_id)


def invoke(client, model, token='one', settings=None):
    return ledger.invoke(client.app.state.db.Session, settings or config(), model,
        lambda: model.structured(Plan, 'Synthetic', {}), **metadata(token))


def payload(**changes):
    return dict(provider='google_cloud', project='test-project', location='us', model_id='gemini-3.8-flash',
        limit_usd='9', per_call_usd='3', expires_at=now()+3600, evidence_ref='ev_synthetic_budget',
        evidence_sha256='a'*64, confirm_operator_spend_authorization=True, **changes)


def test_missing_budget_never_dispatches(client):
    transport = Mock(return_value=plan_response())
    with pytest.raises(ProviderError, match='BUDGET_REQUIRED'):
        invoke(client, Gemini(config(), transport), settings=config(budget=''))
    transport.assert_not_called()


def test_competing_calls_cannot_exceed_reserved_total(client):
    fund(client, limit='3')
    ledger.prepare(client.app.state.db.Session, config(), **metadata('first'))
    with pytest.raises(ProviderError, match='EXHAUSTED'):
        ledger.prepare(client.app.state.db.Session, config(), **metadata('second'))
    assert budget(client).held_nanos == 3_000_000_000


def test_estimates_do_not_refill_budget(client):
    fund(client, limit='3')
    invoke(client, Gemini(config(), lambda *_: plan_response()))
    row = budget(client)
    assert row.held_nanos == 0 and row.committed_nanos == 3_000_000_000
    with pytest.raises(ProviderError, match='EXHAUSTED'):
        invoke(client, Gemini(config(), Mock()), 'second')


def test_unknown_timeout_holds_reservation_after_revocation(client):
    fund(client, limit='3')
    def timeout(*_): raise TimeoutError('Synthetic')
    with pytest.raises(ProviderError):
        invoke(client, Gemini(config(), timeout))
    with client.app.state.db.Session() as db:
        row = db.get(ModelBudget, 'synthetic-budget')
        row.active = False
        db.commit()
    assert budget(client).held_nanos == 3_000_000_000 and budget(client).committed_nanos == 0


def test_expiry_blocks_new_calls_without_releasing_old_liability(client, monkeypatch):
    fund(client)
    ledger.prepare(client.app.state.db.Session, config(), **metadata('first'))
    expired = budget(client).expires_at + 1
    monkeypatch.setattr(budgets, 'now', lambda: expired)
    with pytest.raises(ProviderError, match='INACTIVE'):
        ledger.prepare(client.app.state.db.Session, config(), **metadata('second'))
    assert budget(client).held_nanos == 3_000_000_000


def test_known_non_200_releases_exact_reservation(client, monkeypatch):
    fund(client, limit='3')
    fake_http(monkeypatch, status=429)
    with pytest.raises(ProviderError, match='RATE_LIMITED'):
        invoke(client, Gemini(config()))
    assert budget(client).held_nanos == budget(client).committed_nanos == 0
    invoke(client, Gemini(config(), lambda *_: plan_response()), 'second')
    assert budget(client).committed_nanos == 3_000_000_000


def test_duplicate_attempt_rolls_back_any_reservation(client):
    fund(client, limit='6')
    ledger.prepare(client.app.state.db.Session, config(), **metadata())
    with pytest.raises(ProviderError, match='ALREADY_RECORDED'):
        ledger.prepare(client.app.state.db.Session, config(), **metadata())
    assert budget(client).held_nanos == 3_000_000_000


def test_scope_is_exact_and_cannot_fallback(client):
    fund(client)
    with pytest.raises(ProviderError, match='BUDGET_SCOPE'):
        ledger.prepare(client.app.state.db.Session, config(model_location='eu'), **metadata())
    assert budget(client).held_nanos == 0


def test_legacy_unknown_liability_blocks_new_envelope(client):
    fund(client)
    with client.app.state.db.Session() as db:
        db.add(ModelAttempt(operation_key=ledger.operation_key('legacy'), user_id='demo', phase='chat',
            provider='google_cloud', project='test-project', location='us', model_id='gemini-3.8-flash',
            prompt_version='legacy', thinking='LOW', output_limit=1800))
        db.commit()
    with pytest.raises(ProviderError, match='LEGACY_UNKNOWN'):
        ledger.prepare(client.app.state.db.Session, config(), **metadata())
    assert budget(client).held_nanos == 0


def test_duplicate_settlement_does_not_release_or_charge_twice(client):
    fund(client)
    model = Gemini(config(), lambda *_: plan_response())
    invoke(client, model)
    with client.app.state.db.Session() as db:
        attempt = db.scalar(select(ModelAttempt))
    with pytest.raises(ProviderError, match='ALREADY_SETTLED'):
        ledger.settle(client.app.state.db.Session, attempt.id, model, succeeded=True, error_code=None)
    assert budget(client).committed_nanos == 3_000_000_000


def test_overrun_records_actual_estimate_halts_budget_and_withholds_result(client):
    fund(client)
    data = plan_response()
    data['usageMetadata'] = {'promptTokenCount': 10_000_000, 'candidatesTokenCount': 5, 'totalTokenCount': 10_000_005}
    with pytest.raises(ProviderError, match='BUDGET_OVERRUN'):
        invoke(client, Gemini(config(), lambda *_: data))
    row = budget(client)
    assert not row.active and row.committed_nanos > 3_000_000_000 and row.held_nanos == 0
    with client.app.state.db.Session() as db:
        assert db.scalar(select(ModelAttempt)).budget_state == 'overrun'


def test_revocation_between_reservation_and_dispatch_releases_without_network(client, monkeypatch):
    fund(client)
    original = budgets.dispatch_allowed
    def revoked(factory, settings, attempt_id):
        with factory() as db:
            db.get(ModelBudget, settings.model_budget_id).active = False
            db.commit()
        original(factory, settings, attempt_id)
    monkeypatch.setattr(budgets, 'dispatch_allowed', revoked)
    transport = Mock(return_value=plan_response())
    with pytest.raises(ProviderError, match='INACTIVE'):
        invoke(client, Gemini(config(), transport))
    transport.assert_not_called()
    assert budget(client).held_nanos == budget(client).committed_nanos == 0


@pytest.mark.parametrize('attestation', [False, 1, 'true', None])
def test_explicit_boolean_operator_attestation_required(client, attestation):
    body = payload(); body['confirm_operator_spend_authorization'] = attestation
    assert client.post('/api/v1/admin/model-budgets', json=body, headers={'X-Dev-User': 'admin'}).status_code == 422


def test_admin_authorization_retry_and_revoke_never_refill(client):
    route = '/api/v1/admin/model-budgets'
    body = payload()
    assert client.post(route, json=body).status_code == 403
    assert client.post(route, json=body, headers={'X-Dev-User': 'approver'}).status_code == 403
    headers = {'X-Dev-User': 'admin'}
    first = client.post(route, json=body, headers=headers).json()
    second = client.post(route, json=body, headers=headers).json()
    assert first['id'] == second['id']
    revoked = client.post(route+'/'+first['id']+'/revoke', json={'expected_terms_sha256': first['terms_sha256']}, headers=headers)
    assert revoked.status_code == 200 and not revoked.json()['active']
    assert not client.post(route, json=body, headers=headers).json()['active']


@pytest.mark.parametrize('field,value', [('per_call_usd','0.01'), ('limit_usd','2'), ('limit_usd','NaN'),
    ('expires_at',1), ('expires_at','stale_review'), ('catalog_version','unverified')])
def test_invalid_or_stale_authorization_rejected(client, field, value):
    if value == 'stale_review':
        value = budgets.REVIEW_DEADLINE+1
    body = payload(); body[field] = value
    assert client.post('/api/v1/admin/model-budgets', json=body, headers={'X-Dev-User': 'admin'}).status_code == 422


def test_expired_catalog_cannot_authorize_new_money(client, monkeypatch):
    monkeypatch.setattr(budgets, 'REVIEW_DEADLINE', now()-1)
    assert client.post('/api/v1/admin/model-budgets', json=payload(), headers={'X-Dev-User': 'admin'}).status_code == 422


def test_approval_cannot_be_reused_by_changing_amount_format_or_terms(client):
    route, headers = '/api/v1/admin/model-budgets', {'X-Dev-User': 'admin'}
    body = payload()
    first = client.post(route, json=body, headers=headers).json()
    body['limit_usd'], body['per_call_usd'] = '09.000000', '3.0'
    assert client.post(route, json=body, headers=headers).json()['id'] == first['id']
    body['limit_usd'] = '12'
    assert client.post(route, json=body, headers=headers).status_code == 409
    body['evidence_sha256'] = 'b'*64  # Separate synthetic approval for additional funds.
    created = client.post(route, json=body, headers=headers)
    assert created.status_code == 201 and created.json()['id'] != first['id']
