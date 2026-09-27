"""Synthetic Cloud protocol tests: never acquire credentials or call the network."""
import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from app.config import Settings
from app.errors import ProviderError
from app.providers.gemini import Gemini
from app.providers.gemini_contract import MAX_RESPONSE_BYTES, endpoint
from app.providers.gemini_costs import estimate_usd
from app.schemas import Plan


def response(text='A synthetic answer.'):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 3,
                              'thoughtsTokenCount': 2, 'totalTokenCount': 15},
            'modelVersion': 'gemini-3.8-flash-test'}


def model(transport, **kwargs):
    return Gemini(Settings(model_provider='google_cloud', google_cloud_project='test-project',
                           _env_file=None, **kwargs), transport)


def chat(client):
    return client.chat([{'role': 'user', 'body': 'Synthetic question'}])


@pytest.mark.parametrize('location,host', [
    ('us', 'aiplatform.us.rep.googleapis.com'), ('eu', 'aiplatform.eu.rep.googleapis.com'),
    ('global', 'aiplatform.googleapis.com'),
])
def test_exact_route_and_text_only_payload(location, host):
    transport = Mock(return_value=response())
    client = model(transport, model_location=location)
    assert chat(client) == 'A synthetic answer.'
    url, body = transport.call_args.args
    assert url == f'https://{host}/v1/projects/test-project/locations/{location}/publishers/google/models/gemini-3.8-flash:generateContent'
    assert set(body) == {'systemInstruction', 'contents', 'generationConfig'}
    assert body['generationConfig'] == {'maxOutputTokens': 1800, 'thinkingConfig': {'thinkingLevel': 'LOW'}}
    assert client.last_model_version == 'gemini-3.8-flash-test'
    assert client.last_usage['thoughtsTokenCount'] == 2


@pytest.mark.parametrize('project', ['x', 'PROJECT', 'project/path', 'project?x=1', 'project#fragment', '-project', 'project-', 'x'*31])
def test_bad_project_cannot_change_route(project):
    with pytest.raises(ValueError):
        Settings(model_provider='google_cloud', google_cloud_project=project, _env_file=None)


@pytest.mark.parametrize('kwargs', [{'model_id': 'other-model'}, {'model_location': 'us-central1'}])
def test_no_unverified_model_or_location(kwargs):
    with pytest.raises(ValueError):
        model(Mock(), **kwargs)


@pytest.mark.parametrize('thinking,cap', [('MINIMAL', 100), ('HIGH', 8001), ('HIGH', 0), ('LOW', True), ('MEDIUM', 1.5)])
def test_bad_generation_settings_do_not_call_transport(thinking, cap):
    transport = Mock()
    with pytest.raises(ProviderError, match='CONFIG_INVALID'):
        model(transport).structured(Plan, 'Instruction', {}, thinking=thinking, cap=cap)
    transport.assert_not_called()


@pytest.mark.parametrize('contents', [[], [{'role': 'model', 'parts': [{'text': 'prefill'}]}],
    [{'role': 'system', 'parts': [{'text': 'bad role'}]}],
    [{'role': 'user', 'parts': [{'fileData': {'fileUri': 'https://example.org/example'}}]}],
    [{'role': 'user', 'parts': [{'text': ' '}]}]])
def test_invalid_turns_and_provider_fetch_inputs_rejected(contents):
    transport = Mock()
    with pytest.raises(ProviderError, match='INPUT_INVALID'):
        model(transport)._call('Instruction', contents)
    transport.assert_not_called()


def test_entire_payload_including_system_schema_is_bounded():
    transport = Mock()
    with pytest.raises(ProviderError, match='INPUT_LIMIT'):
        model(transport).structured(Plan, 'x' * 180000, {})
    transport.assert_not_called()


@pytest.mark.parametrize('reason', [None, '', 'MAX_TOKENS', 'SAFETY', 'MALFORMED_FUNCTION_CALL'])
def test_only_final_stop_response_released(reason):
    data = response()
    data['candidates'][0]['finishReason'] = reason
    client = model(lambda *_: data)
    with pytest.raises(ProviderError, match='OUTPUT_INCOMPLETE'):
        chat(client)
    # A rejected output may still have incurred provider charges.
    assert client.last_usage['totalTokenCount'] == 15


@pytest.mark.parametrize('part', [{'functionCall': {'name': 'get_source', 'args': {}}},
    {'text': 'answer', 'functionCall': {'name': 'get_source'}}, {'text': 1}, {'text': 'answer', 'thought': 'false'}])
def test_unexpected_response_parts_rejected(part):
    data = response()
    data['candidates'][0]['content']['parts'].append(part)
    with pytest.raises(ProviderError, match='RESPONSE_INVALID'):
        chat(model(lambda *_: data))


def test_private_thoughts_are_not_displayed():
    data = response()
    data['candidates'][0]['content']['parts'].insert(0, {'text': 'Synthetic hidden thought', 'thought': True})
    assert chat(model(lambda *_: data)) == 'A synthetic answer.'


@pytest.mark.parametrize('field,value', [('totalTokenCount', -1), ('totalTokenCount', 14),
    ('promptTokenCount', True), ('thoughtsTokenCount', '2'), ('cachedContentTokenCount', 11)])
def test_bad_usage_is_not_reported_as_zero(field, value):
    data = response()
    data['usageMetadata'][field] = value
    client = model(lambda *_: data)
    with pytest.raises(ProviderError, match='USAGE_INVALID'):
        chat(client)
    assert client.last_usage == {}


def test_missing_usage_and_stale_usage_rejected():
    transport = Mock(side_effect=[response(), {'candidates': response()['candidates']}])
    client = model(transport)
    chat(client)
    with pytest.raises(ProviderError, match='USAGE_INVALID'):
        chat(client)
    assert client.last_usage == {} and client.last_model_version is None


@pytest.mark.parametrize('mutation,code', [
    ('multiple', 'OUTPUT_INCOMPLETE'), ('grounding', 'UNEXPECTED_TOOL'),
    ('tool_usage', 'UNEXPECTED_TOOL'), ('blocked', 'OUTPUT_BLOCKED'),
    ('no_output_count', 'USAGE_INVALID'), ('bad_version', 'RESPONSE_INVALID'),
])
def test_unexpected_response_state_is_not_released(mutation, code):
    data = response()
    if mutation == 'multiple':
        data['candidates'].append(data['candidates'][0].copy())
    elif mutation == 'grounding':
        data['candidates'][0]['groundingMetadata'] = {'webSearchQueries': ['synthetic']}
    elif mutation == 'tool_usage':
        data['usageMetadata'].update(toolUsePromptTokenCount=1, totalTokenCount=16)
    elif mutation == 'blocked':
        data['promptFeedback'] = {'blockReason': 'SAFETY'}
    elif mutation == 'no_output_count':
        data['usageMetadata'].update(candidatesTokenCount=0, totalTokenCount=12)
    else:
        data['modelVersion'] = 'unexpected content\nnot an identifier'
    with pytest.raises(ProviderError, match=code):
        chat(model(lambda *_: data))


def test_schema_validation_failure_keeps_usage_but_no_result():
    client = model(lambda *_: response('not json'))
    with pytest.raises(ProviderError, match='SCHEMA_INVALID'):
        client.structured(Plan, 'Instruction', {})
    assert client.last_usage['totalTokenCount'] == 15


def fake_http(monkeypatch, status=200, chunks=None, error=None):
    import google.auth
    import google.auth.transport.requests
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    reply = Mock(status_code=status)
    reply.__enter__ = Mock(return_value=reply)
    reply.__exit__ = Mock(return_value=False)
    reply.iter_content.return_value = chunks if chunks is not None else [json.dumps(response()).encode()]
    session.post.return_value = reply
    session.post.side_effect = error
    factory = Mock(return_value=session)
    monkeypatch.setattr(google.auth, 'default', Mock(return_value=(object(), 'test-project')))
    monkeypatch.setattr(google.auth.transport.requests, 'AuthorizedSession', factory)
    return session, factory


def test_http_no_redirect_or_auth_replay(monkeypatch):
    session, factory = fake_http(monkeypatch)
    assert chat(model(None)) == 'A synthetic answer.'
    assert factory.call_args.kwargs == {'max_refresh_attempts': 0}
    assert session.post.call_args.kwargs['allow_redirects'] is False
    assert session.post.call_args.kwargs['timeout'] == (10, 90)
    assert session.post.call_args.kwargs['stream'] is True
    session.post.assert_called_once()


@pytest.mark.parametrize('status,code', [(301, 'REQUEST_FAILED'), (401, 'AUTH_REQUIRED'),
    (403, 'ACCESS_DENIED'), (404, 'UNAVAILABLE'), (429, 'RATE_LIMITED'), (503, 'UNAVAILABLE')])
def test_http_safe_error_and_no_retry(monkeypatch, status, code):
    session, _ = fake_http(monkeypatch, status=status)
    with pytest.raises(ProviderError, match=code):
        chat(model(None))
    session.post.assert_called_once()
    session.post.return_value.iter_content.assert_not_called()


def test_http_timeout_does_not_expose_request_or_retry(monkeypatch):
    from requests.exceptions import Timeout
    session, _ = fake_http(monkeypatch, error=Timeout('Synthetic private request body'))
    with pytest.raises(ProviderError, match='^MODEL_TIMEOUT$'):
        chat(model(None))
    session.post.assert_called_once()


def test_streamed_response_limit(monkeypatch):
    fake_http(monkeypatch, chunks=[b'x' * (MAX_RESPONSE_BYTES + 1)])
    with pytest.raises(ProviderError, match='OUTPUT_LIMIT'):
        chat(model(None))


@pytest.mark.parametrize('location,factor', [('us', '1.1'), ('eu', '1.1'), ('global', '1')])
def test_dated_price_transition_includes_reasoning(location, factor):
    usage = {'promptTokenCount': 1000000, 'candidatesTokenCount': 200000,
             'thoughtsTokenCount': 800000, 'totalTokenCount': 2000000, 'cachedContentTokenCount': 100000}
    intro = estimate_usd(usage, location=location, incurred_on=date(2026, 12, 31))
    later = estimate_usd(usage, location=location, incurred_on=date(2027, 1, 1))
    assert Decimal(intro['estimated_usd']) == Decimal('4.50') * Decimal(factor)
    assert Decimal(later['estimated_usd']) == Decimal(intro['estimated_usd']) * 2
    assert intro['output_and_thinking_tokens'] == 1000000
    assert intro['basis'] == 'standard_text_no_cached_discount_estimate'


@pytest.mark.parametrize('kwargs', [{'location': 'us-central1'}, {'model': 'another-model'},
    {'provider': 'another-provider'}, {'incurred_on': date(2026, 9, 26)}])
def test_no_unverified_prices(kwargs):
    inputs = {'location': 'us', 'incurred_on': date(2026, 9, 27), **kwargs}
    with pytest.raises(ValueError):
        estimate_usd(response()['usageMetadata'], **inputs)


def test_mutated_settings_cannot_bypass_route_validation():
    transport = Mock()
    client = model(transport)
    client.config.model_id = 'another-model'
    with pytest.raises(ProviderError, match='REQUEST_FAILED'):
        chat(client)
    transport.assert_not_called()
    with pytest.raises(ValueError):
        endpoint('test-project', 'another-location')
