"""Bounded lexical/exact-reference retrieval, with permissions applied before model input.

This working baseline deliberately does not claim to have a production semantic index.
The pluggable ranker can be replaced with PostgreSQL FTS + pgvector after evaluation.
"""
import math
import re
from collections import Counter
from sqlalchemy import select
from ..models import Source, Document
from .rights import allowed


def tokens(text):
    return re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', text.lower())


def score(query, text):
    counts = Counter(tokens(text))
    terms = set(tokens(query))
    if not terms:
        return 0.0
    size = max(len(tokens(text)), 1)
    return sum((1 + math.log(1 + counts[t])) for t in terms if t in counts) / math.sqrt(size / 100 + 1)


def search(db, run, query, limit=12):
    candidates = []
    period = run.context.get('period_end')
    framework = run.context.get('framework', 'US_GAAP')
    knowledge_date = run.context.get('knowledge_date')
    # A concrete first-release corpus bound, surfaced in deployment docs.
    sources = db.scalars(select(Source).where(Source.enabled.is_(True)).limit(2000)).all()
    for source in sources:
        # Staged content is not an approved source, even when its metadata is public.
        if not source.reviewed:
            continue
        if (source.policy or {}).get('requires_technical_review') and not allowed(source, 'model_input'):
            continue
        if framework not in {'BOTH', 'UNKNOWN'} and source.framework not in {framework, 'BOTH', 'AUDIT'}:
            continue
        if period and ((source.effective_from and source.effective_from > period) or
                       (source.effective_to and source.effective_to < period)):
            continue
        if (source.policy or {}).get('sec_core'):
            from ..sec_core.integration import evidence_for
            evidence = evidence_for(source, run)
            if evidence is not None:
                candidates.append({**evidence, '_score': score(query, source.title + '\n' + (source.text or ''))})
            continue
        if knowledge_date:
            from datetime import datetime, timezone
            if datetime.fromtimestamp(source.created_at, timezone.utc).date().isoformat() > knowledge_date:
                continue
        if allowed(source, 'model_input') and allowed(source, 'store_text') and allowed(source, 'quote'):
            for i, para in enumerate(re.split(r'\n\s*\n', source.text or '')):
                if not para.strip():
                    continue
                for offset in range(0, len(para), 3000):
                    part = para[offset:offset+3000]
                    candidates.append({'source_id': source.id, 'document_id': None,
                        'title': source.title, 'locator': f'Section {i+1}' + (f' part {offset//3000+1}' if offset else ''),
                        'text': part, 'access': 'primary_text_reviewed' if source.kind in {'standard', 'rule'} else 'secondary_text_reviewed',
                        'source_kind': source.kind, 'policy_version': source.policy_version,
                        '_score': score(query, source.title + '\n' + part)})
        else:
            candidates.append({'source_id': source.id, 'document_id': None, 'title': source.title,
                               'locator': source.title, 'text': None, 'access': 'reference_only',
                               'source_kind': source.kind, 'policy_version': source.policy_version,
                               '_score': score(query, source.title)})
    for doc_id in run.document_ids:
        doc = db.get(Document, doc_id)
        # Defense in depth: caller already verifies membership and all selected documents.
        if not doc or doc.workspace_id != run.workspace_id or doc.status != 'ready':
            continue
        for chunk in doc.chunks:
            candidates.append({'source_id': None, 'document_id': doc.id, 'title': doc.name,
                               'locator': chunk['locator'], 'text': chunk['text'],
                               'access': 'user_document', 'source_kind': 'user_document', 'policy_version': None,
                               '_score': score(query, chunk['text']) + 0.1})
    ranked = sorted(candidates, key=lambda x: x['_score'], reverse=True)
    selected = [x for x in ranked if x['_score'] > 0][:limit]
    for row in selected:
        row.pop('_score', None)
    return selected
