"""Optional SEC-only text acquisition. No unrestricted crawler or user-supplied host.

Do not apply this adapter to PCAOB/DART or mirrors. The operator must separately
approve specific source policies. Production needs network egress controls too.
"""
import ipaddress
import socket
from urllib.parse import urlsplit
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
    # This legacy adapter had no source policy record and must never become an alternate route.
    fail('CONNECTOR_DISABLED', 'Use the unified intake registry with reviewed acquisition and storage rights.', 403)
