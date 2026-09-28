"""Free ASU references and rights-gated filing mentions; no model or network calls."""
import hashlib
from itertools import chain
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from sqlalchemy import select, delete, func
from ..asu_schemas import Catalog, sec_identity
from ..models import ASUMention, ASURefresh, Source, IntakeWork, SourceArtifact, SourceExtraction, now
from . import rights

VERSION = 'asu-mentions-1'
CADENCE_SECONDS = 86400
BATCH_SIZE = 200
# Require the ASU label: unrelated year-number references are not ASU evidence.
PATTERN = re.compile(r'\b(?:ASU|Accounting\s+Standards\s+Update)\s*(?:No\.?\s*)?(20\d{2})\s*[-\u2010-\u2014]\s*(\d{2})(?!\d)', re.I)


@lru_cache(maxsize=1)
def catalog():
    return Catalog.model_validate_json((Path(__file__).resolve().parents[1] / 'asu_data/catalog.json').read_text())


def window(today):
    try:
        return today.replace(year=today.year-2)
    except ValueError:  # February 29, inclusive calendar-year window.
        return today.replace(year=today.year-2, day=28)


def identifiers(text):
    return sorted({f'{a}-{b}' for a, b in PATTERN.findall(text)})


def binding(db, source):
    """Only staged, public SEC filing corpus; never private Document or publisher text."""
    p = source.policy or {}
    artifact = db.get(SourceArtifact, p.get('intake_artifact_id')) if p.get('intake_artifact_id') else None
    extraction = db.get(SourceExtraction, p.get('intake_extraction_id')) if p.get('intake_extraction_id') else None
    work = db.get(IntakeWork, artifact.work_id) if artifact else None
    if (not work or not extraction or extraction.artifact_id != artifact.id or work.family_id != 'SEC_FILINGS'
            or work.source_id != p.get('intake_parent_id') or work.manifest.get('access_mode') != 'public_candidate'
            or source.canonical_url != work.manifest.get('requested_url')
            or extraction.normalized_sha256 != p.get('intake_extraction_sha256')
            or hashlib.sha256((source.text or '').encode()).hexdigest() != p.get('content_sha256')):
        return None
    try:
        cik, accession = sec_identity(source.canonical_url)
    except ValueError:
        return None
    context = {'route': work.manifest['route'], 'audience': 'public'}
    # Metadata derived from protected text is withheld as soon as any gate changes.
    if not all(rights.allowed(source, op, context=context) for op in ('extract', 'store_text', 'display_full', 'redistribute')):
        return None
    return work, artifact, extraction, cik, accession


def refresh(db, *, force=False, timestamp=None, batch_size=BATCH_SIZE):
    """One atomic bounded batch. Lock spans work; crash rolls back cursor and matches.

    Insert-on-conflict serializes SQLite writers too. Source IDs form a fixed upper
    bound; rows inserted behind the cursor are picked up in the next daily sweep.
    A force request resumes an active sweep rather than restarting its cursor.
    """
    timestamp = now() if timestamp is None else timestamp
    if not 1 <= batch_size <= BATCH_SIZE:
        raise ValueError('Invalid ASU refresh batch size.')
    if db.bind.dialect.name == 'postgresql':
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    db.execute(insert(ASURefresh).values(id='filings', cursor='', upper_id='', state='idle', next_due=0,
        scanned=0, eligible=0, matches=0).on_conflict_do_nothing(index_elements=['id']))
    state = db.scalar(select(ASURefresh).where(ASURefresh.id == 'filings').with_for_update())
    if state.state != 'running':
        if not force and state.next_due > timestamp:
            db.commit()
            return False
        state.cursor = ''
        state.upper_id = db.scalar(select(func.max(Source.id))) or ''
        state.state, state.started_at = 'running', timestamp
        state.scanned = state.eligible = state.matches = 0
    rows = db.scalars(select(Source).where(Source.id > state.cursor, Source.id <= state.upper_id)
                      .order_by(Source.id).limit(batch_size)).all()
    for source in rows:
        db.execute(delete(ASUMention).where(ASUMention.source_id == source.id))
        if binding(db, source):
            state.eligible += 1
            ids = identifiers(source.text or '')
            for asu_id in ids:
                db.add(ASUMention(source_id=source.id, asu_id=asu_id,
                    source_revision=rights.revision(source), detected_at=timestamp))
            state.matches += len(ids)
        state.scanned += 1
        state.cursor = source.id
    if len(rows) < batch_size or state.cursor == state.upper_id:
        state.state, state.completed_at = 'idle', timestamp
        state.next_due = timestamp + CADENCE_SECONDS
    db.commit()
    return True


def refresh_status(db):
    s = db.get(ASURefresh, 'filings')
    return {'state': s.state if s else 'never_run', 'started_at': s.started_at if s else None,
            'completed_at': s.completed_at if s else None, 'next_due': s.next_due if s else None,
            'scanned_sources': s.scanned if s else 0, 'eligible_passages': s.eligible if s else 0,
            'detected_mentions': s.matches if s else 0, 'cadence_seconds': CADENCE_SECONDS,
            'overdue': bool(s and s.next_due and s.next_due < now() and s.state != 'running'),
            'scope': 'Authorized staged SEC filing passages. External filing acquisition is separate.',
            'detector_version': VERSION}


def listing(db, q='', topic='', today=None):
    today = today or datetime.now(timezone.utc).date()
    start = window(today)
    pack = catalog()
    items = []
    for a in reversed(pack.asus):
        low, high = a.interval()
        if low > today or high < start:
            continue
        if topic and topic != a.topic:
            continue
        if q.casefold() not in f'{a.id} {a.subject} {a.topic}'.casefold():
            continue
        items.append({**a.model_dump(mode='json'), 'boundary_uncertain': low < start or high > today,
                      'reference_links': sum(f.asu_id == a.id for f in pack.filings)})
    return {'items': items, 'window_start': start.isoformat(), 'window_end': today.isoformat(),
            'catalog_version': pack.version, 'catalog_checked_on': pack.checked_on.isoformat(),
            'catalog_age_days': max(0, (today-pack.checked_on).days),
            'topics': sorted({a.topic for a in pack.asus}), 'refresh': refresh_status(db),
            'coverage': {'registered_asus': len(pack.asus), 'reference_links': len(pack.filings),
                         'companies': len({f.cik for f in pack.filings}), 'complete_universe': False,
                         'retained_reference_artifacts': 0, 'professionally_reviewed': 0},
            'notice': 'Selected reference catalog, not a complete FASB or EDGAR inventory. Issuance dates with year/month precision may straddle the window. ASU text and authoritative effective-date conclusions are not included.'}


def materials(db, asu_id, company='', status='', offset=0, limit=25):
    """Paginate after live authorization, so withdrawn rows do not leak or create gaps."""
    pack = catalog()
    refs = [{**f.model_dump(mode='json'), 'kind': 'reference_only', 'professional_review': 'unreviewed',
             'source_id': None, 'raw_sha256': None, 'acquired_at': None}
            for f in pack.filings if f.asu_id == asu_id]
    rows = db.execute(select(ASUMention, Source).join(Source, Source.id == ASUMention.source_id)
                      .where(ASUMention.asu_id == asu_id).order_by(Source.id)).yield_per(100)
    def derived():
        for mention, source in rows:
            info = binding(db, source)
            if not info or mention.source_revision != rights.revision(source):
                continue
            work, artifact, extraction, cik, accession = info
            yield {'asu_id': asu_id, 'company': f'CIK {cik}', 'cik': cik,
                'accession': f'{accession[:10]}-{accession[10:12]}-{accession[12:]}',
                'form': None, 'filed_on': None, 'period_end': None, 'url': source.canonical_url,
                'locator': source.policy.get('intake_locator', 'Locator unavailable'),
                'status': 'mentioned', 'observation': 'ASU identifier detected. Adoption status requires a reading of the filing.',
                'checked_on': datetime.fromtimestamp(mention.detected_at, timezone.utc).date().isoformat(),
                'kind': 'corpus_mention', 'professional_review': 'unreviewed', 'source_id': source.id,
                'raw_sha256': artifact.raw_sha256, 'acquired_at': artifact.acquired_at,
                'parser_version': extraction.parser_version, 'source_revision': mention.source_revision}
    page, total = [], 0
    for item in chain(refs, derived()):
        if status and item['status'] != status:
            continue
        if company.casefold() not in f"{item['company']} {item['cik']}".casefold():
            continue
        if offset <= total < offset+limit:
            page.append(item)
        total += 1
    return {'items': page, 'total': total, 'offset': offset,
            'next_offset': offset+limit if offset+limit < total else None,
            'notice': 'Company disclosures describe that company, not authoritative GAAP. Reference links have no retained artifact or independent review. Automatic mentions do not establish adoption.'}
