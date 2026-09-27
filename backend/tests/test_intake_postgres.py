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


@pytest.fixture
def pg_url():
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
