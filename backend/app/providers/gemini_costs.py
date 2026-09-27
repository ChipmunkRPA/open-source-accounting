"""Offline, dated standard-rate estimate; not a bill, spend guard or approved allowance.

No cached-input discount is assumed. Include every successful HTTP response, even
if schema/review/task processing subsequently failed. See docs/GEMINI_CONTRACT.md.
"""
from datetime import date
from decimal import Decimal
from .gemini_contract import MODEL_ID, HOSTS, usage_counts

CATALOG_VERSION = 'google-cloud-gemini-3.8-flash-standard-2026-09-27'
OBSERVED_ON = date(2026, 9, 27)
PRICE_CHANGE = date(2027, 1, 1)
SOURCE_URL = 'https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing'


def estimate_usd(usage: dict, *, location: str, incurred_on: date,
                 provider: str = 'google_cloud', model: str = MODEL_ID) -> dict:
    if provider != 'google_cloud' or model != MODEL_ID or location not in HOSTS:
        raise ValueError('No price for this provider/model/location.')
    if type(incurred_on) is not date or incurred_on < OBSERVED_ON:
        raise ValueError('No historical price verified before the observation date.')
    counts = usage_counts(usage)
    if counts['toolUsePromptTokenCount']:
        raise ValueError('Tool billing is outside this text-only estimate.')
    later = incurred_on >= PRICE_CHANGE
    input_rate, output_rate = (('1.50', '7.50') if later else ('0.75', '3.75'))
    multiplier = Decimal('1') if location == 'global' else Decimal('1.1')
    input_rate, output_rate = Decimal(input_rate) * multiplier, Decimal(output_rate) * multiplier
    output_tokens = counts['candidatesTokenCount'] + counts['thoughtsTokenCount']
    amount = (counts['promptTokenCount'] * input_rate + output_tokens * output_rate) / Decimal(1000000)
    return {
        'catalog_version': CATALOG_VERSION, 'source_url': SOURCE_URL,
        'observed_on': OBSERVED_ON.isoformat(), 'incurred_on': incurred_on.isoformat(),
        'provider': provider, 'model': model, 'location': location, 'currency': 'USD',
        'basis': 'standard_text_no_cached_discount_estimate',
        'input_usd_per_million': str(input_rate), 'output_usd_per_million': str(output_rate),
        'input_tokens': counts['promptTokenCount'], 'output_and_thinking_tokens': output_tokens,
        'estimated_usd': format(amount, 'f'),
    }
