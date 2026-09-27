from fastapi import APIRouter, Depends
from sqlalchemy import update
from ..auth import current_user, fresh_user, session
from ..errors import fail
from ..models import ModelBudget, now
from ..model_budget_schemas import BudgetAuthorization, BudgetRevocation, BudgetView
from ..services import model_budgets as budgets

router = APIRouter(tags=['model-operations'])


def admin(user):
    if user.role != 'admin':
        fail('FORBIDDEN', 'Spending authorization requires an operations administrator.', 403)


@router.post('/admin/model-budgets', status_code=201, response_model=BudgetView)
def authorize(payload: BudgetAuthorization, user=Depends(fresh_user), db=Depends(session)):
    admin(user)
    row = budgets.authorize(db, payload, user.id)
    db.commit()
    return budgets.serialize(row)


@router.get('/admin/model-budgets/{budget_id}', response_model=BudgetView)
def read(budget_id: str, user=Depends(current_user), db=Depends(session)):
    admin(user)
    row = db.get(ModelBudget, budget_id)
    if not row:
        fail('NOT_FOUND', 'Budget not found.', 404)
    return budgets.serialize(row)


@router.post('/admin/model-budgets/{budget_id}/revoke', response_model=BudgetView)
def revoke(budget_id: str, payload: BudgetRevocation, user=Depends(fresh_user), db=Depends(session)):
    admin(user)
    changed = db.execute(update(ModelBudget).where(ModelBudget.id == budget_id,
        ModelBudget.terms_sha256 == payload.expected_terms_sha256).values(active=False, revoked_at=now()))
    if changed.rowcount != 1:
        fail('BUDGET_CONFLICT', 'Reload the exact budget before revocation.', 409)
    db.commit()
    return budgets.serialize(db.get(ModelBudget, budget_id))
