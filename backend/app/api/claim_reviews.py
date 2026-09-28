"""Private workspace claim review, separately gated from paid inference."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from ..auth import current_user, fresh_user, session
from ..claim_review_schemas import ClaimDecision
from ..models import RunClaimReview
from ..services import claim_reviews
from ..sec_core.core import canonical, digest
from .common import get_run
from .library import require_editor

router = APIRouter(tags=['claim review'])


@router.get('/runs/{run_id}/claims/{claim_id}/review-packet/export')
def export_packet(run_id: str, claim_id: str,
                  expected_revision: str = Query(pattern=r'^[a-f0-9]{64}$'),
                  expected_sequence: int = Query(ge=0),
                  user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id)
    result = claim_reviews.packet(db, run, claim_id, export_revision=expected_revision,
                                 export_sequence=expected_sequence)
    content = canonical(result)
    db.commit()
    return Response(content, media_type='application/json', headers={
        'Content-Disposition': f'attachment; filename="claim-review-{digest(content)[:16]}.json"',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/runs/{run_id}/claims/{claim_id}/review-packet')
def packet(run_id: str, claim_id: str, user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id)
    result = claim_reviews.packet(db, run, claim_id)
    db.commit()
    return result


@router.get('/runs/{run_id}/claims/{claim_id}/reviews')
def history(run_id: str, claim_id: str, before: int = Query(2147483647, ge=1),
            user=Depends(current_user), db=Depends(session)):
    run = get_run(db, user, run_id)
    rows = db.scalars(select(RunClaimReview).where(RunClaimReview.run_id == run.id,
        RunClaimReview.claim_id == claim_id, RunClaimReview.sequence < before)
        .order_by(RunClaimReview.sequence.desc()).limit(51)).all()
    # No historical findings/body text: stale rights cannot leak past excerpts.
    return {'status': claim_reviews.summary(db, run, claim_id),
        'items': [{'id': r.id, 'sequence': r.sequence, 'revision': r.revision,
                   'created_at': r.created_at, 'integrity_valid': claim_reviews.valid_record(db, r)} for r in rows[:50]],
        'next_before': rows[49].sequence if len(rows) > 50 else None}


@router.post('/runs/{run_id}/claims/{claim_id}/reviews', status_code=201)
def record(run_id: str, claim_id: str, payload: ClaimDecision,
           user=Depends(fresh_user), db=Depends(session)):
    run = get_run(db, user, run_id, 'review')
    require_editor(user)
    result = claim_reviews.decide(db, run, claim_id, payload, user.id)
    db.commit()
    return result
