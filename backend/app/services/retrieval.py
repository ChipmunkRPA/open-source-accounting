"""Bounded lexical/exact-reference retrieval, with permissions applied before model input.

PostgreSQL uses authorized GIN lexical indexes; SQLite streams a development fallback.
Semantic embeddings and reranker evaluation remain separate, unimplemented gates.
"""
import math
import re
from collections import Counter
from ..models import Document
from .rights import allowed
from .applicability import applies
from .dependencies import allowed as dependencies_allowed
from .spreadsheet_context import source_context, document_context


def tokens(text):
    return re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*', text.lower())


def score(query, text):
    counts = Counter(tokens(text))
    terms = set(tokens(query))
    if not terms:
        return 0.0
    size = max(len(tokens(text)), 1)
    return sum((1 + math.log(1 + counts[t])) for t in terms if t in counts) / math.sqrt(size / 100 + 1)


def search(db, run, query, limit=12, *, rights_context=None):
    candidates = []
    period = run.context.get('period_end')
    framework = run.context.get('framework', 'US_GAAP')
    from .source_search import candidates as indexed_candidates
    for source, body_indexed in indexed_candidates(db, query):
        # Bound retained ranking candidates without excluding later corpus matches.
        if len(candidates)>max(limit*4,100):
            candidates=sorted(candidates,key=lambda x:x["_score"],reverse=True)[:limit]
        # Staged content is not an approved source, even when its metadata is public.
        if not source.reviewed:
            continue
        if (source.policy or {}).get('requires_technical_review') and not allowed(source, 'model_input', context=rights_context):
            continue
        if framework not in {'BOTH', 'UNKNOWN'} and source.framework not in {framework, 'BOTH', 'AUDIT'}:
            continue
        if period and ((source.effective_from and source.effective_from > period) or
                       (source.effective_to and source.effective_to < period)):
            continue
        if not body_indexed:
            candidates.append({"source_id":source.id,"document_id":None,"title":source.title,
                "locator":source.title,"text":None,"access":"reference_only","source_kind":source.kind,
                "policy_version":source.policy_version,"_score":score(query,source.title)})
            continue
        if (source.policy or {}).get('sec_core'):
            from ..sec_core.integration import evidence_for
            evidence = evidence_for(source, run, rights_context=rights_context)
            if evidence is not None:
                candidates.append({**evidence, '_score': score(query, source.title + '\n' + (source.text or ''))})
            continue
        if not applies(source, run.context) or not dependencies_allowed(source,'model_input',context=rights_context,accounting_context=run.context):
            continue
        if allowed(source, 'model_input', context=rights_context) and allowed(source, 'store_text', context=rights_context) and allowed(source, 'quote', context=rights_context):
            from . import passage_context
            for i,offset,start,end,part in passage_context.segments(source.text or ''):
                sheet = (source.policy or {}).get('intake_spreadsheet')
                locator = f'Section {i+1}' + (f' part {offset//3000+1}' if offset else '')
                provenance = {}
                if sheet:
                    locator = source.policy['intake_locator'] + f' (paragraph {i+1}, characters {offset+1}–{offset+len(part)})'
                    provenance = {'extraction_context': source_context(source)}
                elif passage_context.required(source):
                    snapshot=passage_context.packet(source,start,end)
                    if snapshot is None:continue
                    locator=passage_context.locator(snapshot)
                    provenance={'extraction_context':snapshot}
                candidates.append({'source_id': source.id, 'document_id': None,
                    'title': source.title, 'locator': locator, **provenance,
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
                               'extraction_context': document_context(doc,chunk),
                               'access': 'user_document', 'source_kind': 'user_document', 'policy_version': None,
                               '_score': score(query, chunk['text']) + 0.1})
    ranked = sorted(candidates, key=lambda x: x['_score'], reverse=True)
    selected = [x for x in ranked if x['_score'] > 0][:limit]
    for row in selected:
        row.pop('_score', None)
        row.setdefault('extraction_context',{})
    return selected
