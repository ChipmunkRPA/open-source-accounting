"""Original public library + deliberately unapproved database staging.

python -m app.content validate
python -m app.content import --author USER_ID

The file library is readable without a subscription. Import never grants rights or
technical approval. Remote URLs are metadata, never automatically fetched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID, uuid5
from pydantic import BaseModel, ConfigDict, Field, model_validator

NAMESPACE = UUID('9ee37063-0285-47cd-b205-09ae2c69a5a1')

class ContentError(ValueError):
    """Invalid or incomplete library; callers must not fall back to arbitrary files."""

class Review(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['unreviewed', 'reviewed']
    reviewer: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode='after')
    def provenance(self):
        if self.status == 'reviewed' and not (self.reviewer and self.reviewed_at):
            raise ValueError('A real reviewer and review date are required.')
        return self

class Item(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=120)
    title: str = Field(min_length=4, max_length=250)
    kind: Literal['guide', 'case', 'template', 'playbook', 'qa_set']
    topic: str = Field(min_length=1, max_length=60)
    framework: Literal['US_GAAP', 'IFRS', 'BOTH', 'AUDIT']
    summary: str = Field(min_length=10, max_length=1500)
    path: str
    version: str = Field(min_length=1, max_length=40)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    published_at: str
    updated_at: str
    author: str
    license: Literal['CC-BY-4.0']
    source_ids: list[str] = Field(min_length=1)
    technical_review: Review
    primary_text_gap: bool
    public_visibility: Literal['editorial_draft', 'reviewed_article']
    agent_eligible_by_default: Literal[False]

class Manifest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1]
    release: str
    generated_at: str
    publication_state: str
    items: list[Item] = Field(min_length=1, max_length=2000)

class Library:
    """Read only manifest-listed, hash-verified original Markdown files."""
    def __init__(self, directory: str | Path):
        self.root = Path(directory).resolve()
        self.manifest = Manifest.model_validate(self._json('manifest.json'))
        source_pack = self._json('references/sources.json')
        refs = source_pack.get('sources', [])
        self.references = {s['id']: s for s in refs}
        if len(refs) != len(self.references):
            raise ContentError('Duplicate reference IDs.')
        for source in refs:
            u = urlparse(source['url'])
            if u.scheme != 'https' or not u.hostname or u.username or u.password:
                raise ContentError('Reference links must be credential-free HTTPS URLs.')
            if source.get('full_text_included') or source.get('automated_fetch_enabled'):
                raise ContentError('This starter pack supports reference metadata, not remote ingestion.')
        self.items: dict[str, Item] = {}
        self.bodies: dict[str, str] = {}
        paths: set[str] = set()
        for item in self.manifest.items:
            if item.id in self.items or item.path in paths:
                raise ContentError('Duplicate item ID or content path.')
            if any(r not in self.references for r in item.source_ids):
                raise ContentError(f'Unknown source reference in {item.id}.')
            raw = self._read(item.path)
            if not item.path.endswith('.md') or hashlib.sha256(raw).hexdigest() != item.sha256:
                raise ContentError(f'Content integrity check failed: {item.id}.')
            text = raw.decode('utf-8')
            if not text.startswith('# ') or 'CC BY 4.0' not in text:
                raise ContentError(f'Missing heading or license attribution: {item.id}.')
            self.items[item.id] = item
            self.bodies[item.id] = text
            paths.add(item.path)

    def _read(self, relative: str) -> bytes:
        p = Path(relative)
        if p.is_absolute() or '..' in p.parts or not p.parts:
            raise ContentError('Unsafe content path.')
        candidate = self.root / p
        # Reject symlinks even when their current target remains inside the pack.
        for parent in [candidate, *candidate.parents]:
            if parent == self.root:
                break
            if parent.is_symlink():
                raise ContentError('Symlinked content is not permitted.')
        if not candidate.resolve().is_relative_to(self.root) or not candidate.is_file():
            raise ContentError('Content file is missing or outside the library.')
        if candidate.stat().st_size > 2_000_000:
            raise ContentError('Content file exceeds the 2 MB limit.')
        return candidate.read_bytes()

    def _json(self, relative):
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj:
                    raise ContentError('Duplicate JSON key.')
                obj[k] = v
            return obj
        return json.loads(self._read(relative), object_pairs_hook=unique)

    def search(self, q='', topic='', kind='', offset=0, limit=24):
        terms = re.findall(r'[a-z0-9-]+', q.lower())
        matches = []
        for item in self.items.values():
            if topic and item.topic != topic or kind and item.kind != kind:
                continue
            text = (item.title + ' ' + item.summary + ' ' + self.bodies[item.id]).lower()
            if terms and not all(term in text for term in terms):
                continue
            matches.append(item)
        matches.sort(key=lambda i: (i.kind, i.title))
        return {'items': [i.model_dump() for i in matches[offset:offset+limit]],
                'total': len(matches), 'offset': offset, 'limit': limit,
                'release': self.manifest.release,
                'facets': {'topics': sorted({i.topic for i in self.items.values()}),
                           'kinds': sorted({i.kind for i in self.items.values()})},
                'notice': 'Original AI-assisted editorial drafts. No professional review is claimed.'}

    def get(self, item_id):
        item = self.items.get(item_id)
        if item is None:
            return None
        return {**item.model_dump(), 'body': self.bodies[item_id],
                'sources': [self.references[r] for r in item.source_ids]}

    def report(self):
        return {'release': self.manifest.release, 'items': len(self.items),
                'references': len(self.references),
                'words': sum(len(t.split()) for t in self.bodies.values()),
                'unreviewed': sum(i.technical_review.status == 'unreviewed' for i in self.items.values()),
                'proprietary_full_text_files': 0}


def stage_library(db, library: Library, author_id: str):
    """Idempotent source staging. Returns IDs; approvals must happen separately."""
    from .models import User, Source, Audit
    author = db.get(User, author_id)
    if not author or author.role not in {'admin', 'rights_approver'}:
        raise ContentError('The importing author must be an existing source administrator.')
    created, existing = [], []
    for item in library.items.values():
        sid = str(uuid5(NAMESPACE, item.id + '@' + item.version))
        old = db.get(Source, sid)
        if old:
            if (old.policy or {}).get('content_sha256') != item.sha256:
                raise ContentError('An immutable item version changed; publish a new version.')
            existing.append(sid)
            continue
        policy = dict(basis='original', commercial_use=True, model_input=True, store_text=True,
                      display_full=True, quote=True, export=True, embed=True, train=False,
                      review_note='CC BY 4.0 original draft; independent rights and technical approval required.',
                      content_item_id=item.id, content_version=item.version, content_sha256=item.sha256,
                      content_license=item.license, content_reference_ids=item.source_ids,
                      requires_technical_review=True, technical_review_status='unreviewed',
                      technical_reviewer_id=None, technical_reviewed_at=None,
                      public_library_notice='AI-assisted editorial draft; not authoritative.')
        source = Source(id=sid, title=item.title, publisher='Open Source Accounting original library',
                        canonical_url='', kind='original_commentary', framework=item.framework,
                        text=library.bodies[item.id], version_label=item.version,
                        policy=policy, reviewed=False, created_by=author_id)
        db.add(source)
        db.flush()
        db.add(Audit(actor_id=author_id, action='content.staged_unapproved', target_id=sid,
                     detail={'content_item_id': item.id, 'version': item.version, 'sha256': item.sha256}))
        created.append(sid)
    return {'created': created, 'existing': existing,
            'status': 'staged_only_no_rights_or_technical_approval_granted'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'import'])
    parser.add_argument('--directory')
    parser.add_argument('--author')
    args = parser.parse_args()
    from .config import Settings
    settings = Settings()
    try:
        library = Library(args.directory or settings.content_dir)
        if args.command == 'validate':
            print(json.dumps(library.report(), indent=2))
            return
        if not args.author:
            parser.error('--author is required for import.')
        from .db import Database
        database = Database(settings.database_url)
        with database.Session() as db:
            result = stage_library(db, library, args.author)
            db.commit()
        print(json.dumps(result, indent=2))
    except (ContentError, ValueError, OSError) as error:
        raise SystemExit(f'Content operation failed: {error}') from error

if __name__ == '__main__':
    main()
