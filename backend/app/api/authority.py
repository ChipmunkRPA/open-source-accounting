"""Restricted relationship review and permission-gated public one-hop navigation."""
from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from ..auth import session,current_user,fresh_user
from ..errors import fail
from ..models import AuthorityRelationship
from ..authority_schemas import RelationshipProposal,RelationshipDecision
from ..services import authority
from .library import require_editor

router=APIRouter(tags=['authority relationships'])


def staff(user):
    if user.role not in {'admin','rights_approver','technical_reviewer'}:
        fail('FORBIDDEN','A scoped source administrator or technical reviewer is required.',403)


@router.post('/editorial/relationships',status_code=201)
def propose_relationship(payload:RelationshipProposal,user=Depends(fresh_user),db=Depends(session)):
    staff(user)
    edge=authority.propose(db,payload,user.id)
    result=authority.summary(db,edge);db.commit();return result


@router.get('/editorial/relationships')
def list_relationships(after:str=Query('',max_length=36),user=Depends(current_user),db=Depends(session)):
    staff(user)
    rows=db.scalars(select(AuthorityRelationship).where(AuthorityRelationship.id>after).order_by(AuthorityRelationship.id).limit(51)).all()
    return {'items':[authority.summary(db,r) for r in rows[:50]],'next_after':rows[49].id if len(rows)>50 else None}


@router.get('/editorial/relationships/{relationship_id}')
def relationship_packet(relationship_id:str,user=Depends(current_user),db=Depends(session)):
    staff(user)
    edge=db.get(AuthorityRelationship,relationship_id)
    if not edge:fail('NOT_FOUND','Relationship not found.',404)
    result=authority.packet(db,edge);db.commit();return result


@router.post('/editorial/relationships/{relationship_id}/review')
def review_relationship(relationship_id:str,payload:RelationshipDecision,user=Depends(fresh_user),db=Depends(session)):
    require_editor(user)
    edge=authority.decide(db,relationship_id,payload,user.id)
    result=authority.summary(db,edge);db.commit();return result


@router.get('/sources/{source_id}/relationships')
def source_relationships(source_id:str,after:str=Query('',max_length=36),limit:int=Query(20,ge=1,le=50),db=Depends(session)):
    result=authority.public_links(db,source_id,after,limit)
    db.commit();return result
