"""Paid access, subscription-anniversary usage windows, and durable task reservations."""
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func
from ..models import Subscription, UsageWindow, Run, now
from ..auth import lock_user
from ..errors import fail


ACTIVE_STATES = {'queued', 'planning', 'retrieving', 'analyzing', 'verifying'}
TERMINAL_STATES = {'completed', 'completed_with_limitations', 'failed', 'cancelled', 'blocked'}


def access(subscription, config, timestamp=None):
    t = now() if timestamp is None else timestamp
    if not subscription:
        return {'state': 'FREE', 'agent_allowed': False, 'access_until': None}
    if subscription.revoked or subscription.status in {'unpaid', 'paused', 'incomplete_expired'}:
        return {'state': 'SUSPENDED', 'agent_allowed': False, 'access_until': None}
    if subscription.paid_until > t:
        state = 'ENDING' if subscription.cancel_at_period_end else 'ACTIVE'
        return {'state': state, 'agent_allowed': True, 'access_until': subscription.paid_until}
    grace_end = subscription.paid_until + config.renewal_grace_days * 86400
    if (subscription.paid_until and subscription.renewal_failed and
        not subscription.cancel_at_period_end and subscription.status == 'past_due' and
        t < grace_end):
        return {'state': 'RENEWAL_GRACE', 'agent_allowed': True, 'access_until': grace_end}
    return {'state': 'EXPIRED' if subscription.paid_until else 'FREE',
            'agent_allowed': False, 'access_until': None}


def require_agent(db, user, config):
    result = access(db.get(Subscription, user.id), config)
    if not result['agent_allowed']:
        fail('SUBSCRIPTION_REQUIRED', 'This Agent action requires the USD 89.99 annual subscription.',
             402, upgrade_path='/pricing')
    return result


def cycle(subscription, timestamp=None):
    """Monthly allowances anchored to original term start, without end-of-month drift."""
    t = now() if timestamp is None else timestamp
    anchor = datetime.fromtimestamp(subscription.term_start or t, timezone.utc)
    point = datetime.fromtimestamp(t, timezone.utc)
    months = max(0, (point.year - anchor.year) * 12 + point.month - anchor.month)
    start = anchor + relativedelta(months=months)
    if start > point:
        months -= 1
        start = anchor + relativedelta(months=months)
    end = anchor + relativedelta(months=months + 1)
    return int(start.timestamp()), int(end.timestamp())


def usage_snapshot(db, user, config):
    sub = db.get(Subscription, user.id)
    if not sub or not sub.term_start:
        return {'limit': config.agent_tasks_per_month, 'consumed': 0, 'reserved': 0,
                'reset_at': None, 'proposed_policy': not config.billing_terms_approved}
    start, end = cycle(sub)
    row = db.get(UsageWindow, (user.id, start))
    return {'limit': config.agent_tasks_per_month, 'consumed': row.consumed if row else 0,
            'reserved': row.reserved if row else 0, 'reset_at': end,
            'proposed_policy': not config.billing_terms_approved}


def reserve(db, user, run, config):
    """Caller transaction includes run admission + job insertion; commit together."""
    lock_user(db, user.id)
    require_agent(db, user, config)
    if run.usage_status in {'reserved', 'consumed'}:
        return
    active = db.scalar(select(func.count()).select_from(Run).where(
        Run.user_id == user.id, Run.state.in_(ACTIVE_STATES), Run.id != run.id))
    if active >= config.agent_concurrency:
        fail('CONCURRENCY_LIMIT', 'Wait for an active task to finish or cancel it.', 429)
    sub = db.get(Subscription, user.id)
    start, end = cycle(sub)
    row = db.get(UsageWindow, (user.id, start))
    if not row:
        row = UsageWindow(user_id=user.id, start_at=start, end_at=end, consumed=0, reserved=0)
        db.add(row)
    if row.consumed + row.reserved >= config.agent_tasks_per_month:
        fail('TASK_LIMIT', 'Your Agent allowance is used. General chat remains free.',
             429, reset_at=end)
    row.reserved += 1
    run.usage_start = start
    run.usage_status = 'reserved'


def settle(db, run, released):
    if run.usage_status != 'reserved' or run.usage_start is None:
        return
    lock_user(db, run.user_id)
    row = db.get(UsageWindow, (run.user_id, run.usage_start))
    if row:
        row.reserved = max(0, row.reserved - 1)
        if released:
            row.consumed += 1
    run.usage_status = 'consumed' if released else 'released'
