"""Allowlisted, bounded acquisition. Block pages are failures, never source text.

SQLite coordinates one machine; PostgreSQL coordinates Cloud Run workers through
one shared database. All production ingestion must use the same rate database.
No proxy rotation, captcha solving, credentials or blocked-source fallbacks.
"""
from __future__ import annotations
import ipaddress
import json
import os
import re
import socket
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request
from .core import CoreError, canonical, digest, official_url
from . import parsers


class Blocked(CoreError):
    pass


def reject_access_page(raw):
    low = raw[:30000].lower()
    if any(x in low for x in (b'undeclared automated tool', b'request rate threshold exceeded',
                              b'request access', b'you\xe2\x80\x99ve exceeded', b'<title>access denied',
                              b'captcha', b'type="password"', b"type='password'", b'<title>sign in',
                              b'<title>log in', b'<title>login')):
        raise Blocked('Access-control page, not source content; stopped')


class RateBudget:
    """A reservation clock shared across processes. PostgreSQL requires pre-created table."""
    def __init__(self, location: str, rate=4.0, clock=time.time, sleeper=time.sleep):
        if not 0 < rate <= 10:
            raise CoreError('Request rate must be positive and at most 10/second')
        self.location, self.interval, self.clock, self.sleep = location, 1 / rate, clock, sleeper
        self.postgres = location.startswith(('postgresql://', 'postgresql+psycopg://'))
        if (os.getenv('K_SERVICE') or os.getenv('CLOUD_RUN_JOB')) and not self.postgres:
            raise CoreError('Cloud workers require one shared PostgreSQL rate-budget database')
        if self.postgres:
            from sqlalchemy import create_engine
            self.engine = create_engine(location, pool_size=1, max_overflow=0)
        else:
            Path(location).parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(location, timeout=30) as db:
                db.execute('CREATE TABLE IF NOT EXISTS sec_request_budget (name TEXT PRIMARY KEY, next_at REAL NOT NULL)')
                db.execute("INSERT OR IGNORE INTO sec_request_budget VALUES ('shared', 0)")

    def reserve(self):
        if self.postgres:
            from sqlalchemy import text
            with self.engine.begin() as db:
                # A single named row serializes reservations across all service replicas.
                row = db.execute(text("SELECT next_at, EXTRACT(EPOCH FROM clock_timestamp()) "
                                      "FROM sec_request_budget WHERE name='shared' FOR UPDATE")).first()
                if row is None:
                    raise CoreError('Operator must initialize the shared rate-budget row')
                now = float(row[1]); slot = max(now, float(row[0]))
                db.execute(text("UPDATE sec_request_budget SET next_at=:n WHERE name='shared'"),
                           {'n': slot + self.interval})
        else:
            with sqlite3.connect(self.location, timeout=30) as db:
                db.execute('BEGIN IMMEDIATE')
                now = self.clock()
                next_at = db.execute("SELECT next_at FROM sec_request_budget WHERE name='shared'").fetchone()[0]
                slot = max(now, next_at)
                db.execute("UPDATE sec_request_budget SET next_at=? WHERE name='shared'", (slot+self.interval,))
        self.sleep(max(0, slot-now))
        return slot


def public_addresses(url, validator=official_url):
    host = urlsplit(validator(url)).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise CoreError('Nonpublic address rejected; production also requires controlled egress')
    return [a[4][0] for a in addresses]


class PinnedHTTPS:
    """Connect to the checked IP while preserving TLS hostname verification; no proxies/cookies."""
    def __init__(self, validator):
        self.validator = validator

    def open(self, request, timeout):
        import http.client
        import ssl
        url = self.validator(request.full_url)
        parts = urlsplit(url)
        address = public_addresses(url, self.validator)[0]
        connection = http.client.HTTPSConnection(parts.hostname, timeout=timeout)
        sock = socket.create_connection((address, 443), timeout=timeout)
        try:
            connection.sock = ssl.create_default_context().wrap_socket(sock, server_hostname=parts.hostname)
            path = parts.path or '/'
            if parts.query:
                path += '?' + parts.query
            connection.request('GET', path, headers={**dict(request.header_items()), 'Connection': 'close'})
            response = connection.getresponse()
            if response.status != 200:
                response.close()
                raise HTTPError(url, response.status, 'Source response rejected', response.headers, None)
            return response
        except BaseException:
            sock.close()
            connection.close()
            raise


class Gateway:
    def __init__(self, user_agent: str, budget: RateBudget, opener=None, resolver=None,
                 validator=official_url, max_bytes=parsers.MAX_BYTES):
        if (not re.search(r'[^\s@]+@[^\s@]+\.[^\s@]+', user_agent) or
                any(c in user_agent for c in '\r\n') or len(user_agent) > 250):
            raise CoreError('Set an application-identifying User-Agent with a real operator contact email')
        self.agent, self.budget = user_agent, budget
        self.validate, self.max_bytes = validator, max_bytes
        self.resolver = resolver or (lambda url: public_addresses(url, validator))
        # Ignore environment proxy configuration. No automatic redirects/cookies.
        self.opener = opener or PinnedHTTPS(validator)

    def get(self, url):
        original = self.validate(url)
        deadline = time.monotonic() + 120
        for redirect in range(4):
            self.validate(url)
            self.resolver(url)
            self.budget.reserve()
            if time.monotonic() > deadline:
                raise CoreError('Acquisition deadline exceeded before request')
            req = Request(url, headers={'User-Agent': self.agent, 'Accept-Encoding': 'identity',
                                        'Accept': 'application/xml,text/html,application/pdf,application/json'})
            try:
                response = self.opener.open(req, timeout=25)
            except HTTPError as exc:
                if exc.code in {301, 302, 303, 307, 308} and exc.headers.get('Location'):
                    url = urljoin(url, exc.headers['Location'])
                    # Recheck before making another request, including a new budget reservation.
                    self.validate(url)
                    continue
                if exc.code in {401, 403, 429}:
                    raise Blocked(f'HTTP {exc.code}: stop; operator review/backoff required') from exc
                raise CoreError(f'Official acquisition failed: HTTP {exc.code}') from exc
            with response:
                if getattr(response, 'status', 200) != 200:
                    raise CoreError('Unexpected source response')
                if response.headers.get('Content-Encoding', 'identity').lower() not in {'', 'identity'}:
                    raise CoreError('Compressed responses are unsupported; no implicit decompression')
                chunks, size = [], 0
                while True:
                    if time.monotonic() > deadline:
                        raise CoreError('Acquisition deadline exceeded')
                    chunk = response.read(min(65536, self.max_bytes + 1 - size))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise CoreError('Source exceeds byte limit')
                raw = b''.join(chunks)
                mime = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
                headers = {k: response.headers.get(k) for k in ('Content-Type', 'ETag', 'Last-Modified', 'Content-Length')
                           if response.headers.get(k) is not None}
            reject_access_page(raw)
            if mime not in {'text/html', 'text/xml', 'application/xml', 'text/plain', 'application/pdf', 'application/json'}:
                raise CoreError('Unsupported Content-Type')
            return {'requested_url': original, 'resolved_url': url, 'raw': raw,
                    'mime': mime, 'method': 'GET', 'status': 200, 'headers': headers,
                    'retrieved_at': datetime.now(timezone.utc).isoformat()}
        raise CoreError('Too many redirects')


def acquire(entry, gateway: Gateway, directory: Path, as_of=None):
    """Download one catalog record and stage immutable raw + normalized artifacts locally."""
    url = entry.get('acquisition_url') or entry['url']
    if '{as_of}' in url:
        from .core import iso_day
        if not as_of:
            raise CoreError('eCFR requires an explicit edition date; not assumed to be today')
        iso_day(as_of)
        url = url.replace('{as_of}', as_of)
    response = gateway.get(url)
    raw_hash = digest(response['raw'])
    mime = response['mime']
    if 'xml' in mime or entry.get('parser') == 'ecfr_xml':
        passages = parsers.ecfr_xml(response['raw'])
    elif mime == 'application/pdf':
        passages = parsers.pdf(response['raw'])
    elif mime == 'text/html':
        passages = parsers.html(response['raw'], entry['family'], entry['title'])
    else:
        raise CoreError('No reviewed parser for this response type')
    snapshot = dict(source_id=entry['id'], requested_url=response['requested_url'],
                    resolved_url=response['resolved_url'], retrieved_at=response['retrieved_at'],
                    raw_sha256=raw_hash, raw_artifact_included=True, parser_version='sec-core-0.7.0',
                    acquisition_method='direct_http', source_as_of=as_of,
                    effective_from=None, effective_to=None, public_available_at=None,
                    coverage='acquired_document_parser_review_pending',
                    rights_review='pending', professional_review='pending',
                    authority_type=entry['authority_type'], passages=passages)
    snapshot['normalized_sha256'] = digest(canonical(passages))
    raw_dir = directory / 'raw'; raw_dir.mkdir(parents=True, exist_ok=True)
    snapshots = directory / 'snapshots'; snapshots.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / (raw_hash + '.bin')
    if not raw_path.exists():
        with raw_path.open('xb') as f:
            f.write(response['raw'])
    elif digest(raw_path.read_bytes()) != raw_hash:
        raise CoreError('Existing raw artifact failed checksum')
    output = snapshots / f'{entry["id"]}-{raw_hash}-{snapshot["normalized_sha256"][:12]}.json'
    if output.exists():
        old = json.loads(output.read_text())
        if old['normalized_sha256'] != snapshot['normalized_sha256']:
            raise CoreError('Immutable normalized snapshot mismatch')
        return {**old, 'status': 'already_staged'}
    output.write_bytes(canonical(snapshot))
    return {**snapshot, 'status': 'staged_no_approval'}
