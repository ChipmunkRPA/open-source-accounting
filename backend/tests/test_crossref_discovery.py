"""Original synthetic bibliographic records only; no publisher licenses or text."""
import copy
import json
from urllib.parse import urlencode
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.crossref_discovery import FIELDS, extract, query_contract
from app.intake_schemas import IntakeCreate
from app.models import SourceArtifact, SourceExtraction, SourceDiscovery
from test_source_intake import ADMIN, payload, registered, fetch, FakeGateway

QUERY = {'select': ','.join(sorted(FIELDS)), 'rows': '10', 'query': 'accounting controls',
         'filter': 'from-pub-date:2020-01-01,until-pub-date:2026-12-31'}
URL = 'https://api.crossref.org/v1/works?'+urlencode(QUERY)
WORK = {'DOI': '10.9999/synthetic-1', 'title': ['Original synthetic research title'], 'type': 'journal-article',
        'publisher': 'Fictional publisher', 'container-title': ['Synthetic journal'],
        'author': [{'given': 'Test', 'family': 'Author', 'affiliation': [{'name': 'Synthetic institution'}]}],
        'issued': {'date-parts': [[2024]]}, 'published-online': {'date-parts': [[2024, 2]]},
        'license': [{'URL': 'http://example.org/synthetic-license', 'content-version': 'am', 'start': {'date-parts': [[2025]]}}],
        'link': [{'URL': 'https://publisher.example/original.pdf', 'content-version': 'vor', 'intended-application': 'text-mining'}],
        'update-to': [{'DOI': '10.9999/synthetic-prior', 'type': 'correction', 'updated': {'date-parts': [[2025, 2, 1]]}}],
        'relation': {'is-version-of': [{'id': '10.9999/synthetic-preprint', 'id-type': 'doi', 'asserted-by': 'subject'}]}}


def page(work=None):
    return json.dumps({'status': 'ok', 'message-type': 'work-list', 'message-version': '1.0.0',
                      'message': {'items': [copy.deepcopy(WORK) if work is None else work], 'total-results': 123,
                                  'next-cursor': 'synthetic-next-page'}}).encode()


def body():
    return payload(family_id='OPEN_LITERATURE', parser='crossref_metadata', requested_url=URL,
                   allowed_mime=['application/json'], coverage_unit='one synthetic scoped Crossref metadata page')


class JSONGateway(FakeGateway):
    def get(self, url):
        result = super().get(url); result['mime'] = 'application/json'; return result


def test_bibliographic_provenance_dates_versions_and_no_rights_inference():
    result = extract(page(), URL)
    item, = result['items']
    assert item['metadata'] == WORK and item['locator'] == '/message/items/0'
    assert item['metadata']['issued']['date-parts'] == [[2024]]
    assert item['edition'] is item['effective_from'] is None
    assert not item['full_text_acquired'] and not item['reuse_authorized']
    assert item['metadata']['license'][0]['content-version'] == 'am'
    assert item['metadata']['link'][0]['content-version'] == 'vor'
    assert item['update_review_status'] == 'not_independently_checked'
    assert result['reported_total_results'] == 123 and len(result['items']) == 1
    assert result['next_cursor'] == 'synthetic-next-page' and result['network_requests'] == 0


@pytest.mark.parametrize('change', [
    {'select': 'DOI,title,abstract'}, {'rows': '101'}, {'rows': '0'}, {'filter': ''},
    {'query': ''}, {'filter': 'from-pub-date:2026-01-01,until-pub-date:2020-01-01'}, {'sample': '10'}])
def test_query_requires_bounded_metadata_scope(change):
    with pytest.raises(ValueError): query_contract('https://api.crossref.org/works?'+urlencode({**QUERY, **change}))


@pytest.mark.parametrize('base', ['http://api.crossref.org/works', 'https://api.crossref.org.evil.example/works',
    'https://api.crossref.org/works/10.9999/example', 'https://user:pw@api.crossref.org/works'])
def test_only_selected_works_route_supported(base):
    with pytest.raises(ValueError): query_contract(base+'?'+urlencode(QUERY))


@pytest.mark.parametrize('field', ['abstract', 'reference', 'full-text', 'assertion', 'unexpected'])
def test_unselected_fields_fail_instead_of_silent_copy(field):
    work = copy.deepcopy(WORK); work[field] = 'Synthetic unexpected content'
    with pytest.raises(ValueError): extract(page(work), URL)


@pytest.mark.parametrize('change', [
    {'DOI': 'not-a-doi'}, {'issued': {'date-parts': [[2024, 2, 31]]}},
    {'title': []}, {'relation': []}, {'author': ['unstructured']},
    {'link': [{'URL':'javascript:alert(1)', 'content-version': 'vor', 'intended-application':'text-mining'}]}])
def test_invalid_records_do_not_produce_partial_discovery(change):
    with pytest.raises(ValueError): extract(page({**WORK, **change}), URL)


def test_duplicate_json_keys_and_duplicate_dois_fail():
    with pytest.raises(ValueError): extract(b'{"status":"ok","status":"error"}', URL)
    data = json.loads(page()); data['message']['items'] *= 2
    with pytest.raises(ValueError): extract(json.dumps(data).encode(), URL)


def test_intake_discover_and_no_evidence_staging(client):
    work = registered(client, body=body())
    raw = fetch(client, work, JSONGateway(page()))
    path = '/api/v1/admin/intake/artifacts/'+raw['id']
    found = client.post(path+'/discover', headers=ADMIN)
    assert found.status_code == 200, found.text
    assert found.json()['adapter_version'] == 'crossref-works-1'
    assert client.post(path+'/parse', headers=ADMIN).json()['error']['code'] == 'DISCOVERY_ONLY'
    snapshot = client.get('/api/v1/admin/intake/discoveries/'+found.json()['id'], headers=ADMIN).json()
    assert snapshot['discovery']['items'][0]['metadata'] == WORK
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0
        assert db.scalar(select(func.count()).select_from(SourceDiscovery)) == 1


def test_abstract_rejected_before_immutable_raw_storage(client):
    work = registered(client, body=body())
    with pytest.raises(HTTPException) as exc:
        fetch(client, work, JSONGateway(page({**WORK, 'abstract': 'Synthetic protected abstract'})))
    assert exc.value.status_code == 422
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0
    assert not list((__import__('pathlib').Path(client.app.state.settings.data_dir)/'objects').rglob('*.bin'))


def test_pre_storage_screening_requires_extract_permission(client):
    data = body(); data['source']['policy']['extract'] = False
    work = registered(client, body=data); gateway = JSONGateway(page())
    with pytest.raises(HTTPException): fetch(client, work, gateway)
    assert gateway.calls == 0


@pytest.mark.parametrize('changes', [{'family_id':'NIST'}, {'redirect_urls':['https://api.crossref.org/works']},
                                    {'allowed_mime':['text/html']}, {'parser':'text'}])
def test_metadata_route_cannot_be_repurposed(changes):
    data = body(); data['manifest'].update(changes)
    with pytest.raises(ValueError): IntakeCreate.model_validate(data)


def test_gateway_does_not_misclassify_captcha_research_title():
    from types import SimpleNamespace
    from app.sec_core.fetch import Gateway
    from test_source_intake import Opener, Response
    raw = page({**WORK, 'title':['Synthetic CAPTCHA research title']})
    gateway = Gateway('OSA tests maintainer@example.test', SimpleNamespace(reserve=lambda: None),
                      opener=Opener(Response(raw, 'application/json')), resolver=lambda _: None, validator=lambda u: u)
    assert gateway.get(URL)['raw'] == raw


@pytest.mark.parametrize('unsafe', [False, True])
def test_manual_json_contract_before_raw_storage(client, unsafe):
    from app.sec_core.core import digest
    data = body(); data['manifest']['route'] = 'authorized_manual'
    raw = page({**WORK, 'abstract': 'Synthetic protected text'}) if unsafe else page()
    data['manifest']['manual_delivery'] = {'raw_sha256':digest(raw), 'byte_count':len(raw),
        'mime':'application/json', 'method':'author_original', 'evidence_ref':'ev_synthetic_metadata',
        'evidence_sha256':digest('Synthetic delivery evidence'), 'received_at':'2026-01-01T00:00:00Z'}
    work = registered(client, body=data)
    response = client.post('/api/v1/admin/intake/works/'+work['id']+'/import', content=raw,
        headers={**ADMIN, 'Idempotency-Key':'metadata-manual', 'Content-Type':'application/json'})
    assert response.status_code == (422 if unsafe else 200), response.text
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == (0 if unsafe else 1)


def test_json_error_body_is_not_acquired(client):
    work = registered(client, body=body())
    with pytest.raises(HTTPException):
        fetch(client, work, JSONGateway(b'{"status":"error","message":"Access denied"}'))
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0


def test_local_crossref_slot_is_exclusive_and_released(tmp_path):
    from app.services.source_concurrency import crossref_slot
    url = 'sqlite:///'+str(tmp_path/'source.db')
    with crossref_slot(url):
        with pytest.raises(HTTPException) as exc:
            with crossref_slot(url): pytest.fail('Concurrent request admitted')
        assert exc.value.status_code == 409
    with pytest.raises(RuntimeError):
        with crossref_slot(url): raise RuntimeError('Synthetic crash')
    with crossref_slot(url): pass


def test_nonfinite_numeric_metadata_fails():
    raw = page().replace(b'"total-results": 123', b'"total-results": 1e999')
    with pytest.raises(ValueError): extract(raw, URL)


def test_invalid_affiliation_shape_fails():
    work = {**WORK, 'author':[{'family':'Synthetic', 'affiliation': None}]}
    with pytest.raises(ValueError): extract(page(work), URL)
