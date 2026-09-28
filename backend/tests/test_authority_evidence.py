"""Synthetic reviews and mock execution only; no real authority or human approval."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import select, delete
from app.models import Source, Evidence, Run, RunAuthorityEvidence, AuthorityRelationship
from app.services import authority_evidence as ae, rights, editorial, applicability, coordinate_evidence as ce
from app.sec_core.core import digest
from app.editorial_schemas import EditorialDecision
from app.applicability_schemas import ApplicabilityDecision
from test_source_search import source
from test_content_library import decision as technical_decision
from test_applicability import applicability_payload, CONTEXT
from test_authority import proposal, review
from conftest import complete_run


def prepared(client, policy=None):
    with client.app.state.db.Session() as db:
        for sid in ('edge-source', 'edge-target'):
            s = source(db, sid)
            s.policy = {**s.policy, **(policy or {}), 'content_sha256': digest(s.text), 'content_reference_ids': []}
            rights.record_approval(s, 'synthetic');db.commit()
            editorial.record(db, s, EditorialDecision.model_validate(technical_decision(s)), 'editor')
            applicability.record(db, s, ApplicabilityDecision.model_validate(applicability_payload(s)), 'editor')
    edge, _ = proposal(client, 'defines')
    result = review(client, edge)
    assert result.status_code == 200, result.text
    return edge


def run_graph(client):
    edge = prepared(client)
    result = complete_run(client, question='Research quasar amortization exception', context=CONTEXT)
    return edge, result


def test_actual_mock_execution_persists_exact_independent_endpoint_evidence(client, monkeypatch):
    from app.providers.gemini import MockGemini
    seen = []
    original = MockGemini.structured
    def observe(self, schema, prompt, data, **kw):
        if 'authority_relationships' in data:
            seen.append(deepcopy(data['authority_relationships']))
        return original(self, schema, prompt, data, **kw)
    monkeypatch.setattr(MockGemini, 'structured', observe)
    edge, result = run_graph(client)
    with client.app.state.db.Session() as db:
        run = db.get(Run, result['id'])
        packets = ae.packets(db, run)
        assert len(packets) == 1 and packets[0]['relationship_id'] == edge['id']
        assert seen and all(p == packets for p in seen)
        assert run.result['authority_relationship_count'] == 1
        for eid in (packets[0]['source_evidence_id'], packets[0]['target_evidence_id']):
            evidence = db.get(Evidence, eid)
            assert rights.evidence_allowed(db, evidence, 'export')
            assert ce.current(db.get(Source, evidence.source_id), evidence)
        assert 'review_note' not in str(packets) and 'ev_synthetic' not in str(packets)
        rights.run_artifact_access(db, run, 'export')


@pytest.mark.parametrize('change', ['revoke', 'delete_edge', 'delete_evidence', 'snapshot', 'locator',
    'offset', 'body', 'access', 'kind', 'title', 'technical', 'applicability', 'rights', 'workspace', 'different_run'])
def test_dependencies_rechecked_at_output(client, change):
    edge, result = run_graph(client)
    with client.app.state.db.Session() as db:
        run = db.get(Run, result['id'])
        item = db.scalar(select(RunAuthorityEvidence).where(RunAuthorityEvidence.run_id == run.id))
        assert item is not None
        evidence = db.get(Evidence, item.target_evidence_id)
        s = db.get(Source, evidence.source_id)
        if change == 'revoke':db.get(AuthorityRelationship, edge['id']).current_review_id = None
        elif change == 'delete_edge':db.execute(delete(AuthorityRelationship).where(AuthorityRelationship.id == edge['id']))
        elif change == 'delete_evidence':db.execute(delete(Evidence).where(Evidence.id == evidence.id))
        elif change == 'snapshot':item.payload = {**item.payload, 'scope': 'Tampered scope'}
        elif change == 'locator':evidence.locator = 'Invented page'
        elif change == 'offset':
            p = deepcopy(evidence.extraction_context);p['citation']['character_start'] = True;evidence.extraction_context = p
        elif change == 'body':s.text += 'Changed'
        elif change == 'access':evidence.access = 'primary_text_reviewed'
        elif change == 'kind':evidence.source_kind = 'standard'
        elif change == 'title':evidence.title = 'Invented standard title'
        elif change == 'technical':s.policy = {**s.policy, 'technical_review_record_id': None}
        elif change == 'applicability':s.policy = {**s.policy, 'applicability_record_id': None}
        elif change == 'rights':s.policy = {**s.policy, 'export': False}
        elif change == 'workspace':
            with pytest.raises(HTTPException):ae.packets(db, run, 'export', context={'workspace_id': 'other'})
            return
        elif change == 'different_run':
            other = Run(user_id=run.user_id, workspace_id=run.workspace_id, workflow=run.workflow,
                        question='Other execution', context=CONTEXT, facts=[], document_ids=[], inputs={})
            db.add(other);db.flush();evidence.run_id = other.id
        db.commit();db.expire_all()
        with pytest.raises(HTTPException) as failure:
            rights.run_artifact_access(db, run, 'export')
        assert failure.value.detail['code'] == 'SOURCE_CHANGED'


def test_public_relationship_review_does_not_admit_unreviewed_sources(client):
    edge, _ = proposal(client)
    assert review(client, edge).status_code == 200
    result = complete_run(client, question='Research quasar amortization', context=CONTEXT)
    with client.app.state.db.Session() as db:
        assert ae.packets(db, db.get(Run, result['id'])) == []


def test_selection_bound_private_priority_and_endpoint_date_gate(client):
    prepared(client)
    from app.services.retrieval import search
    with client.app.state.db.Session() as db:
        run = SimpleNamespace(context=CONTEXT, document_ids=[], workspace_id='demo-workspace')
        context = {'workspace_id': 'demo-workspace'}
        pool = search(db, run, 'quasar', rights_context=context)
        private = {'source_id': None, 'document_id': 'private', 'locator': 'p1', 'text': 'Facts'}
        rows, plans = ae.select_evidence(db, run, [private, *pool], 2, context=context)
        assert rows[0] == private and len(rows) == 2 and plans == []
        rows, plans = ae.select_evidence(db, run, pool, 10, context=context)
        assert len(plans) == 1 and len({ae.key(r) for r in rows}) == len(rows)
        run.context = {**CONTEXT, 'knowledge_date': '2018-01-01'}
        assert ae.select_evidence(db, run, pool, 10, context=context)[1] == []


@pytest.mark.parametrize('value', [None, {}, {'citation': None}, {'version': ce.VERSION, 'citation': []}])
def test_malformed_coordinate_packets_fail_closed(client, value):
    with client.app.state.db.Session() as db:
        s = source(db)
        assert not ce.current(s, SimpleNamespace(extraction_context=value))


def test_relationship_revoked_after_synthesis_prevents_verification_dispatch(client, monkeypatch):
    from app.providers.gemini import MockGemini
    from app.schemas import Analysis, Verification
    from app.worker import tick
    from conftest import activate, create_run, key
    edge = prepared(client)
    original = MockGemini.structured
    verified = []
    def revoke_after_analysis(self, schema, prompt, data, **kw):
        response = original(self, schema, prompt, data, **kw)
        if schema is Analysis:
            with client.app.state.db.Session() as db:
                db.get(AuthorityRelationship, edge['id']).current_review_id = None;db.commit()
        if schema is Verification:
            verified.append(True)
        return response
    monkeypatch.setattr(MockGemini, 'structured', revoke_after_analysis)
    activate(client)
    run = create_run(client, question='Research quasar amortization', context=CONTEXT)
    assert client.post('/api/v1/runs/'+run['id']+'/start', json={'expected_revision': 1, 'confirm_scope': True}, headers=key()).status_code == 202
    assert tick(client.app.state.db, client.app.state.settings)
    with client.app.state.db.Session() as db:
        current = db.get(Run, run['id'])
        assert current.state == 'blocked' and current.error_code == 'SOURCE_CHANGED'
    assert verified == []


def test_coordinate_preserves_literal_spreadsheet_and_generic_intake_context(client):
    from app.services import spreadsheet_context, passage_context
    with client.app.state.db.Session() as db:
        s = source(db)
        for metadata in ({'intake_spreadsheet': {'format': 'xlsx', 'sheet': 'Hidden', 'sheet_state': 'hidden', 'calculated': False}}, {}):
            s.policy = {**s.policy, 'intake_extraction_id': 'synthetic', 'intake_locator': 'Physical page 2 / cell A1',
                        'content_sha256': digest(s.text), **metadata}
            if not metadata:s.policy = {k:v for k,v in s.policy.items() if k != 'intake_spreadsheet'}
            packet = ce.packet(s, 0, len(s.text))
            expected = spreadsheet_context.source_context(s) if metadata else passage_context.packet(s, 0, len(s.text))
            assert packet['extraction_context'] == expected
            e = SimpleNamespace(source_id=s.id, document_id=None, text=s.text, locator=packet['citation']['locator'],
                                access='secondary_text_reviewed', extraction_context=packet)
            assert spreadsheet_context.current(db, e)
            e.extraction_context = {**packet, 'extraction_context': {}}
            assert not spreadsheet_context.current(db, e)


def test_output_rechecks_relationship_after_source_release_locks(client, monkeypatch):
    from app.services import output_rights
    edge, result = run_graph(client)
    original = output_rights.release
    def concurrent_review(db, sources, payload):
        receipt = original(db, sources, payload)
        db.get(AuthorityRelationship, edge['id']).current_review_id = None
        db.flush()
        return receipt
    monkeypatch.setattr(output_rights, 'release', concurrent_review)
    with client.app.state.db.Session() as db:
        run = db.get(Run, result['id'])
        rights.run_artifact_access(db, run)
        with pytest.raises(HTTPException) as error:
            output_rights.run_output(db, run)
        assert error.value.detail['code'] == 'SOURCE_CHANGED'
        db.rollback()


def test_inspection_api_exact_pairs_notices_and_no_subscription_requirement(client):
    _, result = run_graph(client)
    assert client.post('/api/v1/dev/subscription', json={'state':'expired'}).status_code == 200
    response = client.get('/api/v1/runs/'+result['id']+'/relationships')
    assert response.status_code == 200,response.text
    payload = response.json()
    assert len(payload['items']) == 1 and not payload['complete_graph_verified'] and not payload['claim_support_verified']
    assert payload['selection_limits']['relationships'] == 6
    item = payload['items'][0]
    for name in ('source','target'):
        p = item['passages'][name]
        assert digest(p['text']) == p['citation']['passage_text_sha256']
        assert p['evidence_id'] == item['relationship'][name+'_evidence_id']
    assert 'review_note' not in str(payload) and 'ev_synthetic' not in str(payload)
    assert 'source_attributions' in payload
    assert client.get('/api/v1/runs/'+result['id']+'/relationships', headers={'X-Dev-User':'editor'}).status_code == 404


@pytest.mark.parametrize('change', ['edge','source','snapshot','evidence'])
def test_inspection_api_withholds_changed_dependencies(client,change):
    edge, result = run_graph(client)
    with client.app.state.db.Session() as db:
        item = db.scalar(select(RunAuthorityEvidence).where(RunAuthorityEvidence.run_id == result['id']))
        if change == 'edge':db.get(AuthorityRelationship, edge['id']).current_review_id = None
        elif change == 'source':db.get(Source,'edge-target').enabled = False
        elif change == 'snapshot':item.payload = {**item.payload,'scope':'Changed scope'}
        else:db.get(Evidence,item.target_evidence_id).text = 'Changed body'
        db.commit()
    response = client.get('/api/v1/runs/'+result['id']+'/relationships')
    assert response.status_code == 409 and response.json()['error']['code'] == 'SOURCE_CHANGED'
    assert 'quasar' not in response.text


def test_inspection_empty_run_is_not_complete_graph_claim(client):
    result = complete_run(client)
    response = client.get('/api/v1/runs/'+result['id']+'/relationships')
    assert response.status_code == 200,response.text
    payload = response.json()
    assert payload['items'] == [] and not payload['complete_graph_verified']


@pytest.mark.parametrize('exhausted', [False, True])
def test_inspection_preserves_notices_and_shared_output_budget(client,exhausted):
    from app.models import OutputBudget
    prepared(client, {'attribution':'Synthetic inspector notice', 'output_control': {
        'group_id':'inspector-fixture','mode':'bounded','max_chars_per_response':1000000,'max_chars_total':1000000}})
    result = complete_run(client, question='Research quasar amortization', context=CONTEXT)
    if exhausted:
        with client.app.state.db.Session() as db:
            db.get(OutputBudget,'inspector-fixture').released_chars = 999999;db.commit()
    url = '/api/v1/runs/'+result['id']+'/relationships'
    response = client.get(url)
    if exhausted:
        assert response.status_code == 403,response.text
        assert response.json()['error']['code'] == 'SOURCE_OUTPUT_LIMIT'
        return
    assert response.status_code == 200,response.text
    assert response.json()['source_attributions'][0]['notice'] == 'Synthetic inspector notice'
    with client.app.state.db.Session() as db:count = db.get(OutputBudget,'inspector-fixture').released_chars
    assert client.get(url).status_code == 200
    with client.app.state.db.Session() as db:assert db.get(OutputBudget,'inspector-fixture').released_chars == count
