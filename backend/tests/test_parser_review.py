"""Synthetic parser review only; no accounting or legal approvals."""
import base64
import copy
import pytest
from app.models import Source, SourceExtraction, ParserReview, now
from app.services import parser_review, rights
from app.services.storage import Storage
from app.sec_core.core import digest, canonical
from test_source_intake import registered, payload, fetch, parse, ADMIN, RAW

EDITOR = {'X-Dev-User':'editor'}


def prepared(client):
    body = payload(); body['source']['policy']['export'] = True
    work = registered(client, body=body)
    artifact = fetch(client, work); extraction = parse(client, artifact)
    sid = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).json()['source_ids'][0]
    packet = client.get('/api/v1/editorial/extractions/'+extraction['id']+'/packet',headers=EDITOR)
    assert packet.status_code == 200, packet.text
    p = packet.json()['packet']
    decision = {'expected_revision':p['review_revision'], 'expected_sequence':p['review_sequence'],
        'decision':'approved','review_scope':'Synthetic parser and locator check',
        'review_note':'Synthetic test attestation only; not an actual professional review.',
        'evidence_ref':'ev_synthetic_parser','evidence_sha256':'a'*64,'expires_at':now()+3600,
        'checked_passage_indices':list(range(len(p['passages']))),'confirm_raw_and_citations_checked':True}
    return extraction['id'], sid, decision, packet.json()


def record(client, eid, body):
    return client.post('/api/v1/editorial/extractions/'+eid+'/review',headers=EDITOR,json=body)


def test_packet_preserves_raw_bytes_hashes_locators_and_no_approval(client):
    eid, sid, decision, packet = prepared(client)
    assert packet['packet_sha256'] == digest(canonical(packet['packet']))
    assert base64.b64decode(packet['packet']['raw_base64']) == RAW
    assert packet['packet']['identity']['raw_sha256'] == digest(RAW)
    assert packet['packet']['publication_metadata']['notices']
    assert packet['packet']['source']['edition'] == 'fixture-1'
    assert packet['packet']['passages'][0]['locator']
    assert not packet['packet']['approval_granted']
    with client.app.state.db.Session() as db:
        assert not parser_review.current(db.get(Source, sid))
        assert db.query(ParserReview).count() == 0


def test_parser_approval_remains_distinct_and_revocation_invalidates_evidence_revision(client):
    eid, sid, decision, _ = prepared(client)
    assert record(client, eid, decision).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid); version = source.policy_version
        assert parser_review.current(source)
        assert not rights.allowed(source, 'model_input')  # Rights/technical/applicability still absent.
        original = copy.deepcopy(db.query(ParserReview).one().payload)
    revoked = {**decision,'expected_sequence':1,'decision':'revoked','checked_passage_indices':[]}
    assert record(client, eid, revoked).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        assert not parser_review.current(source) and source.policy_version == version+1
        assert db.query(ParserReview).count() == 2
        assert db.query(ParserReview).filter_by(sequence=1).one().payload == original
    history_url = '/api/v1/editorial/extractions/'+eid+'/reviews'
    history = client.get(history_url,headers=EDITOR)
    assert history.status_code == 200
    assert [r['sequence'] for r in history.json()['items']] == [2,1]
    assert client.get(history_url,headers=ADMIN).status_code == 403


@pytest.mark.parametrize('change,status', [({'checked_passage_indices':[]},422),
    ({'checked_passage_indices':[0,0]},422),({'checked_passage_indices':[-1]},422),
    ({'expected_sequence':2},409),({'expected_revision':'0'*64},409),({'expires_at':1},422)])
def test_parser_decision_contract(client, change, status):
    eid, _, body, _ = prepared(client)
    assert record(client, eid, {**body, **change}).status_code == status


def test_stale_retry_does_not_append(client):
    eid, _, body, _ = prepared(client)
    assert record(client, eid, body).status_code == 200
    assert record(client, eid, body).status_code == 409


def test_reviewer_cannot_be_source_author(client):
    eid, sid, body, _ = prepared(client)
    with client.app.state.db.Session() as db:
        child = db.get(Source, sid); parent = db.get(Source, child.policy['intake_parent_id'])
        parent.created_by = 'editor'; db.commit()
    assert record(client, eid, body).status_code == 403


def test_parser_role_and_export_rights_required(client):
    eid, sid, body, _ = prepared(client)
    url = '/api/v1/editorial/extractions/'+eid+'/packet'
    assert client.get(url,headers=ADMIN).status_code == 403
    with client.app.state.db.Session() as db:
        child = db.get(Source, sid); parent = db.get(Source, child.policy['intake_parent_id'])
        parent.policy = {**parent.policy, 'export':False}; rights.record_approval(parent,'approver');db.commit()
    assert client.get(url,headers=EDITOR).status_code == 403


@pytest.mark.parametrize('change', ['locator','body','parser','record','expiry'])
def test_current_rejects_changed_or_expired_provenance(client, monkeypatch, change):
    eid, sid, body, _ = prepared(client)
    assert record(client, eid, body).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        if change == 'locator': source.policy = {**source.policy,'intake_locator':'Changed citation'}
        elif change == 'body': source.text = 'Different body'
        elif change == 'parser': db.get(SourceExtraction,eid).parser_version = 'different-parser'
        elif change == 'record':
            row = db.query(ParserReview).one();row.payload = {**row.payload,'review_note':'Changed after approval'}
        else: monkeypatch.setattr(parser_review,'now',lambda:body['expires_at'])
        assert not parser_review.current(source)


def test_corrupt_artifact_cannot_be_reviewed(client):
    eid, sid, body, _ = prepared(client)
    with client.app.state.db.Session() as db:
        ex = db.get(SourceExtraction,eid)
        path = Storage(client.app.state.settings)._path(ex.object_key)
        path.write_bytes(b'changed')
    assert record(client, eid, body).status_code == 409


def test_parser_expiry_blocks_agent_and_saved_exports_with_other_reviews_present(client, monkeypatch):
    from app.models import Run, Evidence
    from app.services import editorial
    from app.editorial_schemas import EditorialDecision
    from test_content_library import decision as technical_decision
    eid, sid, body, _ = prepared(client)
    assert record(client, eid, body).status_code == 200
    with client.app.state.db.Session() as db:
        source = db.get(Source, sid)
        source.policy = {**source.policy, 'applicability_review_status':'approved'}
        source.reviewed = True; source.approved_by = 'approver'
        rights.record_approval(source, 'approver');db.commit()
        editorial.record(db, source, EditorialDecision.model_validate(technical_decision(source)), 'editor')
        assert rights.allowed(source,'model_input')
        run = Run(workspace_id='demo-workspace',user_id='demo',workflow='deep_research',question='Synthetic test')
        db.add(run); db.flush()
        ev = Evidence(run_id=run.id,source_id=sid,title=source.title,locator=source.policy['intake_locator'],
                      text=source.text,access='full',policy_version=source.policy_version,source_kind=source.kind)
        db.add(ev);db.flush()
        assert rights.evidence_allowed(db,ev,'export')
        monkeypatch.setattr(parser_review,'now',lambda:body['expires_at'])
        assert not rights.allowed(source,'model_input')
        assert not rights.evidence_allowed(db,ev,'export')
