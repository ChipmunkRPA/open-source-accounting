"""Synthetic term reviews only; no actual license or legal conclusion is represented."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Source, OutputBudget, OutputRelease, OutputAmendment, User, now
from app.services import output_rights, rights
from test_output_rights import fixture
from conftest import rights_approval, complete_run

ADMIN = {'X-Dev-User': 'admin'}
APPROVER = {'X-Dev-User': 'approver'}


@pytest.fixture
def work(client):
    with client.app.state.db.Session() as db:
        first, group = fixture(db, per=10, total=10)
        second, _ = fixture(db, group=group, per=10, total=10)
        output_rights.release(db, [db.get(Source, first)], 'alpha'); db.commit()  # Seven characters.
    return client, group, [first, second]


def endpoint(group, row=None):
    base = '/api/v1/admin/output-groups/' + group + '/amendments'
    return base + ('/' + row['id'] + '/review' if row else '')


def proposal(client, group, **changes):
    state = client.get(endpoint(group), headers=ADMIN).json()
    return {'expected_limits_sha256': state['limits_sha256'], 'expected_terms_revision': state['terms_revision'],
        'expected_sources_sha256': state['sources_sha256'], 'new_control': {'mode': 'bounded', 'group_id': group,
            'max_chars_per_response': 20, 'max_chars_total': 30}, 'evidence_ref': 'ev_synthetic_amendment',
        'evidence_sha256': 'c'*64, 'review_expires_at': now()+3600, **changes}


def submit(client, group, **changes):
    response = client.post(endpoint(group), headers=ADMIN, json=proposal(client, group, **changes))
    assert response.status_code == 201, response.text
    return response.json()


def review(client, group, row, **changes):
    state = client.get(endpoint(group), headers=ADMIN).json()
    return client.post(endpoint(group, row), headers=APPROVER, json={'expected_record_sha256': row['record_sha256'],
        'expected_released_chars': state['released_chars'], 'decision': 'apply',
        'confirm_actual_terms_review': True, 'confirm_counters_preserved': True, **changes})


def reapprove(client, ids):
    for sid in ids:
        response = client.post('/api/v1/admin/sources/' + sid + '/approve', headers=APPROVER, json=rights_approval(client, sid))
        assert response.status_code == 200, response.text


def test_apply_preserves_counters_and_receipts_and_requires_source_rereview(work):
    client, group, ids = work
    with client.app.state.db.Session() as db:
        before = [(r.payload_sha256, r.character_count, r.created_at) for r in db.scalars(select(OutputRelease))]
        versions = {sid: db.get(Source, sid).policy_version for sid in ids}
    row = submit(client, group)
    response = review(client, group, row)
    assert response.status_code == 200, response.text
    assert response.json()['released_chars_at_apply'] == 7
    with client.app.state.db.Session() as db:
        budget = db.get(OutputBudget, group)
        assert budget.released_chars == 7 and budget.terms_revision == 2
        assert before == [(r.payload_sha256, r.character_count, r.created_at) for r in db.scalars(select(OutputRelease))]
        for sid in ids:
            source = db.get(Source, sid)
            assert source.policy_version == versions[sid]+1 and not source.reviewed
            assert not rights.allowed(source, 'model_input')
    reapprove(client, ids)
    with client.app.state.db.Session() as db:
        source = db.get(Source, ids[0])
        assert rights.allowed(source, 'model_input')
        output_rights.release(db, [source], 'alpha'); db.commit()
        assert db.get(OutputBudget, group).released_chars == 7
        output_rights.release(db, [source], 'beta'); db.commit()
        assert db.get(OutputBudget, group).released_chars == 13
    assert review(client, group, row).status_code == 409


def test_lower_than_prior_usage_withholds_even_identical_payload(work):
    client, group, ids = work
    with client.app.state.db.Session() as db:
        output_rights.release(db, [db.get(Source, ids[0])], 'x'); db.commit()  # Total now ten.
    row = submit(client, group, new_control={'mode':'bounded','group_id':group,
                 'max_chars_per_response':9,'max_chars_total':9})
    assert review(client, group, row).status_code == 200
    reapprove(client, ids)
    with client.app.state.db.Session() as db:
        with pytest.raises(HTTPException) as error:
            output_rights.release(db, [db.get(Source, ids[0])], 'alpha')
        assert error.value.detail['code'] == 'SOURCE_OUTPUT_LIMIT'
        db.rollback()
        assert db.get(OutputBudget, group).released_chars == 10


def test_unrestricted_transition_still_accumulates_usage(work):
    client, group, ids = work
    row = submit(client, group, new_control={'mode':'unrestricted','group_id':group})
    assert review(client, group, row).status_code == 200
    reapprove(client, ids)
    with client.app.state.db.Session() as db:
        output_rights.release(db, [db.get(Source, ids[0])], 'new large synthetic fragment'); db.commit()
        count = db.get(OutputBudget, group).released_chars
        assert count > 7
    next_row = submit(client, group, new_control={'mode':'bounded','group_id':group,
                      'max_chars_per_response':1,'max_chars_total':1})
    assert review(client, group, next_row).status_code == 200
    with client.app.state.db.Session() as db:
        assert db.get(OutputBudget, group).released_chars == count


def test_usage_drift_requires_review_of_current_counter(work):
    client, group, ids = work
    row = submit(client, group)
    with client.app.state.db.Session() as db:
        output_rights.release(db, [db.get(Source, ids[0])], 'x'); db.commit()
    assert review(client, group, row, expected_released_chars=7).status_code == 409
    assert review(client, group, row).status_code == 200
    with client.app.state.db.Session() as db: assert db.get(OutputBudget, group).released_chars == 10


@pytest.mark.parametrize('change', ['new_source', 'revision', 'disable'])
def test_source_set_or_revision_drift_denies_application(work, change):
    client, group, ids = work
    row = submit(client, group)
    with client.app.state.db.Session() as db:
        if change == 'new_source': fixture(db, group=group, per=10, total=10)
        else:
            source = db.get(Source, ids[0])
            if change == 'revision': source.version_label = 'changed'
            else: source.enabled = False
            db.commit()
    assert review(client, group, row).status_code == 409


def test_same_terms_after_two_amendments_cannot_revive_stale_proposal(work):
    client, group, _ = work
    stale = submit(client, group)
    assert review(client, group, submit(client, group)).status_code == 200
    back = submit(client, group, new_control={'mode':'bounded','group_id':group,
                  'max_chars_per_response':10,'max_chars_total':10})
    assert review(client, group, back).status_code == 200
    assert review(client, group, stale).status_code == 409
    with client.app.state.db.Session() as db:
        assert db.get(OutputBudget, group).released_chars == 7
        assert db.get(OutputBudget, group).terms_revision == 3


def test_loaded_source_cannot_release_after_amendment_even_with_restored_terms(work):
    client, group, ids = work
    with client.app.state.db.Session() as db:
        source = db.get(Source, ids[0])
        assert review(client, group, submit(client, group)).status_code == 200
        back = submit(client, group, new_control={'mode':'bounded','group_id':group,
                      'max_chars_per_response':10,'max_chars_total':10})
        assert review(client, group, back).status_code == 200
        with pytest.raises(HTTPException) as error: output_rights.release(db, [source], 'alpha')
        assert error.value.detail['code'] == 'SOURCE_CHANGED'


def test_superseded_group_terms_deny_before_model_input(work):
    client, group, ids = work
    with client.app.state.db.Session() as db:
        source = db.get(Source, ids[0])
        old_policy = dict(source.policy)
    assert review(client, group, submit(client, group)).status_code == 200
    # A separately submitted late alias with old reviewed terms cannot use the new group ledger.
    with client.app.state.db.Session() as db:
        stale = Source(title='Synthetic late edition', publisher='Fixture', text='Fixture',
                       reviewed=True, enabled=True, policy=old_policy)
        db.add(stale); db.flush(); rights.record_approval(stale, 'approver'); db.commit()
        assert not rights.allowed(stale, 'model_input')


def test_no_ledger_yet_initializes_zero_without_source_approval(work):
    client, _, _ = work
    with client.app.state.db.Session() as db: ids, group = fixture(db)
    row = submit(client, group)
    assert review(client, group, row).status_code == 200
    with client.app.state.db.Session() as db:
        assert db.get(OutputBudget, group).released_chars == 0
        assert not db.get(Source, ids).reviewed


@pytest.mark.parametrize('change', [
    {'new_control': {'mode':'bounded','group_id':'other','max_chars_per_response':20,'max_chars_total':30}},
    {'evidence_ref':'Private legal advice'}, {'evidence_sha256':'bad'}, {'review_expires_at':0},
    {'expected_terms_revision':True}, {'reset_counter':True}])
def test_no_regroup_reset_or_prose_shortcuts(work, change):
    client, group, _ = work
    response = client.post(endpoint(group), headers=ADMIN, json=proposal(client, group, **change))
    assert response.status_code == 422


def test_reviewer_separation_and_attestation(work):
    client, group, _ = work
    row = submit(client, group)
    body = {'expected_record_sha256':row['record_sha256'],'expected_released_chars':7,'decision':'apply',
            'confirm_actual_terms_review':True,'confirm_counters_preserved':True}
    assert client.post(endpoint(group,row), headers=ADMIN, json=body).status_code == 403
    with client.app.state.db.Session() as db:
        db.get(User,'admin').role='rights_approver';db.commit()
    assert client.post(endpoint(group,row), headers=ADMIN, json=body).status_code == 403
    assert review(client,group,row,confirm_actual_terms_review=False).status_code == 422
    assert review(client,group,row,confirm_counters_preserved=False).status_code == 422


def test_expiry_tamper_rejection_and_private_references(work, monkeypatch):
    client,group,_=work
    row=submit(client,group)
    assert client.get(endpoint(group)).status_code==403
    assert 'ev_synthetic' not in str(client.get('/api/v1/admin/audit',headers=ADMIN).json())
    monkeypatch.setattr('app.services.output_amendments.now',lambda: row['proposal']['review_expires_at'])
    assert review(client,group,row).status_code==409
    assert review(client,group,row,decision='reject').status_code==200
    assert review(client,group,row).status_code==409


def test_changed_proposal_cannot_apply(work):
    client,group,_=work
    row=submit(client,group)
    with client.app.state.db.Session() as db:
        record=db.get(OutputAmendment,row['id'])
        record.proposal={**record.proposal,'evidence_ref':'ev_changed_evidence'};db.commit()
    assert review(client,group,row).status_code==409


def test_saved_results_withheld_after_amendment(client):
    with client.app.state.db.Session() as db: _, group = fixture(db, source_id='sample-research')
    run = complete_run(client)
    row = submit(client,group)
    assert review(client,group,row).status_code==200
    assert client.get('/api/v1/runs/'+run['id']).json()['access_blocked']


def test_existing_scope_grant_requires_independent_reverification(client):
    from conftest import scope_grant
    from types import SimpleNamespace
    with client.app.state.db.Session() as db:
        sid, group = fixture(db, source_id='sample-research')
        source = db.get(Source, sid)
        source.policy = {**source.policy, 'scope': {'seat_id': ['synthetic-seat']}}
        rights.record_approval(source, 'approver'); db.commit()
    scope_grant(client)
    def permitted():
        with client.app.state.db.Session() as db:
            context = rights.runtime_context(db, SimpleNamespace(user_id='demo', workspace_id='demo-workspace'), client.app.state.settings)
            return rights.allowed(db.get(Source, sid), 'model_input', context=context)
    assert permitted()
    assert review(client, group, submit(client, group)).status_code == 200
    reapprove(client, [sid])
    assert not permitted()  # Reapproving source terms cannot silently renew the old seat grant.
    scope_grant(client)
    assert permitted()


def test_existing_counsel_decision_cannot_authorize_amended_terms(client):
    from test_counsel import scoped, approved
    # Invoke the fixture body for a synthetic independent counsel + scope setup.
    counsel_work = scoped.__wrapped__(client)
    approved(counsel_work)
    group = 'synthetic'
    assert review(client, group, submit(client, group)).status_code == 200
    response = client.post('/api/v1/admin/sources/sample-research/approve', headers=APPROVER,
                           json=rights_approval(client, 'sample-research'))
    assert response.status_code == 403 and response.json()['error']['code'] == 'COUNSEL_REQUIRED'


def test_bulk_response_is_atomic_and_shares_budget_across_items(work):
    client,group,ids=work
    with client.app.state.db.Session() as db:
        sources=[db.get(Source,sid) for sid in ids]
        with pytest.raises(HTTPException):
            output_rights.release_batch(db,[([sources[0]],'x'),([sources[1]],'y')])
        db.rollback()
        assert db.get(OutputBudget,group).released_chars==7
        result=output_rights.release_batch(db,[([sources[0]],'x'),([sources[1]],'x')])
        db.commit()
        assert len(result)==2 and result[0]==result[1]
        assert db.get(OutputBudget,group).released_chars==10
