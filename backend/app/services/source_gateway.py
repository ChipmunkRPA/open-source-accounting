"""Optional SEC-only text acquisition. No unrestricted crawler or user-supplied host.

Do not apply this adapter to PCAOB/DART or mirrors. The operator must separately
approve specific source policies. Production needs network egress controls too.
"""
import ipaddress
import socket
from urllib.parse import urlsplit
import httpx
from ..errors import fail

HOSTS = {'www.sec.gov', 'sec.gov', 'data.sec.gov'}


def validate_sec_url(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.hostname not in HOSTS or parts.username or parts.password:
        raise ValueError('Only approved HTTPS SEC hosts are supported.')
    if parts.port not in {None, 443}:
        raise ValueError('Nonstandard port is not allowed.')
    for result in socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError('Nonpublic network address rejected.')
    return url


def fetch_sec(url, settings):
    if not settings.source_fetch_enabled or not settings.sec_user_agent:
        fail('CONNECTOR_DISABLED', 'SEC acquisition requires operator approval and an identifying User-Agent.', 403)
    try:
        validate_sec_url(url)
        # No redirects. Do not log body or confidential user input.
        with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
            with client.stream('GET', url, headers={'User-Agent': settings.sec_user_agent}) as response:
                response.raise_for_status()
                kind = response.headers.get('content-type', '')
                if not any(x in kind for x in ('text/plain', 'application/json', 'text/html')):
                    raise ValueError('Only text-based SEC responses are supported by this adapter.')
                chunks, total = [], 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > 2 * 1024 * 1024:
                        raise ValueError('Source exceeds acquisition limit.')
                    chunks.append(chunk)
                return b''.join(chunks).decode('utf-8', errors='replace')
    except (httpx.HTTPError, ValueError, OSError):
        fail('SOURCE_FETCH_FAILED', 'Approved source retrieval failed; no source was published.', 502)
