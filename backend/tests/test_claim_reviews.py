"""Mock runs and synthetic human attestations, never actual professional review."""
from copy import deepcopy
import pytest
from sqlalchemy import select, delete
from app.models import Membership, Run, RunClaimReview, Source, Evidence, User, Job, RunEvent, now
from test_authority_evidence import run_graph
from test_authority import EDITOR


def prepared(client, policy=None):
    if policy is None:
        _, result = run_graph(client)
    else:
        from test_authority_evidence import prepared as prepare_graph, CONTEXT
        from conftest import complete_run
        prepare_graph(client, policy)
        result = complete_run(client, question='Research quasar amortization exception', context=CONTEXT)
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


def export_packet(client,path,p,**changes):
    return client.get(path+'/review-packet/export',params={
        'expected_revision':p['revision'],'expected_sequence':p['status']['sequence'],**changes})


def test_export_exact_json_and_retained_free_access(client):
    _,path=prepared(client);approve(client,path)
    p=client.get(path+'/review-packet').json()
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    r=export_packet(client,path,p)
    assert r.status_code==200,r.text
    assert r.json()['binding']==p['binding'] and r.json()['review']==p['review']
    assert r.json()['export']['permission_checked']=='export'
    assert r.headers['cache-control']=='no-store' and r.headers['x-content-type-options']=='nosniff'
    assert r.headers['content-disposition'].startswith('attachment; filename="claim-review-')
    assert export_packet(client,path,p).content==r.content
    assert client.get(path+'/review-packet/export',params={'expected_revision':p['revision'],'expected_sequence':1},headers={'X-Dev-User':'admin'}).status_code==404


@pytest.mark.parametrize('change',['revision','sequence','export_denied','source_disabled','review_changed','oversized'])
def test_export_fresh_permissions_revision_and_size(client,monkeypatch,change):
    run_id,path=prepared(client, {'export':False} if change=='export_denied' else None);p=client.get(path+'/review-packet').json()
    if change=='revision':p['revision']='0'*64
    elif change=='sequence':p['status']['sequence']=999
    elif change=='oversized':monkeypatch.setattr('app.services.claim_reviews.MAX_EXPORT_BYTES',10)
    elif change=='review_changed':approve(client,path)
    elif change=='export_denied':assert 'binding' in p
    else:
        with client.app.state.db.Session() as db:
            s=db.get(Source,'edge-source')
            s.enabled=False;db.commit()
    r=export_packet(client,path,p)
    assert r.status_code in {403,409,413},r.text
    assert 'quasar amortization' not in r.text


def test_export_omits_expired_findings_and_rechecks_after_lock(client,monkeypatch):
    from app.sec_core.core import canonical,digest
    from app.services import output_rights
    run_id,path=prepared(client);approve(client,path)
    with client.app.state.db.Session() as db:
        row=db.scalar(select(RunClaimReview).where(RunClaimReview.run_id==run_id))
        body=deepcopy(row.payload);body['decision']['expires_at']=1;row.payload=body;row.payload_sha256=digest(canonical(body));db.commit()
    p=client.get(path+'/review-packet').json();r=export_packet(client,path,p)
    assert r.status_code==200 and r.json()['review'] is None and not r.json()['status']['current']
    original=output_rights.release
    def deny_export(db,sources,payload):
        original(db,sources,payload)
        from app.services import rights
        s=db.get(Source,'edge-source');s.policy={**s.policy,'export':False};rights.record_approval(s,'synthetic');db.flush()
    monkeypatch.setattr(output_rights,'release',deny_export)
    assert export_packet(client,path,p).status_code==409


def test_export_notice_accounting_is_deduplicated_and_bounded(client):
    from app.models import OutputBudget,OutputRelease
    from app.services import output_rights
    _,path=prepared(client,{'attribution':'Synthetic mandatory source notice.',
        'output_control':{'mode':'bounded','group_id':'synthetic-claim-export','max_chars_per_response':100000,'max_chars_total':1000000}})
    p=client.get(path+'/review-packet').json()
    with client.app.state.db.Session() as db:
        before=db.get(OutputBudget,'synthetic-claim-export').released_chars
    r=export_packet(client,path,p);assert r.status_code==200,r.text
    assert 'Synthetic mandatory source notice.' in r.text
    with client.app.state.db.Session() as db:
        budget=db.get(OutputBudget,'synthetic-claim-export')
        after=budget.released_chars
        assert after-before==len(output_rights.canonical(r.json()))
        count=len(db.scalars(select(OutputRelease).where(OutputRelease.group_id=='synthetic-claim-export')).all())
    assert export_packet(client,path,p).content==r.content
    with client.app.state.db.Session() as db:
        budget=db.get(OutputBudget,'synthetic-claim-export')
        assert budget.released_chars==after
        assert len(db.scalars(select(OutputRelease).where(OutputRelease.group_id=='synthetic-claim-export')).all())==count
        budget.released_chars=1000001;db.commit()
    blocked=export_packet(client,path,p)
    assert blocked.status_code==403 and 'quasar amortization' not in blocked.text


def test_export_preserves_unicode_and_rechecks_review_status(client,monkeypatch):
    from app.services import output_rights
    run_id,path=prepared(client)
    with client.app.state.db.Session() as db:
        run=db.get(Run,run_id);body=deepcopy(run.result);body['claims'][0]['text']='Synthetic Cafe\u0301 claim <script>untrusted text</script>'
        run.result=body;db.commit()
    approve(client,path);p=client.get(path+'/review-packet').json()
    r=export_packet(client,path,p)
    assert r.status_code==200 and r.json()['binding']['claim']['text']==p['binding']['claim']['text']
    assert 'Cafe\u0301'.encode() in r.content
    original=output_rights.release
    def change_reviewer(db,sources,payload):
        original(db,sources,payload);db.get(User,'editor').role='member';db.flush()
    monkeypatch.setattr(output_rights,'release',change_reviewer)
    assert export_packet(client,path,p).status_code==409


def test_export_reloads_reviewer_membership_after_release(client,monkeypatch):
    from app.services import output_rights
    _,path=prepared(client);approve(client,path);p=client.get(path+'/review-packet').json()
    original=output_rights.release
    retained=[]
    def remove_membership(db,sources,payload):
        retained.append(db.get(Membership,('demo-workspace','editor')))
        original(db,sources,payload)
        db.execute(delete(Membership).where(Membership.workspace_id=='demo-workspace',
            Membership.user_id=='editor').execution_options(synchronize_session=False))
    monkeypatch.setattr(output_rights,'release',remove_membership)
    assert export_packet(client,path,p).status_code==409


def test_coverage_does_not_promote_synthetic_attestations(client):
    run_id,path=prepared(client)
    url=f'/api/v1/runs/{run_id}/claim-review-coverage'
    initial=client.get(url).json()
    assert initial['total_claims']==1 and initial['outcomes']['unreviewed']==1
    assert initial['attested_decision_coverage']==0
    approve(client,path)
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    report=client.get(url).json()
    assert report['outcomes']['supported']==1 and report['attested_decision_coverage']==1
    assert report['verified_professional_adjudications']==0
    assert report['claim_accuracy'] is None and report['numerical_accuracy'] is None
    assert report['review_origin']=='not_independently_verified'
    assert 'Fictional quasar' not in str(report) and 'review_note' not in str(report)
    assert client.get(url,headers={'X-Dev-User':'admin'}).status_code==404
    with client.app.state.db.Session() as db:
        db.get(Source,'edge-source').enabled=False;db.commit()
    stale=client.get(url).json()
    assert stale['outcomes']['stale_revoked_or_invalid']==1
    assert stale['current_attested_decisions']==0 and stale['outcomes']['supported']==0


@pytest.mark.parametrize('kind',['contradicted','unresolved'])
def test_coverage_outcomes_are_not_accuracy(client,kind):
    run_id,path=prepared(client)
    packet=client.get(path+'/review-packet').json();body=decision(packet)
    body['decision']=kind
    for passage in body['passages']:passage['relationship']='contradicts' if kind=='contradicted' else 'unresolved'
    assert client.post(path+'/reviews',headers=EDITOR,json=body).status_code==201
    report=client.get(f'/api/v1/runs/{run_id}/claim-review-coverage').json()
    assert report['outcomes'][kind]==1 and report['claim_accuracy'] is None


@pytest.mark.parametrize('claims,code',[([],200),([{'id':'invalid'}],409)])
def test_coverage_empty_or_invalid_denominator(client,claims,code):
    run_id,_=prepared(client)
    with client.app.state.db.Session() as db:
        run=db.get(Run,run_id);run.result={**run.result,'claims':claims};db.commit()
    response=client.get(f'/api/v1/runs/{run_id}/claim-review-coverage')
    assert response.status_code==code
    if code==200:assert response.json()['attested_decision_coverage'] is None


def test_coverage_rejects_duplicate_claim_denominator(client):
    run_id,_=prepared(client)
    with client.app.state.db.Session() as db:
        run=db.get(Run,run_id);run.result={**run.result,'claims':run.result['claims']*2};db.commit()
    assert client.get(f'/api/v1/runs/{run_id}/claim-review-coverage').status_code==409


def test_coverage_withholds_changed_snapshot(client,monkeypatch):
    from app.services import claim_reviews
    run_id,path=prepared(client);approve(client,path)
    original=claim_reviews.summary
    calls=0
    def changing(*args):
        nonlocal calls
        status=original(*args);calls+=1
        if calls>1:status={**status,'current':False}
        return status
    monkeypatch.setattr(claim_reviews,'summary',changing)
    response=client.get(f'/api/v1/runs/{run_id}/claim-review-coverage')
    assert response.status_code==409
    assert 'SOURCE_CHANGED' in response.text
