"""Deterministic illustrative math, NOT a complete ASC 606/842 accounting engine."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta

CENT = Decimal('0.01')


def number(value, name, minimum=Decimal('0'), maximum=Decimal('1000000000000')):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{name} must be a decimal number.') from None
    if not n.is_finite() or not minimum <= n <= maximum:
        raise ValueError(f'{name} is outside the supported range.')
    return n


def money(n):
    return str(n.quantize(CENT, rounding=ROUND_HALF_UP))


def allocate_revenue(payload):
    """Relative-SSP arithmetic only; last-cent reconciliation is explicit."""
    price = number(payload['transaction_price'], 'Transaction price')
    items = payload['items']
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ValueError('Supply 1–50 allocation items.')
    weights = [number(x['ssp'], 'Standalone selling price') for x in items]
    total = sum(weights)
    if total <= 0:
        raise ValueError('Total SSP must be positive.')
    rounded = [(price * weight / total).quantize(CENT, rounding=ROUND_HALF_UP) for weight in weights]
    rounded[-1] += price.quantize(CENT, rounding=ROUND_HALF_UP) - sum(rounded)
    rows = [{'name': str(item['name'])[:120], 'ssp': money(weight), 'allocated': money(amount)}
            for item, weight, amount in zip(items, weights, rounded)]
    return {'kind': 'relative_ssp_allocation', 'rows': rows, 'total': money(sum(rounded)),
            'assumption': 'User-confirmed transaction price and SSPs; not a determination of performance obligations or discount exceptions.'}


def lease_schedule(payload):
    """Fixed monthly payments in arrears; nominal annual discount rate / 12.

    Excludes ROU-asset amortization, advance payments, modifications, incentives,
    initial direct costs, variable payments, tax, and lease classification.
    """
    payment = number(payload['monthly_payment'], 'Monthly payment')
    annual = number(payload['annual_discount_rate'], 'Annual discount rate', maximum=Decimal('1'))
    periods = payload['months']
    if isinstance(periods, bool) or not isinstance(periods, int) or not 1 <= periods <= 600:
        raise ValueError('months must be an integer from 1 through 600.')
    first_date = date.fromisoformat(payload['first_payment_date'])
    if payload.get('timing', 'arrears') != 'arrears':
        raise ValueError('Only monthly payments in arrears are implemented.')
    rate = annual / Decimal(12)
    balance = payment * periods if rate == 0 else payment * (1 - (1 + rate) ** -periods) / rate
    opening_pv = balance
    rows = []
    for index in range(periods):
        interest = balance * rate
        opening = balance
        principal = payment - interest
        balance -= principal
        if index == periods - 1 and abs(balance) < Decimal('0.000001'):
            balance = Decimal(0)
        rows.append({'period': index + 1, 'date': (first_date + relativedelta(months=index)).isoformat(),
                     'opening': money(opening), 'payment': money(payment), 'interest': money(interest),
                     'principal': money(principal), 'closing': money(balance)})
    return {'kind': 'fixed_payment_liability_schedule', 'present_value': money(opening_pv), 'rows': rows,
            'assumptions': ['Fixed monthly payments in arrears.', 'Annual nominal rate divided by 12.',
                            'Rate is supplied by the user, not selected by the application.',
                            'No lease classification or ROU-asset accounting conclusion.',
                            'Full precision internally; displayed cents may not sum on every row.']}


def check_journal(entries):
    if not isinstance(entries, list) or not 2 <= len(entries) <= 100:
        raise ValueError('Supply 2–100 journal lines.')
    debit = sum(number(x.get('debit', '0'), 'Debit') for x in entries)
    credit = sum(number(x.get('credit', '0'), 'Credit') for x in entries)
    for x in entries:
        if number(x.get('debit', '0'), 'Debit') and number(x.get('credit', '0'), 'Credit'):
            raise ValueError('A line cannot contain both a debit and a credit.')
    return {'debit': money(debit), 'credit': money(credit),
            'balanced': debit.quantize(CENT) == credit.quantize(CENT), 'difference': money(debit - credit)}
