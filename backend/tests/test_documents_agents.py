import io
import pytest
from sqlalchemy import select
from app.models import Document, Memo, Watch, Source, now
from app.agents.catalog import CATALOG
from app.services.watches import check_watches
from app.services.documents import preflight, parse_bytes, safe_filename
from app.services.storage import Storage
from app.config import Settings
from conftest import activate, upload, create_run, complete_run, key


def test_upload_requires_agent(client):
    r=client.post('/api/v1/workspaces/demo-workspace/documents',files={'file':('test.txt',b'Some original text.','text/plain')},data={'authorization_basis':'own_original'})
    assert r.status_code==402


def test_text_upload_and_cross_workspace_guard(client):
    activate(client);doc=upload(client)
    assert doc['status']=='ready' and doc['chunk_count']>0
    assert client.get('/api/v1/documents/'+doc['id']).status_code==200
    assert client.get('/api/v1/documents/'+doc['id'],headers={'X-Dev-User':'admin'}).status_code==404


def test_documents_and_contract_diff(client):
    activate(client)
    old=upload(client,'Original contract. Annual subscription price: 12000.','v1.txt')
    new=upload(client,'Amended contract. Annual subscription price: 15000.','v2.txt')
    result=complete_run(client,'contract_compare',docs=[old['id'],new['id']])
    diff=result['result']['deterministic']['comparison']['diff']
    assert '12000' in diff and '15000' in diff


def test_document_gaap_evidence_and_deletion(client):
    activate(client);doc=upload(client)
    result=complete_run(client,'document_gaap',docs=[doc['id']])
    evidence=client.get(f'/api/v1/runs/{result["id"]}/evidence').json()['items']
    assert any(e['document_id']==doc['id'] for e in evidence)
    mid=client.post(f'/api/v1/runs/{result["id"]}/memo').json()['id']
    assert client.delete('/api/v1/documents/'+doc['id']).status_code==204
    assert client.get('/api/v1/documents/'+doc['id']).status_code==410
    run=client.get('/api/v1/runs/'+result['id']).json()
    assert run['result'] is None and run['error_code']=='DOCUMENT_DELETED'
    with client.app.state.db.Session() as db:
        record=db.get(Document,doc['id'])
        assert record.chunks==[]
        assert 'Content removed' in db.get(Memo,mid).body


def test_missing_document_rejected_before_task_charge(client):
    activate(client);run=create_run(client,'document_gaap')
    r=client.post(f'/api/v1/runs/{run["id"]}/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    assert r.status_code==422
    assert client.get('/api/v1/me').json()['usage']['reserved']==0


def test_block_known_restricted_publisher_upload(client):
    activate(client)
    r=client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file':('restricted.txt',b'Deloitte Accounting Research Tool dart.deloitte.com copyrighted text.','text/plain')},
        data={'authorization_basis':'own_original'})
    assert r.status_code==403
    assert r.json()['error']['code']=='SOURCE_POLICY_BLOCK'


def test_upload_rejects_binary_disguised_text(client):
    activate(client)
    r=client.post('/api/v1/workspaces/demo-workspace/documents',files={'file':('binary.txt',b'\0not text','text/plain')},data={'authorization_basis':'own_original'})
    assert r.status_code==422


def test_pdf_and_docx_parser():
    from reportlab.pdfgen import canvas
    from docx import Document as WordDocument
    p=io.BytesIO();c=canvas.Canvas(p);c.drawString(72,700,'Original fictional contract with a subscription fee.');c.save()
    chunks=parse_bytes(p.getvalue(),'.pdf',10000)
    assert chunks[0]['locator']=='Page 1' and 'subscription' in chunks[0]['text']
    stream=io.BytesIO();d=WordDocument();d.add_paragraph('Fictional agreement between two example companies.');d.save(stream)
    assert 'Fictional' in parse_bytes(stream.getvalue(),'.docx',10000)[0]['text']


@pytest.mark.parametrize('name,expected',[('../../evil.txt','evil.txt'),('C:\\temp\\x.md','x.md'),('abc\x00.txt','abc.txt')])
def test_filename_safety(name,expected):assert safe_filename(name)==expected


def test_storage_path_traversal(tmp_path):
    store=Storage(Settings(data_dir=str(tmp_path),_env_file=None))
    with pytest.raises(ValueError):store.put('../escape',b'x','text/plain')


def test_requires_scanner_when_configured(client):
    activate(client);client.app.state.settings.upload_scanning_required=True
    r=client.post('/api/v1/workspaces/demo-workspace/documents',files={'file':('test.txt',b'Original longer text.','text/plain')},data={'authorization_basis':'own_original'})
    assert r.status_code==503 and r.json()['error']['code']=='SCANNER_UNAVAILABLE'


@pytest.mark.parametrize('task',[row['id'] for row in CATALOG if row['id']!='standards_watch'])
def test_all_workflow_pipelines_with_mock_provider(client,task):
    client.app.state.settings.enable_experimental_agents=True
    activate(client)
    task_row=next(x for x in CATALOG if x['id']==task)
    docs=[upload(client,f'Original contract version {i}. Subscription consideration and implementation terms are under review.',f'example-{i}.txt')['id']
          for i in range(task_row['min_documents'])]
    context={'framework':'BOTH' if task=='framework_compare' else 'US_GAAP'}
    inputs={}
    if task=='revenue_workpaper':inputs={'allocation':{'transaction_price':'120','items':[{'name':'A','ssp':'100'},{'name':'B','ssp':'50'}]}}
    if task=='lease_workpaper':inputs={'lease':{'monthly_payment':'1000','annual_discount_rate':'0.05','months':12,'first_payment_date':'2027-01-31'}}
    result=complete_run(client,task,docs=docs,inputs=inputs,context=context)
    assert result['result']['sections']
    assert result['result']['provider']=='mock'


def test_watch_requires_opt_in_and_pauses_at_expiry(client):
    client.app.state.settings.enable_experimental_agents=True;activate(client)
    missing=client.post('/api/v1/watches',json={'workspace_id':'demo-workspace','topic':'subscription','cadence_days':7,'consent':False})
    assert missing.status_code==422
    watch=client.post('/api/v1/watches',json={'workspace_id':'demo-workspace','topic':'subscription','cadence_days':7,'consent':True}).json()
    with client.app.state.db.Session() as db:
        row=db.get(Watch,watch['id']);row.next_at=0;row.last_source_at=0
        db.get(Source,'sample-research').title='New subscription research content'
        db.commit()
        assert check_watches(db,client.app.state.settings)==1
    assert client.get('/api/v1/notifications').json()['items']
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    with client.app.state.db.Session() as db:
        row=db.get(Watch,watch['id']);row.next_at=0;row.last_source_at=0;db.commit()
        assert check_watches(db,client.app.state.settings)==0
    assert client.delete('/api/v1/watches/'+watch['id']).status_code==204
