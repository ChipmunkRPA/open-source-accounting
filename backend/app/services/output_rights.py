"""Reviewed output notices and conservative cumulative reconstruction limits.

Counts canonical serialized output characters, not a legal safe quotation amount.
A group is shared across users, workspaces, editions and formats; no periodic reset.
"""
import hashlib
import json
import unicodedata
from sqlalchemy import select
from ..models import Source, Evidence, Memo, Run, OutputBudget, OutputRelease
from ..schemas import OutputControl
from ..errors import fail


def canonical(value):
    return unicodedata.normalize('NFC', json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def source_lineage(db, sources):
    result = {}
    def visit(source, path):
        if source.id in path or len(path) >= 20:
            fail('DEPENDENCY_CYCLE', 'Source lineage requires review.', 409)
        if source.id in result: return
        result[source.id] = source
        parent_id = source.policy.get('intake_parent_id')
        if parent_id:
            parent = db.get(Source, parent_id)
            if not parent: fail('SOURCE_CHANGED', 'Parent source is unavailable.', 409)
            visit(parent, path | {source.id})
    for source in sources: visit(source, set())
    return list(result.values())


def run_sources(db, run, visited=None):
    visited = set(visited or ())
    if not run or run.id in visited or len(visited) >= 20:
        fail('DEPENDENCY_CYCLE', 'Output dependencies require review.', 409)
    visited.add(run.id)
    sources = [db.get(Source, e.source_id) for e in db.scalars(select(Evidence).where(
        Evidence.run_id == run.id, Evidence.source_id.is_not(None), Evidence.access != 'reference_only'))]
    if any(s is None for s in sources): fail('SOURCE_CHANGED', 'Source is unavailable.', 409)
    memo_id = (run.inputs or {}).get('memo_id')
    if memo_id:
        memo = db.get(Memo, memo_id)
        if not memo or memo.workspace_id != run.workspace_id:
            fail('SOURCE_CHANGED', 'Input memo is unavailable.', 409)
        if memo.run_id: sources.extend(run_sources(db, db.get(Run, memo.run_id), visited))
    return source_lineage(db, sources)


def notices(db, sources):
    result = []
    seen = set()
    for source in sorted(source_lineage(db, sources), key=lambda row: row.id):
        note = (source.policy or {}).get('attribution', '').strip()
        if not note: continue
        row = {'title': source.title, 'publisher': source.publisher, 'url': source.canonical_url,
               'version': source.version_label, 'notice': note}
        key = canonical(row)
        if key not in seen: result.append(row); seen.add(key)
    return result


def notice_text(rows):
    if not rows: return ''
    return '\n\nSource notices (required by current source policy):\n' + '\n'.join(
        f"{r['title']} — {r['publisher']} — {r['version']}\n{r['url']}\n{r['notice']}" for r in rows)


def release(db, sources, payload):
    """Reserve before response/commit. Caller must authorize body operations separately.

    Insert+row-lock serializes PostgreSQL workers; SQLite insert obtains a write lock.
    Store only a group, digest and counts. Never store another copy of source/output text.
    """
    groups = {}
    for source in source_lineage(db, sources):
        raw = source.policy.get('output_control')
        if raw is None:
            if source.policy.get('basis') in {'license', 'reviewed_use'}:
                fail('OUTPUT_POLICY_REQUIRED', 'Reviewed output terms are required.', 403)
            continue
        try: policy = OutputControl.model_validate(raw)
        except ValueError: fail('OUTPUT_POLICY_REQUIRED', 'Output terms require review.', 403)
        fields = policy.model_dump(mode='json')
        if policy.group_id in groups and groups[policy.group_id] != fields:
            fail('OUTPUT_POLICY_CONFLICT', 'Sources disagree on the shared work limits.', 409)
        groups[policy.group_id] = fields
    serialized = canonical(payload)
    fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
    size = len(serialized)
    for group, control in sorted(groups.items()):
        limits_hash = hashlib.sha256(canonical(control).encode()).hexdigest()
        if db.bind.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        db.execute(insert(OutputBudget).values(group_id=group, limits_sha256=limits_hash, released_chars=0)
                   .on_conflict_do_nothing(index_elements=['group_id']))
        budget = db.scalar(select(OutputBudget).where(OutputBudget.group_id == group).with_for_update())
        if budget.limits_sha256 != limits_hash:
            fail('OUTPUT_POLICY_CONFLICT', 'Changing a policy cannot reset a work output ledger.', 409)
        if control['mode'] == 'bounded' and size > control['max_chars_per_response']:
            fail('SOURCE_OUTPUT_LIMIT', 'The reviewed source output limit would be exceeded.', 403)
        if db.get(OutputRelease, (group, fingerprint)):
            continue
        if control['mode'] == 'bounded' and budget.released_chars + size > control['max_chars_total']:
            fail('SOURCE_OUTPUT_LIMIT', 'The reviewed cumulative source output limit would be exceeded.', 403)
        budget.released_chars += size
        db.add(OutputRelease(group_id=group, payload_sha256=fingerprint, character_count=size))
        db.flush()
    return {'payload_sha256': fingerprint, 'accounted_characters': size}


def run_output(db, run):
    sources = run_sources(db, run)
    payload = {**run.result, 'source_attributions': notices(db, sources)}
    release(db, sources, payload)
    return payload


def memo_output(db, memo, *, body=None, title=None):
    sources = run_sources(db, db.get(Run, memo.run_id)) if memo.run_id else []
    rows = notices(db, sources)
    payload = {'title': memo.title if title is None else title,
               'body': memo.body if body is None else body, 'source_attributions': rows}
    release(db, sources, payload)
    return payload
