"""Restricted, non-content estimates. Never an invoice, billing plan or spend approval."""
from fastapi import APIRouter, Depends, Query, Request
from ..auth import current_user
from ..errors import fail
from ..services.model_attempts import report_snapshot
from ..model_usage_schemas import ModelUsageReport

router = APIRouter(tags=['model-operations'])


@router.get('/admin/model-usage', response_model=ModelUsageReport)
def model_usage(request: Request, start_at: int = Query(ge=0), end_at: int = Query(gt=0),
                user=Depends(current_user)):
    if user.role != 'admin':
        fail('FORBIDDEN', 'Model cost reports require an operations administrator.', 403)
    if not 0 < end_at-start_at <= 31*86400:
        fail('INVALID_REPORT_WINDOW', 'Choose a positive report window of at most 31 days.', 422)
    return report_snapshot(request.app.state.db, start_at=start_at, end_at=end_at)
