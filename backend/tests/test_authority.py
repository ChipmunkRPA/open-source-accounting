"""Synthetic relationship/reviewer fixtures only; no professional accounting approval."""
import pytest
from sqlalchemy import select,func
from app.models import Source,AuthorityRelationship,AuthorityReview,User,now
from app.services import citation_lookup,rights
from test_source_search import source
from test_source_intake import ADMIN

EDITOR={'X-Dev-User':'editor'}


def endpoint(s):
    item=citation_lookup.descriptor(s,0,len(s.text))
    return {k:item[k] for k in ('source_id','revision','locator','character_start','character_end','passage_text_sha256')}


def proposal(client,relation='cites',actor=ADMIN):
    with client.app.state.db.Session() as db:
        for sid in ('edge-source','edge-target'):
            if not db.get(Source,sid):source(db,sid)
        db.commit()
        body={'source':endpoint(db.get(Source,'edge-source')),'target':endpoint(db.get(Source,'edge-target')),
            'relation':relation,'scope':'Synthetic relationship limited to the exact two retained passages.',
            'evidence_ref':'ev_synthetic_authority','evidence_sha256':'a'*64}
    response=client.post('/api/v1/editorial/relationships',headers=actor,json=body)
    assert response.status_code==201,response.text
    return response.json(),body


def decision(edge,**changes):
    return {'expected_revision':edge['revision'],'expected_sequence':edge['sequence'],'decision':'approved',
        'review_note':'Synthetic independent relationship review; not actual professional approval.',
        'evidence_ref':'ev_synthetic_review','evidence_sha256':'b'*64,'expires_at':now()+3600,
        'confirm_actual_review_performed':True,**changes}


def review(client,edge,**changes):
    return client.post('/api/v1/editorial/relationships/'+edge['id']+'/review',headers=EDITOR,json=decision(edge,**changes))


def links(client,sid='edge-source',**params):
    return client.get('/api/v1/sources/'+sid+'/relationships',params=params)


@pytest.mark.parametrize('relation',['cites','amends','supersedes','defines','illustrates','compares'])
def test_direction_exact_bindings_review_and_no_automatic_admission(client,relation):
    edge,body=proposal(client,relation)
    assert not edge['current'] and links(client).json()['items']==[]
    duplicate=client.post('/api/v1/editorial/relationships',headers=ADMIN,json=body).json()
    assert duplicate['id']==edge['id']
    approved=review(client,edge);assert approved.status_code==200,approved.text
    assert approved.json()['current']
    outgoing=links(client).json();incoming=links(client,'edge-target').json()
    assert outgoing['items'][0]['relation']==relation
    assert outgoing['items'][0]['source']==body['source'] and outgoing['items'][0]['target']==body['target']
    assert outgoing['items'][0]['direction']=='outgoing' and incoming['items'][0]['direction']=='incoming'
    assert not outgoing['agent_admission_granted'] and not outgoing['claim_support_verified']
    assert 'review_note' not in str(outgoing) and 'ev_synthetic' not in str(outgoing)
    packet=client.get('/api/v1/editorial/relationships/'+edge['id'],headers=EDITOR).json()
    assert packet['reviews'][0]['payload']['reviewer_id']=='editor'


def test_auth_separation_and_review_sequence(client):
    edge,body=proposal(client,actor=EDITOR)
    assert review(client,edge).status_code==403
    assert client.post('/api/v1/editorial/relationships',json=body).status_code==403
    assert client.get('/api/v1/editorial/relationships').status_code==403
    assert client.post('/api/v1/editorial/relationships/'+edge['id']+'/review',headers=ADMIN,json=decision(edge)).status_code==403
    # A separate administrator proposal can be independently reviewed by the test editor.
    edge,_=proposal(client)
    approved=review(client,edge).json()
    assert review(client,edge).status_code==409
    revoked=review(client,approved,decision='revoked');assert revoked.status_code==200,revoked.text
    assert links(client).json()['items']==[]
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(AuthorityReview))==2


@pytest.mark.parametrize('change',['text','locator','scope','rights','disabled','expired_review','reviewer_deleted','proposal_tamper','review_tamper'])
def test_changed_or_unauthorized_relationship_is_withheld(client,change):
    edge,_=proposal(client);assert review(client,edge).status_code==200
    with client.app.state.db.Session() as db:
        row=db.get(AuthorityRelationship,edge['id']);s=db.get(Source,'edge-target')
        if change=='text':s.text='Changed source';rights.record_approval(s,'synthetic')
        elif change=='locator':s.policy={**s.policy,'intake_locator':'Changed locator'}
        elif change=='scope':s.policy={**s.policy,'scope':{'workspace_id':['private']}};rights.record_approval(s,'synthetic')
        elif change=='rights':s.policy={**s.policy,'display_full':False};rights.record_approval(s,'synthetic')
        elif change=='disabled':s.enabled=False
        elif change=='proposal_tamper':row.payload={**row.payload,'scope':'Forged scope'}
        elif change=='reviewer_deleted':db.delete(db.get(User,'editor'))
        else:
            record=db.get(AuthorityReview,row.current_review_id)
            record.payload={**record.payload,'expires_at':1} if change=='expired_review' else {**record.payload,'decision':'rejected'}
            if change=='expired_review':
                from app.sec_core.core import digest,canonical
                record.payload_sha256=digest(canonical(record.payload))
        db.commit()
    assert links(client).json()['items']==[]


def test_revocation_remains_possible_after_body_rights_expire(client):
    edge,_=proposal(client);approved=review(client,edge).json()
    with client.app.state.db.Session() as db:
        s=db.get(Source,'edge-target');s.policy={**s.policy,'display_full':False};rights.record_approval(s,'synthetic');db.commit()
    assert review(client,approved,decision='revoked').status_code==200
    assert client.get('/api/v1/editorial/relationships/'+edge['id'],headers=EDITOR).status_code==409


def test_bad_passages_expiry_and_self_links_are_not_approved(client):
    edge,body=proposal(client)
    body['source']['locator']='Forged'
    assert client.post('/api/v1/editorial/relationships',headers=ADMIN,json=body).status_code==409
    body['source']=body['target']
    assert client.post('/api/v1/editorial/relationships',headers=ADMIN,json=body).status_code==422
    assert review(client,edge,expires_at=1).status_code==422
    assert review(client,edge,expected_sequence=True).status_code==422
    with client.app.state.db.Session() as db:
        s=db.get(Source,'edge-target');s.text='Changed';rights.record_approval(s,'synthetic');db.commit()
    assert review(client,edge).status_code==409


def test_pagination_explicitly_advances_over_unreviewed_edges(client):
    for relation in ('cites','amends','defines'):proposal(client,relation)
    first=links(client,limit=1).json()
    assert first['items']==[] and first['observed']==1 and first['next_after']
    second=links(client,limit=1,after=first['next_after']).json()
    third=links(client,limit=1,after=second['next_after']).json()
    assert third['next_after'] is None and third['observed']==1


def test_source_deletion_cascades_relationships_and_review_notes(client):
    edge,_=proposal(client);assert review(client,edge).status_code==200
    with client.app.state.db.Session() as db:
        db.delete(db.get(Source,'edge-target'));db.commit()
        assert db.get(AuthorityRelationship,edge['id']) is None
        assert db.scalar(select(func.count()).select_from(AuthorityReview))==0


def test_relationship_output_retains_shared_limits_and_notices(client):
    from app.models import OutputBudget
    with client.app.state.db.Session() as db:
        for sid in ('edge-source','edge-target'):
            s=source(db,sid)
            s.policy={**s.policy,'attribution':'Synthetic relation notice','output_control':{
                'group_id':'authority-fixture','mode':'bounded','max_chars_per_response':2500,'max_chars_total':2500}}
            rights.record_approval(s,'synthetic')
        db.commit()
    edge,_=proposal(client);assert review(client,edge).status_code==200
    first=links(client);assert first.status_code==200,first.text
    assert first.json()['source_attributions']
    with client.app.state.db.Session() as db:first_size=db.get(OutputBudget,'authority-fixture').released_chars
    assert links(client).status_code==200
    with client.app.state.db.Session() as db:assert db.get(OutputBudget,'authority-fixture').released_chars==first_size
    # Simulate already-recorded prior releases leaving less than one new response.
    with client.app.state.db.Session() as db:
        budget=db.get(OutputBudget,'authority-fixture');budget.released_chars=2400;db.commit()
    assert links(client,'edge-target').status_code==403


def test_release_time_review_change_is_denied_and_rolled_back(client,monkeypatch):
    from app.services import authority
    from app.authority_schemas import RelationshipDecision
    edge,_=proposal(client);approved=review(client,edge).json()
    original=authority.output_rights.release
    def changed(db,sources,result):
        original(db,sources,result)
        authority.decide(db,edge['id'],RelationshipDecision.model_validate(decision(approved,decision='revoked')),'editor')
    monkeypatch.setattr(authority.output_rights,'release',changed)
    assert links(client).status_code==409
    with client.app.state.db.Session() as db:
        assert db.get(AuthorityRelationship,edge['id']).sequence==1


def test_malformed_rehashed_proposal_is_withheld(client):
    from app.sec_core.core import digest,canonical
    edge,_=proposal(client);assert review(client,edge).status_code==200
    with client.app.state.db.Session() as db:
        row=db.get(AuthorityRelationship,edge['id']);row.payload={**row.payload,'source':'invalid'}
        row.revision=digest(canonical(row.payload));db.commit()
    assert links(client).json()['items']==[]
