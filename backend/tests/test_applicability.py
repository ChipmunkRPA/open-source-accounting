"""Synthetic dates/reviewers only. Never professional applicability evidence."""
import copy
from types import SimpleNamespace
import pytest
from app.models import Source, ApplicabilityReview, now
from app.services import applicability, editorial, rights
from app.services.retrieval import search
from test_content_library import pack as pack
from test_editorial_ledger import prepared, review, EDITOR

CONTEXT={'framework':'US_GAAP','entity_type':'public','period_start':'2025-01-01','period_end':'2025-12-31','knowledge_date':'2020-06-01'}


def applicability_payload(source,**changes):
    return {'expected_policy_version':source.policy_version,'expected_review_revision':editorial.revision(source),
        'decision':'approved','issued_at':'2019-01-01','publicly_available_at':'2020-01-01',
        'effective_from':'2021-01-01','effective_to':None,'confirm_open_ended':True,
        'frameworks':['US_GAAP','IFRS'],'entity_types':['public'],'conditions':[],
        'review_scope':'Synthetic date and scope test','review_note':'Synthetic test only; no actual professional applicability review.',
        'evidence_ref':'ev_synthetic_dates','evidence_sha256':'a'*64,'expires_at':now()+3600,
        'confirm_actual_applicability_review':True,**changes}


def source_ready(client,pack,technical=True):
    sid,technical_payload=prepared(client,pack)
    if technical:
        from dependency_fixtures import bindings
        technical_payload['reference_bindings']=bindings(client,sid)
        assert review(client,sid,technical_payload).status_code==200
    with client.app.state.db.Session() as db:body=applicability_payload(db.get(Source,sid))
    return sid,body


def decide(client,sid,body):
    return client.post('/api/v1/editorial/sources/'+sid+'/applicability',headers=EDITOR,json=body)


def test_review_distinguishes_import_public_and_effective_dates(client,pack):
    sid,body=source_ready(client,pack)
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert not applicability.applies(source,CONTEXT)
    assert decide(client,sid,body).status_code==200
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);source.created_at=now()+10*365*86400
        assert applicability.applies(source,CONTEXT)
        run=SimpleNamespace(context=CONTEXT,document_ids=[],workspace_id='demo-workspace')
        assert sid in {x['source_id'] for x in search(db,run,source.title,100)}
        assert not applicability.applies(source,{**CONTEXT,'knowledge_date':'2019-12-31'})
        assert not applicability.applies(source,{**CONTEXT,'period_start':'2020-12-31'})


@pytest.mark.parametrize('change',[
    {'entity_type':'unknown'},{'entity_type':'private'},{'framework':'UNKNOWN'},
    {'framework':'BOTH'},{'period_end':'2020-12-31'},{'knowledge_date':'invalid'}])
def test_unknown_or_out_of_scope_context_denied(client,pack,change):
    sid,body=source_ready(client,pack);assert decide(client,sid,body).status_code==200
    with client.app.state.db.Session() as db:assert not applicability.applies(db.get(Source,sid),{**CONTEXT,**change})


@pytest.mark.parametrize('change',[
    {'issued_at':None},{'publicly_available_at':None},{'effective_from':None},{'frameworks':[]},
    {'entity_types':[]},{'confirm_open_ended':False},{'effective_to':'2020-01-01'},
    {'publicly_available_at':'2999-01-01'},{'conditions':['x']}])
def test_approval_requires_explicit_supported_dates_and_scope(client,pack,change):
    sid,body=source_ready(client,pack)
    assert decide(client,sid,{**body,**change}).status_code==422


def test_conditions_require_case_review_not_free_text_bypass(client,pack):
    sid,body=source_ready(client,pack)
    response=decide(client,sid,{**body,'conditions':['Requires verified early-adoption election.']})
    assert response.status_code==200 and response.json()['requires_case_review']
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert applicability.current(source)
        assert not applicability.applies(source,{**CONTEXT,'early_adoption':'Yes, trust me'})


def test_missing_technical_review_and_self_review_fail(client,pack):
    sid,body=source_ready(client,pack,technical=False)
    assert decide(client,sid,body).status_code==409
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);source.created_by='editor';db.commit()
    assert decide(client,sid,body).status_code==403


def test_expiry_and_revocation_preserve_record_and_block_saved_export(client,pack,monkeypatch):
    from app.models import Run,Evidence
    sid,body=source_ready(client,pack);result=decide(client,sid,body);assert result.status_code==200
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);old=copy.deepcopy(db.get(ApplicabilityReview,result.json()['record_id']).payload)
        run=Run(workspace_id='demo-workspace',user_id='demo',workflow='deep_research',question='Synthetic',context=CONTEXT)
        db.add(run);db.flush()
        ev=Evidence(run_id=run.id,source_id=sid,title=source.title,locator='Synthetic',text=source.text,access='full',source_kind=source.kind,policy_version=source.policy_version)
        db.add(ev);db.flush();assert rights.evidence_allowed(db,ev,'export')
        with monkeypatch.context() as m:
            m.setattr(applicability,'now',lambda:body['expires_at'])
            assert not rights.evidence_allowed(db,ev,'export')
        revoke=applicability_payload(source,decision='revoked')
    assert decide(client,sid,revoke).status_code==200
    with client.app.state.db.Session() as db:
        assert not applicability.current(db.get(Source,sid))
        assert db.get(ApplicabilityReview,result.json()['record_id']).payload==old
        assert db.query(ApplicabilityReview).filter(ApplicabilityReview.source_id==sid).count()==2


def test_stale_decision_history_privacy_and_changed_dates(client,pack):
    sid,body=source_ready(client,pack);assert decide(client,sid,body).status_code==200
    assert decide(client,sid,body).status_code==409
    endpoint='/api/v1/editorial/sources/'+sid+'/applicability'
    assert client.get(endpoint).status_code==403
    history=client.get(endpoint,headers=EDITOR);assert history.status_code==200 and history.json()['current']
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);source.effective_from='1900-01-01'
        assert not applicability.current(source)


def test_new_technical_decision_invalidates_date_record(client,pack):
    from test_content_library import decision
    sid,body=source_ready(client,pack);assert decide(client,sid,body).status_code==200
    with client.app.state.db.Session() as db:payload=decision(db.get(Source,sid))
    assert review(client,sid,payload).status_code==200
    with client.app.state.db.Session() as db:assert not applicability.current(db.get(Source,sid))


def test_audit_source_requires_explicit_regime_and_checks_run_scope(client,pack):
    from test_content_library import decision
    sid,_=source_ready(client,pack)
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);source.framework='AUDIT';db.commit();technical=decision(source)
    assert review(client,sid,technical).status_code==200
    with client.app.state.db.Session() as db:body=applicability_payload(db.get(Source,sid))
    assert decide(client,sid,body).status_code==422
    assert decide(client,sid,{**body,'audit_regimes':['PCAOB']}).status_code==200
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert not applicability.applies(source,{**CONTEXT,'audit_regime':'UNKNOWN'})
        assert applicability.applies(source,{**CONTEXT,'audit_regime':'PCAOB'})


def test_bounded_interval_rejects_after_end_and_record_tampering(client,pack):
    sid,body=source_ready(client,pack);body['effective_to']='2025-12-31'
    result=decide(client,sid,body);assert result.status_code==200
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert applicability.applies(source,CONTEXT)
        assert not applicability.applies(source,{**CONTEXT,'period_end':'2026-01-01'})
        row=db.get(ApplicabilityReview,result.json()['record_id']);row.payload={**row.payload,'effective_to':None}
        assert not applicability.current(source)
