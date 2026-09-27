"""Stage selected official excerpts into existing rights + technical-review workflow."""
from uuid import UUID, uuid5
from .core import CoreError, digest

NAMESPACE = UUID('2f7c291f-342c-4f2d-b416-3ba6045e9ad8')


def stage(db, pack, author_id):
    from ..models import User, Source, Audit
    author = db.get(User, author_id)
    if not author or author.role not in {'admin', 'rights_approver'}:
        raise CoreError('An existing source administrator must stage the excerpts')
    created, existing = [], []
    for pid, (doc, excerpt) in pack.passages.items():
        entry = pack.entries[doc['source_id']]
        sid = str(uuid5(NAMESPACE, pid + '@' + doc['snapshot_id']))
        old = db.get(Source, sid)
        if old:
            if digest(old.text or '') != excerpt['sha256']:
                raise CoreError('An immutable staged SEC excerpt was modified')
            existing.append(sid)
            continue
        # Existing rights approval and actual technical-review endpoints are mandatory.
        policy = dict(basis='government_source_excerpt_pending_review', commercial_use=True,
                      model_input=True, store_text=True, quote=True, export=True,
                      display_full=True, embed=False, train=False,
                      requires_technical_review=True, technical_review_status='unreviewed',
                      content_sha256=excerpt['sha256'], content_reference_ids=[doc['source_id']],
                      sec_core=dict(passage_id=pid, source_id=doc['source_id'], locator=excerpt['locator'],
                                    snapshot_id=doc['snapshot_id'], source_as_of=doc.get('source_as_of'),
                                    retrieved_at=doc['retrieved_at'], effective_from=None, effective_to=None,
                                    public_available_at=None, applicability_review_status='pending',
                                    primary_source_text=True, authority_type=doc['authority_type'],
                                    acquisition_method=doc['acquisition_method'], raw_artifact_included=doc.get('raw_artifact_included', False),
                                    coverage=doc.get('coverage', 'selected_excerpt'), context_note=excerpt['context_note']))
        s = Source(id=sid, title=(entry['title']+' — SOURCE PASSAGE: '+excerpt['locator'])[:250],
                   publisher=entry['publisher'], canonical_url=entry['url'],
                   kind='rule' if doc['authority_type']=='commission_rule' else 'staff_guidance' if doc['authority_type']=='staff_guidance' else 'form_instruction',
                   framework='US_GAAP', version_label='excerpt-'+doc['snapshot_id'][:16],
                   text=excerpt['text'], policy=policy, created_by=author_id, reviewed=False)
        db.add(s); db.flush()
        db.add(Audit(actor_id=author_id, action='sec_core.staged_unapproved', target_id=sid,
                     detail={'passage_id': pid, 'sha256': excerpt['sha256'], 'snapshot': doc['snapshot_id']}))
        created.append(sid)
    return {'created': created, 'existing': existing, 'agent_approved': 0,
            'status': 'independent_rights_and_technical_review_required'}


def evidence_for(source, run):
    """Return exact source locator only when existing rights/review checks have passed.

Historical/as-of questions fail closed until an applicability interval and public
availability have actually been reviewed. The retrieval/import timestamp is NEVER
used as an effective/public-availability date for this source family.
"""
    from ..services.rights import allowed
    if not all(allowed(source, op) for op in ['store_text', 'model_input', 'quote']):
        return None
    m = (source.policy or {}).get('sec_core')
    if not m:
        return None
    period, known = run.context.get('period_end'), run.context.get('knowledge_date')
    if period:
        if m.get('applicability_review_status') != 'approved' or not m.get('effective_from'):
            return None
        if period < m['effective_from'] or (m.get('effective_to') and period > m['effective_to']):
            return None
    if known and (not m.get('public_available_at') or known < m['public_available_at']):
        return None
    return {'source_id': source.id, 'document_id': None, 'title': source.title,
            'locator': m['locator'], 'text': source.text, 'access': 'primary_text_reviewed',
            'source_kind': source.kind, 'policy_version': source.policy_version}


def snapshot_pack(snapshot_path, raw_directory, catalog_pack):
    """Reparse a downloaded raw artifact before database staging; never trust JSON alone."""
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from . import parsers
    from .core import canonical, read_json, official_url
    s = read_json(Path(snapshot_path))
    entry = catalog_pack.entries.get(s.get('source_id'))
    if not entry or s.get('acquisition_method') != 'direct_http' or s.get('parser_version') != 'sec-core-0.7.0':
        raise CoreError('Unknown source or unsupported snapshot parser version')
    import re
    raw_hash = s.get('raw_sha256', '')
    if not re.fullmatch('[a-f0-9]{64}', raw_hash):
        raise CoreError('Invalid raw content hash')
    raw_root = Path(raw_directory)
    for parent in [raw_root, *raw_root.parents]:
        if parent.is_symlink():
            raise CoreError('Symlinked raw directory')
    path = raw_root / (raw_hash + '.bin')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > parsers.MAX_BYTES:
        raise CoreError('Missing, symlinked or oversized raw source artifact')
    raw = path.read_bytes()
    if digest(raw) != raw_hash:
        raise CoreError('Raw source hash mismatch')
    expected_url = (entry.get('acquisition_url') or entry['url']).replace('{as_of}', s.get('source_as_of') or '')
    if s['requested_url'] != expected_url:
        raise CoreError('Snapshot requested URL does not match approved catalog route')
    official_url(s['resolved_url'])
    if entry.get('parser') == 'ecfr_xml':
        extracted = parsers.ecfr_xml(raw)
    elif entry.get('parser') == 'pdf':
        extracted = parsers.pdf(raw)
    else:
        extracted = parsers.html(raw, entry['family'], entry['title'])
    if (digest(canonical(extracted)) != s.get('normalized_sha256') or
            extracted != s.get('passages') or s['authority_type'] != entry['authority_type']):
        raise CoreError('Reparsed content/authority does not match snapshot')
    snap_id = digest(canonical({k: s.get(k) for k in ['source_id','raw_sha256','normalized_sha256',
                                                     'requested_url','resolved_url','source_as_of','parser_version']}))
    doc = {'source_id':entry['id'], 'url':entry['url'], 'authority_type':entry['authority_type'],
           'snapshot_id':snap_id, 'source_as_of':s.get('source_as_of'), 'retrieved_at':s['retrieved_at'],
           'acquisition_method':'direct_http', 'raw_artifact_included':True,
           'coverage':'acquired_document_parser_review_pending'}
    rows = {}
    for index, excerpt in enumerate(extracted, 1):
        pid = f'{entry["id"]}-block-{index}'
        if len(excerpt['locator']) > 150:
            raise CoreError('Source locator exceeds schema limit; review parser output')
        rows[pid] = (doc, {**excerpt, 'id':pid, 'context_note':
                          'Parsed official document passage; source block/page is a local exact locator, '
                          'not an invented legal subsection. Review context, embedded third-party text, '
                          'tables, footnotes and historical applicability before use.'})
    return SimpleNamespace(entries=catalog_pack.entries, passages=rows)
