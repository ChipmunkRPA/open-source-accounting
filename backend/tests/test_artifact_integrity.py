"""Synthetic stored objects only; no live acquisition or professional decisions."""
import pytest
from app.models import SourceArtifact,SourceExtraction,Audit,Source
from app.services.storage import Storage
from app.sec_core.core import canonical,digest
from test_source_intake import registered,fetch,parse,ADMIN


def setup(client):
    work=registered(client);artifact=fetch(client,work);ex=parse(client,artifact)
    return work,artifact,ex


def verify(client,artifact):
    return client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/verify',headers=ADMIN)


def test_integrity_is_private_point_in_time_and_no_approval(client):
    work,a,e=setup(client)
    assert client.post('/api/v1/admin/intake/artifacts/'+a['id']+'/verify').status_code==403
    r=verify(client,a);assert r.status_code==200,r.text
    result=r.json();assert result['raw']['status']=='verified' and result['extractions'][0]['status']=='verified'
    assert 'Synthetic original source paragraph' not in str(result)
    with client.app.state.db.Session() as db:
        assert db.query(Audit).filter(Audit.action=='intake.integrity_observed').count()==1
        assert not db.get(Source,work['source_id']).policy.get('technical_review_record_id')
    assert verify(client,a).json()['raw']['status']=='verified'


@pytest.mark.parametrize('damage,expected',[('missing','missing'),('corrupt','mismatch'),('large','oversized')])
def test_raw_damage_observed_and_idempotent_parse_denied(client,damage,expected):
    work,a,e=setup(client);storage=Storage(client.app.state.settings)
    with client.app.state.db.Session() as db:key=db.get(SourceArtifact,a['id']).object_key
    if damage=='missing':storage.delete(key)
    else:storage.put(key,b'x'*(2_000_001 if damage=='large' else 20),'application/xml')
    assert verify(client,a).json()['raw']['status']==expected
    assert client.post('/api/v1/admin/intake/artifacts/'+a['id']+'/parse',headers=ADMIN).status_code==409


def test_normalized_missing_and_invalid_passages(client):
    work,a,e=setup(client);storage=Storage(client.app.state.settings)
    with client.app.state.db.Session() as db:key=db.get(SourceExtraction,e['id']).object_key
    storage.delete(key)
    assert verify(client,a).json()['extractions'][0]['status']=='missing'
    assert client.post('/api/v1/admin/intake/artifacts/'+a['id']+'/parse',headers=ADMIN).status_code==409
    body=canonical([{'text':'Synthetic','locator':'','sha256':digest('Synthetic')}]);checksum=digest(body)
    with client.app.state.db.Session() as db:
        ex=db.get(SourceExtraction,e['id']);artifact=db.get(SourceArtifact,a['id'])
        ex.normalized_sha256=checksum;ex.object_key=f'sources/{work["id"]}/parsed/{artifact.raw_sha256}-{checksum}.json'
        storage.put(ex.object_key,body,'application/json');db.commit()
    assert verify(client,a).json()['extractions'][0]['status']=='invalid_passages'


def test_revoked_rights_stop_before_storage_read(client,monkeypatch):
    work,a,e=setup(client)
    with client.app.state.db.Session() as db:db.get(Source,work['source_id']).enabled=False;db.commit()
    monkeypatch.setattr(Storage,'get_bounded',lambda *_:pytest.fail('Must not read denied bytes'))
    assert verify(client,a).status_code==403


def test_record_key_cannot_select_unrelated_object(client):
    work,a,e=setup(client)
    with client.app.state.db.Session() as db:db.get(SourceArtifact,a['id']).object_key='private/other';db.commit()
    assert verify(client,a).json()['raw']['status']=='invalid_record'


def test_provider_error_redacted(client,monkeypatch):
    work,a,e=setup(client)
    def broken(*_):raise RuntimeError('private bucket credential detail')
    monkeypatch.setattr(Storage,'get_bounded',broken)
    r=verify(client,a);assert r.json()['raw']['status']=='unreadable' and 'credential detail' not in r.text


def test_raw_only_permission_does_not_read_normalized(client,monkeypatch):
    from app.services import rights
    work,a,e=setup(client)
    with client.app.state.db.Session() as db:
        source=db.get(Source,work['source_id']);source.policy={**source.policy,'store_text':False}
        rights.record_approval(source,'approver');db.commit()
    original=Storage.get_bounded
    def read(self,key,maximum):
        assert '/parsed/' not in key
        return original(self,key,maximum)
    monkeypatch.setattr(Storage,'get_bounded',read)
    r=verify(client,a).json()
    assert r['raw']['status']=='verified' and r['extractions'][0]['status']=='not_authorized'


def test_gcs_read_uses_raw_bounded_range_and_maps_missing(client,monkeypatch):
    from google.cloud import storage
    from google.api_core.exceptions import NotFound
    from types import SimpleNamespace
    settings=client.app.state.settings.model_copy(update={'storage_provider':'gcs','gcs_bucket':'synthetic-bucket','google_cloud_project':'synthetic-project'})
    calls=[]
    def download(**kwargs):calls.append(kwargs);return b'1234'
    blob=SimpleNamespace(download_as_bytes=download)
    monkeypatch.setattr(storage,'Client',lambda **_:SimpleNamespace(bucket=lambda _:SimpleNamespace(blob=lambda _:blob)))
    with pytest.raises(OverflowError):Storage(settings).get_bounded('synthetic',3)
    assert calls==[{'start':0,'end':3,'raw_download':True,'timeout':30,'retry':None}]
    def missing(**_):raise NotFound('private object identifier')
    blob.download_as_bytes=missing
    with pytest.raises(FileNotFoundError):Storage(settings).get_bounded('synthetic',3)


def test_local_read_rejects_nonregular_and_escape(client):
    import os
    storage=Storage(client.app.state.settings)
    fifo=storage.root/'synthetic-fifo';os.mkfifo(fifo)
    with pytest.raises(ValueError):storage.get_bounded('synthetic-fifo',100)
    with pytest.raises(ValueError):storage.get_bounded('../outside',100)
