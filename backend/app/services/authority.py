"""One-hop reviewed authority links; never transfers rights, authority or applicability."""
from fastapi import HTTPException
from sqlalchemy import select,or_,update
from ..models import Source,AuthorityRelationship,AuthorityReview,Audit,now,uid
from ..errors import fail
from ..sec_core.core import canonical,digest
from ..authority_schemas import RelationshipProposal,RelationshipDecision
from . import citation_lookup,rights,counsel,output_rights

VERSION='authority-relationships-1'


def integrity(edge):
    p=edge.payload
    if not isinstance(p,dict):return False
    try:RelationshipProposal.model_validate({k:v for k,v in p.items() if k not in {'created_by','version'}})
    except (ValueError,TypeError):return False
    return bool(isinstance(p,dict) and edge.created_by and p.get('version')==VERSION
        and digest(canonical(p))==edge.revision and p.get('created_by')==edge.created_by
        and p.get('source',{}).get('source_id')==edge.source_id
        and p.get('target',{}).get('source_id')==edge.target_id and p.get('relation')==edge.relation)


def endpoints(db,edge,lock=False):
    result={}
    for sid in sorted({edge.source_id,edge.target_id}):
        result[sid]=counsel.lock_source(db,sid) if lock else db.get(Source,sid)
    return result


def validate_endpoint(source,endpoint):
    citation_lookup.authorize(source)
    a,b=endpoint['character_start'],endpoint['character_end']
    if not 0<=a<b<=len(source.text) or b-a>citation_lookup.PASSAGE_CHARS:
        fail('CITATION_RANGE','Relationship passages must be bounded exact source ranges.',422)
    actual=citation_lookup.descriptor(source,a,b)
    if any(actual[k]!=endpoint[k] for k in ('source_id','revision','locator','character_start','character_end','passage_text_sha256')):
        fail('REVISION_CONFLICT','Reload both exact passage citations before proposing or approving a relationship.',409)
    return actual


def valid_endpoints(db,edge,action='display_full',context=None):
    if not integrity(edge):return False
    try:
        for key in ('source','target'):
            endpoint=edge.payload[key];source=db.get(Source,endpoint['source_id'])
            validate_endpoint(source,endpoint)
            if not rights.allowed(source,action,context=context):return False
    except (HTTPException,KeyError,TypeError,ValueError):return False
    return True


def review_record(db,edge):
    record=db.get(AuthorityReview,edge.current_review_id) if edge.current_review_id else None
    if not record or not record.reviewer_id or record.reviewer_id==edge.created_by:return None
    p=record.payload
    if not isinstance(p,dict):return None
    try:RelationshipDecision.model_validate({k:v for k,v in p.items() if k!='reviewer_id'})
    except (ValueError,TypeError):return None
    if (not isinstance(p,dict) or record.relationship_id!=edge.id or record.sequence!=edge.sequence
        or digest(canonical(p))!=record.payload_sha256 or p.get('reviewer_id')!=record.reviewer_id
        or p.get('expected_revision')!=edge.revision or p.get('expected_sequence')!=edge.sequence-1):return None
    return record


def current(db,edge):
    if not valid_endpoints(db,edge):return False
    record=review_record(db,edge)
    return bool(record and record.payload.get('decision')=='approved' and record.payload.get('expires_at',0)>now())


def propose(db,payload,actor_id):
    # Locks use the same deterministic order as output release and source amendments.
    for endpoint in sorted((payload.source,payload.target),key=lambda e:e.source_id):
        source=counsel.lock_source(db,endpoint.source_id)
        validate_endpoint(source,endpoint.model_dump())
        rights.require(source,'store_text')
    body={**payload.model_dump(mode='json'),'created_by':actor_id,'version':VERSION}
    revision=digest(canonical(body));edge_id=uid()
    if db.bind.dialect.name=='postgresql':from sqlalchemy.dialects.postgresql import insert
    else:from sqlalchemy.dialects.sqlite import insert
    created=db.execute(insert(AuthorityRelationship).values(id=edge_id,source_id=payload.source.source_id,
        target_id=payload.target.source_id,relation=payload.relation,revision=revision,payload=body,
        created_by=actor_id,created_at=now(),sequence=0).on_conflict_do_nothing(index_elements=['revision']).returning(AuthorityRelationship.id)).scalar_one_or_none()
    edge=db.scalar(select(AuthorityRelationship).where(AuthorityRelationship.revision==revision))
    if created:db.add(Audit(actor_id=actor_id,action='authority.proposed',target_id=edge.id,detail={'revision':revision}))
    return edge


def decide(db,edge_id,payload,reviewer_id):
    edge=db.get(AuthorityRelationship,edge_id)
    if not edge:fail('NOT_FOUND','Relationship not found.',404)
    endpoints(db,edge,lock=True)
    if db.bind.dialect.name=='sqlite':
        db.execute(update(AuthorityRelationship).where(AuthorityRelationship.id==edge_id).values(sequence=AuthorityRelationship.sequence))
    edge=db.scalar(select(AuthorityRelationship).where(AuthorityRelationship.id==edge_id).with_for_update().execution_options(populate_existing=True))
    if not integrity(edge):fail('RELATIONSHIP_INTEGRITY','Relationship integrity requires investigation.',409)
    if edge.created_by==reviewer_id:fail('SEPARATION_OF_DUTIES','Another technical reviewer must review the relationship.',403)
    if payload.expected_revision!=edge.revision or payload.expected_sequence!=edge.sequence:
        fail('REVISION_CONFLICT','Reload the relationship review sequence.',409)
    if payload.decision=='approved':
        # Validate the stored schema as well as its digest, not arbitrary database JSON.
        RelationshipProposal.model_validate({k:v for k,v in edge.payload.items() if k not in {'created_by','version'}})
        if not valid_endpoints(db,edge):fail('SOURCE_CHANGED','Both exact source passages must remain readable and unchanged.',409)
        for source in endpoints(db,edge).values():rights.require(source,'store_text')
        if payload.expires_at<=now():fail('REVIEW_EXPIRED','Choose an explicit future review expiry.',422)
    body={**payload.model_dump(mode='json'),'reviewer_id':reviewer_id}
    record=AuthorityReview(relationship_id=edge.id,sequence=edge.sequence+1,reviewer_id=reviewer_id,
        payload=body,payload_sha256=digest(canonical(body)))
    db.add(record);db.flush();edge.sequence+=1;edge.current_review_id=record.id
    db.add(Audit(actor_id=reviewer_id,action='authority.reviewed',target_id=edge.id,
        detail={'sequence':edge.sequence,'record_id':record.id,'decision':payload.decision}))
    return edge


def summary(db,edge):
    record=review_record(db,edge)
    return {'id':edge.id,'source_id':edge.source_id,'target_id':edge.target_id,'relation':edge.relation,
        'revision':edge.revision,'sequence':edge.sequence,'current':current(db,edge),
        'decision':record.payload['decision'] if record else 'unreviewed_or_invalid',
        'created_at':edge.created_at,'agent_admission_granted':False}


def packet(db,edge):
    if not valid_endpoints(db,edge):
        fail('SOURCE_CHANGED','Both exact source passages must remain readable and unchanged to inspect review text.',409)
    sources=list(endpoints(db,edge).values())
    for source in sources:rights.require(source,'display_full')
    records=db.scalars(select(AuthorityReview).where(AuthorityReview.relationship_id==edge.id).order_by(AuthorityReview.sequence).limit(101)).all()
    if len(records)>100:fail('REVIEW_HISTORY_LIMIT','Relationship review history requires bounded reconciliation.',409)
    if not integrity(edge) or any(r.payload_sha256!=digest(canonical(r.payload)) for r in records):
        fail('RELATIONSHIP_INTEGRITY','Relationship integrity requires investigation.',409)
    result={**summary(db,edge),'proposal':edge.payload,'reviews':[{'id':r.id,'payload':r.payload,'payload_sha256':r.payload_sha256} for r in records],
        'source_attributions':output_rights.notices(db,sources)}
    output_rights.release(db,sources,result)
    return result


def public_links(db,source_id,after='',limit=20):
    source=db.get(Source,source_id);citation_lookup.authorize(source)
    # Bound observations, not a claim of a complete graph. Explicit cursor advances over excluded rows.
    rows=db.scalars(select(AuthorityRelationship).where(or_(AuthorityRelationship.source_id==source_id,
        AuthorityRelationship.target_id==source_id),AuthorityRelationship.id>after).order_by(AuthorityRelationship.id).limit(limit+1)).all()
    observed=rows[:limit];items=[];sources={source.id:source};expected={}
    for edge in observed:
        if not current(db,edge):continue
        record=review_record(db,edge)
        expected[edge.id]=(edge.sequence,edge.current_review_id)
        for s in endpoints(db,edge).values():sources[s.id]=s
        items.append({'id':edge.id,'relation':edge.relation,'direction':'outgoing' if edge.source_id==source_id else 'incoming',
            'source':edge.payload['source'],'target':edge.payload['target'],'scope':edge.payload['scope'],
            'reviewed_at':record.created_at,'review_expires_at':record.payload['expires_at'],
            'source_kind':db.get(Source,edge.source_id).kind,'target_kind':db.get(Source,edge.target_id).kind})
    result={'source_revision':citation_lookup.revision(source),'items':items,'observed':len(observed),'next_after':observed[-1].id if len(rows)>limit else None,
        'complete_graph_verified':False,'agent_admission_granted':False,'claim_support_verified':False,
        'version':VERSION,'source_attributions':output_rights.notices(db,list(sources.values()))}
    output_rights.release(db,list(sources.values()),result)
    if result['source_revision']!=citation_lookup.revision(source):
        fail('SOURCE_CHANGED','The source changed before relationship release.',409)
    # Serialize release against review changes after source locks, using the same order as decisions.
    for edge_id in sorted(expected):
        edge=db.scalar(select(AuthorityRelationship).where(AuthorityRelationship.id==edge_id).with_for_update().execution_options(populate_existing=True))
        if not edge or expected[edge_id]!=(edge.sequence,edge.current_review_id) or not current(db,edge):
            fail('SOURCE_CHANGED','The relationship changed before release.',409)
    return result
