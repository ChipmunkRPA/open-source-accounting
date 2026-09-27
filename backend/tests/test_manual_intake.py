"""Synthetic manual deliveries, never real licenses or accounting review."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.intake_schemas import IntakeCreate
from app.models import Source, SourceArtifact, IntakeAttempt
from app.services import intake, rights
from app.services.storage import Storage
from app.sec_core.core import digest, canonical
from test_source_intake import ADMIN, RAW, payload, registered, parse


def manual_payload(**changes):
    body = payload(family_id='NIST', route='authorized_manual', manual_delivery={
        'raw_sha256': digest(RAW), 'byte_count': len(RAW), 'mime': 'application/xml',
        'method': 'author_original', 'evidence_ref': 'ev_synthetic_delivery',
        'evidence_sha256': digest('Synthetic delivery evidence only'), 'received_at': '2026-01-01T00:00:00Z'})
    body['manifest'].update(changes)
    return body


def send(client, work, raw=RAW, key='manual-fixture', **headers):
    return client.post('/api/v1/admin/intake/works/'+work['id']+'/import', content=raw,
                       headers={**ADMIN, 'Idempotency-Key': key, 'Content-Type': 'application/xml', **headers})


def test_manual_import_parse_stage_and_duplicate_coverage(client, monkeypatch):
    monkeypatch.setattr(intake, 'make_gateway', lambda *_: pytest.fail('Manual import cannot fetch'))
    work = registered(client, body=manual_payload())
    response = send(client, work)
    assert response.status_code == 200, response.text
    artifact = response.json()
    receipt = artifact['receipt']
    assert receipt['retrieved_at'] is receipt['resolved_url'] is receipt['status'] is None
    assert receipt['imported_at'] and receipt['manual_delivery']['received_at'] == '2026-01-01T00:00:00Z'
    assert receipt['raw_sha256'] == digest(RAW) and not artifact['agent_eligible']
    assert receipt['source_dates']['effective_from'] is None
    assert send(client, work).json()['id'] == artifact['id']
    assert send(client, work, key='different-key').json()['id'] == artifact['id']
    extraction = parse(client, artifact)
    result = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN)
    assert result.status_code == 200 and not result.json()['agent_eligible']
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 1
        assert db.scalar(select(func.count()).select_from(IntakeAttempt)) == 2
        assert not db.get(Source, result.json()['source_ids'][0]).reviewed


@pytest.mark.parametrize('operation', ['acquire', 'store_raw'])
def test_operation_denied_before_storage(client, operation):
    body = manual_payload(); body['source']['policy'][operation] = False
    work = registered(client, body=body)
    assert send(client, work).status_code == 403


def test_approval_and_fresh_admin_required(client):
    work = registered(client, body=manual_payload(), approve=False)
    assert send(client, work).status_code == 403
    assert send(client, work, **{'X-Dev-User': 'demo'}).status_code == 403


@pytest.mark.parametrize('raw,headers,status', [
    (RAW[:-1], {}, 422), (RAW+b'x', {}, 413), (RAW.replace(b'Synthetic', b'Fictional'), {}, 422),
    (RAW, {'Content-Type': 'text/plain'}, 422), (RAW, {'Content-Encoding': 'gzip'}, 422)])
def test_modified_body_size_mime_encoding_never_stored(client, raw, headers, status):
    work = registered(client, body=manual_payload())
    assert send(client, work, raw=raw, **headers).status_code == status
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0


def test_policy_change_between_preflight_and_commit(client):
    work = registered(client, body=manual_payload())
    database = client.app.state.db
    preflight = intake.manual_preflight(database, work['id'], 'key')
    with database.Session() as db:
        source = db.get(Source, work['source_id'])
        source.policy = {**source.policy, 'review_note': 'Changed synthetic review note'}
        source.policy_version += 1
        rights.record_approval(source, 'synthetic-independent-reviewer')
        db.commit()
    with pytest.raises(HTTPException) as exc:
        intake.import_manual(database, client.app.state.settings, work['id'], 'admin', 'key', RAW, 'application/xml', preflight)
    assert exc.value.status_code == 409


def test_storage_crash_retry_reuses_immutable_bytes(client, monkeypatch):
    work = registered(client, body=manual_payload())
    original = Storage.put_immutable
    def crash(self, *args):
        original(self, *args)
        raise KeyboardInterrupt('synthetic post-storage crash')
    database = client.app.state.db
    preflight = intake.manual_preflight(database, work['id'], 'key')
    with monkeypatch.context() as patch:
        patch.setattr(Storage, 'put_immutable', crash)
        with pytest.raises(KeyboardInterrupt):
            intake.import_manual(database, client.app.state.settings, work['id'], 'admin', 'key', RAW, 'application/xml', preflight)
    with database.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0
        assert db.scalar(select(func.count()).select_from(IntakeAttempt)) == 0
    assert send(client, work, key='key').status_code == 200
    assert len(list(Storage(client.app.state.settings).root.rglob('*.bin'))) == 1


def test_revocation_prevents_duplicate_return(client):
    work = registered(client, body=manual_payload())
    assert send(client, work).status_code == 200
    client.post('/api/v1/admin/sources/'+work['source_id']+'/disable', headers=ADMIN)
    assert send(client, work).status_code == 403


@pytest.mark.parametrize('change', [
    {'manual_delivery': None}, {'route': 'official_http'}, {'access_mode': 'reference_only'},
    {'family_id': 'PRIVATE_UPLOADS'}, {'redirect_urls': ['https://example.org/mirror']}, {'max_bytes': 1}])
def test_invalid_manual_registration(change):
    with pytest.raises(ValueError):
        IntakeCreate.model_validate(manual_payload(**change))


def test_old_http_manifest_hash_is_unchanged():
    model = IntakeCreate.model_validate(payload()).manifest
    old = model.model_dump(mode='json'); old.pop('manual_delivery')
    assert digest(canonical(model.canonical_metadata())) == digest(canonical(old))


def test_http_manifest_cannot_use_manual_endpoint(client):
    assert send(client, registered(client)).status_code == 403


def test_access_control_body_is_not_an_artifact(client):
    raw = b'<html><title>Access denied</title>captcha</html>'
    body = manual_payload()
    body['manifest']['manual_delivery'].update(raw_sha256=digest(raw), byte_count=len(raw))
    work = registered(client, body=body)
    assert send(client, work, raw=raw).status_code == 422
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0


def test_expiry_during_storage_prevents_registration(client, monkeypatch):
    body = manual_payload(); body['source']['policy']['expires_at'] = 4102444800
    work = registered(client, body=body)
    original = Storage.put_immutable
    def expire(self, *args):
        original(self, *args)
        monkeypatch.setattr(rights, 'now', lambda: 4102444801)
    monkeypatch.setattr(Storage, 'put_immutable', expire)
    assert send(client, work).status_code == 403
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact)) == 0


def test_cli_sends_exact_bytes_without_redirect_or_proxy(client, tmp_path, monkeypatch, capsys):
    from app import ingest
    raw_file = tmp_path / 'original.xml'; raw_file.write_bytes(RAW)
    work = registered(client, body=manual_payload())
    monkeypatch.setenv('OSA_API_URL', 'https://intake.example')
    monkeypatch.setenv('OSA_INTAKE_TOKEN', 'synthetic-token')
    monkeypatch.setattr('sys.argv', ['ingest', 'import', work['id'], '--file', str(raw_file),
                                   '--mime', 'application/xml', '--request-key', 'cli-fixture'])
    class Client:
        def __init__(self, **kw):
            assert kw['follow_redirects'] is False and kw['trust_env'] is False
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def request(self, verb, url, **kw):
            assert verb == 'POST' and url.endswith('/'+work['id']+'/import')
            assert kw['content'] == RAW and kw['json'] is None
            assert kw['headers']['Content-Type'] == 'application/xml'
            return client.post('/api/v1/admin/intake/works/'+work['id']+'/import', content=kw['content'],
                               headers={**ADMIN, 'Content-Type': 'application/xml', 'Idempotency-Key': 'cli-fixture'})
    monkeypatch.setattr(ingest.httpx, 'Client', Client)
    ingest.main()
    output = capsys.readouterr().out
    assert 'acquired_not_reviewed' in output and 'synthetic-token' not in output
