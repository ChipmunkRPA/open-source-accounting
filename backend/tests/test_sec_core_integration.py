from conftest import rights_approval
from pathlib import Path
from types import SimpleNamespace
import hashlib
import pytest
from app.sec_core.core import CorePack, CoreError
from app.sec_core.integration import stage, evidence_for
from app.models import Source
from app.services.retrieval import search
from test_applicability import applicability_payload, CONTEXT

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
        assert evidence_for(db.get(Source,sid),run) is None
        payload=applicability_payload(db.get(Source,sid))
    assert client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',headers={'X-Dev-User':'editor'},json=payload).status_code==200
    run.context=CONTEXT.copy()
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
        payload=applicability_payload(s,issued_at='2022-12-13',publicly_available_at='2022-12-13',effective_from='2022-12-13',effective_to='2026-09-27')
    assert client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload).status_code==403
    r=client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload,headers={'X-Dev-User':'editor'})
    assert r.status_code==200,r.text
    assert client.post(f'/api/v1/editorial/sec-core/{sid}/applicability',json=payload,headers={'X-Dev-User':'editor'}).status_code==409
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid);run=SimpleNamespace(context={**CONTEXT,'knowledge_date':'2026-01-01'})
        assert evidence_for(s,run)
        run.context['knowledge_date']='2022-12-12';assert evidence_for(s,run) is None
        s.enabled=False;run.context={};assert evidence_for(s,run) is None


def test_sec_legacy_flags_never_grant_applicability(client):
    sid=staged(client);approve(client,sid)
    from app.services import rights
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        s.policy={**s.policy,'sec_core':{**s.policy['sec_core'],'applicability_review_status':'approved',
            'effective_from':'2000-01-01','public_available_at':'2000-01-01'}}
        db.commit()
        assert not rights.allowed(s,'model_input')
        assert evidence_for(s,SimpleNamespace(context=CONTEXT)) is None


def test_sec_ledger_expiry_revocation_and_saved_exports(client,monkeypatch):
    from app.models import Run,Evidence,ApplicabilityReview
    from app.services import applicability,rights
    sid=staged(client);approve(client,sid)
    with client.app.state.db.Session() as db:payload=applicability_payload(db.get(Source,sid))
    url=f'/api/v1/editorial/sec-core/{sid}/applicability'
    result=client.post(url,headers={'X-Dev-User':'editor'},json=payload)
    assert result.status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        assert 'applicability_review_note' not in s.policy['sec_core']
        run=Run(workspace_id='demo-workspace',user_id='demo',workflow='deep_research',question='Synthetic',context=CONTEXT)
        db.add(run);db.flush()
        ev=Evidence(run_id=run.id,source_id=sid,title=s.title,text=s.text,locator=s.policy['sec_core']['locator'],access='primary_text_reviewed',source_kind=s.kind,policy_version=s.policy_version)
        db.add(ev);db.flush()
        assert rights.evidence_allowed(db,ev,'export')
        with monkeypatch.context() as patch:
            patch.setattr(applicability,'now',lambda:payload['expires_at'])
            assert evidence_for(s,run) is None
            assert not rights.evidence_allowed(db,ev,'export')
        revoke=applicability_payload(s,decision='revoked')
    assert client.post(url,headers={'X-Dev-User':'editor'},json=revoke).status_code==200
    with client.app.state.db.Session() as db:
        s=db.get(Source,sid)
        assert not applicability.current(s)
        assert db.get(ApplicabilityReview,result.json()['record_id']).payload['decision']=='approved'
    history=client.get(f'/api/v1/editorial/sources/{sid}/applicability',headers={'X-Dev-User':'editor'})
    assert history.status_code==200 and len(history.json()['items'])==2 and not history.json()['current']


@pytest.mark.parametrize('change',[{'period_start':'1999-01-01'},{'entity_type':'private'},{'period_end':None}])
def test_sec_scope_and_period_start_are_enforced(client,change):
    sid=staged(client);approve(client,sid)
    with client.app.state.db.Session() as db:payload=applicability_payload(db.get(Source,sid))
    assert client.post(f'/api/v1/editorial/sources/{sid}/applicability',headers={'X-Dev-User':'editor'},json=payload).status_code==200
    with client.app.state.db.Session() as db:
        assert evidence_for(db.get(Source,sid),SimpleNamespace(context={**CONTEXT,**change})) is None
