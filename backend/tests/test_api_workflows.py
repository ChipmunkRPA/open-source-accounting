import json
from sqlalchemy import select
from app.models import Run, Evidence, Source, Job, Idempotency, User, Subscription, now
from app.worker import tick
from app.providers.gemini import MockGemini
from app.errors import ProviderError
from conftest import key, activate, create_run, complete_run, upload


def test_health_and_ui(client):
    assert client.get('/api/v1/health').json()['status'] == 'ok'
    assert client.get('/').status_code == 200
    assert 'entry.js' in client.get('/').text
    assert client.get('/assets/main.js').status_code == 200
    assert client.get('/api/v1/does-not-exist').status_code == 404


def test_free_chat_has_no_agent_usage(client):
    chat = client.post('/api/v1/chats', json={}).json()
    answer = client.post(f'/api/v1/chats/{chat["id"]}/messages', json={'message':'Please explain research assumptions.'}, headers=key())
    assert answer.status_code == 200
    assert answer.json()['source_access'] == 'none'
    assert 'DEMO RESPONSE' in answer.json()['body']
    me = client.get('/api/v1/me').json()
    assert me['access']['state'] == 'FREE'
    assert me['usage']['consumed'] == me['usage']['reserved'] == 0


def test_chat_idempotency_and_mismatch(client):
    chat = client.post('/api/v1/chats', json={}).json()
    path=f'/api/v1/chats/{chat["id"]}/messages'
    k=key();body={'message':'An example question.'}
    first=client.post(path,json=body,headers=k)
    second=client.post(path,json=body,headers=k)
    assert first.json()==second.json()
    assert len(client.get('/api/v1/chats/'+chat['id']).json()['messages'])==2
    assert client.post(path,json={'message':'A different question.'},headers=k).status_code==409


def test_chat_rate_limit_does_not_require_payment(client):
    client.app.state.settings.chat_messages_per_hour=1
    chat=client.post('/api/v1/chats',json={}).json()
    path=f'/api/v1/chats/{chat["id"]}/messages'
    assert client.post(path,json={'message':'First'},headers=key()).status_code==200
    r=client.post(path,json={'message':'Second'},headers=key())
    assert r.status_code==429 and r.json()['error']['code']=='CHAT_RATE_LIMIT'


def test_free_draft_and_paid_start_boundary(client):
    run=create_run(client)
    assert client.post(f'/api/v1/runs/{run["id"]}/scope').json()['no_model_call']
    r=client.post(f'/api/v1/runs/{run["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    assert r.status_code==402
    assert client.get('/api/v1/runs/'+run['id']).json()['state']=='draft'


def test_duplicate_start_reserves_once(client):
    activate(client);run=create_run(client);k=key();payload={'expected_revision':1,'confirm_scope':True}
    path=f'/api/v1/runs/{run["id"]}/start'
    assert client.post(path,json=payload,headers=k).status_code==202
    assert client.post(path,json=payload,headers=k).status_code==202
    me=client.get('/api/v1/me').json()
    assert me['usage']['reserved']==1
    with client.app.state.db.Session() as db:
        assert len(db.scalars(select(Job)).all())==1


def test_successful_research_claims_and_memo(client):
    result=complete_run(client,'memo')
    assert result['result']['provider']=='mock'
    assert result['result']['model_id']=='gemini-3.8-flash'
    assert result['memo_id']
    evidence=client.get(f'/api/v1/runs/{result["id"]}/evidence').json()['items']
    assert evidence and all(e['text'] is None for e in evidence)
    me=client.get('/api/v1/me').json()
    assert me['usage']['consumed']==1 and me['usage']['reserved']==0
    assert len(client.get(f'/api/v1/runs/{result["id"]}/events').json()['items'])>=5


def test_no_cross_workspace_or_chat_leak(client):
    run=create_run(client)
    assert client.get('/api/v1/runs/'+run['id'],headers={'X-Dev-User':'admin'}).status_code==404
    assert client.get('/api/v1/workspaces/reviewer-private/documents').status_code==404
    chat=client.post('/api/v1/chats',json={}).json()
    assert client.get('/api/v1/chats/'+chat['id'],headers={'X-Dev-User':'reviewer'}).status_code==404


def test_cancel_refunds_reserved_task(client):
    activate(client);run=create_run(client)
    client.post(f'/api/v1/runs/{run["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    assert client.post(f'/api/v1/runs/{run["id"]}/cancel').status_code==200
    assert client.get('/api/v1/me').json()['usage']['reserved']==0
    assert not tick(client.app.state.db,client.app.state.settings)


def test_failure_releases_reservation(client,monkeypatch):
    activate(client);run=create_run(client)
    client.post(f'/api/v1/runs/{run["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    def error(*args,**kw):raise ProviderError('MODEL_REQUEST_FAILED')
    monkeypatch.setattr(MockGemini,'structured',error)
    assert tick(client.app.state.db,client.app.state.settings)
    result=client.get('/api/v1/runs/'+run['id']).json()
    assert result['state']=='failed' and result['error_code']=='MODEL_REQUEST_FAILED'
    assert client.get('/api/v1/me').json()['usage']['reserved']==0


def test_expiry_before_worker_blocks_execution(client):
    activate(client);run=create_run(client)
    client.post(f'/api/v1/runs/{run["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    tick(client.app.state.db,client.app.state.settings)
    assert client.get('/api/v1/runs/'+run['id']).json()['state']=='blocked'


def test_source_disable_withholds_existing_artifact(client):
    result=complete_run(client,'memo')
    evidence=client.get(f'/api/v1/runs/{result["id"]}/evidence').json()['items']
    source=next(x for x in evidence if x['source_id'] and x['access']!='reference_only')
    assert client.post('/api/v1/admin/sources/'+source['source_id']+'/disable',headers={'X-Dev-User':'admin'}).status_code==200
    blocked=client.get('/api/v1/runs/'+result['id']).json()
    assert blocked['access_blocked'] and blocked['result'] is None
    assert client.get('/api/v1/memos/'+result['memo_id']+'/export').status_code==409


def test_reference_only_never_exposes_source_body(client):
    detail=client.get('/api/v1/sources/ref-asc606').json()
    assert detail['text'] is None and detail['access']=='reference_only'


def test_followup_preserves_parent_and_needs_new_execution(client):
    original=complete_run(client)
    child=client.post(f'/api/v1/runs/{original["id"]}/follow-ups',json={'question':'Consider a new fact: the implementation is performed by another supplier.'},headers=key()).json()
    assert child['state']=='draft' and child['parent_id']==original['id']
    assert client.get('/api/v1/runs/'+original['id']).json()['result']==original['result']


def test_memo_expiry_edit_review_and_export(client):
    result=complete_run(client,'memo');mid=result['memo_id']
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    memo=client.get('/api/v1/memos/'+mid).json()
    review=client.post(f'/api/v1/memos/{mid}/reviews',json={'expected_revision':memo['revision'],'note':'Reviewed structure only.'})
    assert review.json()['review_state']=='self_reviewed'
    changed=client.put('/api/v1/memos/'+mid,json={'expected_revision':memo['revision'],'title':memo['title'],'body':memo['body']+'\nManual edit.'})
    assert changed.status_code==200 and changed.json()['review_state']=='draft'
    assert client.put('/api/v1/memos/'+mid,json={'expected_revision':1,'title':'Stale','body':'Stale'}).status_code==409
    for fmt,signature in [('md',b'#'),('docx',b'PK'),('pdf',b'%PDF'),('html',b'<!doctype')]:
        response=client.get(f'/api/v1/memos/{mid}/export?format={fmt}')
        assert response.status_code==200 and response.content.startswith(signature)


def test_independent_review_cannot_edit(client):
    result=complete_run(client,'memo');mid=result['memo_id']
    reviewer={'X-Dev-User':'reviewer'}
    r=client.post(f'/api/v1/memos/{mid}/reviews',json={'expected_revision':1,'note':'Independent scope-limited review.'},headers=reviewer)
    assert r.json()['review_state']=='independently_reviewed'
    assert client.put('/api/v1/memos/'+mid,json={'expected_revision':1,'title':'x','body':'x'},headers=reviewer).status_code==403


def test_source_two_person_approval(client):
    body={'title':'New original checklist','publisher':'Test authors','kind':'original_commentary','text':'Original non-authoritative research checklist.',
          'policy':{'basis':'original','commercial_use':True,'store_text':True,'model_input':True,'display_full':True,'quote':True,'export':True,'review_note':'Original material created solely for this automated test.'}}
    row=client.post('/api/v1/admin/sources',json=body,headers={'X-Dev-User':'approver'}).json()
    assert client.get('/api/v1/sources/'+row['id']).status_code==404
    assert client.post('/api/v1/admin/sources/'+row['id']+'/approve',headers={'X-Dev-User':'approver'}).status_code==403
    with client.app.state.db.Session() as db:
        db.get(User,'admin').role='rights_approver';db.commit()
    assert client.post('/api/v1/admin/sources/'+row['id']+'/approve',headers={'X-Dev-User':'admin'}).status_code==200
    assert client.get('/api/v1/sources/'+row['id']).json()['text']==body['text']


def test_memo_critique_from_saved_memo(client):
    result=complete_run(client,'memo')
    critique=complete_run(client,'memo_review',inputs={'memo_id':result['memo_id']})
    assert 'memo_under_review' in critique['result']['deterministic']


def test_concurrency_limit(client):
    activate(client);client.app.state.settings.agent_concurrency=1
    one,two=create_run(client),create_run(client)
    assert client.post(f'/api/v1/runs/{one["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key()).status_code==202
    response=client.post(f'/api/v1/runs/{two["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    assert response.status_code==429 and response.json()['error']['code']=='CONCURRENCY_LIMIT'


def test_new_facts_invalidate_scope(client):
    run=create_run(client)
    updated=client.put(f'/api/v1/runs/{run["id"]}/facts',json={'expected_revision':1,'facts':[{'text':'A new confirmed fact.','status':'confirmed'}],'context':{'framework':'US_GAAP'}})
    assert updated.status_code==200 and updated.json()['revision']==2
    assert client.put(f'/api/v1/runs/{run["id"]}/facts',json={'expected_revision':1,'facts':[],'context':{}}).status_code==409
