"""Original synthetic lexical fixtures; no live corpus approval."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models import Source, SourceSearchIndex, Audit
from app.services import rights, source_search
from test_source_intake import ADMIN


def source(db, sid='search-fixture'):
    row=Source(id=sid,title='Synthetic lexical fixture',publisher='Tests',text='quasar amortization exception 1250',
        reviewed=True,policy={'basis':'original','commercial_use':True,**{op:True for op in rights.OPERATIONS}})
    db.add(row);db.flush();rights.record_approval(row,'synthetic');db.flush()
    return row


def test_index_api_is_explicit_revision_bound_and_idempotent(client):
    with client.app.state.db.Session() as db:
        row=source(db);db.commit();sid=row.id
    url='/api/v1/admin/sources/'+sid+'/search-index'
    assert client.get(url).status_code==403
    state=client.get(url,headers=ADMIN).json()
    assert state['global_index_allowed'] and not state['stored']
    body={'expected_revision':state['expected_revision']}
    assert client.post(url,headers=ADMIN,json={'expected_revision':'a'*64}).status_code==409
    assert client.post(url,headers=ADMIN,json=body).status_code==200
    assert client.post(url,headers=ADMIN,json=body).status_code==200
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceSearchIndex))==1
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action=='source.indexed'))==1
    assert client.get(url,headers=ADMIN).json()['current']
    assert client.delete(url,headers=ADMIN).status_code==200
    assert not client.get(url,headers=ADMIN).json()['stored']


@pytest.mark.parametrize('change',['embed','store_text','reviewed','scope','disabled','body','version'])
def test_index_invalidates_on_operation_or_revision_change(client,change):
    with client.app.state.db.Session() as db:
        row=source(db);entry=source_search.rebuild(db,row,source_search.revision(row),'admin')
        assert source_search.current(row,entry)
        if change in {'embed','store_text'}:row.policy={**row.policy,change:False}
        elif change=='scope':row.policy={**row.policy,'scope':{'workspace_id':['demo-workspace']}}
        elif change=='reviewed':row.reviewed=False
        elif change=='disabled':row.enabled=False
        elif change=='body':row.text='different body'
        elif change=='version':row.policy_version+=1
        assert not source_search.current(row,entry)


def test_unreviewed_and_oversized_text_are_not_indexed(client):
    with client.app.state.db.Session() as db:
        row=source(db);row.reviewed=False
        with pytest.raises(HTTPException) as exc:source_search.rebuild(db,row,source_search.revision(row),'admin')
        assert exc.value.status_code==403
        row.reviewed=True;row.text='x'*100001;rights.record_approval(row,'synthetic')
        with pytest.raises(HTTPException) as exc:source_search.rebuild(db,row,source_search.revision(row),'admin')
        assert exc.value.status_code==422
        assert db.get(SourceSearchIndex,row.id) is None


def test_disable_removes_index(client):
    with client.app.state.db.Session() as db:
        row=source(db);source_search.rebuild(db,row,source_search.revision(row),'admin');db.commit()
    assert client.post('/api/v1/admin/sources/search-fixture/disable',headers=ADMIN).status_code==200
    with client.app.state.db.Session() as db:assert db.get(SourceSearchIndex,'search-fixture') is None


def test_query_is_literal_bounded_and_deterministic():
    assert source_search.query_terms("ASC 606-10 | 'lease' & !lease") == ['606-10','asc','lease']
    with pytest.raises(HTTPException):source_search.query_terms(' '.join('word'+str(i) for i in range(65)))
    with pytest.raises(HTTPException):source_search.query_terms('x'*257)
