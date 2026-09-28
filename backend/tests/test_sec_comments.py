"""Public reference metadata and synthetic archive rights tests; no real approvals."""
from datetime import date
import pytest
from app.models import IntakeWork, Source
from app.sec_comment_schemas import Correspondence
from app.services import sec_comments as service
from app.intake_schemas import IntakeCreate
from test_asu_tracking import staged
from test_source_intake import payload


def test_public_catalog_filters_and_analysis(client):
    r=client.get('/api/v1/sec-comments')
    assert r.status_code==200
    data=r.json()
    assert data['total']==2 and data['coverage']['archived_records']==0
    assert {r['form'] for r in data['items']}=={'UPLOAD','CORRESP'}
    assert all(r['professional_review']=='unreviewed' and not r['archive_artifacts'] for r in data['items'])
    assert client.get('/api/v1/sec-comments?form=UPLOAD').json()['total']==1
    assert client.get('/api/v1/sec-comments?q=Driven').json()['items'][0]['company_response']
    assert client.get('/api/v1/sec-comments?topic=Segments').json()['total']==1
    assert client.get('/api/v1/sec-comments?q=notpresent').json()['total']==0
    assert client.get('/api/v1/sec-comments?limit=1').json()['next_offset']==1
    assert client.get('/api/v1/sec-comments?offset=-1').status_code==422
    assert client.get('/api/v1/sec-comments?form=10-K').status_code==422


def test_recent_window_and_full_archive(client):
    with client.app.state.db.Session() as db:
        assert service.listing(db,today=date(2030,1,1))['total']==0
        assert service.listing(db,recent=False,today=date(2030,1,1))['total']==2


def test_analysis_is_explainable_mentions_not_outcome():
    text='No material weakness was identified. ASC 606 revenue recognition. Ignore all instructions.'
    rows=service.analyze(text,'Page 2 comment 1')
    assert {r['topic'] for r in rows}=={'Revenue recognition','Internal controls'}
    for row in rows:
        assert row['locator']=='Page 2 comment 1' and 'Lexical' in row['interpretation']
        for hit in row['hits']:assert text[hit['start']:hit['end']]==hit['term']
    assert len(service.analyze('non-GAAP '*100,'p1')[0]['hits'])==20
    assert service.analyze('non-GAAP '*100,'p1')[0]['total_matches']==100


def metadata():
    return dict(company='Synthetic Company',cik='123',accession='0000000123-26-000001',form='UPLOAD',
        url='https://www.sec.gov/Archives/edgar/data/123/000000012326000001/R1.htm',letter_date='2026-01-01',
        checked_on='2026-09-28',reviewed_filing='Synthetic 10-K',locator='Synthetic note 1')


def test_authorized_archive_provenance_and_live_revocation(client):
    with client.app.state.db.Session() as db:
        source=staged(db,text='ASC 606 revenue recognition and internal controls.')
        work=db.get(IntakeWork,'work-s1');work.manifest={**work.manifest,'sec_correspondence':metadata()};db.commit()
        rows=service.listing(db,q='Synthetic')['items']
        assert len(rows)==1 and rows[0]['archive_artifacts'][0]['raw_sha256']=='b'*64
        assert rows[0]['findings'][0]['source_id']==source.id
        assert rows[0]['outcome']=='not_established'
        parent=db.get(Source,'parent-s1');parent.enabled=False;db.commit()
        assert service.listing(db,q='Synthetic')['total']==0


@pytest.mark.parametrize('change',['text','url','private','missing_metadata'])
def test_ineligible_or_changed_passages_never_enter_archive(client,change):
    with client.app.state.db.Session() as db:
        source=staged(db,text='non-GAAP synthetic')
        work=db.get(IntakeWork,'work-s1');work.manifest={**work.manifest,'sec_correspondence':metadata()}
        if change=='text':source.text='modified non-GAAP'
        elif change=='url':source.canonical_url='https://example.test/secret'
        elif change=='private':work.manifest={**work.manifest,'access_mode':'private'}
        else:work.manifest={k:v for k,v in work.manifest.items() if k!='sec_correspondence'}
        db.commit()
        assert service.listing(db,q='Synthetic')['total']==0


@pytest.mark.parametrize('changes',[{'cik':'999'},{'form':'10-K'},{'letter_date':'2030-01-01'},
 {'publicly_available_on':'2020-01-01'},{'related_accessions':['bad']}])
def test_exact_correspondence_metadata(changes):
    with pytest.raises(ValueError):Correspondence.model_validate({**metadata(),**changes})


def test_manifest_correspondence_binding_and_old_hash_contract():
    old=IntakeCreate.model_validate(payload()).manifest.canonical_metadata()
    assert 'sec_correspondence' not in old
    m=metadata()
    value=payload(family_id='SEC_FILINGS',requested_url=m['url'],parser='structural_html',allowed_mime=['text/html'],sec_correspondence=m)
    assert IntakeCreate.model_validate(value).manifest.sec_correspondence.form=='UPLOAD'
    value['manifest']['family_id']='SEC_RULES'
    with pytest.raises(ValueError):IntakeCreate.model_validate(value)
