from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from pydantic import Field
from typing import Literal
from ..schemas import Strict
from ..auth import fresh_user, current_user, session, lock_user
from ..models import Subscription, Audit, now
from ..errors import fail
from ..services.billing import StripeAPI, checkout, verify_signature, process_event, reconcile
from ..services.entitlements import access
from ..services.idempotency import begin

router = APIRouter(tags=['billing'])


class CheckoutRequest(Strict):
    accepted_annual_terms: Literal[True]


class DemoRequest(Strict):
    state: Literal['free', 'active', 'ending', 'expired', 'past_due']


@router.post('/billing/checkout')
def begin_checkout(payload: CheckoutRequest, request: Request, idempotency_key: str = Header(default=''),
                   user=Depends(fresh_user), db=Depends(session)):
    lock_user(db, user.id)
    record, repeat = begin(db, user.id, 'billing.checkout', idempotency_key, payload.model_dump())
    if repeat and record.response:
        return record.response
    result = checkout(db, user, request.app.state.settings, idempotency_key)
    record.response = result
    db.add(Audit(actor_id=user.id, action='checkout.terms_accepted', target_id=result['session_id'],
                 detail={'price_cents': 8999, 'currency': 'usd', 'interval': 'year'}))
    db.commit()
    return result


@router.post('/billing/portal')
def portal(request: Request, user=Depends(fresh_user), db=Depends(session)):
    if not user.stripe_customer_id:
        fail('NO_BILLING_ACCOUNT', 'There is no Stripe customer account yet.', 409)
    result = StripeAPI(request.app.state.settings).request('POST', 'billing_portal/sessions',
                {'customer': user.stripe_customer_id, 'return_url': request.app.state.settings.app_origin+'/billing'})
    return {'url': result['url']}


@router.post('/billing/sync')
def sync(request: Request, user=Depends(current_user), db=Depends(session)):
    config = request.app.state.settings
    sub = db.get(Subscription, user.id)
    api = StripeAPI(config)
    if sub and sub.provider_id:
        reconcile(db, user, sub.provider_id, config, api)
    elif user.stripe_customer_id:
        rows = api.request('GET', 'subscriptions', {'customer': user.stripe_customer_id, 'status': 'all', 'limit': 20})
        matching = [s for s in rows.get('data', []) if any(i.get('price', {}).get('id') == config.stripe_price_id
                    for i in s.get('items', {}).get('data', []))]
        if matching:
            reconcile(db, user, matching[0]['id'], config, api)
    db.commit()
    return access(db.get(Subscription, user.id), config)


@router.post('/billing/cancel-renewal')
def cancel_renewal(request: Request, user=Depends(fresh_user), db=Depends(session)):
    return change_renewal(True, request, user, db)


@router.post('/billing/resume-renewal')
def resume_renewal(request: Request, user=Depends(fresh_user), db=Depends(session)):
    return change_renewal(False, request, user, db)


def change_renewal(cancel, request, user, db):
    config = request.app.state.settings
    record = db.get(Subscription, user.id)
    if not record or not access(record, config)['agent_allowed']:
        fail('NO_ACTIVE_SUBSCRIPTION', 'There is no active subscription to update.', 409)
    if config.demo_billing_enabled and config.app_env in {'local', 'test'} and (record.provider_id or '').startswith('demo_'):
        record.cancel_at_period_end = cancel
    else:
        api = StripeAPI(config)
        api.request('POST', 'subscriptions/'+record.provider_id, {'cancel_at_period_end': str(cancel).lower()})
        reconcile(db, user, record.provider_id, config, api)
    db.add(Audit(actor_id=user.id, action='billing.renewal_changed', target_id=user.id, detail={'cancel': cancel}))
    db.commit()
    return access(record, config)


@router.post('/billing/webhook')
async def stripe_webhook(request: Request, stripe_signature: str = Header(default=''), db=Depends(session)):
    config = request.app.state.settings
    # Route accepts only provider-signed events, never browser-authenticated plan changes.
    if not config.billing_enabled:
        fail('BILLING_DISABLED', 'Billing webhooks are disabled.', 503)
    event = verify_signature(await request.body(), stripe_signature, config.stripe_webhook_secret)
    return process_event(db, event, config)


@router.post('/dev/subscription')
def demo_subscription(payload: DemoRequest, request: Request, user=Depends(current_user), db=Depends(session)):
    config = request.app.state.settings
    if config.app_env not in {'local', 'test'} or not config.demo_billing_enabled or config.model_provider != 'mock':
        fail('NOT_FOUND', 'Not found.', 404)
    record = db.get(Subscription, user.id)
    if not record:
        record = Subscription(user_id=user.id)
        db.add(record)
    record.provider_id = 'demo_'+user.id
    record.term_start = now()
    record.paid_until = int((datetime.now(timezone.utc)+relativedelta(years=1)).timestamp())
    record.cancel_at_period_end = payload.state == 'ending'
    record.status, record.revoked, record.renewal_failed = 'active', False, False
    if payload.state == 'free':
        record.paid_until, record.term_start, record.status = 0, 0, 'free'
    elif payload.state in {'expired', 'past_due'}:
        record.paid_until, record.term_start = now()-1, now()-366*86400
        record.status = 'past_due' if payload.state == 'past_due' else 'canceled'
        record.renewal_failed = payload.state == 'past_due'
    db.commit()
    return {'demo_only': True, 'charged': False, **access(record, config)}
