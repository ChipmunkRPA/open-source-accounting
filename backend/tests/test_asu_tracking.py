"""Synthetic ingestion bindings; no real license or professional-review attestation."""
import hashlib
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from app.models import Source, SourceArtifact, SourceExtraction, IntakeWork, ASUMention, ASURefresh
from app.services import asu_tracking as asu, rights
from app.asu_schemas import ASU, FilingReference, sec_identity

ADMIN = {'X-Dev-User': 'admin'}


def staged(db, sid='s1', text='We adopted ASU 2025-08.', **changes):
    url='https://www.sec.gov/Archives/edgar/data/123/000000012326000001/R1.htm'
    policy={op: True for op in ('extract','store_text','display_full','redistribute')}
    policy.update(basis='government_work', commercial_use=True)
    parent=Source(id='parent-'+sid,title='Synthetic filing',publisher='Synthetic',canonical_url=url,
                  text=None,policy=policy,reviewed=True)
    db.add(parent);db.flush();rights.record_approval(parent,'synthetic')
    work=IntakeWork(id='work-'+sid,source_id=parent.id,family_id='SEC_FILINGS',work_id=sid,edition='1',
        manifest={'route':'official_http','access_mode':'public_candidate','requested_url':url},manifest_sha256='a'*64)
    db.add(work);db.flush()
    artifact=SourceArtifact(id='art-'+sid,work_id=work.id,raw_sha256='b'*64,object_key='synthetic',byte_count=10,mime='text/html',receipt={})
    db.add(artifact);db.flush()
    extraction=SourceExtraction(id='ext-'+sid,artifact_id=artifact.id,parser_version='synthetic-only',normalized_sha256='c'*64,object_key='synthetic-normalized',passage_count=1)
    db.add(extraction);db.flush()
    p={**policy,'intake_parent_id':parent.id,'intake_parent_policy_version':1,'intake_artifact_id':artifact.id,
       'intake_extraction_id':extraction.id,'intake_extraction_sha256':'c'*64,
       'content_sha256':hashlib.sha256(text.encode()).hexdigest(),'intake_locator':'Synthetic note 1'}
    s=Source(id=sid,title='Synthetic filing passage',publisher='Synthetic',canonical_url=url,text=text,policy=p,reviewed=True)
    for k,v in changes.items():setattr(s,k,v)
    db.add(s);db.flush();rights.record_approval(s,'synthetic');db.commit()
    return s


def test_catalog_reference_counts_and_adoption(client):
    # Public endpoints do not depend on a verified identity or subscription.
    response=client.get('/api/v1/asu-tracking',headers={'X-Dev-User':'unknown'})
    assert response.status_code==200
    data=response.json()
    assert data['coverage']==dict(registered_asus=16,reference_links=12,companies=2,complete_universe=False,retained_reference_artifacts=0,professionally_reviewed=0)
    filings=client.get('/api/v1/asu-tracking/2025-08/filings?status=early_adopted').json()
    assert filings['total']==1
    assert filings['items'][0]['company']=='Home BancShares, Inc.'
    assert filings['items'][0]['raw_sha256'] is None
    assert filings['items'][0]['professional_review']=='unreviewed'
    assert client.get('/api/v1/asu-tracking/2025-08/filings?status=approved').status_code==422
    assert client.get('/api/v1/asu-tracking/2099-99/filings').status_code==404


def test_calendar_window_and_precision(client):
    assert asu.window(date(2028,2,29))==date(2026,2,28)
    with client.app.state.db.Session() as db:
        ids=lambda d:{a['id']:a for a in asu.listing(db,today=d)['items']}
        assert '2024-03' in ids(date(2026,11,4))
        assert '2024-03' not in ids(date(2026,11,5))
        assert ids(date(2026,11,5))['2024-04']['boundary_uncertain']
        assert '2024-04' not in ids(date(2026,12,1))
        assert '2026-01' not in ids(date(2026,4,22))
        assert not asu.listing(db,q='impossible query')['items']
        assert {a['topic'] for a in asu.listing(db,topic='326')['items']}=={'326'}


@pytest.mark.parametrize('text,expected',[
 ('ASU 2025-08 and ASU No. 2025–08', ['2025-08']),
 ('Accounting Standards Update No. 2025-06', ['2025-06']),
 ('2025-08, not labeled', []), ('ASU 2025-081', []),
 ('We have not adopted ASU 2025-08. Early adoption is permitted.', ['2025-08']),
 ('ASU 2024-03 and ASU 2025-01', ['2024-03','2025-01'])])
def test_identifier_detection_never_infers_adoption(text,expected):
    assert asu.identifiers(text)==expected


@pytest.mark.parametrize('url',[
 'http://www.sec.gov/Archives/edgar/data/1/000000000126000001/R1.htm',
 'https://sec.gov.evil.test/Archives/edgar/data/1/000000000126000001/R1.htm',
 'https://www.sec.gov@evil.test/Archives/edgar/data/1/000000000126000001/R1.htm',
 'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/../secret',
 'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/R1.htm?x=1'])
def test_official_links_only(url):
    with pytest.raises(ValueError):sec_identity(url)


def test_metadata_validation():
    row=asu.catalog().asus[0].model_dump()
    with pytest.raises(ValueError):ASU.model_validate({**row,'issued':'2024-11','date_precision':'day'})
    with pytest.raises(ValueError):ASU.model_validate({**row,'official_url':'https://example.com/asu'})
    filing=asu.catalog().filings[0].model_dump()
    with pytest.raises(ValueError):FilingReference.model_validate({**filing,'cik':'999'})


def test_refresh_idempotence_live_revocation_and_deletion(client):
    with client.app.state.db.Session() as db:
        source=staged(db)
        assert asu.refresh(db,timestamp=100)
        assert not asu.refresh(db,timestamp=101)
        result=asu.materials(db,'2025-08',company='123')['items']
        assert len(result)==1 and result[0]['status']=='mentioned'
        assert result[0]['raw_sha256']=='b'*64
        assert asu.refresh(db,force=True,timestamp=102)
        assert db.scalar(select(func.count()).select_from(ASUMention))==1
        parent=db.get(Source,'parent-s1');parent.enabled=False;db.commit()
        assert not asu.materials(db,'2025-08',company='123')['items']
        parent.enabled=True;db.commit()
        source.text='tampered';db.commit()
        assert not asu.materials(db,'2025-08',company='123')['items']
        db.delete(source);db.commit()
        assert db.scalar(select(func.count()).select_from(ASUMention))==0


@pytest.mark.parametrize('mutation', ['private','wrong_family','hold','scoped','unreviewed','wrong_artifact'])
def test_unavailable_sources_never_leak(client,mutation):
    with client.app.state.db.Session() as db:
        source=staged(db)
        if mutation=='private':
            w=db.get(IntakeWork,'work-s1');w.manifest={**w.manifest,'access_mode':'private'}
        if mutation=='wrong_family':db.get(IntakeWork,'work-s1').family_id='FASB'
        if mutation=='hold':source.policy={**source.policy,'integrity_holds':{'raw':'changed'}}
        if mutation=='scoped':
            source.policy={**source.policy,'scope':{'audience':['internal_ingestion']}}
            rights.record_approval(source,'synthetic')
        if mutation=='unreviewed':source.reviewed=False
        if mutation=='wrong_artifact':source.policy={**source.policy,'intake_artifact_id':'missing'}
        db.commit();asu.refresh(db)
        assert not asu.materials(db,'2025-08',company='123')['items']
        assert db.scalar(select(func.count()).select_from(ASUMention))==0


def test_batches_resume_and_revisit_late_sources(client):
    with client.app.state.db.Session() as db:
        staged(db,'zz-original')
        for _ in range(30):
            asu.refresh(db,timestamp=100,batch_size=1)
            state=db.get(ASURefresh,'filings')
            if state.state=='idle':break
        assert state.state=='idle' and state.scanned>1
        scanned=state.scanned
        staged(db,'aa-late')
        assert not asu.refresh(db,timestamp=101,batch_size=1)
        for _ in range(30):
            asu.refresh(db,timestamp=100+asu.CADENCE_SECONDS,batch_size=1)
            if state.state=='idle':break
        assert state.scanned==scanned+2
        assert len(asu.materials(db,'2025-08',company='123')['items'])==2


def test_refresh_is_admin_only(client):
    assert client.post('/api/v1/admin/asu-tracking/refresh').status_code==403
    r=client.post('/api/v1/admin/asu-tracking/refresh',headers=ADMIN)
    assert r.status_code==200 and r.json()['completed_at']
    assert client.get('/api/v1/asu-tracking/2025-08/filings?offset=-1').status_code==422


def test_concurrent_refresh_sqlite(client):
    database=client.app.state.db
    with database.Session() as db:staged(db)
    def run(_):
        with database.Session() as db:return asu.refresh(db,timestamp=100)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(2)))
    assert sorted(results)==[False,True]
    with database.Session() as db:assert db.scalar(select(func.count()).select_from(ASUMention))==1


def test_filtered_pagination(client):
    with client.app.state.db.Session() as db:
        one=asu.materials(db,'2025-01',limit=1)
        two=asu.materials(db,'2025-01',offset=one['next_offset'],limit=1)
        assert one['total']==2 and two['next_offset'] is None
        assert one['items'][0]['cik']!=two['items'][0]['cik']
        assert asu.materials(db,'2025-01',company='home')['total']==1


def test_refresh_crash_rolls_back_cursor_and_mentions(client,monkeypatch):
    with client.app.state.db.Session() as db:
        staged(db)
        original=asu.identifiers
        def broken(_):raise RuntimeError('synthetic crash')
        monkeypatch.setattr(asu,'identifiers',broken)
        with pytest.raises(RuntimeError):asu.refresh(db,timestamp=100)
        db.rollback()
        assert db.scalar(select(func.count()).select_from(ASUMention))==0
        monkeypatch.setattr(asu,'identifiers',original)
        asu.refresh(db,timestamp=101)
        assert asu.materials(db,'2025-08',company='123')['total']==1


def test_refresh_crosses_two_thousand_sources(client):
    with client.app.state.db.Session() as db:
        db.add_all([Source(id=f'synthetic-{n:05}',title='Synthetic',publisher='Synthetic') for n in range(2050)])
        db.commit()
        staged(db,'zz-final')
        batches=0
        while True:
            asu.refresh(db,timestamp=100)
            batches+=1
            if db.get(ASURefresh,'filings').state=='idle':break
            assert batches<20
        assert batches>10
        assert asu.materials(db,'2025-08',company='123')['total']==1
