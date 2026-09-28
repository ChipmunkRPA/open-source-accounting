"""Original synthetic passages and mock Agent execution; no professional review."""
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.models import Source,Run,Evidence
from app.sec_core.core import digest,canonical
from app.services import passage_context as pc,rights,retrieval


def source(text='Original α amount 1250.\n\n  Exception: excluded.\n \nLast paragraph.',locator='Physical page 2, block 3'):
    return SimpleNamespace(id='synthetic',text=text,policy_version=2,version_label='fixture',policy={
        'intake_extraction_id':'ex','intake_artifact_id':'raw','intake_parser_version':'synthetic-parser-1',
        'intake_locator':locator,'content_sha256':digest(text)})


def test_segments_bind_absolute_unicode_offsets_across_blank_lines_and_parts():
    s=source('α'*3001+'\n \n\tSecond paragraph\n\nEnd')
    pieces=list(pc.segments(s.text))
    assert [(a,b) for _,_,a,b,_ in pieces]==[(0,3000),(3000,3001),(3004,3021),(3023,3026)]
    for _,_,a,b,text in pieces:
        packet=pc.packet(s,a,b)
        evidence=SimpleNamespace(text=text,locator=pc.locator(packet),extraction_context=packet)
        assert text==s.text[a:b] and pc.current(s,evidence)
        assert packet['passage_text_sha256']==digest(text)


@pytest.mark.parametrize('loc',['PDF physical page 7 (printed iv), block 2','DOCX word/document.xml paragraph 9',
    'HTML #note-7 table 2 row 4 cell 3','/CFR/TITLE[1]/SECTION[4]/P[2]'])
def test_general_retrieval_retains_intake_locators(client,monkeypatch,loc):
    monkeypatch.setattr(retrieval,'allowed',lambda *a,**kw:True)
    monkeypatch.setattr(retrieval,'applies',lambda *a,**kw:True)
    monkeypatch.setattr(retrieval,'dependencies_allowed',lambda *a,**kw:True)
    fixture=source(locator=loc)
    with client.app.state.db.Session() as db:
        s=Source(id=fixture.id,title='quasar original',publisher='Fixture',text=fixture.text,
            reviewed=True,policy=fixture.policy);db.add(s);db.commit()
        run=SimpleNamespace(context={'framework':'US_GAAP'},document_ids=[],workspace_id='demo-workspace')
        rows=[r for r in retrieval.search(db,run,'quasar') if r['source_id']==s.id]
        assert len(rows)==3
        for row in rows:
            assert row['locator'].startswith(loc+' (characters ')
            assert pc.current(s,Evidence(run_id='synthetic',**row))


@pytest.mark.parametrize('change',['text','locator','hash','offset','clear','provenance'])
def test_tampered_evidence_is_rejected(change):
    s=source();snapshot=pc.packet(s,0,22)
    evidence=SimpleNamespace(text=s.text[:22],locator=pc.locator(snapshot),extraction_context=snapshot)
    assert pc.current(s,evidence)
    if change=='text':evidence.text='Other text'
    elif change=='locator':evidence.locator='Another page'
    elif change=='hash':snapshot['passage_text_sha256']='0'*64
    elif change=='offset':snapshot['character_start']=True
    elif change=='clear':evidence.extraction_context={}
    else:s.policy={**s.policy,'intake_parser_version':'changed'}
    assert not pc.current(s,evidence)


def test_oversized_details_are_explicitly_omitted_but_bound():
    s=source();s.policy['intake_pdf']={'warning':'x'*20000}
    snapshot=pc.packet(s,0,22)
    assert snapshot['provenance_details_omitted'] and 'provenance' not in snapshot
    assert len(canonical(snapshot))<=pc.MAX_CONTEXT_BYTES
    evidence=SimpleNamespace(text=s.text[:22],locator=pc.locator(snapshot),extraction_context=snapshot)
    assert pc.current(s,evidence)
    s.policy['intake_pdf']={'warning':'y'*20000}
    assert not pc.current(s,evidence)


def test_mismatched_staged_body_hash_cannot_create_packet():
    s=source();s.policy['content_sha256']='0'*64
    assert pc.packet(s,0,22) is None


def test_actual_intake_reviews_mock_run_and_saved_citation_checks(client):
    from test_parser_review import prepared,record
    from test_content_library import decision as technical_decision
    from app.services import editorial,applicability
    from app.editorial_schemas import EditorialDecision
    from app.applicability_schemas import ApplicabilityDecision
    from test_applicability import applicability_payload,CONTEXT
    from conftest import complete_run
    eid,sid,decision,_=prepared(client)
    assert record(client,eid,decision).status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);s.reviewed=True;rights.record_approval(s,'approver');db.commit()
        editorial.record(db,s,EditorialDecision.model_validate(technical_decision(s)),'editor')
        applicability.record(db,s,ApplicabilityDecision.model_validate(applicability_payload(s)),'editor')
    result=complete_run(client,question='Research synthetic original source paragraph for intake testing.',context=CONTEXT)
    with client.app.state.db.Session() as db:
        run=db.get(Run,result['id']);s=db.get(Source,sid)
        evidence=db.scalar(select(Evidence).where(Evidence.run_id==run.id,Evidence.source_id==sid))
        assert evidence and evidence.locator.startswith(s.policy['intake_locator'])
        assert rights.evidence_allowed(db,evidence,'export')
        evidence.locator='Fabricated page';db.commit()
        assert not rights.evidence_allowed(db,evidence,'export')
        evidence.locator=pc.locator(evidence.extraction_context);evidence.extraction_context={};db.commit()
        assert not rights.evidence_allowed(db,evidence,'export')
