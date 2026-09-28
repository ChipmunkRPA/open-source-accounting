"""Synthetic SEC metadata only; no real acquisition/rights/accounting review."""
import copy
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.sec_submissions import extract, endpoint
from app.intake_schemas import IntakeCreate
from app.models import SourceArtifact, SourceExtraction, SourceDiscovery
from test_source_intake import ADMIN, payload, registered, fetch, FakeGateway

URL='https://data.sec.gov/submissions/CIK0000000123.json'
HISTORY='https://data.sec.gov/submissions/CIK0000000123-submissions-001.json'
TABLE={'accessionNumber':['0000000456-26-000001','0000000456-26-000002'],
       'filingDate':['2026-05-01','2026-06-01'],'reportDate':['2026-03-31','2026-03-31'],
       'form':['10-Q','10-Q/A'],'primaryDocument':['issuer-20260331.htm','amendment.htm'],
       'acceptanceDateTime':['2026-05-01T16:01:02.000Z','2026-06-01T16:01:02.000Z'],
       'size':[1234,5678],'isXBRL':[1,1],'isInlineXBRL':[1,1]}


def envelope():
    return {'cik':123,'name':'Synthetic issuer','filings':{'recent':copy.deepcopy(TABLE),
        'files':[{'name':'CIK0000000123-submissions-001.json','filingCount':2,
                  'filingFrom':'2024-01-01','filingTo':'2025-01-01'}]}}


def raw(data=None):return json.dumps(envelope() if data is None else data).encode()


def body():
    return payload(family_id='SEC_FILINGS',parser='sec_submissions',requested_url=URL,
                   allowed_mime=['application/json'],coverage_unit='one synthetic submissions snapshot')


class JSONGateway(FakeGateway):
    def get(self,url):
        result=super().get(url);result['mime']='application/json';return result


def test_columns_dates_urls_amendments_and_history_are_separate():
    result=extract(raw(),URL)
    a,b=result['items']
    assert a['cik']=='0000000123' and a['accession'].startswith('0000000456')
    assert a['url']=='https://www.sec.gov/Archives/edgar/data/123/000000045626000001/issuer-20260331.htm'
    assert a['locator']=='/filings/recent/accessionNumber/0' and a['metadata']=={k:v[0] for k,v in TABLE.items()}
    assert a['filed_on']=='2026-05-01' and a['period_end']=='2026-03-31'
    assert b['is_amendment'] and b['amends_accession'] is None
    assert result['older_files'][0]['url']==HISTORY
    assert result['older_files'][0]['status']=='linked_not_acquired'
    assert not result['complete_filing_history'] and result['network_requests']==0
    assert not a['full_text_acquired'] and not a['reuse_authorized'] and not a['agent_eligible']


def test_history_without_reported_identity_is_explicit():
    result=extract(raw(TABLE),HISTORY)
    assert result['issuer_identity_basis']=='endpoint_only'
    assert result['items'][0]['company'] is None
    assert result['items'][0]['locator']=='/accessionNumber/0'


def test_missing_primary_and_period_remain_unknown():
    data=envelope();t=data['filings']['recent'];t['primaryDocument'][0]='';t['reportDate'][0]=''
    a=extract(raw(data),URL)['items'][0]
    assert a['url'] is None and a['period_end'] is None and a['index_url'].endswith('-index.html')


@pytest.mark.parametrize('url',[
 'http://data.sec.gov/submissions/CIK0000000123.json',
 'https://data.sec.gov.evil.test/submissions/CIK0000000123.json',
 'https://data.sec.gov/submissions/CIK123.json',
 'https://data.sec.gov/submissions/CIK0000000123.json?x=1',
 'https://user@data.sec.gov/submissions/CIK0000000123.json',
 'https://data.sec.gov/submissions/CIK0000000123-submissions-001.json#x',
 'https://data.sec.gov/submissions/../secret',
 'https://data.sec.gov/submissions/CIK0000000000.json'])
def test_exact_routes_only(url):
    with pytest.raises(ValueError):endpoint(url)


@pytest.mark.parametrize('field,value',[
 ('accessionNumber','bad'),('filingDate','2026-02-30'),('reportDate','2026'),
 ('primaryDocument','../secret.htm'),('primaryDocument','https://evil.test/a'),
 ('primaryDocument','a%2fsecret.htm'),('acceptanceDateTime','2026-05-01T12:00:00'),
 ('size',True),('isXBRL',3)])
def test_invalid_record_rejects_whole_snapshot(field,value):
    data=envelope();data['filings']['recent'][field][1]=value
    with pytest.raises(ValueError):extract(raw(data),URL)


@pytest.mark.parametrize('change',['length','unknown','duplicate','foreign_cik','foreign_history','missing_inventory'])
def test_schema_identity_and_pagination_integrity(change):
    data=envelope();t=data['filings']['recent']
    if change=='length':t['form'].pop()
    if change=='unknown':t['body']=['unrequested','text']
    if change=='duplicate':t['accessionNumber'][1]=t['accessionNumber'][0]
    if change=='foreign_cik':data['cik']=999
    if change=='foreign_history':data['filings']['files'][0]['name']='CIK0000000999-submissions-001.json'
    if change=='missing_inventory':del data['filings']['files']
    with pytest.raises(ValueError):extract(raw(data),URL)


def test_duplicate_keys_and_nonfinite_input():
    with pytest.raises(ValueError):extract(b'{"cik":123,"cik":999}',URL)
    with pytest.raises(ValueError):extract(b'{"cik":NaN}',URL)


def test_intake_snapshot_discovery_idempotence_and_no_evidence(client):
    work=registered(client,body=body())
    artifact=fetch(client,work,JSONGateway(raw()))
    path='/api/v1/admin/intake/artifacts/'+artifact['id']
    first=client.post(path+'/discover',headers=ADMIN)
    assert first.status_code==200,first.text
    assert first.json()['adapter_version']=='sec-submissions-1'
    assert first.json()['candidate_count']==2
    assert client.post(path+'/discover',headers=ADMIN).json()['id']==first.json()['id']
    snapshot=client.get('/api/v1/admin/intake/discoveries/'+first.json()['id'],headers=ADMIN)
    assert snapshot.json()['discovery']['items'][0]['filed_on']=='2026-05-01'
    assert client.post(path+'/parse',headers=ADMIN).json()['error']['code']=='DISCOVERY_ONLY'
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction))==0
        assert db.scalar(select(func.count()).select_from(SourceDiscovery))==1


def test_malformed_metadata_never_retained(client):
    work=registered(client,body=body())
    with pytest.raises(HTTPException):fetch(client,work,JSONGateway(b'{"body":"not submissions"}'))
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceArtifact))==0


def test_no_acquisition_without_extraction_authorization(client):
    data=body();data['source']['policy']['extract']=False
    work=registered(client,body=data);gateway=JSONGateway(raw())
    with pytest.raises(HTTPException):fetch(client,work,gateway)
    assert gateway.calls==0


@pytest.mark.parametrize('changes',[{'family_id':'FASB'},{'allowed_mime':['text/html']},
 {'redirect_urls':['https://data.sec.gov/submissions/CIK0000000999.json']},{'parser':'text'}])
def test_adapter_route_cannot_be_repurposed(changes):
    data=body();data['manifest'].update(changes)
    with pytest.raises(ValueError):IntakeCreate.model_validate(data)


def test_pilot_registration_files_have_no_grants():
    root=Path(__file__).resolve().parents[2]/'content/asu_pilot'
    paths=list(root.glob('*.json'))
    assert len(paths)==2
    for path in paths:
        item=IntakeCreate.model_validate_json(path.read_text())
        assert item.source.policy.basis=='reference_only'
        assert item.manifest.route=='reference_only'
        assert not item.source.policy.acquire and not item.source.policy.extract


def test_numeric_overflow_and_row_budget_reject():
    data=raw().replace(b'"cik": 123',b'"cik": 123, "flags": 1e999')
    with pytest.raises(ValueError):extract(data,URL)
    data=envelope();data['filings']['recent']={k:[v[0]]*10001 for k,v in TABLE.items()}
    with pytest.raises(ValueError):extract(raw(data),URL)


def test_empty_snapshot_and_history_range():
    data=envelope();data['filings']['recent']={k:[] for k in TABLE};data['filings']['files']=[]
    assert extract(raw(data),URL)['items']==[]
    data=envelope();data['filings']['files'][0]['filingFrom']='2026-01-01'
    with pytest.raises(ValueError):extract(raw(data),URL)


def test_reference_proposal_registration_cannot_acquire(client):
    path=Path(__file__).resolve().parents[2]/'content/asu_pilot/0000023197.json'
    work=registered(client,approve=False,body=json.loads(path.read_text()))
    gateway=JSONGateway(raw())
    with pytest.raises(HTTPException):fetch(client,work,gateway)
    assert gateway.calls==0
