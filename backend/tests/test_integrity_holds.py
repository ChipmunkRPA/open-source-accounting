"""Operational quarantine fixtures, never publisher or professional approvals."""
from app.models import Source,SourceArtifact,Audit
from app.services import rights
from app.services.storage import Storage
from test_artifact_integrity import setup,verify
from test_source_intake import ADMIN,APPROVER,RAW
from conftest import rights_approval


def damage(client,artifact):
    with client.app.state.db.Session() as db:key=db.get(SourceArtifact,artifact['id']).object_key
    Storage(client.app.state.settings).put(key,b'corrupt','application/xml')
    return key


def release(client,artifact,version,headers=APPROVER):
    return client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/release-hold',headers=headers,
        json={'expected_policy_version':version,'note':'Synthetic restored object verification only.',
              'confirm_reverification_and_stale_evidence':True})


def test_failure_blocks_staged_output_and_repair_does_not_auto_release(client):
    work,a,e=setup(client)
    staged=client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN).json()
    sid=staged['source_ids'][0]
    r=client.post('/api/v1/admin/sources/'+sid+'/approve',headers=APPROVER,json=rights_approval(client,sid))
    assert r.status_code==200
    with client.app.state.db.Session() as db:assert rights.allowed(db.get(Source,sid),'display_full')
    key=damage(client,a);bad=verify(client,a).json()
    assert bad['integrity_hold'] and bad['work_on_hold']
    assert client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN).status_code==409
    with client.app.state.db.Session() as db:
        assert not rights.allowed(db.get(Source,sid),'display_full')
        parent=db.get(Source,work['source_id'])
        assert not rights.allowed(parent,'export') and not rights.allowed(parent,'model_input')
        assert rights.allowed(parent,'store_raw')
    again=verify(client,a).json();assert again['policy_version']==bad['policy_version']
    Storage(client.app.state.settings).put(key,RAW,'application/xml')
    good=verify(client,a).json();assert good['raw']['status']=='verified' and good['integrity_hold']
    assert release(client,a,good['policy_version'],ADMIN).status_code==403
    assert release(client,a,good['policy_version']-1).status_code==409
    restored=release(client,a,good['policy_version']);assert restored.status_code==200,restored.text
    assert not restored.json()['work_on_hold'] and not restored.json()['old_evidence_restored']
    with client.app.state.db.Session() as db:
        assert not rights.allowed(db.get(Source,sid),'display_full')  # Old parent revision never revives.
        assert db.query(Audit).filter(Audit.action=='intake.integrity_hold_released').count()==1
    assert release(client,a,restored.json()['policy_version']).status_code==409


def test_failed_release_retains_observation_and_hold(client):
    work,a,e=setup(client);damage(client,a);bad=verify(client,a).json()
    assert release(client,a,bad['policy_version']).status_code==409
    with client.app.state.db.Session() as db:
        assert a['id'] in db.get(Source,work['source_id']).policy['integrity_holds']
        assert db.query(Audit).filter(Audit.action=='intake.integrity_observed').count()==2


def test_rights_approval_cannot_remove_integrity_hold(client):
    work,a,e=setup(client);damage(client,a);verify(client,a)
    r=client.post('/api/v1/admin/sources/'+work['source_id']+'/approve',headers=APPROVER,json=rights_approval(client,work['source_id']))
    assert r.status_code==200
    with client.app.state.db.Session() as db:
        assert not rights.allowed(db.get(Source,work['source_id']),'display_full')


def test_metadata_and_storage_permissions_stay_separate(client):
    work,a,e=setup(client);damage(client,a);verify(client,a)
    r=client.get('/api/v1/admin/intake/works/'+work['id'],headers=ADMIN)
    assert r.json()['integrity_holds'][a['id']]['failures'][0]['status']=='mismatch'
    assert r.json()['operations']['store_raw'] and not r.json()['operations']['display_full']
    assert client.post('/api/v1/admin/intake/artifacts/'+a['id']+'/release-hold',headers=APPROVER,json={}).status_code==422


def test_releasing_one_artifact_preserves_other_hold(client):
    from app.sec_core.core import digest
    work,a,e=setup(client);first_key=damage(client,a);verify(client,a)
    with client.app.state.db.Session() as db:
        checksum=digest(b'other');other=SourceArtifact(work_id=work['id'],raw_sha256=checksum,byte_count=5,
            object_key=f'sources/{work["id"]}/raw/{checksum}.bin',mime='application/xml',receipt={})
        db.add(other);db.commit();other_id=other.id
    verify(client,{'id':other_id})
    Storage(client.app.state.settings).put(first_key,RAW,'application/xml')
    good=verify(client,a).json()
    r=release(client,a,good['policy_version']);assert r.status_code==200 and r.json()['work_on_hold']
    with client.app.state.db.Session() as db:
        assert set(db.get(Source,work['source_id']).policy['integrity_holds'])=={other_id}
