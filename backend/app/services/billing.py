"""Stripe REST integration with signed webhooks and canonical reconciliation.

No client-supplied plan grants access. No use of a successful redirect as proof of
payment. Live execution requires an approved terms policy and explicit API version.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import quote
import httpx
from sqlalchemy import select
from ..models import User, Subscription, BillingEvent, Audit, now
from ..errors import fail, ProviderError
from ..auth import lock_user
from .entitlements import access


class StripeAPI:
    def __init__(self, config, transport=None):
        self.config, self.transport = config, transport

    def request(self, method, path, data=None, key=None):
        if not self.config.billing_enabled:
            fail('BILLING_DISABLED', 'Live billing is not enabled.', 503)
        headers = {'Authorization': f'Bearer {self.config.stripe_secret_key}',
                   'Stripe-Version': self.config.stripe_api_version}
        if key:
            headers['Idempotency-Key'] = key
        try:
            if self.transport:
                return self.transport(method, path, data or {}, headers)
            with httpx.Client(timeout=25, follow_redirects=False, trust_env=False) as client:
                response = client.request(method, 'https://api.stripe.com/v1/' + path,
                    headers=headers, params=data if method == 'GET' else None,
                    data=data if method != 'GET' else None)
                response.raise_for_status()
                return response.json()
        except Exception:
            raise ProviderError('BILLING_PROVIDER_FAILURE') from None


def validate_price(price, expected_id, require_active=True):
    recurring = price.get('recurring') or {}
    if not (price.get('id') == expected_id and (not require_active or price.get('active') is True) and
            price.get('unit_amount') == 8999 and price.get('currency') == 'usd' and
            recurring.get('interval') == 'year' and recurring.get('interval_count') == 1 and
            recurring.get('usage_type', 'licensed') == 'licensed'):
        fail('PRICE_MISMATCH', 'The configured product is not the approved USD 89.99 annual plan.', 503)


def checkout(db, user, config, key, stripe=None):
    if not config.billing_terms_approved:
        fail('TERMS_NOT_APPROVED', 'Checkout is unavailable until the operator approves and publishes the purchase terms.', 503)
    stripe = stripe or StripeAPI(config)
    lock_user(db, user.id)
    if access(db.get(Subscription, user.id), config)['agent_allowed']:
        fail('ALREADY_SUBSCRIBED', 'Manage your existing subscription in Billing.', 409)
    price = stripe.request('GET', f'prices/{quote(config.stripe_price_id, safe="")}')
    validate_price(price, config.stripe_price_id)
    if not user.stripe_customer_id:
        customer = stripe.request('POST', 'customers', {'email': user.email, 'metadata[app_user_id]': user.id},
                                  key='customer-' + user.id)
        user.stripe_customer_id = customer['id']
        db.flush()
    existing = stripe.request('GET', 'subscriptions', {'customer': user.stripe_customer_id, 'status': 'all', 'limit': 100})
    if any(x.get('status') in {'active', 'trialing', 'past_due', 'incomplete'} and
           any((i.get('price') or {}).get('id') == config.stripe_price_id for i in x.get('items', {}).get('data', []))
           for x in existing.get('data', [])):
        fail('EXISTING_SUBSCRIPTION', 'An existing or pending subscription must be reconciled before another checkout.', 409)
    checkout_session = stripe.request('POST', 'checkout/sessions', {
        'mode': 'subscription', 'customer': user.stripe_customer_id,
        'client_reference_id': user.id, 'line_items[0][price]': config.stripe_price_id,
        'line_items[0][quantity]': '1', 'allow_promotion_codes': 'false',
        'subscription_data[metadata][app_user_id]': user.id,
        'metadata[app_user_id]': user.id,
        'success_url': config.app_origin + '/billing?checkout=returned',
        'cancel_url': config.app_origin + '/pricing?checkout=cancelled',
        'billing_address_collection': 'required',
    }, key='checkout-' + user.id + '-' + key)
    return {'url': checkout_session['url'], 'session_id': checkout_session['id']}


def verify_signature(body: bytes, signature: str, secret: str, timestamp=None):
    if not secret or len(body) > 1024 * 1024:
        fail('WEBHOOK_INVALID', 'Invalid webhook.', 400)
    values = {}
    for part in signature.split(','):
        k, _, v = part.partition('=')
        values.setdefault(k, []).append(v)
    try:
        signed_at = int(values['t'][0])
    except (KeyError, ValueError):
        fail('WEBHOOK_SIGNATURE', 'Invalid webhook signature.', 400)
    if abs((int(time.time()) if timestamp is None else timestamp) - signed_at) > 300:
        fail('WEBHOOK_EXPIRED', 'Webhook timestamp is outside the acceptance window.', 400)
    wanted = hmac.new(secret.encode(), str(signed_at).encode() + b'.' + body, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(wanted, v) for v in values.get('v1', [])):
        fail('WEBHOOK_SIGNATURE', 'Invalid webhook signature.', 400)
    try:
        event = json.loads(body)
        if not isinstance(event.get('id'), str) or not isinstance(event.get('type'), str):
            raise ValueError()
        return event
    except (ValueError, AttributeError):
        fail('WEBHOOK_INVALID', 'Invalid event envelope.', 400)


def object_id(obj):
    return obj.get('id') if isinstance(obj, dict) else obj


def invoice_subscription(invoice):
    return object_id(invoice.get('subscription') or
                     ((invoice.get('parent') or {}).get('subscription_details') or {}).get('subscription'))


def paid_period(invoice, subscription_id, price_id):
    """Only a matching, settled recurring invoice can extend paid access.

    Unknown API shapes fail closed. Trial, zero-dollar, manual out-of-band payment,
    discounts, and migration exceptions require a separately reviewed policy.
    """
    if invoice.get('status') != 'paid' or invoice.get('amount_paid', 0) < 8999:
        return None
    if invoice.get('currency') != 'usd' or invoice_subscription(invoice) != subscription_id:
        return None
    if invoice.get('paid_out_of_band'):
        return None
    items = invoice.get('lines', {})
    if items.get('has_more'):
        return None  # This single-seat offer should not require truncated-line inference.
    periods = []
    for line in items.get('data', []):
        p = object_id(line.get('price') or ((line.get('pricing') or {}).get('price_details') or {}).get('price'))
        period = line.get('period') or {}
        if p == price_id and line.get('quantity', 1) == 1 and line.get('amount', 0) >= 8999:
            start, end = period.get('start', 0), period.get('end', 0)
            if start and 300 * 86400 <= end - start <= 370 * 86400:
                periods.append((start, end))
    return max(periods, key=lambda x: x[1]) if periods else None


def reconcile(db, user, subscription_id, config, stripe=None):
    """Lock the account, then retrieve canonical provider state—not event-order state."""
    stripe = stripe or StripeAPI(config)
    lock_user(db, user.id)
    data = stripe.request('GET', f'subscriptions/{quote(subscription_id, safe="")}', {'expand[]': 'latest_invoice'})
    if object_id(data.get('customer')) != user.stripe_customer_id:
        fail('BILLING_OWNERSHIP', 'Subscription ownership mismatch.', 403)
    items = data.get('items', {}).get('data', [])
    if len(items) != 1 or items[0].get('quantity', 1) != 1:
        fail('PRICE_MISMATCH', 'Unexpected subscription items.', 409)
    validate_price(items[0].get('price', {}), config.stripe_price_id, require_active=False)
    record = db.get(Subscription, user.id)
    if not record:
        record = Subscription(user_id=user.id, provider_id=subscription_id, paid_until=0, term_start=0)
        db.add(record)
    elif record.provider_id and record.provider_id != subscription_id and record.paid_until > now():
        fail('DUPLICATE_SUBSCRIPTION', 'A different paid subscription is already attached to this account.', 409)
    record.provider_id = subscription_id
    record.status = data.get('status', 'unknown')
    record.cancel_at_period_end = bool(data.get('cancel_at_period_end'))
    record.renewal_failed = record.status == 'past_due'
    invoice = data.get('latest_invoice')
    if isinstance(invoice, str):
        invoice = stripe.request('GET', f'invoices/{quote(invoice, safe="")}')
    period = paid_period(invoice or {}, subscription_id, config.stripe_price_id)
    if period and period[1] >= record.paid_until:
        if not record.term_start:
            record.term_start = period[0]
        record.paid_until = period[1]
        record.last_invoice_id = invoice['id']
        record.renewal_failed = False
    # Pause, unpaid, or immediate cancellation cannot extend access.
    if data.get('pause_collection'):
        record.status = 'paused'
    # Transient billing status is separate from hard risk revocation. Recovery
    # to active may restore paid access; refunds/disputes remain revoked.
    if record.status == 'canceled' and not data.get('cancel_at_period_end'):
        record.paid_until = min(record.paid_until, int(data.get('ended_at') or now()))
    record.last_reconciled = now()
    return record


def process_event(db, event, config, stripe=None):
    existing = db.get(BillingEvent, event['id'])
    if existing and existing.status == 'processed':
        return {'received': True, 'duplicate': True}
    obj = (event.get('data') or {}).get('object') or {}
    if not existing:
        existing = BillingEvent(id=event['id'], event_type=event['type'], object_id=obj.get('id', ''))
        db.add(existing)
        db.flush()
    customer = object_id(obj.get('customer'))
    subscription_id = None
    kind = event['type']
    if kind.startswith('customer.subscription.'):
        subscription_id = obj.get('id')
    elif kind.startswith('invoice.'):
        subscription_id = invoice_subscription(obj)
    elif kind.startswith('checkout.session.'):
        subscription_id = object_id(obj.get('subscription'))
    user = db.scalar(select(User).where(User.stripe_customer_id == customer)) if customer else None
    if user and subscription_id:
        reconcile(db, user, subscription_id, config, stripe)
    elif kind in {'charge.refunded', 'charge.dispute.created'}:
        # Resolve dispute charge by canonical fetch. Restrict revocation to current paid invoice.
        api = stripe or StripeAPI(config)
        charge = obj if kind == 'charge.refunded' else api.request('GET', f'charges/{quote(object_id(obj.get("charge")) or "", safe="")}')
        customer = object_id(charge.get('customer'))
        user = db.scalar(select(User).where(User.stripe_customer_id == customer)) if customer else None
        record = db.get(Subscription, user.id) if user else None
        if record and object_id(charge.get('invoice')) == record.last_invoice_id and (
                kind == 'charge.dispute.created' or charge.get('refunded') is True):
            record.revoked = True
            db.add(Audit(actor_id='stripe', action='billing.coverage_revoked', target_id=user.id,
                         detail={'event_id': event['id']}))
    existing.status = 'processed'
    db.add(Audit(actor_id='stripe', action='webhook.processed', target_id=event['id'],
                 detail={'event_type': kind}))
    db.commit()
    return {'received': True, 'duplicate': False}
