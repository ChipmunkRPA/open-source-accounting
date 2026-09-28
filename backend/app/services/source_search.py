"""Explicit authorized corpus indexing. No provider calls or inferred source approval."""
import re
from sqlalchemy import select, func, literal_column, union
from ..models import Source, SourceSearchIndex, Audit
from ..sec_core.core import canonical, digest
from ..errors import fail
from . import rights, editorial

VERSION='postgres-simple-lexical-1'
INDEX_CONTEXT={'route':'source_index','audience':'internal_ingestion'}
MAX_BODY_CHARS=100000


def revision(source):
    return digest(canonical({'rights':rights.revision(source),'editorial':editorial.revision(source),
        'policy_version':source.policy_version,'spreadsheet':source.policy.get('intake_spreadsheet'),
        'technical_record':source.policy.get('technical_review_record_id'),
        'applicability_record':source.policy.get('applicability_record_id')}))


def index_allowed(source, visited=None):
    # Global source index cannot store seat/workspace/provider-scoped licensed material.
    seen=set(visited or ())
    if not source or source.id in seen or len(seen)>=10 or source.policy.get('scope'):
        return False
    seen.add(source.id)
    if not all(rights.allowed(source,op,context=INDEX_CONTEXT) for op in ('embed','store_text')):
        return False
    if source.policy.get('intake_parent_id'):
        from sqlalchemy.orm import object_session
        db=object_session(source)
        return bool(db and index_allowed(db.get(Source,source.policy['intake_parent_id']),seen))
    return True


def current(source, entry):
    return bool(entry and entry.index_version==VERSION and entry.revision==revision(source)
                and entry.search_text==source.title+'\n'+(source.text or '') and index_allowed(source))


def rebuild(db, source, expected_revision, actor_id):
    if expected_revision!=revision(source):
        fail('REVISION_CONFLICT','Reload the exact source revision before indexing.',409)
    if not index_allowed(source):
        fail('SOURCE_POLICY_BLOCK','Current unscoped indexing and text-storage permission and required reviews are needed.',403)
    if not source.text or len(source.text)>MAX_BODY_CHARS:
        fail('INDEX_SOURCE_SIZE','Index a nonempty staged source passage of at most 100,000 characters; split larger works through intake.',422)
    entry=db.get(SourceSearchIndex,source.id)
    if current(source,entry):
        return entry
    if entry is None:
        entry=SourceSearchIndex(source_id=source.id);db.add(entry)
    entry.revision=revision(source);entry.index_version=VERSION
    entry.search_text=source.title+'\n'+source.text
    from ..models import now
    entry.created_at=now()
    db.add(Audit(actor_id=actor_id,action='source.indexed',target_id=source.id,
                 detail={'index_version':VERSION,'revision':entry.revision,'characters':len(source.text)}))
    db.flush()
    return entry


def remove(db, source, actor_id):
    entry=db.get(SourceSearchIndex,source.id)
    if entry:db.delete(entry)
    db.add(Audit(actor_id=actor_id,action='source.index_removed',target_id=source.id))
    db.flush()


def query_terms(query):
    # Tokens cannot introduce tsquery operators or SQL. OR retains lexical recall.
    terms=sorted(set(re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)*',query.lower())))
    if len(terms)>64 or any(len(term)>256 for term in terms):
        fail('RETRIEVAL_QUERY_LIMIT','Use at most 64 distinct lexical terms of at most 256 characters.',422)
    return terms


def matching_ids(query):
    terms=query_terms(query)
    needle=func.to_tsquery(literal_column("'simple'"),' | '.join(terms))
    titles=select(Source.id).where(func.to_tsvector(literal_column("'simple'"),Source.title).op('@@')(needle))
    bodies=select(SourceSearchIndex.source_id).where(
        func.to_tsvector(literal_column("'simple'"),SourceSearchIndex.search_text).op('@@')(needle))
    return union(titles,bodies)


def candidates(db, query):
    """Stream all matching IDs; never take the first arbitrary 2,000 sources."""
    statement=select(Source).where(Source.enabled.is_(True),Source.reviewed.is_(True))
    postgres=db.bind.dialect.name=='postgresql'
    if postgres:
        if not query_terms(query):return
        statement=statement.where(Source.id.in_(matching_ids(query)))
    for source in db.scalars(statement.order_by(Source.id).execution_options(yield_per=100)):
        if postgres:
            entry=db.get(SourceSearchIndex,source.id)
            body_indexed=current(source,entry)
            # An old index cannot reveal a changed/revoked body. Metadata hits remain references.
            yield source,body_indexed
        else:
            # SQLite is a development compatibility path, not an indexed scale claim.
            yield source,True
