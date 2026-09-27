"""Synthetic output licenses only; reviewed limits are not safe-harbor legal advice."""
import io
import json
import uuid
import zipfile
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models import Source, OutputBudget, OutputRelease, Run
from app.schemas import OutputControl
from app.services import output_rights, rights
from app.worker import tick
from conftest import complete_run, activate, create_run, key


def fixture(db, group=None, per=100000, total=1000000, mode='bounded', source_id=None):
    group = group or 'fixture-'+str(uuid.uuid4())
    control = {'mode': mode, 'group_id': group}
    if mode == 'bounded': control.update(max_chars_per_response=per, max_chars_total=total)
    source = db.get(Source, source_id) if source_id else None
    if not source:
        source = Source(title='Synthetic author work', publisher='Test author', text='Original fixture source text.',
                        canonical_url='https://example.test/fixture', reviewed=True,
                        created_by='admin', approved_by='approver', kind='original_commentary')
        db.add(source); db.flush()
    source.policy = {**source.policy, 'basis': 'license', 'commercial_use': True, 'store_text': True,
                     'model_input': True, 'quote': True, 'export': True, 'display_full': True,
                     'license_evidence_ref': 'synthetic-only-not-a-real-license',
                     'attribution': 'Fixture Author. Required synthetic notice. <script>never execute</script>',
                     'output_control': control}
    rights.record_approval(source, 'approver')
    db.commit()
    return source.id, group


@pytest.mark.parametrize('control', [
    {'mode': 'bounded', 'group_id': 'x'},
    {'mode': 'bounded', 'group_id': 'x', 'max_chars_per_response': True, 'max_chars_total': 100},
    {'mode': 'bounded', 'group_id': 'x', 'max_chars_per_response': 101, 'max_chars_total': 100},
    {'mode': 'unrestricted', 'group_id': 'x', 'max_chars_total': 100},
])
def test_output_limits_require_explicit_typed_terms(control):
    with pytest.raises(ValueError): OutputControl.model_validate(control)


@pytest.mark.parametrize('action', ['quote', 'display_full', 'export', 'model_input'])
def test_license_without_reviewed_output_terms_denies_body(client, action):
    with client.app.state.db.Session() as db:
        sid, _ = fixture(db)
        source = db.get(Source, sid); source.policy = {**source.policy, 'output_control': None}
        rights.record_approval(source, 'approver'); db.commit()
        assert not rights.allowed(source, action)
        assert rights.allowed(source, 'store_text')


def test_budget_accumulates_and_identical_rereads_are_idempotent(client):
    database = client.app.state.db
    with database.Session() as db:
        sid, group = fixture(db, per=8, total=13)
        source = db.get(Source, sid)
        output_rights.release(db, [source], 'alpha'); db.commit()  # 7 canonical characters
        output_rights.release(db, [source], 'alpha'); db.commit()
        assert db.get(OutputBudget, group).released_chars == 7
        output_rights.release(db, [source], 'beta'); db.commit()  # 6 more
        assert db.get(OutputBudget, group).released_chars == 13
        with pytest.raises(HTTPException): output_rights.release(db, [source], 'z')
        db.rollback()
        assert db.get(OutputBudget, group).released_chars == 13
        assert db.scalar(select(func.count()).select_from(OutputRelease)) == 2


def test_group_shared_across_source_editions_and_approval_cannot_reset(client):
    with client.app.state.db.Session() as db:
        first, group = fixture(db, per=10, total=10)
        second, _ = fixture(db, group=group, per=10, total=10)
        output_rights.release(db, [db.get(Source, first)], 'alpha'); db.commit()
        with pytest.raises(HTTPException): output_rights.release(db, [db.get(Source, second)], 'beta')
        db.rollback()
        source = db.get(Source, first)
        source.policy = {**source.policy, 'output_control': {'mode': 'bounded', 'group_id': group,
                         'max_chars_per_response': 100, 'max_chars_total': 1000}}
        rights.record_approval(source, 'approver'); db.commit()
        with pytest.raises(HTTPException) as error: output_rights.release(db, [source], 'alpha')
        assert error.value.detail['code'] == 'OUTPUT_POLICY_CONFLICT'


def test_new_output_limits_invalidate_prior_rights_approval(client):
    with client.app.state.db.Session() as db:
        sid, _ = fixture(db)
        source = db.get(Source, sid)
        assert rights.allowed(source, 'quote')
        source.policy = {**source.policy, 'output_control': {'mode': 'unrestricted', 'group_id': 'other'}}
        assert not rights.allowed(source, 'quote')


def test_source_evidence_notices_and_all_export_formats(client):
    with client.app.state.db.Session() as db:
        sid, group = fixture(db, source_id='sample-research')
    source = client.get('/api/v1/sources/'+sid).json()
    assert source['text'] and source['source_attributions'][0]['notice'].startswith('Fixture Author')
    run = complete_run(client)
    assert run['result']['source_attributions']
    items = client.get('/api/v1/runs/'+run['id']+'/evidence').json()['items']
    eid = next(row['id'] for row in items if row['source_id'] == sid)
    response = client.get('/api/v1/evidence/'+eid).json()
    assert response['text'] and response['source_attributions']
    memo = client.post('/api/v1/runs/'+run['id']+'/memo').json()
    assert memo['source_attributions']
    # Required notices remain server-owned even if the user replaces every editable character.
    response = client.put('/api/v1/memos/'+memo['id'], json={'title': 'Edited draft', 'body': 'New body',
                           'expected_revision': memo['revision']})
    assert response.status_code == 200 and response.json()['source_attributions']
    for format in ('md', 'html', 'docx', 'pdf'):
        exported = client.get('/api/v1/memos/'+memo['id']+'/export', params={'format': format})
        assert exported.status_code == 200, exported.text
        if format == 'docx':
            with zipfile.ZipFile(io.BytesIO(exported.content)) as archive: text = archive.read('word/document.xml').decode()
        elif format == 'pdf':
            from pypdf import PdfReader
            text = '\n'.join(page.extract_text() for page in PdfReader(io.BytesIO(exported.content)).pages)
        else: text = exported.text
        assert 'Required synthetic notice' in text
        if format in {'html', 'docx'}: assert '<script>never execute</script>' not in text
    history = client.get('/api/v1/memos/'+memo['id']+'/revisions').json()['items']
    assert all(row['source_attributions'] for row in history)
    with client.app.state.db.Session() as db:
        before = db.get(OutputBudget, group).released_chars
    client.get('/api/v1/memos/'+memo['id']+'/export?format=md')
    with client.app.state.db.Session() as db:
        assert db.get(OutputBudget, group).released_chars == before


def test_worker_does_not_release_over_limit_result(client):
    with client.app.state.db.Session() as db:
        fixture(db, source_id='sample-research', per=10, total=10)
    activate(client); run = create_run(client)
    assert client.post('/api/v1/runs/'+run['id']+'/start', json={'expected_revision': 1, 'confirm_scope': True}, headers=key()).status_code == 202
    tick(client.app.state.db, client.app.state.settings)
    with client.app.state.db.Session() as db:
        row = db.get(Run, run['id'])
        assert row.state == 'blocked' and row.error_code == 'SOURCE_OUTPUT_LIMIT' and row.result is None
        assert db.scalar(select(func.count()).select_from(OutputRelease)) == 0


def test_public_full_text_cannot_bypass_response_limit(client):
    with client.app.state.db.Session() as db: sid, _ = fixture(db, per=0, total=0)
    assert client.get('/api/v1/sources/'+sid).status_code == 403


def test_saved_result_budget_is_shared_with_collaborator(client):
    with client.app.state.db.Session() as db: sid, group = fixture(db, source_id='sample-research')
    run = complete_run(client)
    with client.app.state.db.Session() as db: before = db.get(OutputBudget, group).released_chars
    response = client.get('/api/v1/runs/'+run['id'], headers={'X-Dev-User': 'reviewer'})
    assert response.status_code == 200 and response.json()['result']
    with client.app.state.db.Session() as db: assert db.get(OutputBudget, group).released_chars == before


def test_ledger_stores_only_hash_and_count_not_output_text(client):
    with client.app.state.db.Session() as db:
        sid, group = fixture(db)
        output_rights.release(db, [db.get(Source, sid)], 'secret synthetic text'); db.commit()
        row = db.scalar(select(OutputRelease).where(OutputRelease.group_id == group))
        assert 'secret synthetic text' not in json.dumps({k:v for k,v in vars(row).items() if not k.startswith('_')})


def test_source_backed_export_cannot_omit_policy_session(client):
    from app.models import Memo
    from app.services.memos import export_bytes
    run = complete_run(client)
    memo = client.post('/api/v1/runs/'+run['id']+'/memo').json()
    with client.app.state.db.Session() as db:
        with pytest.raises(ValueError, match='authorized database session'):
            export_bytes(db.get(Memo, memo['id']), 'md')


def test_failed_multiwork_release_rolls_back_all_reservations(client):
    with client.app.state.db.Session() as db:
        first, group = fixture(db, group='a-work', per=100, total=100)
        second, _ = fixture(db, group='z-work', per=0, total=0)
        with pytest.raises(HTTPException):
            output_rights.release(db, [db.get(Source, first), db.get(Source, second)], 'fragment')
        db.rollback()
        assert db.get(OutputBudget, group) is None
        assert db.scalar(select(func.count()).select_from(OutputRelease)) == 0
