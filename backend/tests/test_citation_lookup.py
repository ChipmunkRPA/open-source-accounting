"""Synthetic exact readings; no actual accounting support or rights approvals."""
import pytest
from app.models import Source, OutputBudget
from app.sec_core.core import digest
from app.services import rights
from test_source_search import source


def fixture(client, text='Original α exception.\n\nSecond paragraph.'):
    with client.app.state.db.Session() as db:
        s=source(db,'exact-fixture');s.text=text
        s.policy={**s.policy,'intake_locator':'Synthetic page 2, paragraph 3'}
        rights.record_approval(s,'synthetic');db.commit()
    return '/api/v1/sources/exact-fixture/passages'


def payload(item):
    return {'expected_revision':item['revision'],'locator':item['locator'],
        'character_start':item['character_start'],'character_end':item['character_end'],
        'passage_text_sha256':item['passage_text_sha256']}


def test_public_exact_unicode_resolution_and_paged_inventory(client):
    text='α'*3001+'\n\n'+('Original exception. '*300)
    url=fixture(client,text)
    page=client.get(url,params={'limit':1}).json();assert len(page['items'])==1
    item=page['items'][0];assert item['character_end']==3000
    assert item['passage_text_sha256']==digest(text[:3000])
    assert page['next_start']==3000 and not page['agent_admission_granted']
    second=client.get(url,params={'start':page['next_start'],'limit':1}).json()
    assert second['items'][0]['character_start']==3000
    result=client.post(url+'/resolve',json=payload(item))
    assert result.status_code==200,result.text
    assert result.json()['text']==text[:3000] and not result.json()['claim_support_verified']
    assert result.json()['citation']['locator'].startswith('Synthetic page 2, paragraph 3')


@pytest.mark.parametrize('change',['revision','locator','hash','boolean','outside','reversed','oversized'])
def test_exact_citation_mismatches_fail(client,change):
    url=fixture(client,'Original '+('a'*4000));item=client.get(url).json()['items'][0];body=payload(item)
    if change=='revision':body['expected_revision']='0'*64
    elif change=='locator':body['locator']='Fabricated page'
    elif change=='hash':body['passage_text_sha256']='0'*64
    elif change=='boolean':body['character_start']=True
    elif change=='outside':body['character_end']=99999
    elif change=='reversed':body['character_start']=body['character_end']
    else:body['character_end']=3001
    response=client.post(url+'/resolve',json=body)
    assert response.status_code==(409 if change in {'revision','locator','hash'} else 422),response.text
    assert 'text' not in response.json()


@pytest.mark.parametrize('change',['disabled','unreviewed','scope','expired','revoked','body','locator','provenance'])
def test_changed_or_restricted_sources_cannot_resolve_old_citation(client,change):
    url=fixture(client);body=payload(client.get(url).json()['items'][0])
    with client.app.state.db.Session() as db:
        s=db.get(Source,'exact-fixture')
        if change=='disabled':s.enabled=False
        elif change=='unreviewed':s.reviewed=False
        elif change=='body':s.text='Replacement';rights.record_approval(s,'synthetic')
        else:
            update={'scope':{'scope':{'workspace_id':['secret']}},'expired':{'expires_at':1},
                'revoked':{'display_full':False},'locator':{'intake_locator':'Changed locator'},
                'provenance':{'intake_parser_version':'changed'}}[change]
            s.policy={**s.policy,**update};rights.record_approval(s,'synthetic')
        db.commit()
    result=client.post(url+'/resolve',json=body)
    assert result.status_code in {403,404,409},result.text
    assert 'text' not in result.json()


def test_source_record_is_not_represented_as_retained_page(client):
    url=fixture(client)
    with client.app.state.db.Session() as db:
        s=db.get(Source,'exact-fixture');s.policy={k:v for k,v in s.policy.items() if k!='intake_locator'};db.commit()
    item=client.get(url).json()['items'][0]
    assert item['locator_kind']=='source_record' and item['source_locator']=='source:exact-fixture'
    assert client.get(url,params={'start':99999}).status_code==422
    assert client.get('/api/v1/sources/missing/passages').status_code==404


def test_lookup_retains_notices_and_shared_output_budget(client):
    url=fixture(client)
    with client.app.state.db.Session() as db:
        s=db.get(Source,'exact-fixture')
        s.policy={**s.policy,'attribution':'Synthetic author notice','output_control':{
            'group_id':'citation-fixture','mode':'bounded','max_chars_per_response':3000,
            'max_chars_total':4000}}
        rights.record_approval(s,'synthetic');db.commit()
    page=client.get(url);assert page.status_code==200,page.text
    assert page.json()['source_attributions'][0]['notice']=='Synthetic author notice'
    with client.app.state.db.Session() as db:
        first=db.get(OutputBudget,'citation-fixture').released_chars
    assert client.get(url).status_code==200
    with client.app.state.db.Session() as db:assert db.get(OutputBudget,'citation-fixture').released_chars==first
    body=payload(page.json()['items'][0]);response=client.post(url+'/resolve',json=body)
    assert response.status_code==200,response.text
    # A new page coordinate cannot bypass the same work's cumulative ledger.
    statuses=[client.get(url,params={'start':i}).status_code for i in range(1,10)]
    assert 403 in statuses


def test_real_intake_fixture_retains_exact_locator_without_agent_approval(client):
    from test_parser_review import prepared,record
    eid,sid,decision,_=prepared(client)
    assert record(client,eid,decision).status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);s.reviewed=True;rights.record_approval(s,'synthetic');db.commit()
        locator=s.policy['intake_locator']
    url='/api/v1/sources/'+sid+'/passages'
    response=client.get(url);assert response.status_code==200,response.text
    item=response.json()['items'][0]
    assert item['source_locator']==locator
    resolved=client.post(url+'/resolve',json=payload(item))
    assert resolved.status_code==200,resolved.text
    assert not resolved.json()['agent_admission_granted']
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);s.policy={**s.policy,'content_sha256':'0'*64};db.commit()
    assert client.get(url).status_code==409


def test_provenance_change_during_release_rolls_back(client,monkeypatch):
    from app.services import citation_lookup
    url=fixture(client);body=payload(client.get(url).json()['items'][0])
    original=citation_lookup.output_rights.release
    def changed(db,sources,response):
        original(db,sources,response)
        sources[0].policy={**sources[0].policy,'intake_locator':'Changed during release'}
        db.flush()
    monkeypatch.setattr(citation_lookup.output_rights,'release',changed)
    result=client.post(url+'/resolve',json=body)
    assert result.status_code==409,result.text
    with client.app.state.db.Session() as db:
        assert db.get(Source,'exact-fixture').policy['intake_locator']=='Synthetic page 2, paragraph 3'
