"""Bounded reviewer worklist; metadata listing does not load raw source bytes."""
import pytest
from app.models import Source, SourceExtraction
from app.services import rights
from app.services.storage import Storage
from test_parser_review import prepared, record, EDITOR


def test_worklist_is_metadata_only_and_role_gated(client, monkeypatch):
    eid, sid, body, _ = prepared(client)
    body['review_note']='PRIVATE_SYNTHETIC_PARSER_FINDING must not appear in the worklist.'
    assert record(client,eid,body).status_code==200
    monkeypatch.setattr(Storage,'get',lambda *_:pytest.fail('Listing must not read artifacts'))
    result=client.get('/api/v1/editorial/extractions',headers=EDITOR)
    assert result.status_code==200
    row=result.json()['items'][0]
    assert row['id']==eid and row['last_decision']=='approved' and row['review_sequence']==1
    assert row['packet_permitted']
    assert 'raw_base64' not in result.text and 'PRIVATE_SYNTHETIC_PARSER_FINDING' not in result.text
    assert 'Synthetic original source paragraph' not in result.text
    assert client.get('/api/v1/editorial/extractions').status_code==403


def test_worklist_paginates_without_omitting_same_timestamp(client):
    eid, sid, body, _=prepared(client)
    with client.app.state.db.Session() as db:
        first=db.get(SourceExtraction,eid)
        other=SourceExtraction(artifact_id=first.artifact_id,parser_version='synthetic-v2',
            normalized_sha256=first.normalized_sha256,object_key=first.object_key,
            passage_count=first.passage_count,parsed_at=first.parsed_at)
        db.add(other);db.commit();ids={eid,other.id}
    first=client.get('/api/v1/editorial/extractions?limit=1',headers=EDITOR).json()
    second=client.get('/api/v1/editorial/extractions?limit=1&offset=1',headers=EDITOR).json()
    assert first['next_offset']==1 and second['next_offset'] is None
    assert {first['items'][0]['id'],second['items'][0]['id']}==ids


def test_worklist_rechecks_packet_permission(client):
    eid,sid,body,_=prepared(client)
    with client.app.state.db.Session() as db:
        parent=db.get(Source,db.get(Source,sid).policy['intake_parent_id'])
        parent.policy={**parent.policy,'export':False};rights.record_approval(parent,'approver');db.commit()
    assert not client.get('/api/v1/editorial/extractions',headers=EDITOR).json()['items'][0]['packet_permitted']


@pytest.mark.parametrize('query',['offset=-1','limit=0','limit=101'])
def test_worklist_bounds(client,query):
    assert client.get('/api/v1/editorial/extractions?'+query,headers=EDITOR).status_code==422
