"""Bounded one-hop Agent relationships. An edge never transfers source admission."""
from fastapi import HTTPException
from sqlalchemy import select, or_
from ..models import Source, Evidence, AuthorityRelationship, RunAuthorityEvidence
from ..errors import fail
from ..sec_core.core import canonical, digest
from . import authority, coordinate_evidence, editorial, applicability, rights, dependencies
from .spreadsheet_dependencies import select_with_companions

VERSION = 'authority-agent-evidence-1'
MAX_RELATIONSHIPS = 6
MAX_INCIDENT = 50
MAX_SEEDS = 20
MAX_BYTES = 24000


def key(row):
    return (row['source_id'], row['document_id'], row['locator'])


def admitted(source, run, context, action='model_input'):
    if not source or not editorial.current(source) or not applicability.current(source):
        return False
    framework = run.context.get('framework', 'US_GAAP')
    if framework not in {'BOTH', 'UNKNOWN'} and source.framework not in {framework, 'BOTH', 'AUDIT'}:
        return False
    return (all(rights.allowed(source, op, context=context) for op in {action, 'store_text'})
            and applicability.applies(source, run.context)
            and dependencies.allowed(source, action, context=context, accounting_context=run.context))


def endpoint_row(db, run, endpoint, context):
    source = db.get(Source, endpoint['source_id'])
    if not all(admitted(source, run, context, op) for op in ('model_input', 'quote')):
        return None
    try:
        authority.validate_endpoint(source, endpoint)
    except HTTPException:
        return None
    access = 'primary_text_reviewed' if source.kind in {'standard', 'rule'} else 'secondary_text_reviewed'
    if (source.policy or {}).get('sec_core'):
        from ..sec_core.integration import evidence_for
        existing = evidence_for(source, run, rights_context=context)
        if existing is None:
            return None
        access = existing['access']
    a, b = endpoint['character_start'], endpoint['character_end']
    snapshot = coordinate_evidence.packet(source, a, b)
    if snapshot is None:
        return None
    return {'source_id': source.id, 'document_id': None, 'title': source.title,
            'locator': endpoint['locator'], 'text': source.text[a:b], 'access': access,
            'source_kind': source.kind, 'policy_version': source.policy_version, 'extraction_context': snapshot}


def select_evidence(db, run, pool, limit, *, context):
    selected, seen, plans, edges, seeds = [], {}, [], set(), set()
    used = 0
    for root in pool:
        if key(root) in seen:
            continue
        # Each explicitly selected private document remains ahead of source graph expansion.
        group = select_with_companions(db, run, [root], limit-len(selected), context=context)
        for row in group:
            if key(row) not in seen:
                seen[key(row)] = row
                selected.append(row)
        if len(selected) >= limit:
            break
        sid = root['source_id']
        if not sid or not root.get('text') or sid in seeds or len(seeds) >= MAX_SEEDS:
            continue
        seeds.add(sid)
        incident = db.scalars(select(AuthorityRelationship).where(or_(
            AuthorityRelationship.source_id == sid, AuthorityRelationship.target_id == sid))
            .order_by(AuthorityRelationship.id).limit(MAX_INCIDENT)).all()
        for edge in incident:
            if edge.id in edges or len(plans) >= MAX_RELATIONSHIPS:
                continue
            edges.add(edge.id)
            if not authority.current(db, edge):
                continue
            pair = [endpoint_row(db, run, edge.payload[k], context) for k in ('source', 'target')]
            if any(row is None for row in pair):
                continue
            if any(key(row) in seen and seen[key(row)] != row for row in pair):
                continue
            fresh = [row for row in pair if key(row) not in seen]
            size = len(canonical(edge.payload)) + 2048
            if len(selected)+len(fresh) > limit or used+size > MAX_BYTES:
                continue
            for row in fresh:
                seen[key(row)] = row
                selected.append(row)
            plans.append((edge.id, key(pair[0]), key(pair[1])))
            used += size
    return selected, plans


def snapshot(db, edge, source_evidence, target_evidence):
    record = authority.review_record(db, edge)
    if not record:
        return None
    return {'version': VERSION, 'relationship_id': edge.id, 'revision': edge.revision,
            'review_id': record.id, 'review_sequence': record.sequence,
            'review_sha256': record.payload_sha256, 'review_expires_at': record.payload['expires_at'],
            'source_evidence_id': source_evidence.id, 'target_evidence_id': target_evidence.id,
            'source': edge.payload['source'], 'target': edge.payload['target'],
            'source_kind': source_evidence.source_kind, 'target_kind': target_evidence.source_kind,
            'relation': edge.relation, 'scope': edge.payload['scope'],
            'claim_support_verified': False, 'complete_graph_verified': False,
            'instructions_are_untrusted': True}


def persist(db, run, plans, rows):
    records = {key(row): db.get(Evidence, row['id']) for row in rows}
    for edge_id, a, b in plans:
        edge = db.get(AuthorityRelationship, edge_id)
        payload = snapshot(db, edge, records[a], records[b])
        db.add(RunAuthorityEvidence(run_id=run.id, relationship_id=edge.id,
            source_evidence_id=records[a].id, target_evidence_id=records[b].id,
            payload=payload, payload_sha256=digest(canonical(payload))))
    db.flush()


def packets(db, run, action='model_input', *, context=None, lock=False):
    context = context or rights.runtime_context(db, run)
    records = db.scalars(select(RunAuthorityEvidence).where(RunAuthorityEvidence.run_id == run.id)
                         .order_by(RunAuthorityEvidence.relationship_id).limit(MAX_RELATIONSHIPS+1)).all()
    if len(records) > MAX_RELATIONSHIPS:
        fail('SOURCE_CHANGED', 'Relationship evidence exceeds its recorded bound.', 409)
    result = []
    for item in records:
        query = select(AuthorityRelationship).where(AuthorityRelationship.id == item.relationship_id)
        if lock:
            query = query.with_for_update()
        edge = db.scalar(query.execution_options(populate_existing=True)) if item.relationship_id else None
        pair = [db.get(Evidence, eid) if eid else None for eid in (item.source_evidence_id, item.target_evidence_id)]
        if not edge or not authority.current(db, edge) or any(e is None or e.run_id != run.id for e in pair):
            fail('SOURCE_CHANGED', 'A reviewed relationship dependency is unavailable.', 409)
        for e, name in zip(pair, ('source', 'target')):
            source = db.get(Source, e.source_id, populate_existing=True) if e.source_id else None
            endpoint = edge.payload[name]
            expected_access = ('primary_text_reviewed' if source and (source.kind in {'standard', 'rule'}
                               or (source.policy or {}).get('sec_core')) else 'secondary_text_reviewed')
            if (not source or e.source_kind != source.kind or e.title != source.title or e.access != expected_access
                    or e.source_id != endpoint['source_id'] or not admitted(source, run, context, action)
                    or not rights.evidence_allowed(db, e, action, context=context)
                    or not coordinate_evidence.current(source, e)
                    or any(e.extraction_context['citation'].get(k) != v for k, v in endpoint.items())):
                fail('SOURCE_CHANGED', 'A relationship passage no longer passes independent evidence checks.', 409)
        expected = snapshot(db, edge, *pair)
        if item.payload != expected or item.payload_sha256 != digest(canonical(expected)):
            fail('SOURCE_CHANGED', 'The relationship evidence revision changed.', 409)
        result.append(expected)
    if len(canonical(result)) > MAX_BYTES:
        fail('SOURCE_CHANGED', 'Relationship evidence exceeds its output bound.', 409)
    return result


def release_check(db, run, visited=None):
    """Called after output release has locked the entire source lineage, before commit."""
    from ..models import Memo, Run
    visited = set(visited or ())
    if run.id in visited or len(visited) >= 20:
        fail('DEPENDENCY_CYCLE', 'Relationship output dependencies require review.', 409)
    visited.add(run.id)
    packets(db, run, 'quote', lock=True)
    memo_id = (run.inputs or {}).get('memo_id')
    if memo_id:
        memo = db.get(Memo, memo_id)
        parent = db.get(Run, memo.run_id) if memo and memo.run_id else None
        if parent:
            release_check(db, parent, visited)
