from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from ..auth import current_user, session, workspace_access, verified_identity
from ..schemas import Preferences, FeedbackCreate
from ..models import Subscription, Workspace, Membership, Feedback, Notification
from ..services.entitlements import access, usage_snapshot
from ..agents.catalog import public_catalog
from .common import get_run

router = APIRouter()


@router.get('/health', tags=['system'])
def health():
    return {'status': 'ok', 'version': '0.6.0'}


@router.get('/config', tags=['system'])
def public_config(request: Request):
    s = request.app.state.settings
    return {'app_env': s.app_env, 'auth_mode': s.auth_mode, 'model_provider': s.model_provider,
            'model_id': s.model_id, 'firebase_api_key': s.firebase_api_key,
            'firebase_project_id': s.firebase_project_id, 'firebase_auth_domain': s.firebase_auth_domain,
            'firebase_tenant_id': s.firebase_tenant_id, 'mfa_required': s.auth_mode == 'firebase',
            'mfa_methods': ['totp', 'phone'], 'auth_recent_seconds': s.auth_recent_seconds, 'billing_enabled': s.billing_enabled,
            'demo_billing_enabled': s.demo_billing_enabled, 'billing_terms_approved': s.billing_terms_approved,
            'annual_price_cents': 8999, 'currency': 'usd', 'interval': 'year',
            'agent_tasks_per_month': s.agent_tasks_per_month, 'max_upload_mb': s.max_upload_mb,
            'experimental_agents_enabled': s.enable_experimental_agents}


@router.get('/me', tags=['account'])
def me(request: Request, user=Depends(current_user), db=Depends(session)):
    s = request.app.state.settings
    sub = db.get(Subscription, user.id)
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role,
            'security': {'mode': request.state.identity.mode, 'mfa_verified': request.state.identity.mfa_verified,
                         'factor': request.state.identity.factor, 'auth_time': request.state.identity.auth_time},
            'preferences': user.preferences, 'access': access(sub, s), 'usage': usage_snapshot(db, user, s),
            'subscription': {'paid_until': sub.paid_until, 'cancel_at_period_end': sub.cancel_at_period_end,
                             'status': sub.status} if sub else None}


@router.put('/me/preferences', tags=['account'])
def preferences(payload: Preferences, user=Depends(current_user), db=Depends(session)):
    user.preferences = payload.model_dump()
    db.commit()
    return user.preferences


@router.get('/agents', tags=['agents'])
def agents(request: Request):
    return {'items': public_catalog(request.app.state.settings)}


@router.post('/feedback', status_code=201, tags=['account'])
def feedback(payload: FeedbackCreate, user=Depends(current_user), db=Depends(session)):
    if payload.run_id:
        get_run(db, user, payload.run_id)
    row = Feedback(user_id=user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    return {'id': row.id, 'status': 'received'}


@router.get('/notifications', tags=['account'])
def notifications(user=Depends(current_user), db=Depends(session)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                       .order_by(Notification.created_at.desc()).limit(100)).all()
    return {'items': [{'id': r.id, 'title': r.title, 'body': r.body, 'read': r.read,
                       'created_at': r.created_at} for r in rows]}


@router.post('/notifications/{notification_id}/read', tags=['account'])
def read_notification(notification_id: str, user=Depends(current_user), db=Depends(session)):
    from ..errors import fail
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user.id:
        fail('NOT_FOUND', 'Notification not found.', 404)
    row.read = True
    db.commit()
    return {'read': True}


@router.get('/auth/status', tags=['authentication'])
def auth_status(identity=Depends(verified_identity)):
    # No account/workspace provisioning here; only an enrollment/sign-in gate.
    return {'mode': identity.mode, 'email_verified': identity.email_verified,
            'mfa_required': identity.mode != 'dev', 'mfa_verified': identity.mfa_verified,
            'methods': ['totp', 'phone'], 'current_factor': identity.factor,
            'next_step': ('verify_email' if not identity.email_verified else
                          'enroll_or_challenge' if identity.mode != 'dev' and not identity.mfa_verified else 'ready')}
