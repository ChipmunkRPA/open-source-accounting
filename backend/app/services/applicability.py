"""General source date/entity applicability, independent from permissions and technical review."""
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import object_session
from ..models import ApplicabilityReview, Audit, now
from ..sec_core.core import canonical, digest
from ..errors import fail
from . import editorial, parser_review, rights, output_rights


def parser_record(db,source):
    ex=source.policy.get('intake_extraction_id')
    row=parser_review.latest(db,ex) if ex else None
    return row.id if row else None


def current(source):
    db=object_session(source)
    policy=source.policy or {}
    rid=policy.get('applicability_record_id')
    if not db or not rid:return None
    row=db.get(ApplicabilityReview,rid)
    if not row or row.source_id!=source.id or not row.reviewer_id or row.payload_sha256!=digest(canonical(row.payload)):return None
    p=row.payload
    if (p.get('decision')!='approved' or p.get('expires_at',0)<=now()
            or p.get('reviewer_id')!=row.reviewer_id or p.get('expected_review_revision')!=editorial.revision(source)
            or p.get('technical_record_id')!=policy.get('technical_review_record_id') or not editorial.current(source)
            or p.get('effective_from')!=source.effective_from or p.get('effective_to')!=source.effective_to):return None
    if policy.get('intake_extraction_id') and (not parser_review.current(source) or p.get('parser_record_id')!=parser_record(db,source)):
        return None
    return row


def applies(source,context):
    policy=source.policy or {}
    required=any(context.get(k) for k in ('period_start','period_end','knowledge_date')) or policy.get('intake_extraction_id') or policy.get('sec_core') or policy.get('applicability_record_id')
    if not required:return True
    row=current(source)
    if row is None:return False
    p=row.payload
    if (context.get('framework') not in p['frameworks'] or context.get('entity_type') not in p['entity_types']
            or p['conditions'] or (p['audit_regimes'] and context.get('audit_regime') not in p['audit_regimes'])):return False
    if (policy.get('intake_extraction_id') or policy.get('sec_core')) and not context.get('period_end'):return False
    try:
        for key in ('period_start','period_end'):
            if context.get(key):
                period=date.fromisoformat(str(context[key]))
                if period<date.fromisoformat(p['effective_from']) or (p['effective_to'] and period>date.fromisoformat(p['effective_to'])):return False
        if context.get('knowledge_date') and date.fromisoformat(str(context['knowledge_date']))<date.fromisoformat(p['publicly_available_at']):return False
    except (ValueError,TypeError):return False
    return True


def record(db,source,payload,actor_id):
    if source.created_by==actor_id:fail('SEPARATION_OF_DUTIES','A different reviewer must assess applicability.',403)
    if payload.expected_policy_version!=source.policy_version or payload.expected_review_revision!=editorial.revision(source):
        fail('REVISION_CONFLICT','Reload the source and exact technical revision.',409)
    if payload.expires_at<=now():fail('REVIEW_EXPIRED','Choose an explicit future expiry.',422)
    if payload.decision=='approved':
        rights.require(source,'display_full')
        if not editorial.current(source) or (source.policy.get('intake_extraction_id') and not parser_review.current(source)):
            fail('REVIEW_REQUIRED','Current technical and any required parser review must precede applicability approval.',409)
        if source.framework not in {'BOTH','AUDIT',*payload.frameworks}:
            fail('REVIEW_SCOPE','The source framework must be represented in the reviewed scope.',422)
        if source.framework=='AUDIT' and not payload.audit_regimes:
            fail('REVIEW_SCOPE','Audit sources require explicit audit-regime scope.',422)
    terms={**payload.model_dump(mode='json'),'reviewer_id':actor_id,
           'technical_record_id':source.policy.get('technical_review_record_id'),
           'parser_record_id':parser_record(db,source)}
    row=ApplicabilityReview(source_id=source.id,reviewer_id=actor_id,payload=terms,payload_sha256=digest(canonical(terms)))
    db.add(row);db.flush()
    source.policy={**source.policy,'applicability_record_id':row.id,'applicability_review_status':payload.decision}
    if payload.decision=='approved':
        source.effective_from=terms['effective_from'];source.effective_to=terms['effective_to']
    source.policy_version+=1
    db.add(Audit(actor_id=actor_id,action='content.applicability_review',target_id=source.id,
        detail={'record_id':row.id,'payload_sha256':row.payload_sha256,'decision':payload.decision}))
    db.commit()
    return {'record_id':row.id,'policy_version':source.policy_version,'current':current(source) is not None,
            'requires_case_review':bool(payload.conditions),'agent_admission_granted':False}


def history(db,source):
    rights.require(source,'display_full')
    rows=db.scalars(select(ApplicabilityReview).where(ApplicabilityReview.source_id==source.id)
                    .order_by(ApplicabilityReview.payload['expected_policy_version'].as_integer().desc(),ApplicabilityReview.id).limit(100)).all()
    supporting=output_rights.history_sources(db,source)
    result={'source_attributions':output_rights.notices(db,supporting),'source_id':source.id,'current_record_id':source.policy.get('applicability_record_id'),
            'current':current(source) is not None,'items':[{'id':r.id,'created_at':r.created_at,
            'payload':r.payload,'payload_sha256':r.payload_sha256} for r in rows]}
    output_rights.release(db,supporting,result);db.commit();return result
