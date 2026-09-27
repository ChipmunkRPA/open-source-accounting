"""Synthetic dependency graphs; no primary text acquisition or human approval."""
import pytest
from app.models import Source
from app.services import rights,dependencies
from test_content_library import pack as pack
from test_editorial_ledger import prepared,review
from dependency_fixtures import bindings


def linked(client,pack):
    sid,payload=prepared(client,pack)
    payload['reference_bindings']=bindings(client,sid)
    assert review(client,sid,payload).status_code==200
    return sid,payload['reference_bindings'][0]['source_id']


def test_reference_metadata_alone_does_not_admit_original(client,pack):
    sid,payload=prepared(client,pack);assert review(client,sid,payload).status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        assert rights.allowed(s,'display_full') and rights.allowed(s,'export')
        assert not rights.allowed(s,'model_input')
        assert not dependencies.allowed(s,'export')


@pytest.mark.parametrize('change',['disabled','revision','policy','rights','technical','output','attribution'])
def test_dependency_changes_withhold_parent_operations(client,pack,change):
    sid,tid=linked(client,pack)
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);target=db.get(Source,tid)
        assert rights.allowed(s,'model_input') and dependencies.allowed(s,'export')
        if change=='disabled':target.enabled=False
        elif change=='revision':target.version_label='changed'
        elif change=='policy':target.policy_version+=1
        elif change=='rights':target.reviewed=False
        elif change=='technical':target.policy={**target.policy,'technical_review_record_id':None}
        elif change=='output':target.policy={**target.policy,'output_control':{}}
        else:target.policy={**target.policy,'attribution':'Mandatory target notice'}
        assert not rights.allowed(s,'model_input')
        assert not dependencies.allowed(s,'export')


@pytest.mark.parametrize('change,status',[('self',422),('missing',409),('locator',409),('stale',409),('partial',422),('duplicate',422)])
def test_binding_validation(client,pack,change,status):
    sid,payload=prepared(client,pack);payload['reference_bindings']=bindings(client,sid)
    b=payload['reference_bindings'][0]
    if change=='self':b['source_id']=sid
    elif change=='missing':b['source_id']='missing'
    elif change=='locator':b['locator']='invented paragraph'
    elif change=='stale':b['policy_version']+=1
    elif change=='partial':payload['reference_bindings']=payload['reference_bindings'][:1]
    else:payload['reference_bindings'].append(b.copy())
    assert review(client,sid,payload).status_code==status


def test_dependency_period_scope_withholds_parent(client,pack):
    sid,_=linked(client,pack)
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        assert dependencies.allowed(s,'export',accounting_context={'framework':'US_GAAP','entity_type':'public','period_end':'2025-12-31'})
        assert not dependencies.allowed(s,'export',accounting_context={'framework':'US_GAAP','entity_type':'public','period_end':'2000-12-31'})


def test_saved_export_and_retrieval_recheck_dependency(client,pack):
    from app.models import Run,Evidence
    from app.services.retrieval import search
    sid,tid=linked(client,pack)
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid);target=db.get(Source,tid)
        run=Run(workspace_id='demo-workspace',user_id='demo',workflow='deep_research',question='Synthetic',context={'framework':'US_GAAP','entity_type':'public'},document_ids=[])
        db.add(run);db.flush()
        ev=Evidence(run_id=run.id,source_id=sid,title=source.title,text=source.text,locator='Synthetic',access='full',source_kind=source.kind,policy_version=source.policy_version)
        db.add(ev);db.flush()
        assert rights.evidence_allowed(db,ev,'export')
        assert sid in {r['source_id'] for r in search(db,run,source.title,100)}
        target.enabled=False
        assert not rights.evidence_allowed(db,ev,'export')
        assert sid not in {r['source_id'] for r in search(db,run,source.title,100)}
