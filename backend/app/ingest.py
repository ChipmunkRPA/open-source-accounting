"""Resumable intake commands against the authenticated API. Tokens come only from environment."""
import argparse
import json
import os
from urllib.parse import urlsplit
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='step', required=True)
    sub.add_parser('discover')
    sub.add_parser('inventory')
    sub.add_parser('coverage')
    registration = sub.add_parser('register'); registration.add_argument('--file', required=True)
    manual = sub.add_parser('import'); manual.add_argument('id')
    manual.add_argument('--file', required=True); manual.add_argument('--mime', required=True)
    manual.add_argument('--request-key', required=True)
    sub.add_parser('discover-index').add_argument('id')
    sub.add_parser('discovery').add_argument('id')
    for step in ('preview', 'acquire', 'parse', 'stage'):
        command = sub.add_parser(step); command.add_argument('id')
        if step == 'acquire':
            command.add_argument('--request-key', required=True)
    args = parser.parse_args()
    base = os.environ.get('OSA_API_URL', '').rstrip('/')
    parts = urlsplit(base)
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or (parts.scheme != 'https' and not (
            parts.scheme == 'http' and parts.hostname in {'127.0.0.1', 'localhost'})):
        parser.error('OSA_API_URL must be HTTPS (or explicit localhost for local development).')
    token = os.environ.get('OSA_INTAKE_TOKEN')
    if not token:
        parser.error('Supply a fresh MFA-authenticated admin token through OSA_INTAKE_TOKEN.')
    if hasattr(args, 'id'):
        from uuid import UUID
        try:
            UUID(args.id)
        except ValueError:
            parser.error('Expected a server-issued UUID.')
    route = '/api/v1/admin/intake/'
    verb, body, extra, raw = 'GET', None, {}, None
    if args.step in {'discover', 'inventory', 'coverage'}:
        route += {'discover': 'families', 'inventory': 'works', 'coverage': 'coverage'}[args.step]
    elif args.step == 'register':
        from pathlib import Path
        route += 'works'; verb = 'POST'; body = json.loads(Path(args.file).read_text())
    elif args.step == 'preview':
        route += 'works/' + args.id
    elif args.step == 'discover-index':
        route += 'artifacts/' + args.id + '/discover'; verb = 'POST'
    elif args.step == 'discovery':
        route += 'discoveries/' + args.id
    elif args.step == 'import':
        from pathlib import Path
        with Path(args.file).open('rb') as handle:
            raw = handle.read(16_000_001)
        if not raw or len(raw) > 16_000_000:
            parser.error('Manual files must contain 1–16,000,000 bytes.')
        route += 'works/' + args.id + '/import'; verb = 'POST'
        extra.update({'Idempotency-Key': args.request_key, 'Content-Type': args.mime})
    else:
        route += {'acquire': 'works/', 'parse': 'artifacts/', 'stage': 'extractions/'}[args.step] + args.id + '/' + args.step
        verb = 'POST'
        if args.step == 'acquire':
            extra['Idempotency-Key'] = args.request_key
    with httpx.Client(timeout=180, follow_redirects=False, trust_env=False) as client:
        response = client.request(verb, base+route, json=body, content=raw,
                                  headers={'Authorization': 'Bearer '+token, **extra})
    if response.status_code >= 300:
        raise SystemExit(f'Intake stopped: HTTP {response.status_code}. Inspect the authenticated admin status; no fallback attempted.')
    print(json.dumps(response.json(), indent=2))


if __name__ == '__main__':
    main()
