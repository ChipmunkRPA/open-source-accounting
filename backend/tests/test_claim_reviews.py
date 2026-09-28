"""Mock runs and synthetic human attestations, never actual professional review."""
from copy import deepcopy
import pytest
from sqlalchemy import select, delete
from app.models import Membership, Run, RunClaimReview, Source, Evidence, User, Job, RunEvent, now
from test_authority_evidence import run_graph
from test_authority import EDITOR


def prepared(client):
    _, result = run_graph(client)
    with client.app.state.db.Session() as db:
        db.add(Membership(workspace_id='demo-workspace', user_id='editor', role='reviewer'))
        run = db.get(Run, result['id'])
        e = db.scalar(select(Evidence).where(Evidence.run_id == run.id, Evidence.source_id == 'edge-source'))
        run.result = {**run.result, 'claims': [{'id': 'synthetic-claim', 'text': 'Fictional quasar accounting proposition.',
                      'basis': 'source', 'evidence_ids': [e.id]}]}
        db.commit()
    return result['id'], '/api/v1/runs/'+result['id']+'/claims/synthetic-claim'


def decision(packet, **changes):
    return dict(expected_revision=packet['revision'], expected_sequence=packet['status']['sequence'],
        decision='supported', passages=[{'evidence_id': p['evidence_id'], 'relationship': 'supports',
                    'rationale': 'Synthetic support assessment for this exact fictional passage.'} for p in packet['binding']['passages']],
        review_note='Synthetic claim decision, never actual professional approval.',
        competence_scope='Synthetic test competence statement, not verified credentials.', evidence_ref='ev_synthetic_claim',
        evidence_sha256='a'*64, expires_at=now()+3600, confirm_actual_review_performed=True,
        confirm_competence_and_independence=True, **changes)


def approve(client, path):
    p = client.get(path+'/review-packet', headers=EDITOR)
    assert p.status_code == 200, p.text
    response = client.post(path+'/reviews', headers=EDITOR, json=decision(p.json()))
    assert response.status_code == 201, response.text
    return p.json(), response.json()


def test_exact_private_review_and_retained_free_read(client):
    run_id, path = prepared(client)
    p, status = approve(client, path)
    assert status['current'] and status['decision']=='supported'
    assert not status['source_rights_granted'] and not status['deliverable_approval_granted']
    client.post('/api/v1/dev/subscription', json={'state':'expired'})
    r = client.get(path+'/review-packet')
    assert r.status_code==200 and r.json()['review']['review_note']
    assert r.json()['binding']==p['binding']
    h = client.get(path+'/reviews').json()
    assert len(h['items'])==1 and h['status']['current']
    assert 'Synthetic claim decision' not in str(h)
    with client.app.state.db.Session() as db:
        row=db.scalar(select(RunClaimReview).where(RunClaimReview.run_id==run_id))
        assert 'text' not in row.payload and row.revision==p['revision']
        assert db.get(Run,run_id).state=='completed_with_limitations'


@pytest.mark.parametrize('change',['source','claim','facts','evidence','context','expired','review_hash','reviewer_role','reviewer_deleted'])
def test_changes_invalidate_decision(client,change):
    run_id,path=prepared(client);approve(client,path)
    with client.app.state.db.Session() as db:
        run=db.get(Run,run_id);row=db.scalar(select(RunClaimReview).where(RunClaimReview.run_id==run_id))
        if change=='source':db.get(Source,'edge-source').enabled=False
        elif change=='claim':
            result=deepcopy(run.result);result['claims'][0]['text']+=' Changed.';run.result=result
        elif change=='facts':run.facts=[{'text':'Changed facts','status':'confirmed'}]
        elif change=='context':run.context={**run.context,'entity':'PUBLIC'}
        elif change=='evidence':
            db.scalar(select(Evidence).where(Evidence.run_id==run_id,Evidence.source_id=='edge-source')).locator='Changed locator'
        elif change=='expired':
            from app.sec_core.core import digest,canonical
            body=deepcopy(row.payload);body['decision']['expires_at']=1;row.payload=body;row.payload_sha256=digest(canonical(body))
        elif change=='review_hash':row.payload_sha256='0'*64
        elif change=='reviewer_role':db.get(User,'editor').role='member'
        elif change=='reviewer_deleted':row.reviewer_id=None
        db.commit()
    assert not client.get(path+'/reviews').json()['status']['current']
    p=client.get(path+'/review-packet')
    assert p.status_code!=200 or p.json()['review'] is None


def test_membership_role_independence_and_sequence(client):
    run_id,path=prepared(client)
    p=client.get(path+'/review-packet').json();body=decision(p)
    assert client.post(path+'/reviews',json=body).status_code==403
    assert client.get(path+'/review-packet',headers={'X-Dev-User':'admin'}).status_code==404
    assert client.post(path+'/reviews',headers={'X-Dev-User':'admin'},json=body).status_code==404
    with client.app.state.db.Session() as db:
        db.get(Run,run_id).user_id='editor';db.commit()
    assert client.post(path+'/reviews',headers=EDITOR,json=body).status_code==403
    with client.app.state.db.Session() as db:
        db.get(Run,run_id).user_id='demo';db.commit()
    assert client.post(path+'/reviews',headers=EDITOR,json=body).status_code==201
    assert client.post(path+'/reviews',headers=EDITOR,json=body).status_code==409


def test_revocation_remains_possible_after_source_denial(client):
    run_id,path=prepared(client);p,status=approve(client,path)
    with client.app.state.db.Session() as db:
        db.get(Source,'edge-source').enabled=False;db.commit()
    body=decision(p);body.update(expected_sequence=status['sequence'],decision='revoked',passages=[])
    response=client.post(path+'/reviews',headers=EDITOR,json=body)
    assert response.status_code==201 and not response.json()['current']
    assert response.json()['decision']=='revoked'
    assert len(client.get(path+'/reviews').json()['items'])==2


@pytest.mark.parametrize('change',['revision','missing_binding','wrong_binding','unresolved_support','contradicted_without_passage','attestation'])
def test_review_contract_refuses_incomplete_or_stale_assessments(client,change):
    _,path=prepared(client);p=client.get(path+'/review-packet').json();body=decision(p)
    if change=='revision':body['expected_revision']='0'*64
    elif change=='missing_binding':body['decision']='unresolved';body['passages']=[]
    elif change=='wrong_binding':body['passages'][0]['evidence_id']='other'
    elif change=='unresolved_support':body['passages'][0]['relationship']='unresolved'
    elif change=='contradicted_without_passage':body['decision']='contradicted'
    else:body['confirm_actual_review_performed']=False
    assert client.post(path+'/reviews',headers=EDITOR,json=body).status_code in {409,422}


def test_final_source_recheck_and_delete_cascade(client,monkeypatch):
    from app.services import output_rights
    run_id,path=prepared(client)
    original=output_rights.release
    def revoke(db,sources,payload):
        original(db,sources,payload)
        db.get(Source,'edge-source').enabled=False;db.flush()
    monkeypatch.setattr(output_rights,'release',revoke)
    assert client.get(path+'/review-packet').status_code==409
    monkeypatch.setattr(output_rights,'release',original)
    approve(client,path)
    with client.app.state.db.Session() as db:
        db.execute(delete(Job).where(Job.run_id==run_id))
        db.execute(delete(RunEvent).where(RunEvent.run_id==run_id))
        db.execute(delete(Run).where(Run.id==run_id));db.commit()
        assert db.scalar(select(RunClaimReview).where(RunClaimReview.run_id==run_id)) is None


@pytest.mark.parametrize('kind',['contradicted','unresolved'])
def test_non_supporting_outcomes_are_preserved(client,kind):
    _,path=prepared(client);p=client.get(path+'/review-packet').json();body=decision(p)
    body['decision']=kind
    body['passages'][0]['relationship']='contradicts' if kind=='contradicted' else 'unresolved'
    response=client.post(path+'/reviews',headers=EDITOR,json=body)
    assert response.status_code==201 and response.json()['current']
    assert response.json()['decision']==kind and not response.json()['deliverable_approval_granted']


@pytest.mark.parametrize('change',['viewer','author','membership_removed','binding_tampered'])
def test_scoped_independence_and_saved_binding_integrity(client,change):
    run_id,path=prepared(client);p=client.get(path+'/review-packet').json()
    if change in {'membership_removed','binding_tampered'}:approve(client,path)
    with client.app.state.db.Session() as db:
        if change=='viewer':db.get(Membership,('demo-workspace','editor')).role='viewer'
        elif change=='author':db.get(Source,'edge-source').created_by='editor'
        elif change=='membership_removed':db.delete(db.get(Membership,('demo-workspace','editor')))
        else:
            from app.sec_core.core import digest,canonical
            row=db.scalar(select(RunClaimReview).where(RunClaimReview.run_id==run_id))
            body=deepcopy(row.payload);body['binding']['passages'][0]['locator']='Invented locator'
            row.payload=body;row.payload_sha256=digest(canonical(body))
        db.commit()
    if change in {'viewer','author'}:
        assert client.post(path+'/reviews',headers=EDITOR,json=decision(p)).status_code==403
    else:
        assert not client.get(path+'/reviews').json()['status']['current']
        assert client.get(path+'/review-packet').json()['review'] is None
