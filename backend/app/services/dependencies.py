"""Exact staged publication dependencies; links alone never admit original drafts."""
from sqlalchemy.orm import object_session
from ..models import Source, EditorialReview
from ..errors import fail
from . import editorial


def locator(source):
    p=source.policy or {}
    return p.get('intake_locator') or p.get('sec_core',{}).get('locator') or source.canonical_url


def validate_bindings(db,source,bindings):
    from .rights import require
    refs=set(source.policy.get('content_reference_ids',[]))
    pairs=set()
    for b in bindings:
        pair=(b.reference_id,b.source_id)
        target=db.get(Source,b.source_id)
        if b.reference_id not in refs or pair in pairs or b.source_id==source.id:
            fail('REFERENCE_BINDING_INVALID','Choose distinct listed references and different staged sources.',422)
        pairs.add(pair)
        if (not target or not target.text or target.policy_version!=b.policy_version
                or editorial.revision(target)!=b.review_revision or locator(target)!=b.locator):
            fail('REFERENCE_BINDING_STALE','Reload the exact staged source and locator.',409)
        require(target,'display_full')
    if {b.reference_id for b in bindings}!=refs:
        fail('REFERENCE_BINDING_INCOMPLETE','Bind every listed reference before submitting a dependency set.',422)


def allowed(source,action,*,context=None,accounting_context=None,visited=None,_budget=None):
    """Runtime dependency checks do not alter public educational/draft display rights."""
    budget=_budget if _budget is not None else [500]
    budget[0]-=1
    if budget[0]<0:return False
    policy=source.policy or {}
    db=object_session(source)
    row=db.get(EditorialReview,policy.get('technical_review_record_id')) if db and policy.get('technical_review_record_id') else None
    bindings=row.payload.get('reference_bindings',[]) if row else []
    required=bool(policy.get('content_item_id'))
    if not required and not bindings:return True
    if not row or not editorial.current(source):return False
    refs=set(policy.get('content_reference_ids',[]))
    if required and (not refs or {b.get('reference_id') for b in bindings}!=refs):return False
    seen=set(visited or ())
    if source.id in seen or len(seen)>=10:return False
    seen.add(source.id)
    from .rights import allowed as rights_allowed
    from .applicability import applies
    for b in bindings:
        target=db.get(Source,b.get('source_id'))
        if (not target or target.id in seen or not target.text or target.policy_version!=b.get('policy_version')
                or editorial.revision(target)!=b.get('review_revision') or locator(target)!=b.get('locator')):return False
        # The dependency must permit the actual operation, not merely viewing its metadata.
        if not rights_allowed(target,action,context=context,_visited=seen,_check_dependencies=False):return False
        if target.policy.get('requires_technical_review') and not editorial.current(target):return False
        if accounting_context is not None and not applies(target,accounting_context):return False
        if not allowed(target,action,context=context,accounting_context=accounting_context,visited=seen,_budget=budget):return False
    return True


def output_bindings(source, *, all_bodies=False):
    """Retain obligations from all decisions for this exact body, even after revocation.

    These are output obligations, not current evidence approval. No text is copied.
    """
    from sqlalchemy import select
    from ..sec_core.core import canonical,digest
    db=object_session(source)
    if db is None:return []
    query=select(EditorialReview).where(EditorialReview.source_id==source.id)
    if not all_bodies:query=query.where(EditorialReview.payload['content_sha256'].as_string()==digest(source.text or ''))
    rows=db.scalars(query.limit(501)).all()
    if len(rows)>500:fail('DEPENDENCY_LIMIT','Publication review history requires bounded reconciliation.',409)
    bindings={}
    for row in rows:
        if row.payload_sha256!=digest(canonical(row.payload)):
            fail('SOURCE_CHANGED','Publication dependency history failed integrity checks.',409)
        for b in row.payload.get('reference_bindings',[]):
            key=(b['source_id'],b['review_revision'],b['locator'])
            bindings[key]=b
    if len(bindings)>500:fail('DEPENDENCY_LIMIT','Publication dependencies require bounded reconciliation.',409)
    return list(bindings.values())


def output_allowed(source,action,*,context=None,visited=None,_budget=None):
    """Current operation rights apply to every retained exact-body dependency."""
    from fastapi import HTTPException
    from .rights import allowed as rights_allowed
    try:bindings=output_bindings(source)
    except HTTPException:return False
    if not bindings:return True
    budget=_budget if _budget is not None else [500]
    budget[0]-=1
    seen=set(visited or ())
    if source.id in seen or len(seen)>=10 or budget[0]<0:return False
    seen.add(source.id)
    db=object_session(source)
    for b in bindings:
        target=db.get(Source,b['source_id'])
        if (not target or target.id in seen or editorial.revision(target)!=b['review_revision']
                or locator(target)!=b['locator']):return False
        if not rights_allowed(target,action,context=context,_visited=seen,_check_dependencies=False):return False
        if not output_allowed(target,action,context=context,visited=seen,_budget=budget):return False
    return True
