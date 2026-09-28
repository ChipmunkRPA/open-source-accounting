"""Synthetic recovery revisions; no independent human approvals asserted."""
import pytest
from app.models import Source,SourceArtifact,SourceExtraction,Audit
from app.services import rights
from app.services.storage import Storage
from test_artifact_integrity import setup,verify
from test_source_intake import ADMIN,APPROVER,RAW
from test_integrity_holds import damage,release
from conftest import rights_approval


def prepared(client):
    work,a,e=setup(client)
    ids=client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN).json()['source_ids']
    key=damage(client,a);verify(client,a);Storage(client.app.state.settings).put(key,RAW,'application/xml')
    checked=verify(client,a).json();r=release(client,a,checked['policy_version']);assert r.status_code==200
    return work,a,e,ids,r.json()['policy_version']


def restage(client,e,version,headers=ADMIN,**changes):
    body={'expected_parent_policy_version':version,'expected_normalized_sha256':e['normalized_sha256'],
          'confirm_fresh_reviews_required':True};body.update(changes)
    return client.post('/api/v1/admin/intake/extractions/'+e['id']+'/restage',headers=headers,json=body)


def test_fresh_versions_preserve_old_sources_and_retry_identity(client):
    work,a,e,old_ids,version=prepared(client)
    with client.app.state.db.Session() as db:
        old=db.get(Source,old_ids[0]);snapshot=(old.text,dict(old.policy),old.policy_version,old.reviewed)
    assert client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN).status_code==409
    r=restage(client,e,version);assert r.status_code==200,r.text
    result=r.json();assert result['created']==1 and result['predecessor_source_ids']==old_ids
    assert result['source_ids']!=old_ids and not result['approval_granted'] and not result['prior_evidence_restored']
    retry=restage(client,e,version).json();assert retry['source_ids']==result['source_ids'] and retry['created']==0
    with client.app.state.db.Session() as db:
        old=db.get(Source,old_ids[0]);new=db.get(Source,result['source_ids'][0])
        assert (old.text,old.policy,old.policy_version,old.reviewed)==snapshot
        assert new.text==old.text and new.version_label==old.version_label
        assert not new.reviewed and new.approved_by is None and not rights.allowed(new,'model_input')
        assert new.policy['technical_review_status']=='unreviewed'
        assert new.policy['applicability_review_status']=='pending'
        assert not new.policy.get('technical_review_record_id') and not new.policy.get('applicability_record_id')
        assert db.query(Audit).filter(Audit.action=='intake.restaged_unapproved').count()==1
    # Even rights approval alone does not create parser/technical/applicability decisions.
    sid=result['source_ids'][0]
    assert client.post('/api/v1/admin/sources/'+sid+'/approve',headers=APPROVER,json=rights_approval(client,sid)).status_code==200
    with client.app.state.db.Session() as db:
        assert rights.allowed(db.get(Source,sid),'display_full')
        assert not rights.allowed(db.get(Source,sid),'model_input')
        assert not rights.allowed(db.get(Source,old_ids[0]),'display_full')


def test_roles_stale_expected_hash_and_current_binding(client):
    work,a,e=setup(client)
    with client.app.state.db.Session() as db:version=db.get(Source,work['source_id']).policy_version
    assert restage(client,e,version,headers={}).status_code==403
    assert restage(client,e,version).status_code==409
    client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN)
    assert restage(client,e,version).status_code==409
    assert restage(client,e,version+1).status_code==409
    assert restage(client,e,version,expected_normalized_sha256='0'*64).status_code==409
    assert restage(client,e,version,confirm_fresh_reviews_required=False).status_code==422


@pytest.mark.parametrize('change',['raw','normalized','predecessor'])
def test_corrupt_recovery_creates_no_sources(client,change):
    work,a,e,old_ids,version=prepared(client)
    with client.app.state.db.Session() as db:
        before=db.query(Source).count()
        if change=='predecessor':db.get(Source,old_ids[0]).text='changed';db.commit()
        else:
            obj=db.get(SourceArtifact,a['id']) if change=='raw' else db.get(SourceExtraction,e['id'])
            Storage(client.app.state.settings).put(obj.object_key,b'wrong','application/octet-stream')
    assert restage(client,e,version).status_code==409
    with client.app.state.db.Session() as db:assert db.query(Source).count()==before


def test_holds_block_recovery(client):
    work,a,e,old_ids,version=prepared(client);damage(client,a);checked=verify(client,a).json()
    assert restage(client,e,checked['policy_version']).json()['error']['code']=='INTEGRITY_HOLD'


def test_partial_passage_failure_rolls_back_new_versions(client):
    from test_source_intake import registered,fetch,parse,FakeGateway
    work=registered(client)
    raw=b'<ECFR><SECTION N="229.999"><P ID="a">Synthetic first paragraph.</P><P ID="b">Synthetic second paragraph.</P></SECTION></ECFR>'
    a=fetch(client,work,FakeGateway(raw));e=parse(client,a)
    ids=client.post('/api/v1/admin/intake/extractions/'+e['id']+'/stage',headers=ADMIN).json()['source_ids']
    assert len(ids)==2
    with client.app.state.db.Session() as db:
        parent=db.get(Source,work['source_id']);parent.policy_version+=1;version=parent.policy_version
        db.get(Source,ids[1]).text='invalid second predecessor';db.commit();before=db.query(Source).count()
    assert restage(client,e,version).status_code==409
    with client.app.state.db.Session() as db:assert db.query(Source).count()==before


@pytest.mark.parametrize('field',['intake_extraction_id','intake_artifact_id','intake_passage_index'])
def test_retry_rejects_tampered_revision_identity(client,field):
    work,a,e,old_ids,version=prepared(client)
    sid=restage(client,e,version).json()['source_ids'][0]
    with client.app.state.db.Session() as db:
        row=db.get(Source,sid);row.policy={**row.policy,field:'tampered'};db.commit()
    assert restage(client,e,version).status_code==409
