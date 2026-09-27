"""Reviewed Cloud REST contract. No caller-controlled hosts or model substitution."""
import re

MODEL_ID = 'gemini-3.8-flash'
HOSTS = {
    'us': 'aiplatform.us.rep.googleapis.com',
    'eu': 'aiplatform.eu.rep.googleapis.com',
    'global': 'aiplatform.googleapis.com',
}
# Application limits, deliberately smaller than the provider's model limits.
MAX_REQUEST_BYTES = 180000
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_OUTPUT_TOKENS = 8000
USAGE_FIELDS = ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount',
                'totalTokenCount', 'cachedContentTokenCount', 'toolUsePromptTokenCount')


def endpoint(project: str, location: str, model: str = MODEL_ID) -> str:
    if model != MODEL_ID or location not in HOSTS:
        raise ValueError('Unsupported model or location; no fallback is permitted.')
    # A path component, never a URL, project alias, query or credential. Project
    # existence/IAM/quota must still be checked in the approved staging project.
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]', project):
        raise ValueError('GOOGLE_CLOUD_PROJECT must be a project ID (6–30 lowercase characters).')
    return (f'https://{HOSTS[location]}/v1/projects/{project}/locations/{location}'
            f'/publishers/google/models/{model}:generateContent')


def usage_counts(raw: dict) -> dict[str, int]:
    """Reject incomplete/impossible counters instead of reporting fabricated zero cost."""
    if not isinstance(raw, dict) or not {'promptTokenCount', 'totalTokenCount'} <= raw.keys():
        raise ValueError('Missing usage metadata.')
    counts = {k: raw.get(k, 0) for k in USAGE_FIELDS}
    if any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError('Invalid token counts.')
    if counts['cachedContentTokenCount'] > counts['promptTokenCount']:
        raise ValueError('Cached tokens exceed prompt tokens.')
    total = sum(counts[k] for k in ('promptTokenCount', 'candidatesTokenCount',
                                   'thoughtsTokenCount', 'toolUsePromptTokenCount'))
    if total != counts['totalTokenCount']:
        raise ValueError('Inconsistent token total.')
    return counts
