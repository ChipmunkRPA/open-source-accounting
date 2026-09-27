"""Durable database-backed worker. Run separately from the API; supports --once for Cloud Run Jobs."""
import argparse
import time
from sqlalchemy import select, or_, and_, update
from .config import Settings
from .db import Database
from .models import Job, Run, uid, now
from .agents.orchestrator import execute, emit
from .services.entitlements import settle


def claim(db_factory, config):
    with db_factory() as db:
        timestamp = now()
        eligible = or_(Job.state == 'queued', and_(Job.state == 'running', Job.lease_until < timestamp))
        job = db.scalar(select(Job).where(eligible, Job.available_at <= timestamp)
                        .order_by(Job.created_at).with_for_update(skip_locked=True).limit(1))
        if not job:
            return None
        if job.attempts >= config.max_job_attempts:
            run = db.get(Run, job.run_id)
            emit(db, run, 'failed', error_code='WORKER_RETRIES_EXHAUSTED')
            run.error_code = 'WORKER_RETRIES_EXHAUSTED'
            settle(db, run, False)
            job.state = 'done'
            db.commit()
            return None
        owner = uid()
        # Conditional update is also a compare-and-swap for SQLite's local mode.
        accepted = db.execute(update(Job).where(Job.id == job.id, eligible).values(
            state='running', lease_owner=owner, lease_until=timestamp+config.worker_lease_seconds,
            attempts=Job.attempts+1))
        if accepted.rowcount != 1:
            db.rollback()
            return None
        job_id = job.id
        db.commit()
        return job_id, owner


def tick(database, settings):
    next_job = claim(database.Session, settings)
    if next_job:
        execute(database.Session, *next_job, settings)
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='Drain currently available jobs and exit.')
    args = parser.parse_args()
    config = Settings()
    database = Database(config.database_url)
    if config.auto_create_schema:
        database.create_all()
    from .services.watches import check_watches
    while True:
        did_work = tick(database, config)
        if not did_work:
            with database.Session() as db:
                check_watches(db, config)
            if args.once:
                break
            time.sleep(config.worker_poll_seconds)


if __name__ == '__main__':
    main()
