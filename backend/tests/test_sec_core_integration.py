from conftest import rights_approval
from pathlib import Path
from types import SimpleNamespace
import hashlib
import pytest
from app.sec_core.core import CorePack, CoreError
from app.sec_core.integration import stage, evidence_for
from app.models import Source
from app.services.retrieval import search

PACK=Path(__file__).resolve().parents[2]/'content'/'sec_core'


def staged(client):
    with client.app.state.db.Session() as db:
        result=stage(db,CorePack(PACK),'admin');db.commit()
        sid=next(s for s in result['created']+result['existing'] if db.get(Source,s).policy['sec_core']['passage_id']=='cfi-100-04')
        return sid


def approve(client,sid):
    assert client.post(f'/api/v1/admin/sources/{sid}/approve',json=rights_approval(client,sid),headers={'X-Dev-User':'approver'}).status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        from app.services.editorial import revision
        from app.models import now
        body=dict(expected_policy_version=s.policy_version,expected_review_revision=revision(s),
                  review_scope='Synthetic SEC technical scope', evidence_ref='ev_synthetic_sec', evidence_sha256='a'*64,
                  expires_at=now()+3600, content_sha256=hashlib.sha256(s.text.encode()).hexdigest(),decision='approved',review_note='TEST ONLY: fixture approval; no real professional review.',checked_reference_ids=['sec-cfi-nongaap'],confirm_actual_review_performed=True)
    r=client.post(f'/api/v1/editorial/sources/{sid}/review',headers={'X-Dev-User':'editor'},json=body)
    assert r.status_code==200,r.text


def test_public_reading_no_account(client):
    h={'X-Dev-User':'does-not-exist'}
    r=client.get('/api/v1/sec-core',headers=h);assert r.status_code==200 and r.json()['selected_excerpts']==28
    r=client.get('/api/v1/sec-core/search?q=accelerate%20revenue',headers=h)
    assert r.status_code==200 and any(x['id']=='cfi-100-04' for x in r.json()['items'])
    assert not r.json()['agent_approved']
    assert client.get('/api/v1/sec-core/passages/cfi-100-04',headers=h).json()['locator']=='CFI Non-GAAP 100.04'
    assert client.get('/api/v1/sec-core/passages/missing').status_code==404
    assert client.get('/api/v1/sec-core/search?family=notvalid').status_code==422


def test_stage_idempotent_no_auto_approval(client):
    with client.app.state.db.Session() as db:
        a=stage(db,CorePack(PACK),'admin');db.commit()
        b=stage(db,CorePack(PACK),'admin')
        assert len(a['created'])==28 and not b['created'] and len(b['existing'])==28
        run=SimpleNamespace(context={},workspace_id='demo-workspace',document_ids=[])
        assert all(evidence_for(db.get(Source,s),run) is None for s in a['created'])
        with pytest.raises(CoreError):stage(db,CorePack(PACK),'demo')


def test_independent_gates_and_locator(client):
    sid=staged(client);run=SimpleNamespace(context={},workspace_id='demo-workspace',document_ids=[])
    with client.app.state.db.Session() as db:assert evidence_for(db.get(Source,sid),run) is None
    approve(client,sid)
    with client.app.state.db.Session() as db:
        e=evidence_for(db.get(Source,sid),run)
        assert e['locator']=='CFI Non-GAAP 100.04' and e['access']=='primary_text_reviewed'
        assert e['source_kind']=='staff_guidance'
        found=search(db,run,'accelerate revenue',12)
        assert any(x['source_id']==sid and x['locator']=='CFI Non-GAAP 100.04' for x in found)
        run.context={'knowledge_date':'2026-01-01'}
        assert evidence_for(db.get(Source,sid),run) is None
        run.context={'period_end':'2025-12-31'}
        assert evidence_for(db.get(Source,sid),run) is None


def test_applicability_explicit_review_and_disabled_source(client):
    sid=staged(client);approve(client,sid)
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        payload=dict(expected_policy_version=s.policy_version,content_sha256=hashlib.sha256(s.text.encode()).hexdigest(),effective_from='2022-12-13',effective_to='2026-09-27',public_available_at='2022-12-13',review_note='TEST ONLY: reviewer confirms fixture interval, not a real legal conclusion.',confirm_source_history_checked=True)
    assert client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload).status_code==403
    r=client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload,headers={'X-Dev-User':'editor'})
    assert r.status_code==200,r.text
    assert client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload,headers={'X-Dev-User':'editor'}).status_code==409
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);run=SimpleNamespace(context={'period_end':'2025-12-31','knowledge_date':'2026-01-01'})
        assert evidence_for(s,run)
        run.context['knowledge_date']='2022-12-12';assert evidence_for(s,run) is None
        s.enabled=False;run.context={};assert evidence_for(s,run) is None
