"""Synthetic intake receipts and review contracts; never publisher approvals or live downloads."""
import io
from types import SimpleNamespace
from urllib.error import HTTPError
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.intake_schemas import IntakeCreate
from app.models import Source, IntakeWork, SourceArtifact, SourceExtraction, IntakeAttempt
from app.services import intake, rights
from app.services.storage import Storage
from app.sec_core.fetch import Gateway, Blocked, PinnedHTTPS
from app.sec_core.core import CoreError, digest
from conftest import rights_approval

ADMIN = {'X-Dev-User': 'admin'}
APPROVER = {'X-Dev-User': 'approver'}
RAW = b'<ECFR><SECTION N="229.999"><P ID="a">Synthetic original source paragraph for intake testing.</P></SECTION></ECFR>'


def payload(**manifest_changes):
    manifest = dict(family_id='SEC_RULES', work_id='synthetic-work', edition='fixture-1', language='en',
                    jurisdiction='US', authority_type='synthetic_rule', coverage_unit='one synthetic section',
                    access_mode='public_candidate', route='official_http', requested_url='https://www.ecfr.gov/fixture.xml',
                    parser='ecfr_xml', allowed_mime=['application/xml'], date_notes='Dates not established in synthetic fixture.',
                    notices=['Synthetic fixture authored for tests; not a real regulation.'])
    manifest.update(manifest_changes)
    return {'source': {'title': 'Synthetic work', 'publisher': 'Test author', 'canonical_url': manifest['requested_url'],
                       'version_label': manifest['edition'], 'kind': 'rule', 'policy': {
                           'basis': 'original', 'commercial_use': True, 'acquire': True, 'store_raw': True,
                           'extract': True, 'store_text': True, 'display_full': True, 'model_input': True, 'quote': True,
                           'review_note': 'Synthetic original fixture permission, not a publisher license.'}}, 'manifest': manifest}


def registered(client, approve=True, body=None):
    response = client.post('/api/v1/admin/intake/works', headers=ADMIN, json=body or payload())
    assert response.status_code == 201, response.text
    row = response.json()
    if approve:
        response = client.post('/api/v1/admin/sources/'+row['source_id']+'/approve', headers=APPROVER,
                               json=rights_approval(client, row['source_id']))
        assert response.status_code == 200, response.text
    return row


class FakeGateway:
    def __init__(self, raw=RAW, callback=None):
        self.raw, self.callback, self.calls = raw, callback, 0
    def get(self, url):
        self.calls += 1
        if self.callback:
            self.callback()
        return {'raw': self.raw, 'mime': 'application/xml', 'requested_url': url, 'resolved_url': url,
                'method': 'GET', 'status': 200, 'headers': {'ETag': 'fixture-v1'}, 'retrieved_at': '2026-09-27T18:00:00+00:00'}


def fetch(client, work, gateway=None, key='fixture'):
    return intake.acquire(client.app.state.db, client.app.state.settings, work['id'], 'admin', key,
                          gateway_factory=lambda *_: gateway or FakeGateway())


def parse(client, artifact):
    response = client.post(f'/api/v1/admin/intake/artifacts/{artifact["id"]}/parse', headers=ADMIN)
    assert response.status_code == 200, response.text
    return response.json()


def test_family_discovery_and_preview_are_offline(client, monkeypatch):
    monkeypatch.setattr(Gateway, 'get', lambda *_: pytest.fail('No network in discovery'))
    assert len(client.get('/api/v1/admin/intake/families', headers=ADMIN).json()['items']) == 32
    work = registered(client, approve=False)
    preview = client.get('/api/v1/admin/intake/works/'+work['id'], headers=ADMIN).json()
    assert not any(preview['operations'].values()) and not preview['artifacts']
    assert client.get('/api/v1/admin/intake/works').status_code == 403


@pytest.mark.parametrize('operation', ['acquire', 'store_raw'])
def test_missing_preacquisition_operation_never_calls_network(client, operation):
    body = payload(); body['source']['policy'][operation] = False
    work = registered(client, body=body); gateway = FakeGateway()
    with pytest.raises(HTTPException) as error:
        fetch(client, work, gateway)
    assert error.value.status_code == 403 and gateway.calls == 0


def test_unapproved_and_disabled_connector_do_not_fetch(client):
    work = registered(client, approve=False)
    gateway = FakeGateway()
    with pytest.raises(HTTPException): fetch(client, work, gateway)
    assert gateway.calls == 0
    client.post('/api/v1/admin/sources/'+work['source_id']+'/approve', headers=APPROVER,
                json=rights_approval(client, work['source_id']))
    response = client.post('/api/v1/admin/intake/works/'+work['id']+'/acquire', headers={**ADMIN, 'Idempotency-Key': 'key'})
    assert response.status_code == 403


def test_separate_acquire_parse_stage_and_exact_receipts(client):
    work = registered(client); gateway = FakeGateway()
    artifact = fetch(client, work, gateway)
    assert artifact['raw_sha256'] == digest(RAW) and not artifact['agent_eligible']
    assert artifact['receipt']['source_dates']['effective_from'] is None
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0
    assert fetch(client, work, gateway)['id'] == artifact['id'] and gateway.calls == 1
    # A different request with identical bytes records one immutable artifact, not duplicate coverage.
    assert fetch(client, work, gateway, key='another')['id'] == artifact['id']
    extraction = parse(client, artifact)
    assert parse(client, artifact)['id'] == extraction['id']
    assert extraction['passage_count'] == 1
    staged = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).json()
    assert not staged['agent_eligible']
    again = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).json()
    assert again['source_ids'] == staged['source_ids']
    with client.app.state.db.Session() as db:
        row = db.get(Source, staged['source_ids'][0])
        assert not row.reviewed and not rights.allowed(row, 'model_input')
        assert row.policy['intake_locator'] == '17 CFR 229.999 — source block 1'
    counts = client.get('/api/v1/admin/intake/coverage', headers=ADMIN).json()
    assert counts['registered_work_editions'] == counts['acquired_raw_artifacts'] == counts['parsed_artifact_versions'] == 1


def test_immutable_edition_and_manifest_tampering(client):
    work = registered(client)
    assert client.post('/api/v1/admin/intake/works', headers=ADMIN, json=payload()).status_code == 409
    with client.app.state.db.Session() as db:
        row = db.get(IntakeWork, work['id']); row.manifest = {**row.manifest, 'requested_url': 'https://mirror.example/a'}; db.commit()
    with pytest.raises(HTTPException) as exc: fetch(client, work)
    assert exc.value.status_code == 409


def test_source_dates_preserved_without_applicability_approval(client):
    work = registered(client, body=payload(effective_from='2027-01-01', effective_to='2028-12-31'))
    extraction = parse(client, fetch(client, work))
    staged = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).json()
    with client.app.state.db.Session() as db:
        for sid in [work['source_id'], *staged['source_ids']]:
            source = db.get(Source, sid)
            assert source.effective_from == '2027-01-01' and source.effective_to == '2028-12-31'
        assert source.policy['applicability_review_status'] == 'pending'


def test_conflicting_source_dates_rejected():
    body = payload(effective_from='2027-01-01')
    body['source']['effective_from'] = '2026-01-01'
    with pytest.raises(ValueError, match='Source dates'):
        IntakeCreate.model_validate(body)


@pytest.mark.parametrize('action', ['extract', 'store_text'])
def test_parsing_requires_separate_permission(client, action):
    body = payload(); body['source']['policy'][action] = False
    work = registered(client, body=body); artifact = fetch(client, work)
    assert client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN).status_code == 403


def test_raw_integrity_checked_before_parser(client):
    artifact = fetch(client, registered(client))
    with client.app.state.db.Session() as db:
        row = db.get(SourceArtifact, artifact['id'])
        Storage(client.app.state.settings)._path(row.object_key).write_bytes(b'corrupt')
    assert client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN).status_code == 409


def test_parser_failure_retains_raw_without_staging(client):
    artifact = fetch(client, registered(client), FakeGateway(b'<broken'))
    assert client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN).status_code == 422
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 1
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0


def test_rights_expiring_during_download_prevent_storage(client):
    work = registered(client)
    def expire():
        with client.app.state.db.Session() as db:
            row = db.get(Source, work['source_id']); row.policy = {**row.policy, 'expires_at': 1}
            rights.record_approval(row, 'synthetic-reviewer'); db.commit()
    with pytest.raises(HTTPException): fetch(client, work, FakeGateway(callback=expire))
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0


def test_crash_resume_lease_and_idempotency(client):
    work = registered(client)
    def crash(): raise KeyboardInterrupt('simulated process crash')
    with pytest.raises(KeyboardInterrupt): fetch(client, work, FakeGateway(callback=crash))
    with pytest.raises(HTTPException) as exc: fetch(client, work)
    assert exc.value.status_code == 409
    with client.app.state.db.Session() as db:
        attempt = db.scalar(select(IntakeAttempt)); attempt.lease_until = 0; db.commit()
    assert fetch(client, work)['raw_sha256'] == digest(RAW)
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(IntakeAttempt)) == 1


def test_blocked_route_cannot_retry_with_another_key(client):
    work = registered(client)
    def blocked(): raise Blocked('403 fixture')
    with pytest.raises(HTTPException): fetch(client, work, FakeGateway(callback=blocked))
    gateway = FakeGateway()
    with pytest.raises(HTTPException): fetch(client, work, gateway, key='bypass-attempt')
    assert gateway.calls == 0
    with client.app.state.db.Session() as db:
        assert not db.get(Source, work['source_id']).enabled


def test_parent_revocation_withholds_staged_body(client):
    work = registered(client); artifact = fetch(client, work); extraction = parse(client, artifact)
    sid = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).json()['source_ids'][0]
    client.post('/api/v1/admin/sources/'+sid+'/approve', headers=APPROVER, json=rights_approval(client, sid))
    assert client.get('/api/v1/sources/'+sid).json()['text']
    client.post('/api/v1/admin/sources/'+work['source_id']+'/disable', headers=ADMIN)
    assert client.get('/api/v1/sources/'+sid).json()['text'] is None


@pytest.mark.parametrize('url', ['http://www.sec.gov/a', 'https://user:x@www.sec.gov/a', 'https://www.sec.gov:444/a', 'https://www.sec.gov/a#part'],
                         ids=['http', 'fixture-credentials', 'nonstandard-port', 'fragment'])
def test_invalid_routes_rejected(url):
    with pytest.raises(ValueError): IntakeCreate.model_validate(payload(requested_url=url))


class Response(io.BytesIO):
    def __init__(self, raw, mime='application/xml'):
        super().__init__(raw); self.status = 200
        self.headers = {'Content-Type': mime, 'ETag': 'one', 'Set-Cookie': 'secret-omitted'}


class Opener:
    def __init__(self, response): self.response = response; self.calls = 0
    def open(self, *args, **kwargs):
        self.calls += 1
        if isinstance(self.response, Exception): raise self.response
        return self.response


@pytest.mark.parametrize('raw', [b'<html>CAPTCHA</html>', b'<title>Login</title>', b'<input type="password">'])
def test_html_login_or_challenge_is_never_source(raw):
    gateway = Gateway('OSA tests maintainer@example.test', SimpleNamespace(reserve=lambda: None),
                      opener=Opener(Response(raw, 'text/html')), resolver=lambda u: None)
    with pytest.raises(Blocked): gateway.get('https://www.sec.gov/fixture')


def test_headers_filtered_and_exact_redirect_enforced(client):
    settings = client.app.state.settings
    settings.source_fetch_enabled = True; settings.sec_user_agent = 'OSA tests maintainer@example.test'
    manifest = IntakeCreate.model_validate(payload()).manifest.model_dump(mode='json')
    gateway = intake.make_gateway(settings, manifest)
    gateway.resolver = lambda u: None
    gateway.opener = Opener(Response(RAW))
    assert 'Set-Cookie' not in gateway.get(manifest['requested_url'])['headers']
    gateway.opener = Opener(HTTPError(manifest['requested_url'], 302, 'redirect', {'Location': 'https://www.ecfr.gov/not-approved'}, None))
    with pytest.raises(CoreError): gateway.get(manifest['requested_url'])
    assert gateway.opener.calls == 1


def test_immutable_storage_never_replaces_bytes(client):
    store = Storage(client.app.state.settings)
    store.put_immutable('test/one', b'first', 'text/plain')
    store.put_immutable('test/one', b'first', 'text/plain')
    with pytest.raises(ValueError): store.put_immutable('test/one', b'second', 'text/plain')
    assert store.get('test/one') == b'first'


def test_https_connection_uses_checked_ip_and_original_tls_hostname(monkeypatch):
    import socket
    import ssl
    import http.client
    from urllib.request import Request
    from app.sec_core import fetch as module
    observed = {}
    sock = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(module, 'public_addresses', lambda *_: ['93.184.215.14'])
    def connect(address, timeout):
        observed['address'] = address
        return sock
    monkeypatch.setattr(socket, 'create_connection', connect)
    def wrap(value, server_hostname):
        observed['tls_hostname'] = server_hostname
        return value
    monkeypatch.setattr(ssl, 'create_default_context', lambda: SimpleNamespace(wrap_socket=wrap))
    class Connection:
        def __init__(self, host, timeout): observed['connection_host'] = host
        def request(self, method, path, headers): observed['request'] = (method, path, headers)
        def getresponse(self): return Response(RAW)
        def close(self): pass
    monkeypatch.setattr(http.client, 'HTTPSConnection', Connection)
    PinnedHTTPS(lambda url: url).open(Request('https://www.sec.gov/path?edition=1'), timeout=25)
    assert observed['address'] == ('93.184.215.14', 443)
    assert observed['tls_hostname'] == 'www.sec.gov'
    assert observed['request'][1] == '/path?edition=1'


def test_legacy_sec_cli_cannot_bypass_registry(monkeypatch):
    from app.sec_core.__main__ import main
    monkeypatch.setattr('sys.argv', ['sec_core', 'acquire', 'sec-cfi-nongaap', '--acknowledge-access-policy'])
    with pytest.raises(SystemExit, match='unified intake registry'):
        main()
