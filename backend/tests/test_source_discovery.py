"""Synthetic publisher indexes; no publisher text, permissions or live crawling."""
import json
from urllib.parse import urlsplit
import pytest
from sqlalchemy import select, func
from app.source_discovery import extract
from app.sec_core.core import CoreError, digest
from app.models import SourceDiscovery, SourceArtifact, IntakeWork
from app.services.storage import Storage
from test_source_intake import ADMIN, registered, payload, fetch, FakeGateway

RAW = b'''<main><a href="/pub/one.pdf#page=2">Original synthetic <b>work</b></a>
<a href="/pub/one.pdf">Download</a><a href="https://outside.example/book">Outside</a>
<a href="javascript:alert(1)">Active</a><a href="#top">Same index</a></main>'''
BASE = 'https://csrc.nist.gov/publications'


def artifact(client, *, family='NIST', url=BASE, policy_changes=None, raw=RAW):
    body = payload(family_id=family, requested_url=url, parser='structural_html', allowed_mime=['text/html'])
    body['source']['policy'].update(policy_changes or {})
    work = registered(client, body=body)
    class HTMLGateway(FakeGateway):
        def get(self, url):
            result = super().get(url); result['mime'] = 'text/html'; return result
    return work, fetch(client, work, HTMLGateway(raw=raw))


def discover(client, row):
    return client.post('/api/v1/admin/intake/artifacts/'+row['id']+'/discover', headers=ADMIN)


def test_extract_deduplicates_urls_retains_exact_occurrences():
    result = extract(RAW, BASE, ['csrc.nist.gov'])
    assert result['raw_sha256'] == digest(RAW) and result['anchors_observed'] == 5
    assert result['excluded_occurrences'] == {'outside_family_hosts': 1, 'unsafe_url': 1, 'same_index': 1}
    item, = result['items']
    assert item['url'] == 'https://csrc.nist.gov/pub/one.pdf'
    assert item['occurrences'][0] == {'locator': 'HTML anchor 1', 'href': '/pub/one.pdf#page=2',
                                    'fragment': 'page=2', 'label': 'Original synthetic work'}
    assert len(item['occurrences']) == 2 and item['edition'] is item['effective_from'] is None
    assert result['network_requests'] == 0


@pytest.mark.parametrize('raw', [b'<base href="https://other.example/">', b'<a href="/a"><a href="/b">x</a>',
    b'<a href="/unclosed">', b'<title>Access denied</title>', b'\xff',
    b'<a href="/a">'+b'x'*2001+b'</a>'])
def test_malformed_or_unsafe_index_fails_without_partial_results(raw):
    with pytest.raises((CoreError, ValueError)):
        extract(raw, BASE, ['csrc.nist.gov'])


def test_hidden_and_non_https_links_are_excluded():
    raw = b'<form><a href="/hidden">Hidden</a></form><a href="http://csrc.nist.gov/a">Old</a><a href="https://user:pw@csrc.nist.gov/a">Credential</a>'
    assert extract(raw, BASE, ['csrc.nist.gov'])['items'] == []


def test_no_implicit_subdomain_or_external_base():
    with pytest.raises(CoreError): extract(RAW, 'https://fake.csrc.nist.gov/a', ['csrc.nist.gov'])
    result = extract(b'<a href="https://csrc.nist.gov.evil.example/a">x</a>', BASE, ['csrc.nist.gov'])
    assert result['items'] == []


def test_max_links_fails_closed(monkeypatch):
    monkeypatch.setattr('app.source_discovery.MAX_LINKS', 1)
    with pytest.raises(CoreError): extract(RAW, BASE, ['csrc.nist.gov'])


def test_durable_discovery_is_separate_from_work_registration(client):
    work, raw = artifact(client)
    response = discover(client, raw)
    assert response.status_code == 200, response.text
    row = response.json()
    assert row['candidate_count'] == 1 and not row['agent_eligible']
    assert discover(client, raw).json()['id'] == row['id']
    output = client.get('/api/v1/admin/intake/discoveries/'+row['id'], headers=ADMIN).json()['discovery']
    assert output['artifact_id'] == raw['id'] and output['family_id'] == 'NIST'
    assert output['source_dates']['effective_from'] is None
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceDiscovery)) == 1
        assert db.scalar(select(func.count()).select_from(IntakeWork)) == 1
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 1
    client.post('/api/v1/admin/sources/'+work['source_id']+'/disable', headers=ADMIN)
    assert discover(client, raw).status_code == 403
    assert client.get('/api/v1/admin/intake/discoveries/'+row['id'], headers=ADMIN).status_code == 403


@pytest.mark.parametrize('family,url', [('SEC_FORMS','https://www.sec.gov/forms'),
    ('NIST',BASE),('FASB','https://www.fasb.org/'),('PUBLISHERS','https://dart.deloitte.com/'),
    ('LOCAL_FRAMEWORKS','https://www.aasb.gov.au/')])
def test_family_recipe_hosts_control_discovery(client, family, url):
    _, row = artifact(client, family=family, url=url)
    response = discover(client, row)
    # The test uses exact current registry hosts, never guesses equivalent aliases.
    from app.services.intake import families
    hosts = {urlsplit(u).hostname for u in families(client.app.state.settings)[family]['seed_urls']}
    assert response.status_code == (200 if urlsplit(url).hostname in hosts else 422), response.text


@pytest.mark.parametrize('operation', ['extract','store_text'])
def test_no_discovery_without_operation_rights(client, operation):
    _, row = artifact(client, policy_changes={operation: False})
    assert discover(client, row).status_code == 403


def test_candidate_labels_require_display_permission(client):
    _, row = artifact(client, policy_changes={'display_full': False})
    found = discover(client, row).json()
    assert client.get('/api/v1/admin/intake/discoveries/'+found['id'], headers=ADMIN).status_code == 403


def test_raw_and_discovery_integrity(client):
    _, row = artifact(client)
    found = discover(client, row).json()
    with client.app.state.db.Session() as db:
        snapshot = db.get(SourceDiscovery, found['id'])
        Storage(client.app.state.settings)._path(snapshot.object_key).write_bytes(b'corrupt')
    assert client.get('/api/v1/admin/intake/discoveries/'+found['id'], headers=ADMIN).status_code == 409


def test_bad_raw_index_never_registers_snapshot(client):
    _, row = artifact(client)
    with client.app.state.db.Session() as db:
        raw = db.get(SourceArtifact, row['id'])
        Storage(client.app.state.settings)._path(raw.object_key).write_bytes(b'corrupt')
    assert discover(client, row).status_code == 409


def test_recipe_change_creates_new_immutable_snapshot(client, monkeypatch):
    _, row = artifact(client)
    first = discover(client, row).json()
    from app.services import intake
    original = intake.families
    def revised(settings):
        recipes = json.loads(json.dumps(original(settings)))
        recipes['NIST']['seed_status'] = 'Changed synthetic recipe'
        return recipes
    monkeypatch.setattr(intake, 'families', revised)
    second = discover(client, row).json()
    assert second['id'] != first['id'] and second['recipe_sha256'] != first['recipe_sha256']
    assert client.get('/api/v1/admin/intake/discoveries/'+first['id'], headers=ADMIN).status_code == 200


def test_resolved_index_url_controls_relative_links(client):
    _, row = artifact(client)
    with client.app.state.db.Session() as db:
        saved = db.get(SourceArtifact, row['id'])
        saved.receipt = {**saved.receipt, 'resolved_url': 'https://csrc.nist.gov/new/index.html'}
        db.commit()
    found = discover(client, row).json()
    data = client.get('/api/v1/admin/intake/discoveries/'+found['id'], headers=ADMIN).json()['discovery']
    assert data['base_url'] == 'https://csrc.nist.gov/new/index.html'


def test_non_html_artifact_requires_another_adapter(client):
    row = fetch(client, registered(client))
    assert discover(client, row).status_code == 422


def test_discovery_does_not_recover_body_from_reference_only_records(client):
    body = payload(access_mode='reference_only', route='reference_only')
    work = registered(client, body=body)
    # No artifact can be acquired for this reference-only work.
    assert client.post('/api/v1/admin/intake/works/'+work['id']+'/acquire', headers={**ADMIN, 'Idempotency-Key': 'ref'}).status_code == 403
