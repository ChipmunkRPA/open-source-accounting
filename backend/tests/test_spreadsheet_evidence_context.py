"""Synthetic evidence packets and mock Agent runs; no professional approval."""
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.models import Evidence, Document, Run
from app.services import spreadsheet_context as ctx, rights
from conftest import activate, complete_run
from test_spreadsheet_comments import workbook
from test_spreadsheet_parser import MIME


def test_context_keeps_same_sheet_qualifications_and_reports_limits(monkeypatch):
    chunk={'locator':"'Sheet1'!A2",'text':'1250','spreadsheet':{'sheet':'Sheet1','format':'xlsx','calculated':False}}
    comment={'locator':"'Sheet1'!A2 comment",'text':'Amount is in thousands', 'spreadsheet':{'sheet':'Sheet1','comment':{'cell':'A2'}}}
    other={'locator':"'Other'!A2 comment",'text':'Private other sheet','spreadsheet':{'sheet':'Other','comment':{'cell':'A2'}}}
    doc=SimpleNamespace(chunks=[chunk,comment,other],checksum='a'*64)
    packet=ctx.document_context(doc,chunk)
    assert [r['text'] for r in packet['related']]==['Amount is in thousands']
    assert not packet['context_partial'] and not packet['complete_document_verified']
    monkeypatch.setattr(ctx,'MAX_RELATED',0)
    packet=ctx.document_context(doc,chunk)
    assert packet['context_partial'] and packet['omitted_context_chunks']==1
    assert not packet['related']


def test_metadata_budget_does_not_silently_expand():
    packet=ctx.base({'format':'xlsx','warning':'x'*30000})
    assert packet['context_partial'] and len(str(packet))<1000


def test_source_context_is_persistable_and_explicitly_incomplete():
    source=SimpleNamespace(policy={'intake_spreadsheet':{'format':'xlsx','sheet':'S','calculated':False}})
    packet=ctx.source_context(source)
    ev=Evidence(run_id='synthetic',extraction_context=packet,locator='x'*500,title='Test',access='full',source_kind='rule')
    assert ev.extraction_context['related_source_context']=='not_attached'
    assert ev.extraction_context['context_partial']
    assert ev.locator=='x'*500


def test_actual_mock_agent_persists_context_and_changed_comment_revokes(client):
    activate(client)
    upload=client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file':('original-notes.xlsx',workbook(),MIME)},data={'authorization_basis':'own_original'})
    assert upload.status_code==201,upload.text
    result=complete_run(client,docs=[upload.json()['id']])
    with client.app.state.db.Session() as db:
        run=db.get(Run,result['id'])
        evidence=list(db.scalars(select(Evidence).where(Evidence.run_id==run.id,Evidence.document_id.is_not(None))))
        assert evidence
        target=next(e for e in evidence if e.extraction_context.get('related') and 'row_hidden' in e.extraction_context['literal_extraction'])
        assert any(r['kind']=='comment' for r in target.extraction_context['related'])
        assert rights.evidence_allowed(db,target)
        doc=db.get(Document,target.document_id)
        chunks=[dict(c) for c in doc.chunks]
        for c in chunks:
            if c.get('spreadsheet',{}).get('comment'):
                c['text']='Changed qualification after the run.'
        doc.chunks=chunks;db.commit()
        assert not rights.evidence_allowed(db,target)


@pytest.mark.parametrize('clear',[False,True])
def test_context_snapshot_tampering_is_denied(client,clear):
    activate(client)
    upload=client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file':('original-notes.xlsx',workbook(),MIME)},data={'authorization_basis':'own_original'})
    result=complete_run(client,docs=[upload.json()['id']])
    with client.app.state.db.Session() as db:
        ev=db.scalar(select(Evidence).where(Evidence.run_id==result['id'],Evidence.document_id.is_not(None)))
        ev.extraction_context={} if clear else {**ev.extraction_context,'document_checksum':'forged'};db.commit()
        assert not rights.evidence_allowed(db,ev)


def test_table_and_workbook_declarations_are_attached_with_exact_locators():
    chunk={'locator':"'S'!B5",'text':'2500','spreadsheet':{'sheet':'S','format':'xlsx'}}
    table={'locator':"'S'!A4:B9 table Balance",'text':'Column B: amount in USD thousands',
           'spreadsheet':{'sheet':'S','table':{'range':'A4:B9'}}}
    declaration={'locator':'Workbook declarations','text':'Date system and calculation properties',
                 'spreadsheet':{'defined_names':[],'date_system':'1904'}}
    packet=ctx.document_context(SimpleNamespace(chunks=[chunk,table,declaration],checksum='b'*64),chunk)
    assert [r['locator'] for r in packet['related']]==[table['locator'],declaration['locator']]
    assert not packet['context_partial']


def test_context_byte_budget_is_explicit_and_bounded():
    from app.sec_core.core import canonical
    chunk={'locator':'A1','text':'1','spreadsheet':{'format':'xlsx','sheet':'S'}}
    related=[{'locator':str(i),'text':'界'*5000,'spreadsheet':{'sheet':'S','comment':{}}} for i in range(30)]
    packet=ctx.document_context(SimpleNamespace(chunks=[chunk,*related],checksum='b'*64),chunk)
    assert len(canonical(packet))<=ctx.MAX_CONTEXT_CHARS
    assert packet['context_partial'] and packet['omitted_context_chunks']>0
