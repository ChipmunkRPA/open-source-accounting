"""Synthetic licensed dependencies; no real permission or professional review."""
import pytest
from fastapi import HTTPException
from app.models import Source,OutputBudget,EditorialReview,now
from app.services import editorial,rights,output_rights
from app.editorial_schemas import EditorialDecision
from app.sec_core.core import digest
from test_output_rights import fixture
from conftest import complete_run


def link(db,*,per=100000,total=1000000,parent_id=None):
    tid,group=fixture(db,per=per,total=total)
    target=db.get(Source,tid)
    parent=db.get(Source,parent_id) if parent_id else None
    if not parent:
        parent=Source(title='Synthetic derived commentary',publisher='Test fixture',text='Synthetic derived prose.',
            canonical_url='https://example.test/derived',kind='original_commentary',reviewed=True,created_by='admin',approved_by='approver',
            policy={'basis':'original','commercial_use':True,'display_full':True,'quote':True,'export':True,'model_input':True,'store_text':True})
        db.add(parent);db.flush()
    parent.policy={**parent.policy,'requires_technical_review':True,'content_reference_ids':['synthetic-target']}
    rights.record_approval(parent,'approver');db.commit()
    payload=EditorialDecision(expected_policy_version=parent.policy_version,expected_review_revision=editorial.revision(parent),
        content_sha256=digest(parent.text),decision='approved',review_scope='Synthetic derived-output scope',
        review_note='Synthetic dependency only; no actual publication or professional review.',evidence_ref='ev_synthetic_derived',evidence_sha256='a'*64,
        expires_at=now()+3600,checked_reference_ids=['synthetic-target'],confirm_actual_review_performed=True,
        reference_bindings=[{'reference_id':'synthetic-target','source_id':target.id,'review_revision':editorial.revision(target),
            'policy_version':target.policy_version,'locator':target.canonical_url}])
    editorial.record(db,parent,payload,'editor')
    return parent.id,tid,group,payload


def test_inherited_group_limits_and_notices(client):
    with client.app.state.db.Session() as db:
        sid,tid,group,_=link(db,per=8,total=13)
        source=db.get(Source,sid)
        assert rights.allowed(source,'model_input')
        assert output_rights.notices(db,[source])[0]['notice'].startswith('Fixture Author')
        output_rights.release(db,[source],'alpha');db.commit()
        output_rights.release(db,[db.get(Source,tid)],'alpha');db.commit()
        assert db.get(OutputBudget,group).released_chars==7
        output_rights.release(db,[source],'beta');db.commit()
        with pytest.raises(HTTPException):output_rights.release(db,[source],'z')
        db.rollback();assert db.get(OutputBudget,group).released_chars==13


def test_revocation_cannot_remove_exact_body_output_obligations(client):
    with client.app.state.db.Session() as db:
        sid,tid,group,payload=link(db)
        source=db.get(Source,sid)
        payload=payload.model_copy(update={'expected_policy_version':source.policy_version,'decision':'revoked','reference_bindings':[]})
        editorial.record(db,source,payload,'editor')
        assert not rights.allowed(source,'model_input')
        assert rights.allowed(source,'export')
        assert {s.id for s in output_rights.source_lineage(db,[source])}=={sid,tid}
        output_rights.release(db,[source],'derived');db.commit()
        assert db.get(OutputBudget,group).released_chars==9
        target=db.get(Source,tid);target.reviewed=False
        assert not rights.allowed(source,'export') and not rights.allowed(source,'display_full')


@pytest.mark.parametrize('change',['missing','revision','tampered_history'])
def test_stale_dependency_denies_derived_display(client,change):
    with client.app.state.db.Session() as db:
        sid,tid,_,_=link(db);source=db.get(Source,sid);target=db.get(Source,tid)
        if change=='missing':target.enabled=False
        elif change=='revision':target.version_label='changed'
        else:
            record=db.get(EditorialReview,source.policy['technical_review_record_id'])
            record.payload={**record.payload,'reference_bindings':[]}
        assert not rights.allowed(source,'display_full') and not rights.allowed(source,'export')


def test_derived_source_and_private_history_include_notice(client):
    with client.app.state.db.Session() as db:sid,_,group,_=link(db)
    r=client.get('/api/v1/sources/'+sid);assert r.status_code==200
    assert r.json()['source_attributions'][0]['notice'].startswith('Fixture Author')
    r=client.get('/api/v1/editorial/sources/'+sid+'/reviews',headers={'X-Dev-User':'editor'})
    assert r.status_code==200 and r.json()['source_attributions']
    with client.app.state.db.Session() as db:assert db.get(OutputBudget,group).released_chars>0


def test_derived_run_and_memo_export_inherit_notice(client):
    with client.app.state.db.Session() as db:_,_,group,_=link(db,parent_id='sample-research')
    run=complete_run(client)
    assert any('Required synthetic notice' in n['notice'] for n in run['result']['source_attributions'])
    memo=client.post('/api/v1/runs/'+run['id']+'/memo').json()
    for format in ['md','html']:
        r=client.get('/api/v1/memos/'+memo['id']+'/export',params={'format':format})
        assert r.status_code==200 and 'Required synthetic notice' in r.text
    with client.app.state.db.Session() as db:assert db.get(OutputBudget,group).released_chars>0


def test_history_retains_old_body_obligations(client):
    with client.app.state.db.Session() as db:
        sid,tid,_,_=link(db)
        source=db.get(Source,sid);source.text='Different synthetic draft body.'
        rights.record_approval(source,'approver');db.commit()
    url='/api/v1/editorial/sources/'+sid+'/reviews'
    r=client.get(url,headers={'X-Dev-User':'editor'})
    assert r.status_code==200 and r.json()['source_attributions']
    with client.app.state.db.Session() as db:
        db.get(Source,tid).reviewed=False;db.commit()
    assert client.get(url,headers={'X-Dev-User':'editor'}).status_code==403


def test_rebinding_same_body_cannot_remove_prior_group(client):
    with client.app.state.db.Session() as db:
        sid,first,group1,_=link(db)
        _,second,group2,_=link(db,parent_id=sid)
        source=db.get(Source,sid)
        assert {s.id for s in output_rights.source_lineage(db,[source])}=={sid,first,second}
        output_rights.release(db,[source],'shared');db.commit()
        assert db.get(OutputBudget,group1).released_chars==db.get(OutputBudget,group2).released_chars==8


def test_nested_dependencies_inherit_all_groups(client):
    from app.sec_core.core import canonical
    with client.app.state.db.Session() as db:
        first,_,group1,_=link(db)
        second,_,group2,_=link(db)
        parent=db.get(Source,first);target=db.get(Source,second)
        # Synthetic historical attestation adds a nested dependency, not an approval.
        payload={'content_sha256':digest(parent.text),'reference_bindings':[{'source_id':second,
            'review_revision':editorial.revision(target),'locator':target.canonical_url}]}
        db.add(EditorialReview(source_id=first,decision='changes_requested',review_revision=editorial.revision(parent),
            payload=payload,payload_sha256=digest(canonical(payload)),expires_at=now()+3600));db.commit()
        output_rights.release(db,[parent],'nested');db.commit()
        assert db.get(OutputBudget,group1).released_chars==db.get(OutputBudget,group2).released_chars==8
