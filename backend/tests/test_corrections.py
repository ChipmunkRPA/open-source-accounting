from app.models import Source,CorrectionEvent,Audit
from app.services import editorial,rights
from conftest import key
ADMIN={'X-Dev-User':'admin'}
URL='/api/v1/admin/corrections'


def payload(client):
    with client.app.state.db.Session() as db:
        s=db.get(Source,'sample-research')
        return {'source_id':s.id,'kind':'correction','expected_policy_version':s.policy_version,
                'expected_review_revision':editorial.revision(s),'note':'Synthetic correction rationale only.'}


def create(client):
    r=client.post(URL,json=payload(client),headers={**ADMIN,**key()});assert r.status_code==201,r.text
    return r.json()


def act(client,row,action):
    return client.post(URL+'/'+row['id']+'/actions',headers=ADMIN,json={'expected_version':row['version'],'action':action,'note':'Synthetic administrative action only.'})


def test_private_roles_and_validation(client):
    assert client.get(URL).status_code==403
    assert client.post(URL,json=payload(client),headers=key()).status_code==403
    row=create(client)
    assert client.get(URL+'/'+row['id']).status_code==403
    assert client.post(URL+'/'+row['id']+'/actions',json={'expected_version':1,'action':'disable','note':'Synthetic rationale'}).status_code==403
    assert client.get(URL,headers=ADMIN,params={'limit':101}).status_code==422
    body=payload(client);body['note']=' '*12
    assert client.post(URL,json=body,headers={**ADMIN,**key()}).status_code==422


def test_idempotent_create_stale_binding_and_private_audit(client):
    body=payload(client);headers={**ADMIN,**key()}
    first=client.post(URL,json=body,headers=headers)
    assert client.post(URL,json=body,headers=headers).json()==first.json()
    body['note']='A different synthetic note.'
    assert client.post(URL,json=body,headers=headers).status_code==409
    body['expected_policy_version']+=1
    assert client.post(URL,json=body,headers={**ADMIN,**key()}).status_code==409
    with client.app.state.db.Session() as db:
        assert db.query(CorrectionEvent).count()==1
        assert 'rationale' not in str([a.detail for a in db.query(Audit).all()])


def test_state_transitions_stale_writes_and_history(client):
    row=create(client)
    assert act(client,row,'resolve').status_code==409
    triaged=act(client,row,'triage').json()
    assert act(client,row,'dismiss').status_code==409
    closed=act(client,triaged,'resolve').json()
    assert closed['status']=='resolved'
    assert act(client,closed,'disable').status_code==409
    reopened=act(client,closed,'reopen').json()
    assert reopened['status']=='open'
    detail=client.get(URL+'/'+row['id'],headers=ADMIN).json()
    assert [e['action'] for e in detail['events']]==['reopen','resolve','triage','open']
    assert client.get(URL,headers=ADMIN,params={'status':'resolved'}).json()['total']==0


def test_disable_invalidates_operations_and_resolution_never_restores(client):
    row=create(client)
    disabled=act(client,row,'disable').json()
    assert not disabled['source_enabled']
    assert disabled['current_policy_version']==row['policy_version']+1
    assert client.get('/api/v1/sources/sample-research').status_code==404
    with client.app.state.db.Session() as db:
        s=db.get(Source,'sample-research')
        assert not rights.allowed(s,'model_input') and not rights.allowed(s,'display_full')
    again=act(client,disabled,'disable').json()
    assert again['current_policy_version']==disabled['current_policy_version']
    resolved=act(client,again,'resolve').json()
    assert not resolved['source_enabled']
    assert client.get(URL+'/'+row['id'],headers=ADMIN).json()['source_changed']


def test_case_impact_is_private_and_disable_reaches_derived_output(client):
    from test_derived_output import link
    with client.app.state.db.Session() as db:
        pid,tid,_,_=link(db);db.commit();target=db.get(Source,tid)
        body={'source_id':target.id,'kind':'takedown','expected_policy_version':target.policy_version,
              'expected_review_revision':editorial.revision(target),'note':'Synthetic inherited issue only.'}
    row=client.post(URL,json=body,headers={**ADMIN,**key()}).json()
    path=URL+'/'+row['id']+'/impact'
    assert client.get(path).status_code==403
    report=client.get(path,headers=ADMIN).json()
    assert pid in report['affected_source_ids']
    assert act(client,row,'disable').status_code==200
    with client.app.state.db.Session() as db:
        assert not rights.allowed(db.get(Source,pid),'display_full')


def test_action_blank_note_rejected_and_detail_paginated(client):
    row=create(client)
    assert client.post(URL+'/'+row['id']+'/actions',headers=ADMIN,json={'expected_version':1,'action':'dismiss','note':' '*12}).status_code==422
    dismissed=act(client,row,'dismiss').json();assert dismissed['status']=='dismissed'
    events=client.get(URL+'/'+row['id'],headers=ADMIN,params={'offset':1,'limit':1}).json()['events']
    assert len(events)==1 and events[0]['action']=='open'
