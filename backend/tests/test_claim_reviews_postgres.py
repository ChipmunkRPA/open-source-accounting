"""Two actual PostgreSQL sessions; synthetic unresolved assessment only."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import os
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.evaluation.postgres import isolated_postgres
from app.models import User, Workspace, Membership, Run, RunClaimReview, now
from app.services import claim_reviews
from app.claim_review_schemas import ClaimDecision


def test_postgres_claim_sequence_serializes_reviewers():
    value = os.environ.get('OSA_EVALUATION_POSTGRES_URL')
    if not value:pytest.skip('Dedicated empty local PostgreSQL evaluation DB not supplied')
    with isolated_postgres(value) as (factory, _):
        with factory(0) as database:
            with database.Session() as db:
                db.add_all([User(id='owner'), User(id='reviewer', role='technical_reviewer')]);db.flush()
                db.add(Workspace(id='workspace', name='Synthetic', owner_id='owner'));db.flush()
                db.add_all([Membership(workspace_id='workspace',user_id='owner',role='owner'),
                            Membership(workspace_id='workspace',user_id='reviewer',role='reviewer')])
                run=Run(id='run',workspace_id='workspace',user_id='owner',workflow='deep_research',
                    question='Synthetic missing evidence',state='completed_with_limitations',
                    result={'claims':[{'id':'claim','text':'Synthetic unresolved claim.', 'basis':'inference','evidence_ids':[]}]})
                db.add(run);db.commit()
                revision=claim_reviews.binding(db,run,'claim')[1]
            payload=ClaimDecision(expected_revision=revision,expected_sequence=0,decision='unresolved',
                review_note='Synthetic unresolved assessment only; no professional review.',
                competence_scope='Synthetic role and competence attestation for concurrency test.',
                evidence_ref='ev_synthetic',evidence_sha256='a'*64,expires_at=now()+3600,
                confirm_actual_review_performed=True,confirm_competence_and_independence=True)
            start=Barrier(2)
            def submit():
                with database.Session() as db:
                    run=db.get(Run,'run');start.wait(timeout=10)
                    try:
                        result=claim_reviews.decide(db,run,'claim',payload,'reviewer');db.commit()
                        return result['sequence']
                    except HTTPException as exc:
                        db.rollback();return exc.detail['code']
            with ThreadPoolExecutor(max_workers=2) as executor:
                results=list(executor.map(lambda _:submit(),range(2)))
            assert sorted(map(str,results))==['1','REVISION_CONFLICT']
            with database.Session() as db:
                assert len(db.scalars(select(RunClaimReview)).all())==1
