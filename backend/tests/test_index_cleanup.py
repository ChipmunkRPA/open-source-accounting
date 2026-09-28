"""Synthetic retained/removed index observations; no real corpus or backup erasure."""
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import select,func
from app.models import Source,SourceSearchIndex,SearchIndexSweep,Audit
from app.services import source_search,index_cleanup,rights
from test_source_search import source
from test_source_intake import ADMIN


def indexed(db,sid):
    row=source(db,sid);source_search.rebuild(db,row,source_search.revision(row),'admin');return row


def test_api_resume_exact_counts_receipts_and_idempotency(client):
    with client.app.state.db.Session() as db:
        for i in range(105):
            row=indexed(db,f'cleanup-{i:03}')
            if i%2==0:row.enabled=False
        db.commit()
    url='/api/v1/admin/search-index/sweeps'
    headers={**ADMIN,'Idempotency-Key':str(uuid4())}
    assert client.post(url,headers={'Idempotency-Key':headers['Idempotency-Key']}).status_code==403
    start=client.post(url,headers=headers);assert start.status_code==200,start.text
    state=start.json();assert state['initial_stored']==105 and state['sequence']==0
    assert client.post(url,headers=headers).json()['id']==state['id']
    path=url+'/'+state['id']
    state=client.post(path+'/advance',headers=ADMIN,json={'expected_sequence':0}).json()
    assert (state['scanned'],state['retained'],state['removed'])==(100,50,50)
    assert state['state']=='running'
    assert client.post(path+'/advance',headers=ADMIN,json={'expected_sequence':0}).status_code==409
    state=client.post(path+'/advance',headers=ADMIN,json={'expected_sequence':1}).json()
    assert (state['scanned'],state['retained'],state['removed'],state['vanished'])==(105,52,53,0)
    assert state['state']=='completed' and not state['atomic_inventory'] and not state['backup_erasure_verified']
    assert client.post(path+'/advance',headers=ADMIN,json={'expected_sequence':2}).json()==state
    receipt=client.get(path+'/receipts',headers=ADMIN).json()
    assert len(receipt['items'])==2
    assert len(receipt['items'][0]['receipt']['observations'])==100
    assert 'quasar amortization exception' not in str(receipt)
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceSearchIndex))==52
        assert db.scalar(select(func.count()).select_from(Source).where(Source.id.like('cleanup-%')))==105
        assert db.scalar(select(func.count()).select_from(SearchIndexSweep))==1


def test_rollback_preserves_rows_cursor_counters_and_receipt(client,monkeypatch):
    with client.app.state.db.Session() as db:
        for i in range(3):
            row=indexed(db,f'rollback-{i}');row.enabled=False
        sweep=index_cleanup.start(db,'admin',str(uuid4()));sid=sweep.id;db.commit()
        original=source_search.current;calls=[]
        def explode(source,entry):
            calls.append(source.id)
            if len(calls)==2:raise RuntimeError('synthetic crash')
            return original(source,entry)
        with monkeypatch.context() as patch:
            patch.setattr(source_search,'current',explode)
            with pytest.raises(RuntimeError):index_cleanup.advance(db,sid,0,'admin')
            db.rollback()
        state=db.get(SearchIndexSweep,sid)
        assert state.cursor=='' and state.sequence==0 and state.removed==0
        assert db.scalar(select(func.count()).select_from(SourceSearchIndex))==3
        assert not list(db.scalars(select(Audit).where(Audit.action=='source.index_cleanup_batch')))
        index_cleanup.advance(db,sid,0,'admin');db.commit()
        assert state.removed==3 and state.state=='completed'


@pytest.mark.parametrize('change',['expired','scope','parent_revoked','text','index_version'])
def test_cleanup_removes_stale_and_transitive_unauthorized_entries(client,change):
    with client.app.state.db.Session() as db:
        parent=source(db,'parent-fixture');child=source(db,'child-fixture')
        child.policy={**child.policy,'intake_parent_id':parent.id,'intake_parent_policy_version':parent.policy_version}
        rights.record_approval(child,'synthetic')
        entry=source_search.rebuild(db,child,source_search.revision(child),'admin')
        if change=='expired':child.policy={**child.policy,'expires_at':1}
        elif change=='scope':child.policy={**child.policy,'scope':{'workspace_id':['private']}}
        elif change=='parent_revoked':parent.enabled=False
        elif change=='text':child.text='changed'
        elif change=='index_version':entry.index_version='obsolete'
        sweep=index_cleanup.start(db,'admin',str(uuid4()));db.commit()
        index_cleanup.advance(db,sweep.id,0,'admin');db.commit()
        assert sweep.removed==1 and db.get(SourceSearchIndex,child.id) is None
        assert db.get(Source,child.id) is not None


def test_entries_behind_cursor_require_new_sweep(client):
    with client.app.state.db.Session() as db:
        indexed(db,'b');indexed(db,'z')
        sweep=index_cleanup.start(db,'admin',str(uuid4()));db.commit()
        index_cleanup.advance(db,sweep.id,0,'admin',batch_size=1);db.commit()
        late=indexed(db,'a');late.enabled=False;db.commit()
        index_cleanup.advance(db,sweep.id,1,'admin');db.commit()
        assert sweep.scanned==2 and sweep.retained==2 and sweep.state=='completed'
        assert db.get(SourceSearchIndex,'a') is not None
        second=index_cleanup.start(db,'admin',str(uuid4()));db.commit()
        index_cleanup.advance(db,second.id,0,'admin');db.commit()
        assert second.scanned==3 and second.removed==1


def test_receipt_corruption_denies_history(client):
    with client.app.state.db.Session() as db:
        indexed(db,'receipt-fixture');sweep=index_cleanup.start(db,'admin',str(uuid4()));db.commit()
        index_cleanup.advance(db,sweep.id,0,'admin');db.commit()
        receipt=db.scalar(select(Audit).where(Audit.action=='source.index_cleanup_batch'))
        receipt.detail={**receipt.detail,'receipt_sha256':'0'*64};db.commit();sid=sweep.id
    result=client.get('/api/v1/admin/search-index/sweeps/'+sid+'/receipts',headers=ADMIN)
    assert result.status_code==409 and 'CLEANUP_RECEIPT_INTEGRITY' in result.text


def test_empty_sweep_and_invalid_sequence(client):
    with client.app.state.db.Session() as db:
        sweep=index_cleanup.start(db,'admin',str(uuid4()));db.commit()
        assert sweep.state=='completed' and sweep.initial_stored==0
        assert index_cleanup.advance(db,sweep.id,0,'admin').sequence==0
        with pytest.raises(HTTPException):index_cleanup.advance(db,sweep.id,1,'admin')



def test_version_change_preserves_old_receipt_scope_and_request_identity(client,monkeypatch):
    with client.app.state.db.Session() as db:
        indexed(db,'version-fixture');key=str(uuid4())
        sweep=index_cleanup.start(db,'admin',key);db.commit();old_id=sweep.id
        monkeypatch.setattr(index_cleanup,'VERSION','synthetic-next-version')
        assert index_cleanup.start(db,'admin',key).id==old_id
        assert index_cleanup.status(sweep)['cleanup_version']=='source-index-cleanup-1'
        with pytest.raises(HTTPException) as exc:index_cleanup.advance(db,sweep.id,0,'admin')
        assert exc.value.detail['code']=='CLEANUP_VERSION_CHANGED'
        assert db.get(SourceSearchIndex,'version-fixture') is not None


def test_saved_sweep_listing_is_admin_only_and_keyset_paginated(client):
    with client.app.state.db.Session() as db:
        for i in range(23):
            db.add(SearchIndexSweep(id=f'00000000-0000-0000-0000-{i:012}',cleanup_version=index_cleanup.VERSION,
                request_sha256=f'{i:064}',actor_id='admin',started_at=100,state='completed'))
        db.commit()
    url='/api/v1/admin/search-index/sweeps'
    assert client.get(url).status_code==403
    first=client.get(url,headers=ADMIN).json()
    assert len(first['items'])==20 and first['next_before']==first['items'][-1]['id']
    second=client.get(url+'?before='+first['next_before'],headers=ADMIN).json()
    assert len(second['items'])==3 and second['next_before'] is None
    ids=[r['id'] for r in first['items']+second['items']]
    assert len(set(ids))==23 and ids==sorted(ids,reverse=True)
    assert client.get(url+'?before=missing',headers=ADMIN).status_code==404
    assert client.get(url+'?before='+'x'*37,headers=ADMIN).status_code==422


def test_index_inventory_does_not_invent_current_or_approved_coverage(client):
    with client.app.state.db.Session() as db:
        row=indexed(db,'stale-inventory');row.enabled=False;db.commit()
    url='/api/v1/admin/search-index/inventory'
    assert client.get(url).status_code==403
    result=client.get(url,headers=ADMIN).json()
    assert result['stored_entries']==1 and result['current_entries'] is None and result['approval_granted'] is False
