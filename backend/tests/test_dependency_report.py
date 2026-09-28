"""Staged metadata report tests. No source acquisition or actual human approval."""
from app.models import Source,EditorialReview,OutputRelease
from app.services import editorial
from app.sec_core.core import canonical,digest
from test_content_library import pack as pack,stage,decision
from test_dependencies import linked
from test_editorial_ledger import EDITOR,review

URL='/api/v1/editorial/dependency-report'


def test_report_roles_and_pagination(client,pack):
    stage(client,pack)
    assert client.get(URL).status_code==403
    r=client.get(URL,headers=EDITOR,params={'limit':10}).json()
    assert len(r['items'])==10 and r['total']>=63
    assert len([f for f in r['families'] if f['family_id']!='UNCLASSIFIED'])==32
    original=next(f for f in r['families'] if f['family_id']=='ORIGINAL')
    assert original['staged_sources']==63 and original['original_sources_missing_bindings']==63
    assert original['artifact_records']==0 and original['current_technical_records']==0
    assert client.get(URL,headers=EDITOR,params={'limit':101}).status_code==422
    assert client.get(URL,headers=EDITOR,params={'affected_by':'unknown'}).status_code==404


def test_missing_stale_and_no_private_text(client,pack):
    sid,tid=linked(client,pack)
    with client.app.state.db.Session() as db:
        db.get(Source,tid).policy_version+=1;db.commit()
    r=client.get(URL,headers=EDITOR,params={'limit':100}).json()
    row=next(s for s in r['items'] if s['source_id']==sid)
    assert row['stale_bindings'] and not row['missing_reference_ids']
    assert 'text' not in row and 'review_note' not in str(r) and 'evidence_ref' not in str(r)
    with client.app.state.db.Session() as db:assert db.query(OutputRelease).count()==0


def test_reverse_impact_retains_revoked_and_transitive_links(client,pack):
    sid,tid=linked(client,pack)
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);payload=decision(s,decision='revoked')
        outer=Source(title='Synthetic outer dependent',publisher='Fixture',text='Synthetic outer body',policy={})
        db.add(outer);db.flush()
        data={'content_sha256':digest(outer.text),'reference_bindings':[{'source_id':sid,'review_revision':editorial.revision(s),'locator':s.canonical_url}]}
        db.add(EditorialReview(source_id=outer.id,decision='changes_requested',review_revision=editorial.revision(outer),payload=data,payload_sha256=digest(canonical(data)),expires_at=1));db.commit();oid=outer.id
    assert review(client,sid,payload).status_code==200
    r=client.get(URL,headers=EDITOR,params={'affected_by':tid}).json()
    assert {sid,oid}.issubset(r['affected_source_ids']) and r['graph_complete']
    assert r['report_sha256']==client.get(URL,headers=EDITOR,params={'affected_by':tid}).json()['report_sha256']


def test_corrupt_graph_reports_incomplete(client,pack):
    sid,tid=linked(client,pack)
    with client.app.state.db.Session() as db:
        row=db.get(EditorialReview,db.get(Source,sid).policy['technical_review_record_id'])
        row.payload_sha256='0'*64;db.commit()
    r=client.get(URL,headers=EDITOR,params={'affected_by':tid}).json()
    assert r['graph_complete'] is False


def test_report_bound_fails_instead_of_truncating(client,monkeypatch):
    from app.services import dependency_report
    monkeypatch.setattr(dependency_report,'MAX_SOURCES',0)
    assert client.get(URL,headers=EDITOR).status_code==422


def test_artifact_and_extraction_records_are_not_claimed_verified_bytes(client):
    from app.models import IntakeWork,SourceArtifact,SourceExtraction
    with client.app.state.db.Session() as db:
        s=Source(title='Synthetic IFRS metadata',publisher='Fixture',text='',policy={});db.add(s);db.flush()
        work=IntakeWork(source_id=s.id,family_id='IFRS',work_id='synthetic',edition='test',manifest={},manifest_sha256='a'*64)
        db.add(work);db.flush()
        artifact=SourceArtifact(work_id=work.id,raw_sha256='b'*64,object_key='not-stored',byte_count=1,mime='text/plain',receipt={})
        db.add(artifact);db.flush()
        db.add(SourceExtraction(artifact_id=artifact.id,parser_version='synthetic',normalized_sha256='c'*64,object_key='not-stored',passage_count=2));db.commit()
    r=client.get(URL,headers=EDITOR).json()
    family=next(f for f in r['families'] if f['family_id']=='IFRS')
    assert family['artifact_records']==1 and family['extraction_records']==1
    assert 'bytes, indexing and evaluations were not verified' in r['notice']


def test_bundled_sec_excerpts_not_counted_as_http_artifacts(client):
    from test_sec_core_integration import staged
    staged(client)
    r=client.get(URL,headers=EDITOR).json()
    sec=[f for f in r['families'] if f['family_id'].startswith('SEC_')]
    assert sum(f['staged_sources'] for f in sec)==28
    assert sum(f['artifact_records'] for f in sec)==0


def test_historical_cycles_are_reported_without_infinite_traversal(client):
    with client.app.state.db.Session() as db:
        a=Source(title='Synthetic A',publisher='Fixture',text='A',policy={})
        b=Source(title='Synthetic B',publisher='Fixture',text='B',policy={})
        db.add_all([a,b]);db.flush()
        for source,target in [(a,b),(b,a)]:
            data={'content_sha256':digest(source.text),'reference_bindings':[{'source_id':target.id,'review_revision':editorial.revision(target),'locator':target.canonical_url}]}
            db.add(EditorialReview(source_id=source.id,decision='changes_requested',review_revision=editorial.revision(source),payload=data,payload_sha256=digest(canonical(data)),expires_at=1))
        db.commit();ids={a.id,b.id}
    r=client.get(URL,headers=EDITOR,params={'affected_by':a.id}).json()
    assert set(r['cyclic_or_dependent_source_ids'])==ids
    assert r['affected_source_ids']==[b.id]
