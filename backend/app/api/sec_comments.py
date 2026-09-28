"""Free anonymous correspondence reading; no client-controlled fetching or inference."""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from ..auth import session
from ..services import sec_comments

router=APIRouter(tags=['SEC comment letters'])


@router.get('/sec-comments')
def listing(q:str=Query('',max_length=200),topic:str=Query('',max_length=80),
            form:Literal['UPLOAD','CORRESP']|None=None,recent:bool=True,
            offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),db=Depends(session)):
    return sec_comments.listing(db,q,topic,form or '',recent,offset,limit)
