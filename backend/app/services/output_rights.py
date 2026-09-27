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


def policy_current(source, control):
    """An old per-source approval cannot transmit under superseded group terms."""
    from sqlalchemy.orm import object_session
    db = object_session(source)
    if db is None: return False  # A detached object cannot verify current group terms.
    row = db.execute(select(OutputBudget.limits_sha256).where(OutputBudget.group_id == control['group_id'])).first()
    return row is None or row[0] == hashlib.sha256(canonical(control).encode()).hexdigest()


def release_batch(db, requests):
    """Reserve before response/commit. Caller must authorize body operations separately.

    Insert+row-lock serializes PostgreSQL workers; SQLite insert obtains a write lock.
    Store only a group, digest and counts. Never store another copy of source/output text.
    """
    from . import rights, counsel
    lineages = [(source_lineage(db, sources), payload) for sources, payload in requests]
    lineage = list({source.id: source for sources, _ in lineages for source in sources}.values())
    # Lock source rows before group rows, as amendments do. Compare the caller's
    # authorized snapshot with fresh state, including an A->B->A policy transition.
    snapshots = {s.id: (s.policy_version, rights.revision(s), s.enabled, s.reviewed) for s in lineage}
    current = []
    for source_id in sorted(snapshots):
        source = counsel.lock_source(db, source_id)
        if snapshots[source_id] != (source.policy_version, rights.revision(source), source.enabled, source.reviewed):
            fail('SOURCE_CHANGED', 'Source rights changed before output release.', 409)
        current.append(source)
    groups, source_groups = {}, {}
    for source in current:
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
        source_groups[source.id] = policy.group_id
    budgets = {}
    for group, control in sorted(groups.items()):
        limits_hash = hashlib.sha256(canonical(control).encode()).hexdigest()
        if db.bind.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        db.execute(insert(OutputBudget).values(group_id=group, limits_sha256=limits_hash, released_chars=0)
                   .on_conflict_do_nothing(index_elements=['group_id']))
        budget = db.scalar(select(OutputBudget).where(OutputBudget.group_id == group).with_for_update()
                           .execution_options(populate_existing=True))
        if budget.limits_sha256 != limits_hash:
            fail('OUTPUT_POLICY_CONFLICT', 'Changing a policy cannot reset a work output ledger.', 409)
        budgets[group] = budget
    results = []
    for sources, payload in lineages:
        serialized = canonical(payload)
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        size = len(serialized)
        selected = {source_groups[s.id] for s in sources if s.id in source_groups}
        for group in sorted(selected):
            control, budget = groups[group], budgets[group]
            if control['mode'] == 'bounded' and size > control['max_chars_per_response']:
                fail('SOURCE_OUTPUT_LIMIT', 'The reviewed source output limit would be exceeded.', 403)
            if control['mode'] == 'bounded' and budget.released_chars > control['max_chars_total']:
                fail('SOURCE_OUTPUT_LIMIT', 'Prior releases exceed the current reviewed cumulative limit.', 403)
            if db.get(OutputRelease, (group, fingerprint)):
                continue
            if control['mode'] == 'bounded' and budget.released_chars + size > control['max_chars_total']:
                fail('SOURCE_OUTPUT_LIMIT', 'The reviewed cumulative source output limit would be exceeded.', 403)
            budget.released_chars += size
            db.add(OutputRelease(group_id=group, payload_sha256=fingerprint, character_count=size))
            db.flush()
        results.append({'payload_sha256': fingerprint, 'accounted_characters': size})
    return results


def release(db, sources, payload):
    return release_batch(db, [(sources, payload)])[0]


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
