"""Optional real PostgreSQL contracts on an explicitly designated migrated test database.

Synthetic licenses/artifacts only. These tests do not make HTTP or Cloud requests.
"""
import multiprocessing
import os
from uuid import uuid4
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, text
from app.config import Settings
from app.db import Database
from app.intake_schemas import IntakeCreate
from app.models import User, Source, SourceArtifact, IntakeAttempt
from app.sec_core.fetch import RateBudget
from app.services import intake, rights
from test_source_intake import payload, FakeGateway


def model_attempt_worker(url, actor, operation_key, entered, release, results, start=None):
    from app.providers.gemini import Gemini
    from app.schemas import Plan
    from app.services import model_attempts
    from app.services import model_budgets
    import time
    model_budgets.REVIEW_DEADLINE = int(time.time())+30*86400  # Synthetic quote freshness in this test process.
    from app.errors import ProviderError
    database = Database(url)
    config = Settings(model_provider='google_cloud', google_cloud_project='test-project', model_budget_id=actor, _env_file=None)
    def transport(*_):
        results.put(('dispatch',))
        entered.set()
        assert release.wait(15)
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text':
            '{"issues":[],"missing_questions":[],"proposed_queries":[],"scope":"synthetic"}'}]}}],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 5, 'totalTokenCount': 15}}
    model = Gemini(config, transport)
    try:
        if start is not None:
            assert start.wait(15)
        model_attempts.invoke(database.Session, config, model, lambda: model.structured(Plan, 'Synthetic', {}),
            key=operation_key, phase='planning', user_id=actor, thinking='MEDIUM', output_limit=2500,
            prompt_version='synthetic')
        results.put(('finished',))
    except ProviderError as exc:
        results.put(('error', str(exc)))
    finally:
        database.engine.dispose()


def test_postgres_model_budget_admits_only_one_competing_call(pg_url):
    from app.models import ModelBudget, ModelAttempt
    from app.services.model_attempts import operation_key
    from conftest import synthetic_model_budget
    database = Database(pg_url)
    actor = str(uuid4())
    with database.Session() as db:
        db.add(User(id=actor, role='admin')); db.commit()
    synthetic_model_budget(database, budget_id=actor, actor=actor, limit='3')
    ctx = multiprocessing.get_context('spawn')
    entered, release, start, results = ctx.Event(), ctx.Event(), ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=model_attempt_worker, args=(pg_url, actor,
        operation_key('budget-race', actor, index), entered, release, results, start)) for index in range(2)]
    try:
        for process in workers: process.start()
        start.set()
        events = [results.get(timeout=20), results.get(timeout=20)]
        assert ('dispatch',) in events
        assert ('error', 'MODEL_BUDGET_EXHAUSTED_OR_INACTIVE') in events
        release.set()
        assert results.get(timeout=20) == ('finished',)
        for process in workers:
            process.join(15); assert process.exitcode == 0
        with database.Session() as db:
            budget = db.get(ModelBudget, actor)
            assert budget.held_nanos == 0 and budget.committed_nanos == 3_000_000_000
            assert db.scalar(select(func.count()).select_from(ModelAttempt).where(ModelAttempt.budget_id == actor)) == 1
    finally:
        release.set()
        for process in workers:
            if process.pid:
                if process.is_alive(): process.terminate()
                process.join(5)
        database.engine.dispose()


def test_postgres_model_operation_has_one_dispatch_owner(pg_url):
    from app.models import ModelAttempt
    from app.services.model_attempts import operation_key
    database = Database(pg_url)
    actor = str(uuid4())
    with database.Session() as db:
        db.add(User(id=actor, role='admin'))
        db.commit()
    from conftest import synthetic_model_budget
    synthetic_model_budget(database, budget_id=actor, actor=actor)
    key = operation_key('synthetic-concurrency', actor)
    ctx = multiprocessing.get_context('spawn')
    entered, release, results = ctx.Event(), ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=model_attempt_worker, args=(pg_url, actor, key, entered, release, results)) for _ in range(2)]
    try:
        workers[0].start()
        assert entered.wait(15)
        assert results.get(timeout=15) == ('dispatch',)
        workers[1].start()
        assert results.get(timeout=15) == ('error', 'MODEL_ATTEMPT_ALREADY_RECORDED')
        release.set()
        assert results.get(timeout=15) == ('finished',)
        for process in workers:
            process.join(15)
            assert process.exitcode == 0
        with database.Session() as db:
            records = db.scalars(select(ModelAttempt).where(ModelAttempt.operation_key == key)).all()
            assert len(records) == 1 and records[0].cost_state == 'estimated'
            assert records[0].usage['totalTokenCount'] == 15
    finally:
        release.set()
        for process in workers:
            if process.pid:
                if process.is_alive(): process.terminate()
                process.join(5)
        database.engine.dispose()


def test_postgres_cost_report_uses_one_snapshot(pg_url, monkeypatch):
    from app.models import ModelAttempt, Run, Workspace, now
    from app.services import model_attempts
    database = Database(pg_url)
    actor, wid, rid = str(uuid4()), str(uuid4()), str(uuid4())
    stamp = now()
    def receipt(key, amount):
        return ModelAttempt(operation_key=model_attempts.operation_key(key, rid), user_id=actor,
            workspace_id=wid, run_id=rid, phase='planning', provider='google_cloud', project='test-project',
            location='us', model_id='gemini-3.8-flash', prompt_version='synthetic', thinking='MEDIUM',
            output_limit=2500, started_at=stamp, outcome='succeeded', cost_state='estimated',
            cost_estimate={'estimated_usd': amount})
    with database.Session() as db:
        db.add(User(id=actor)); db.flush()
        db.add(Workspace(id=wid, owner_id=actor, name='Synthetic')); db.flush()
        db.add(Run(id=rid, user_id=actor, workspace_id=wid, workflow='deep_research', question='Synthetic', state='analyzing'))
        db.flush()
        db.add(receipt('before', '1'))
        db.commit()
    original = model_attempts.report
    def concurrent_completion(db, **kwargs):
        assert db.scalar(select(Run.state).where(Run.id == rid)) == 'analyzing'
        with database.Session() as other:
            other.add(receipt('after', '2'))
            other.get(Run, rid).state = 'completed_with_limitations'
            other.commit()
        assert db.scalar(select(Run.state).where(Run.id == rid)) == 'analyzing'
        # The report must still see this cohort as active until the NEXT snapshot.
        report = original(db, **kwargs)
        assert report['agent_cohort']['active_runs'] >= 1
        assert report['agent_cohort']['estimated_model_usd_per_completed_run'] is None
        return report
    monkeypatch.setattr(model_attempts, 'report', concurrent_completion)
    try:
        model_attempts.report_snapshot(database, start_at=stamp-10, end_at=stamp+10)
    finally:
        database.engine.dispose()


@pytest.fixture
def pg_url(monkeypatch):
    import time
    monkeypatch.setattr('app.services.model_budgets.REVIEW_DEADLINE', int(time.time())+30*86400)
    url = os.environ.get('OSA_POSTGRES_TEST_URL', '')
    if not url:
        pytest.skip('Requires explicitly supplied migrated disposable PostgreSQL database')
    from sqlalchemy.engine import make_url
    parsed = make_url(url)
    assert parsed.drivername == 'postgresql+psycopg' and (parsed.database or '').startswith('osa_')
    assert os.environ.get('OSA_DISPOSABLE_TEST_DATABASE') == 'true', 'Refusing a database not designated disposable'
    return url


def reserve_worker(url, start, results):
    budget = RateBudget(url, sleeper=lambda _: None)
    try:
        assert start.wait(10)
        results.put([budget.reserve() for _ in range(4)])
    finally:
        budget.engine.dispose()


def test_postgres_budget_serializes_reservations_across_processes(pg_url):
    db = Database(pg_url)
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE sec_request_budget SET next_at=0 WHERE name='shared'"))
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=reserve_worker, args=(pg_url, start, results)) for _ in range(4)]
    try:
        for process in workers: process.start()
        start.set()
        slots = sorted(slot for _ in workers for slot in results.get(timeout=20))
        for process in workers:
            process.join(10)
            assert process.exitcode == 0
        assert len(slots) == len(set(slots)) == 16
        assert all(b-a >= 0.249999 for a, b in zip(slots, slots[1:]))
    finally:
        for process in workers:
            if process.is_alive(): process.terminate()
            process.join(5)
        db.engine.dispose()


def acquire_worker(url, directory, work_id, actor, request_key, entered, release, results):
    db = Database(url)
    settings = Settings(app_env='test', database_url=url, data_dir=directory, _env_file=None)
    def fixture_response():
        # Marker proves only the lease owner made a synthetic request.
        with (Path(directory) / 'requests.txt').open('a') as stream: stream.write('request\n')
        entered.set()
        assert release.wait(15)
    try:
        artifact = intake.acquire(db, settings, work_id, actor, request_key,
                                  gateway_factory=lambda *_: FakeGateway(callback=fixture_response))
        results.put(('acquired', artifact['id']))
    except HTTPException as exc:
        results.put(('http', exc.status_code))
    finally:
        db.engine.dispose()


def test_postgres_duplicate_request_has_one_network_owner(pg_url, tmp_path):
    db = Database(pg_url)
    settings = Settings(app_env='test', database_url=pg_url, data_dir=str(tmp_path), _env_file=None)
    actor, approver = str(uuid4()), str(uuid4())
    with db.Session() as session:
        session.add_all([User(id=actor, role='admin'), User(id=approver, role='rights_approver')])
        session.commit()
        work = intake.register(session, settings, IntakeCreate.model_validate(payload(work_id=str(uuid4()))), actor)
        source = session.get(Source, work.source_id)
        source.reviewed, source.approved_by = True, approver
        rights.record_approval(source, approver)  # Explicit synthetic test attestation only.
        session.commit()
        work_id = work.id
    ctx = multiprocessing.get_context('spawn')
    entered, release, results = ctx.Event(), ctx.Event(), ctx.Queue()
    args = (pg_url, str(tmp_path), work_id, actor, 'same-request', entered, release, results)
    workers = [ctx.Process(target=acquire_worker, args=args) for _ in range(2)]
    try:
        workers[0].start()
        assert entered.wait(15)
        workers[1].start()
        assert results.get(timeout=15) == ('http', 409)
        release.set()
        result = results.get(timeout=15)
        assert result[0] == 'acquired'
        for process in workers:
            process.join(10)
            assert process.exitcode == 0
        assert (tmp_path / 'requests.txt').read_text().splitlines() == ['request']
        with db.Session() as session:
            assert session.scalar(select(func.count()).select_from(SourceArtifact).where(SourceArtifact.work_id == work_id)) == 1
            assert session.scalar(select(func.count()).select_from(IntakeAttempt).where(IntakeAttempt.work_id == work_id)) == 1
        def no_network(*_): pytest.fail('Completed retry must not download again')
        assert intake.acquire(db, settings, work_id, actor, 'same-request', gateway_factory=no_network)['id'] == result[1]
    finally:
        release.set()
        for process in workers:
            if process.pid:
                if process.is_alive(): process.terminate()
                process.join(5)
        db.engine.dispose()


def output_worker(url, source_id, payload, start, results):
    from app.services.output_rights import release
    database = Database(url)
    try:
        assert start.wait(15)
        with database.Session() as session:
            release(session, [session.get(Source, source_id)], payload)
            session.commit()
            results.put('released')
    except HTTPException as error:
        results.put(error.detail['code'])
    finally:
        database.engine.dispose()


@pytest.mark.parametrize('duplicate', [False, True])
def test_postgres_output_limit_serializes_across_accounts(pg_url, duplicate):
    from app.models import OutputBudget, OutputRelease
    database = Database(pg_url)
    group = 'synthetic-'+str(uuid4())
    with database.Session() as session:
        source = Source(title='Synthetic concurrency source', publisher='Test author', text='Fixture only',
                        policy={'output_control': {'mode': 'bounded', 'group_id': group,
                                'max_chars_per_response': 10, 'max_chars_total': 10}})
        session.add(source); session.commit(); source_id = source.id
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    payloads = ['alpha']*4 if duplicate else ['alpha', 'beta']
    workers = [ctx.Process(target=output_worker, args=(pg_url, source_id, p, start, results)) for p in payloads]
    try:
        for process in workers: process.start()
        start.set()
        states = [results.get(timeout=20) for _ in workers]
        for process in workers:
            process.join(10)
            assert process.exitcode == 0
        assert states.count('released') == (4 if duplicate else 1)
        assert states.count('SOURCE_OUTPUT_LIMIT') == (0 if duplicate else 1)
        with database.Session() as session:
            assert session.get(OutputBudget, group).released_chars in {6, 7}
            assert session.scalar(select(func.count()).select_from(OutputRelease).where(OutputRelease.group_id == group)) == 1
    finally:
        for process in workers:
            if process.is_alive(): process.terminate()
            process.join(5)
        database.engine.dispose()


def counsel_worker(url, source_id, record_id, fingerprint, actor, approval, mode, start, results):
    from app.api.sources import approve_source
    from app.api.counsel import revoke
    from app.schemas import RightsApproval
    from app.counsel_schemas import CounselRevocation
    database = Database(url)
    try:
        assert start.wait(15)
        with database.Session() as session:
            user = session.get(User, actor)
            if mode == 'approve':
                approve_source(source_id, RightsApproval.model_validate(approval), user=user, db=session)
            else:
                revoke(source_id, record_id, CounselRevocation(expected_record_sha256=fingerprint,
                       reason='operator_hold'), user=user, db=session)
            results.put((mode, 200))
    except HTTPException as error:
        results.put((mode, error.status_code))
    finally:
        database.engine.dispose()


@pytest.mark.parametrize('revoking', [False, True])
def test_postgres_counsel_activation_and_revocation_serialize(pg_url, revoking):
    from app.counsel_schemas import CounselSubmission
    from app.models import CounselRecord, now
    from app.services import counsel
    database = Database(pg_url)
    author, approver, reviewer = [str(uuid4()) for _ in range(3)]
    context = {'route': 'hosted_agent', 'audience': 'workspace', 'jurisdiction': 'synthetic'}
    with database.Session() as session:
        session.add_all([User(id=author, role='admin'), User(id=approver, role='rights_approver'),
                         User(id=reviewer, role='counsel_reviewer')]); session.commit()
        source = Source(title='Synthetic counsel race', publisher='Test only', text='Synthetic fixture',
            created_by=author, enabled=True, reviewed=False, policy={'basis': 'reviewed_use',
            'model_input': True, 'commercial_use': True, 'license_evidence_ref': 'ev_synthetic_bundle',
            'scope': {k: [v] for k, v in context.items()}, 'output_control': {'mode': 'bounded',
            'group_id': str(uuid4()), 'max_chars_per_response': 100, 'max_chars_total': 100}})
        session.add(source); session.flush()
        approval = {'expected_rights_revision': rights.revision(source),
                    'expected_policy_version': source.policy_version, 'confirm_actual_rights_review': True}
        proposal = {k: v for k, v in approval.items() if k != 'confirm_actual_rights_review'}
        proposal.update(operations=['model_input'], evidence_ref='ev_synthetic_bundle', evidence_sha256='a'*64,
            assessments={key: 'ev_synthetic_' + key for key in ('purpose', 'nature', 'amount_and_substantiality',
                'output_and_reconstruction', 'market_effect', 'access_route_and_terms', 'jurisdiction')},
            effective_at=now()-10, expires_at=now()+3600)
        record = counsel.submit(session, source, CounselSubmission.model_validate(proposal), author)
        record.status, record.reviewed_by, record.reviewed_at = 'approved', reviewer, now()
        session.commit()
        source_id, record_id, fingerprint = source.id, record.id, record.record_sha256
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    modes = ['approve', 'revoke' if revoking else 'approve']
    workers = [ctx.Process(target=counsel_worker, args=(pg_url, source_id, record_id, fingerprint,
                approver, approval, mode, start, results)) for mode in modes]
    try:
        for process in workers: process.start()
        start.set()
        outcomes = [results.get(timeout=20) for _ in workers]
        for process in workers:
            process.join(10)
            assert process.exitcode == 0
        with database.Session() as session:
            source = session.get(Source, source_id)
            record = session.get(CounselRecord, record_id)
            if revoking:
                assert ('revoke', 200) in outcomes
                assert any(mode == 'approve' and status in {200, 403} for mode, status in outcomes)
                assert record.status == 'revoked'
                assert not rights.allowed(source, 'model_input', context=context)
            else:
                assert sorted(status for _, status in outcomes) == [200, 409]
                assert source.policy_version == record.activated_policy_version == 2
                assert counsel.permitted(source, 'model_input')
                assert not rights.allowed(source, 'model_input', context=context)  # No verified jurisdiction assignment.
    finally:
        for process in workers:
            if process.is_alive(): process.terminate()
            process.join(5)
        database.engine.dispose()


def scope_worker(url, source_id, record_id, fingerprint, actor, mode, start, results):
    from app.api.source_scopes import approve, revoke
    from app.scope_schemas import ScopeApproval, ScopeRevocation
    database = Database(url)
    try:
        assert start.wait(15)
        with database.Session() as session:
            user = session.get(User, actor)
            if mode == 'approve':
                approve(source_id, record_id, ScopeApproval(expected_record_sha256=fingerprint,
                    confirm_actual_entitlement_verification=True), user=user, db=session)
            else:
                revoke(source_id, record_id, ScopeRevocation(expected_record_sha256=fingerprint,
                    reason='operator_hold'), user=user, db=session)
            results.put((mode, 200))
    except HTTPException as error:
        results.put((mode, error.status_code))
    finally:
        database.engine.dispose()


@pytest.mark.parametrize('revoking', [False, True])
def test_postgres_scope_review_serializes_replacement_and_revocation(pg_url, revoking):
    from app.models import Workspace, Membership, SourceScopeGrant, now
    from app.scope_schemas import ScopeSubmission
    from app.services import source_scopes
    database = Database(pg_url)
    author, approver, subject = [str(uuid4()) for _ in range(3)]
    with database.Session() as session:
        session.add_all([User(id=author, role='admin'), User(id=approver, role='rights_approver'), User(id=subject)])
        session.commit()
        workspace = Workspace(owner_id=subject, name='Synthetic scope race')
        session.add(workspace); session.flush()
        session.add(Membership(workspace_id=workspace.id, user_id=subject, role='owner'))
        source = Source(title='Synthetic scoped work', publisher='Test only', text='Fixture',
            created_by=author, approved_by=approver, enabled=True, reviewed=True,
            policy={'basis': 'original', 'commercial_use': True, 'model_input': True,
                    'scope': {'seat_id': ['synthetic-seat']}})
        session.add(source); session.flush(); rights.record_approval(source, approver); session.commit()
        payload = ScopeSubmission(expected_policy_version=source.policy_version,
            expected_rights_revision=rights.revision(source), subject_user_id=subject, workspace_id=workspace.id,
            operations=['model_input'], values={'seat_id': 'synthetic-seat'}, provider='mock', project='',
            region='us', model_id='gemini-3.8-flash', evidence_ref='ev_synthetic_entitlement', evidence_sha256='b'*64,
            effective_at=now()-10, expires_at=now()+3600)
        records = [source_scopes.submit(session, source, payload, author) for _ in range(2)]
        session.commit()
        source_id = source.id
        entries = [(r.id, r.record_sha256) for r in records]
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    # Competing distinct approvals exercise supersession + the partial unique index.
    # Same-record approval/revocation must finish revoked regardless of lock ordering.
    modes = ['approve', 'revoke' if revoking else 'approve']
    jobs = [(entries[0], modes[0]), (entries[0] if revoking else entries[1], modes[1])]
    workers = [ctx.Process(target=scope_worker, args=(pg_url, source_id, record, digest,
                approver, mode, start, results)) for (record, digest), mode in jobs]
    try:
        for process in workers: process.start()
        start.set()
        outcomes = [results.get(timeout=20) for _ in workers]
        for process in workers:
            process.join(10)
            assert process.exitcode == 0
        with database.Session() as session:
            rows = session.scalars(select(SourceScopeGrant).where(SourceScopeGrant.source_id == source_id)).all()
            if revoking:
                assert ('revoke', 200) in outcomes
                assert any(mode == 'approve' and status in {200, 409} for mode, status in outcomes)
                assert session.get(SourceScopeGrant, entries[0][0]).status == 'revoked'
                assert not any(row.status == 'approved' for row in rows)
            else:
                assert outcomes == [('approve', 200), ('approve', 200)]
                assert sorted(row.status for row in rows) == ['approved', 'superseded']
    finally:
        for process in workers:
            if process.is_alive(): process.terminate()
            process.join(5)
        database.engine.dispose()


def amendment_worker(url, source_id, group, record_id, fingerprint, actor, mode, ready, start, results):
    from app.api.output_amendments import review
    from app.output_amendment_schemas import OutputAmendmentReview
    from app.services.output_rights import release
    database = Database(url)
    try:
        with database.Session() as session:
            source = session.get(Source, source_id)  # Deliberately retain the pre-amendment snapshot.
            user = session.get(User, actor)
            ready.put(True)
            assert start.wait(15)
            if mode == 'apply':
                review(group, record_id, OutputAmendmentReview(expected_record_sha256=fingerprint,
                    expected_released_chars=7, decision='apply', confirm_actual_terms_review=True,
                    confirm_counters_preserved=True), user=user, db=session)
            else:
                release(session, [source], 'x')
                session.commit()
            results.put((mode, 200))
    except HTTPException as error:
        results.put((mode, error.detail['code']))
    finally:
        database.engine.dispose()


@pytest.mark.parametrize('releasing', [False, True])
def test_postgres_amendment_serializes_usage_and_terms_without_reset(pg_url, releasing):
    from app.models import OutputBudget, OutputRelease, OutputAmendment, now
    from app.services import output_rights, output_amendments
    from app.output_amendment_schemas import OutputAmendmentSubmission
    database = Database(pg_url)
    author, approver, group = [str(uuid4()) for _ in range(3)]
    with database.Session() as session:
        session.add_all([User(id=author, role='admin'), User(id=approver, role='rights_approver')]);session.commit()
        source=Source(title='Synthetic amendment race',publisher='Test only',text='Fixture',
            enabled=True,reviewed=True,created_by=author,approved_by=approver,
            policy={'basis':'original','commercial_use':True,'quote':True,'output_control':{
                'mode':'bounded','group_id':group,'max_chars_per_response':10,'max_chars_total':10}})
        session.add(source);session.flush();rights.record_approval(source,approver);session.commit()
        output_rights.release(session,[source],'alpha');session.commit()
        state=output_amendments.preview(session,group)
        payload=OutputAmendmentSubmission(expected_limits_sha256=state['limits_sha256'],
            expected_terms_revision=state['terms_revision'],expected_sources_sha256=state['sources_sha256'],
            new_control={'mode':'bounded','group_id':group,'max_chars_per_response':20,'max_chars_total':20},
            evidence_ref='ev_synthetic_amendment',evidence_sha256='c'*64,review_expires_at=now()+3600)
        rows=[output_amendments.submit(session,group,payload,author) for _ in range(2)]
        session.commit()
        source_id=source.id
        records=[(row.id,row.record_sha256) for row in rows]
    ctx=multiprocessing.get_context('spawn')
    ready,start,results=ctx.Queue(),ctx.Event(),ctx.Queue()
    modes=['apply','release' if releasing else 'apply']
    workers=[ctx.Process(target=amendment_worker,args=(pg_url,source_id,group,rid,digest,approver,mode,
             ready,start,results)) for (rid,digest),mode in zip(records,modes)]
    try:
        for process in workers:process.start()
        for _ in workers:assert ready.get(timeout=20)
        start.set()
        outcomes=[results.get(timeout=20) for _ in workers]
        for process in workers:
            process.join(10);assert process.exitcode==0
        with database.Session() as session:
            budget=session.get(OutputBudget,group)
            counted=session.scalar(select(func.sum(OutputRelease.character_count)).where(OutputRelease.group_id==group))
            assert budget.released_chars==counted
            applied=session.scalar(select(func.count()).select_from(OutputAmendment).where(
                OutputAmendment.group_id==group,OutputAmendment.status=='applied'))
            if releasing:
                assert set(outcomes) in ({('apply',200),('release','SOURCE_CHANGED')},
                                        {('apply','REVISION_CONFLICT'),('release',200)})
                assert (budget.released_chars,budget.terms_revision,applied) in {(7,2,1),(10,1,0)}
            else:
                assert sorted(str(result) for _,result in outcomes)==['200','REVISION_CONFLICT']
                assert budget.released_chars==7 and budget.terms_revision==2 and applied==1
    finally:
        start.set()
        for process in workers:
            if process.is_alive():process.terminate()
            process.join(5)
        database.engine.dispose()


def batch_output_worker(url, source_ids, start, results):
    from app.services.output_rights import release_batch
    database=Database(url)
    try:
        with database.Session() as session:
            sources=[session.get(Source,sid) for sid in source_ids]
            assert start.wait(15)
            release_batch(session,[([source],'alpha') for source in sources])
            session.commit();results.put('released')
    finally:
        database.engine.dispose()


def test_postgres_bulk_readers_share_lock_order_despite_opposite_item_order(pg_url):
    from app.models import OutputBudget
    database=Database(pg_url)
    groups=[str(uuid4()),str(uuid4())]
    with database.Session() as session:
        sources=[Source(title='Synthetic bulk item',publisher='Test only',policy={'output_control':{
            'mode':'bounded','group_id':group,'max_chars_per_response':10,'max_chars_total':10}}) for group in groups]
        session.add_all(sources);session.commit();ids=[s.id for s in sources]
    ctx=multiprocessing.get_context('spawn')
    start,results=ctx.Event(),ctx.Queue()
    workers=[ctx.Process(target=batch_output_worker,args=(pg_url,order,start,results)) for order in (ids,ids[::-1])]
    try:
        for process in workers:process.start()
        start.set()
        assert [results.get(timeout=20) for _ in workers]==['released','released']
        for process in workers:
            process.join(10);assert process.exitcode==0
        with database.Session() as session:
            assert [session.get(OutputBudget,group).released_chars for group in groups]==[7,7]
    finally:
        for process in workers:
            if process.is_alive():process.terminate()
            process.join(5)
        database.engine.dispose()


def manual_import_worker(url, directory, work_id, actor, key, start, results):
    from test_source_intake import RAW
    database = Database(url)
    settings = Settings(app_env='test', database_url=url, data_dir=directory, _env_file=None)
    try:
        preflight = intake.manual_preflight(database, work_id, key)
        assert start.wait(15)
        artifact = intake.import_manual(database, settings, work_id, actor, key, RAW, 'application/xml', preflight)
        results.put(artifact['id'])
    finally:
        database.engine.dispose()


@pytest.mark.parametrize('same_key', [True, False])
def test_postgres_manual_imports_register_one_artifact(pg_url, tmp_path, same_key):
    from test_manual_intake import manual_payload
    database = Database(pg_url)
    settings = Settings(app_env='test', database_url=pg_url, data_dir=str(tmp_path), _env_file=None)
    actor, approver = str(uuid4()), str(uuid4())
    with database.Session() as session:
        session.add_all([User(id=actor, role='admin'), User(id=approver, role='rights_approver')]); session.commit()
        body = manual_payload(work_id=str(uuid4()))
        work = intake.register(session, settings, IntakeCreate.model_validate(body), actor)
        source = session.get(Source, work.source_id)
        source.reviewed, source.approved_by = True, approver
        rights.record_approval(source, approver)
        session.commit()
        work_id = work.id
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=manual_import_worker, args=(pg_url, str(tmp_path), work_id, actor,
        'same' if same_key else str(index), start, results)) for index in range(2)]
    try:
        for process in workers: process.start()
        start.set()
        assert results.get(timeout=25) == results.get(timeout=25)
        for process in workers:
            process.join(15); assert process.exitcode == 0
        with database.Session() as session:
            assert session.scalar(select(func.count()).select_from(SourceArtifact).where(SourceArtifact.work_id == work_id)) == 1
            assert session.scalar(select(func.count()).select_from(IntakeAttempt).where(IntakeAttempt.work_id == work_id)) == (1 if same_key else 2)
    finally:
        for process in workers:
            if process.pid:
                if process.is_alive(): process.terminate()
                process.join(5)
        database.engine.dispose()


def discovery_worker(url, directory, artifact_id, actor, start, results):
    from app.services import discovery
    database = Database(url)
    settings = Settings(app_env='test', database_url=url, data_dir=directory, _env_file=None)
    try:
        assert start.wait(15)
        with database.Session() as db:
            results.put(discovery.discover(db, settings, artifact_id, actor)['id'])
    finally:
        database.engine.dispose()


def test_postgres_discovery_concurrency_keeps_one_snapshot(pg_url, tmp_path):
    from test_manual_intake import manual_payload
    from test_source_discovery import RAW, BASE
    from app.sec_core.core import digest
    from app.models import SourceDiscovery
    database = Database(pg_url)
    settings = Settings(app_env='test', database_url=pg_url, data_dir=str(tmp_path), _env_file=None)
    actor, approver = str(uuid4()), str(uuid4())
    with database.Session() as db:
        db.add_all([User(id=actor, role='admin'), User(id=approver, role='rights_approver')]); db.commit()
        body = manual_payload(work_id=str(uuid4()), requested_url=BASE, allowed_mime=['text/html'], parser='structural_html')
        body['source']['canonical_url'] = BASE
        body['manifest']['manual_delivery'].update(raw_sha256=digest(RAW), byte_count=len(RAW), mime='text/html')
        work = intake.register(db, settings, IntakeCreate.model_validate(body), actor)
        source = db.get(Source, work.source_id)
        source.reviewed, source.approved_by = True, approver
        rights.record_approval(source, approver); db.commit()
        work_id = work.id
    preflight = intake.manual_preflight(database, work_id, 'synthetic-index')
    artifact = intake.import_manual(database, settings, work_id, actor, 'synthetic-index', RAW, 'text/html', preflight)
    ctx = multiprocessing.get_context('spawn')
    start, results = ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=discovery_worker, args=(pg_url, str(tmp_path), artifact['id'], actor, start, results)) for _ in range(2)]
    try:
        for process in workers: process.start()
        start.set()
        assert results.get(timeout=25) == results.get(timeout=25)
        for process in workers:
            process.join(15); assert process.exitcode == 0
        with database.Session() as db:
            assert db.scalar(select(func.count()).select_from(SourceDiscovery).where(SourceDiscovery.artifact_id == artifact['id'])) == 1
    finally:
        for process in workers:
            if process.pid:
                if process.is_alive(): process.terminate()
                process.join(5)
        database.engine.dispose()
