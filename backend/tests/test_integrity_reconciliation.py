"""Synthetic operator reconciliation; no real token or Cloud access."""
import json
import os
import httpx
import pytest
from app.reconcile_integrity import collect,advance,report,validate,base_url,save_state,state_lock
from test_source_intake import registered,fetch,parse,ADMIN
from app.models import Source


class AdminClient:
    def __init__(self,client):self.client=client
    def get(self,path,**kwargs):return self.client.get(path,headers=ADMIN,**kwargs)
    def post(self,path,**kwargs):return self.client.post(path,headers=ADMIN,**kwargs)


def test_real_api_inventory_resume_and_family_units(client,tmp_path):
    w=registered(client);a=fetch(client,w);parse(client,a)
    w2=registered(client,body=__import__('test_source_intake').payload(work_id='synthetic-second'));fetch(client,w2)
    admin=AdminClient(client);state=collect(admin,'http://localhost:8000')
    assert len(state['inventory']['items'])==2 and len(state['inventory']['families'])==32
    assert client.get('/api/v1/admin/intake/artifacts').status_code==403
    page=client.get('/api/v1/admin/intake/artifacts?limit=1',headers=ADMIN).json()
    assert len(page['items'])==1 and page['next_after']
    assert len(client.get('/api/v1/admin/intake/artifacts',headers=ADMIN,params={'after':page['next_after'],'limit':1}).json()['items'])==1
    path=tmp_path/'state.json';save=lambda value:save_state(path,value)
    first=advance(admin,state,1,save);assert first['remaining']==1
    resumed=json.loads(path.read_text());validate(resumed,'http://localhost:8000')
    second=advance(admin,resumed,1,save);assert second['remaining']==0
    r=report(resumed);family=next(f for f in r['families'] if f['family_id']=='SEC_RULES')
    assert family['verified_raw']==2 and family['inventory_artifacts']==2 and family['observed_extractions_verified']==1
    assert os.stat(path).st_mode & 0o077==0
    assert 'Synthetic original source paragraph' not in path.read_text()
    assert advance(admin,resumed,25,save)['completed_this_run']==0


def test_denial_is_not_verified_or_retried(client):
    w=registered(client);fetch(client,w);admin=AdminClient(client);state=collect(admin,'https://example.test')
    with client.app.state.db.Session() as db:db.get(Source,w['source_id']).enabled=False;db.commit()
    result=advance(admin,state,1,lambda _:None);assert result['remaining']==0
    family=next(f for f in report(state)['families'] if f['family_id']=='SEC_RULES')
    assert family['denied']==1 and family['verified_raw']==0


def test_auth_and_transport_pause_leave_pending(client):
    w=registered(client);fetch(client,w);state=collect(AdminClient(client),'https://example.test')
    for code,body in [(401,{}),(403,{'error':{'code':'RECENT_AUTH_REQUIRED'}}),(429,{}),(503,{})]:
        fake=httpx.Client(base_url='https://example.test',transport=httpx.MockTransport(lambda _:httpx.Response(code,json=body)))
        assert 'paused' in advance(fake,state,1,lambda _:pytest.fail('No result to persist'))
        assert not state['results'];fake.close()
    class Broken:
        def post(self,*args,**kwargs):raise httpx.ConnectError('sensitive provider message')
    assert advance(Broken(),state,1,lambda _:None)['paused']=='transport_error'


def test_stale_raw_precondition_reads_no_bytes(client,monkeypatch):
    from app.services.storage import Storage
    w=registered(client);a=fetch(client,w)
    monkeypatch.setattr(Storage,'get_bounded',lambda *_:pytest.fail('Stale request must not read'))
    r=client.post('/api/v1/admin/intake/artifacts/'+a['id']+'/verify',headers=ADMIN,json={'expected_raw_sha256':'0'*64})
    assert r.status_code==409


def test_membership_and_origin_integrity(client):
    state=collect(AdminClient(client),'https://example.test')
    with pytest.raises(ValueError):validate(state,'https://other.test')
    state['inventory']['families'].append('invented')
    with pytest.raises(ValueError):validate(state,'https://example.test')
    for url in ['http://external.test','https://user:secret@example.test','https://example.test/path','https://example.test?token=x']:
        with pytest.raises(ValueError):base_url(url)


def test_private_state_lock_and_symlink_rejection(tmp_path):
    path=tmp_path/'state.json'
    with state_lock(path):
        with pytest.raises(BlockingIOError):
            with state_lock(path):pass
    target=tmp_path/'target';target.write_text('private');path.symlink_to(target)
    with pytest.raises(ValueError):
        with state_lock(path):pass


def test_duplicate_cursor_and_inventory_bound(client,monkeypatch):
    import app.reconcile_integrity as module
    w=registered(client);fetch(client,w)
    monkeypatch.setattr(module,'MAX_ARTIFACTS',0)
    with pytest.raises(ValueError):collect(AdminClient(client),'https://example.test')


def test_cli_plan_run_report_and_result_corruption(client,tmp_path,monkeypatch,capsys):
    import app.reconcile_integrity as module
    w=registered(client);fetch(client,w)
    class OperatorSession(AdminClient):
        def __enter__(self):return self
        def __exit__(self,*_):return False
    def connect(**kwargs):
        assert kwargs['follow_redirects'] is False and kwargs['trust_env'] is False
        assert kwargs['headers']['Authorization']=='Bearer synthetic-do-not-log'
        return OperatorSession(client)
    monkeypatch.setattr(module.httpx,'Client',connect)
    monkeypatch.setenv('OSA_ADMIN_ID_TOKEN','synthetic-do-not-log')
    path=tmp_path/'private-state.json'
    for command in ['plan','run','report']:
        monkeypatch.setattr('sys.argv',['reconcile',command,'--base-url','https://example.test','--state',str(path),'--steps','1'])
        module.main()
    output=capsys.readouterr().out
    assert 'synthetic-do-not-log' not in output and 'verified_raw' in output
    state=json.loads(path.read_text());validate(state,'https://example.test')
    aid=next(iter(state['results']));state['results'][aid]['observation']['raw']['status']='invented'
    with pytest.raises(ValueError):validate(state,'https://example.test')


def test_family_partition_marks_other_families_out_of_scope(client):
    w=registered(client);fetch(client,w);admin=AdminClient(client)
    state=collect(admin,'https://example.test','ORIGINAL')
    assert not state['inventory']['items']
    rows=report(state)['families']
    assert [r['family_id'] for r in rows if r['in_scope']]==['ORIGINAL']
    state=collect(admin,'https://example.test','SEC_RULES');assert len(state['inventory']['items'])==1
    with pytest.raises(ValueError):collect(admin,'https://example.test','invented')
