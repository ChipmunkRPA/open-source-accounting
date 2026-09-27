"""Validated catalog and selected official excerpts; standard library only.

The shipped excerpt bundle is NOT a raw website mirror. Hashes verify the actual
normalized text in the bundle, not bytes that were never downloaded. No review
status or subscription can be inferred from a URL or a successful parser run.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

FAMILIES = {'reg_sx', 'reg_sk', 'reg_g', 'sab', 'frm', 'cfi', 'forms'}
AUTHORITIES = {'commission_rule', 'staff_guidance', 'form_instruction', 'index'}
HOSTS = {'www.sec.gov', 'sec.gov', 'data.sec.gov', 'www.ecfr.gov', 'www.govinfo.gov'}
ID = re.compile(r'^[a-z0-9][a-z0-9_-]{1,119}$')


class CoreError(ValueError):
    pass


def digest(text: str | bytes) -> str:
    return hashlib.sha256(text.encode('utf-8') if isinstance(text, str) else text).hexdigest()


def canonical(data) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def official_url(value: str) -> str:
    try:
        u = urlsplit(value)
        port = u.port
    except ValueError as exc:
        raise CoreError('Malformed source URL') from exc
    if (u.scheme != 'https' or u.hostname not in HOSTS or u.username or u.password
            or port not in {None, 443} or any(c in value for c in '\r\n\x00')
            or '\\' in value):
        raise CoreError('Only credential-free, allowlisted government HTTPS URLs are permitted')
    return value


def iso_day(value):
    if value is not None:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise CoreError('Date must be YYYY-MM-DD, or null when not established')
        date.fromisoformat(value)


def read_json(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 20_000_000:
        raise CoreError('Missing, symlinked or oversized source pack')
    return json.loads(path.read_text(encoding='utf-8'))


class CorePack:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        for p in [self.root, *self.root.parents]:
            if p.is_symlink():
                raise CoreError('Symlinked pack directory')
        self.catalog = read_json(self.root / 'catalog.json')
        self.bundle = read_json(self.root / 'excerpts.json')
        if self.catalog.get('schema_version') != 1 or self.bundle.get('schema_version') != 1:
            raise CoreError('Unsupported SEC pack schema')
        self.entries = {}
        for e in self.catalog['sources']:
            if (not ID.fullmatch(e['id']) or e['id'] in self.entries or e['family'] not in FAMILIES
                    or e['authority_type'] not in AUTHORITIES):
                raise CoreError('Invalid or duplicate catalog record')
            official_url(e['url'])
            if e.get('acquisition_url'):
                official_url(e['acquisition_url'].replace('{as_of}', '2026-09-24'))
            self.entries[e['id']] = e
        self.documents = {}
        self.passages = {}
        for d in self.bundle['documents']:
            if d['source_id'] not in self.entries or d['source_id'] in self.documents:
                raise CoreError('Unknown or duplicate document')
            e = self.entries[d['source_id']]
            if d['url'] != e['url'] or d['authority_type'] != e['authority_type']:
                raise CoreError('Document identity does not match the catalog')
            if (d.get('coverage') != 'selected_excerpts' or d.get('raw_artifact_included') is not False
                    or d.get('acquisition_method') != 'web_tool_transcription'
                    or d.get('professional_review') != 'pending' or d.get('rights_review') != 'pending'):
                raise CoreError('Shipped pack must not pretend to be full, raw or independently approved')
            stamp = datetime.fromisoformat(d['retrieved_at'].replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise CoreError('Timezone required for retrieval timestamp')
            iso_day(d.get('source_as_of'))
            iso_day(d.get('effective_from'))
            if not d['passages'] or len(d['passages']) > 10000:
                raise CoreError('Invalid passage count')
            for p in d['passages']:
                if (not ID.fullmatch(p['id']) or p['id'] in self.passages or not p['text'].strip()
                        or not p['locator'] or len(p['locator']) > 150
                        or digest(p['text']) != p['sha256']):
                    raise CoreError('Passage integrity or locator failure')
                iso_day(p.get('published_or_revised_at'))
                if not p.get('context_note') or not p.get('verification_locator'):
                    raise CoreError('Excerpt context and verification locator required')
                self.passages[p['id']] = (d, p)
            if digest(canonical(d['passages'])) != d['normalized_sha256']:
                raise CoreError('Normalized document hash mismatch')
            identity = {k: d[k] for k in ['source_id', 'url', 'authority_type', 'source_as_of',
                                         'coverage', 'acquisition_method', 'normalized_sha256']}
            if digest(canonical(identity)) != d.get('snapshot_id'):
                raise CoreError('Document provenance hash mismatch')
            self.documents[d['source_id']] = d

    def report(self):
        families = []
        for family in sorted(FAMILIES):
            entries = [e for e in self.entries.values() if e['family'] == family]
            docs = [d for d in self.documents.values() if self.entries[d['source_id']]['family'] == family]
            families.append(dict(family=family, inventoried=len(entries), excerpted=len(docs),
                                 excerpts=sum(len(d['passages']) for d in docs), full_documents=0,
                                 professionally_reviewed=0, agent_approved=0))
        return dict(schema_version=1, release=self.bundle['release'], sources_inventoried=len(self.entries),
                    sources_with_excerpts=len(self.documents), selected_excerpts=len(self.passages),
                    excerpt_words=sum(len(p['text'].split()) for _, p in self.passages.values()),
                    complete_source_documents=0, original_http_artifacts=0,
                    professional_reviewed=0, agent_approved=0, families=families,
                    notice='Selected official-source transcriptions; pending independent review. Not full SEC coverage.')

    def public_source(self, source_id):
        if source_id not in self.entries:
            return None
        return {'source': self.entries[source_id], 'document': self.documents.get(source_id),
                'agent_approved': False, 'notice': self.report()['notice']}

    def preview(self, query: str, limit: int = 12, family: str | None = None):
        """Read-only FTS preview, NOT Agent admission. Rebuilt from validated bundle."""
        if not 1 <= limit <= 100 or len(query) > 500:
            raise CoreError('Invalid preview query or limit')
        if family is not None and family not in FAMILIES:
            raise CoreError('Unknown family')
        terms = re.findall(r'[\w]+', query.lower())[:32]
        if not terms:
            return []
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE VIRTUAL TABLE search USING fts5(pid UNINDEXED, family UNINDEXED, locator, body)')
            db.executemany('INSERT INTO search VALUES (?,?,?,?)', [
                (pid, self.entries[d['source_id']]['family'], p['locator'], p['text'])
                for pid, (d, p) in self.passages.items()])
            # Only quoted lexical tokens enter MATCH; user FTS syntax is not executed.
            match = ' OR '.join('"' + t.replace('"', '""') + '"' for t in terms)
            rows = db.execute('SELECT pid FROM search WHERE search MATCH ? '
                              'AND (? IS NULL OR family=?) ORDER BY bm25(search) LIMIT ?',
                              (match, family, family, limit)).fetchall()
        return [self.passage(row[0]) for row in rows]

    def passage(self, pid):
        if pid not in self.passages:
            return None
        d, p = self.passages[pid]
        return {**p, 'source_id': d['source_id'], 'url': d['url'],
                'authority_type': d['authority_type'], 'retrieved_at': d['retrieved_at'],
                'source_as_of': d.get('source_as_of'), 'coverage': d['coverage'],
                'professional_review': 'pending', 'agent_approved': False,
                'snapshot_id': d['snapshot_id']}
