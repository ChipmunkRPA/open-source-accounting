"""Public EDGAR correspondence archive and transparent, non-model topic analysis."""
from collections import Counter
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
import re
from sqlalchemy import select
from ..models import Source, IntakeWork
from ..sec_comment_schemas import Catalog, Correspondence
from .asu_tracking import binding, window

VERSION='sec-comment-topics-1'
TOPICS={
    'Non-GAAP measures': r'\bnon[-\s]?gaap\b|\bitem\s+10\(e\)',
    'Segments': r'\bsegment(?:s|ation)?\b|\bASC\s*280\b',
    'Revenue recognition': r'\brevenue recognition\b|\bASC\s*606\b',
    'Materiality and errors': r'\bmateriality\b|\bSAB\s*(?:99|108|1\.[MN])\b|\bASC\s*250\b',
    'Internal controls': r'\binternal controls?\b|\bmaterial weakness(?:es)?\b|\bICFR\b',
    'Liquidity and going concern': r'\bliquidity\b|\bgoing concern\b',
    'Business combinations': r'\bbusiness combinations?\b|\bASC\s*805\b',
    'Fair value and impairment': r'\bfair value\b|\bimpairment\b',
    'Taxes': r'\bincome tax(?:es)?\b|\bASC\s*740\b',
    'Cybersecurity': r'\bcybersecurity\b',
}
NOTICE=('Selected public filing-review correspondence, not a complete SEC archive. Letter/filing dates are not public-release dates. '
        'Letters are fact-specific staff correspondence, not findings of wrongdoing or authoritative rules. '
        'Company responses and draft analysis are not staff acceptance or professional approval. Rulemaking comments are a separate collection.')


@lru_cache(maxsize=1)
def catalog():
    return Catalog.model_validate_json((Path(__file__).resolve().parents[1]/'sec_comment_data/catalog.json').read_text())


def analyze(text, locator):
    findings=[]
    for topic,pattern in TOPICS.items():
        hits=[];count=0
        for m in re.finditer(pattern,text,re.I):
            count+=1
            if len(hits)<20:hits.append(m)
        if hits:
            findings.append({'topic':topic,'locator':locator,'hits':[{'term':m.group(), 'start':m.start(),'end':m.end()} for m in hits[:20]],
                             'total_matches':count,'interpretation':'Lexical mention only; read the full letter and response.'})
    return findings


def records(db):
    merged={}
    for r in catalog().records:
        item=r.model_dump(mode='json')
        item.update(kind='reference_only',professional_review='unreviewed',outcome='not_established',
                    archive_artifacts=[],findings=[],analysis_partial=False,analysis_method='original_editorial_draft')
        merged[r.accession]=item
    # Stream staged records; never inspect private Documents. Explicit scan limit is reported.
    query=select(Source).join(IntakeWork,IntakeWork.source_id==Source.policy['intake_parent_id'].as_string()).where(
        Source.enabled.is_(True),Source.policy['intake_extraction_id'].as_string().is_not(None),
        IntakeWork.family_id=='SEC_FILINGS',IntakeWork.manifest['sec_correspondence'].as_string().is_not(None)).order_by(Source.id)
    scanned=0;truncated=False
    for source in db.scalars(query).yield_per(100):
        scanned+=1
        if scanned>20000:
            truncated=True;break
        info=binding(db,source)
        if not info:continue
        work,artifact,extraction,_,_=info
        metadata=work.manifest.get('sec_correspondence')
        if not metadata:continue
        try:r=Correspondence.model_validate(metadata)
        except ValueError:continue
        if r.url!=source.canonical_url:continue
        item=merged.get(r.accession)
        if item and item['url']!=r.url:continue  # Conflicting document requires explicit reconciliation.
        if item is None:
            item=r.model_dump(mode='json')
            item.update(topics=[],staff_concern='Not independently summarized.',company_response='Not independently summarized.',
                analysis='Automatic topic matches identify passages for reading; no position or outcome is inferred.',
                follow_up='Reconcile the complete public correspondence chain and reviewed filing.',
                kind='authorized_archive',professional_review='unreviewed',outcome='not_established',
                archive_artifacts=[],findings=[],analysis_partial=False,analysis_method=VERSION)
            merged[r.accession]=item
        item['kind']='authorized_archive'
        proof={'artifact_id':artifact.id,'raw_sha256':artifact.raw_sha256,'acquired_at':artifact.acquired_at,
               'extraction_id':extraction.id,'normalized_sha256':extraction.normalized_sha256,'parser_version':extraction.parser_version}
        if proof not in item['archive_artifacts']:
            if len(item['archive_artifacts'])<100:item['archive_artifacts'].append(proof)
            else:item['analysis_partial']=True
        hits=analyze(source.text or '',source.policy.get('intake_locator','unverified'))
        remaining=max(0,100-len(item['findings']))
        if len(hits)>remaining:item['analysis_partial']=True
        item['findings'].extend({**h,'source_id':source.id,'text_sha256':source.policy['content_sha256'],
                                 'analysis_version':VERSION} for h in hits[:remaining])
        item['topics']=sorted(set(item['topics'])|{h['topic'] for h in hits})
    return sorted(merged.values(),key=lambda r:(r['letter_date'],r['accession']),reverse=True),truncated


def listing(db,q='',topic='',form='',recent=True,offset=0,limit=25,today=None):
    today=today or datetime.now(timezone.utc).date()
    rows,truncated=records(db)
    rows=[r for r in rows if (not recent or window(today)<=date.fromisoformat(r['letter_date'])<=today)
          and (not form or r['form']==form) and (not topic or topic in r['topics'])
          and q.casefold() in ' '.join([r['company'],r['cik'],r['accession'],r['reviewed_filing'],*r['topics']]).casefold()]
    return {'items':rows[offset:offset+limit],'total':len(rows),'next_offset':offset+limit if offset+limit<len(rows) else None,
        'window_start':window(today).isoformat() if recent else None,'window_end':today.isoformat(),
        'topics':list(TOPICS),'topic_counts':dict(Counter(t for r in rows for t in set(r['topics']))),
        'coverage':{'reference_records':sum(r['kind']=='reference_only' for r in rows),
                    'archived_records':sum(bool(r['archive_artifacts']) for r in rows),
                    'complete_universe':False,'scan_truncated':truncated},
        'catalog_version':catalog().version,'catalog_checked_on':str(catalog().checked_on),
        'refresh':'Authorized retained corpus is read on every request. External discovery is not activated.',
        'notice':NOTICE}
