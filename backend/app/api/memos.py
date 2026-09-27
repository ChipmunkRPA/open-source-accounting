from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from ..auth import current_user, session, workspace_access
from ..schemas import MemoCreate, MemoUpdate, ReviewCreate
from ..models import Memo, MemoRevision, Review, Membership, now
from ..services import memos as service
from ..services import output_rights
from ..errors import fail
from .common import get_memo

router = APIRouter(tags=['memos'])


@router.get('/memos')
def list_memos(user=Depends(current_user), db=Depends(session)):
    rows = db.scalars(select(Memo).join(Membership, Membership.workspace_id == Memo.workspace_id)
                      .where(Membership.user_id == user.id).order_by(Memo.updated_at.desc()).limit(100)).all()
    return {'items': [{'id': m.id, 'title': m.title, 'workspace_id': m.workspace_id,
                       'revision': m.revision, 'updated_at': m.updated_at} for m in rows]}


@router.post('/memos', status_code=201)
def create_manual(payload: MemoCreate, user=Depends(current_user), db=Depends(session)):
    workspace_access(db, user, payload.workspace_id, 'edit')
    memo = Memo(**payload.model_dump(), created_by=user.id, revision=1)
    db.add(memo)
    db.flush()
    service.save_revision(db, memo, user.id)
    db.commit()
    return service.serial(db, memo)


@router.get('/memos/{memo_id}')
def memo_detail(memo_id: str, user=Depends(current_user), db=Depends(session)):
    memo = get_memo(db, user, memo_id)
    service.verify_access(db, memo)
    return service.serial(db, memo)


@router.put('/memos/{memo_id}')
def edit(memo_id: str, payload: MemoUpdate, user=Depends(current_user), db=Depends(session)):
    memo = get_memo(db, user, memo_id, 'edit')
    service.verify_access(db, memo)
    # SQL compare-and-swap prevents concurrent editors overwriting one another.
    from sqlalchemy import update
    result = db.execute(update(Memo).where(Memo.id == memo.id, Memo.revision == payload.expected_revision)
                        .values(title=payload.title, body=payload.body, revision=Memo.revision+1, updated_at=now()))
    if result.rowcount != 1:
        fail('REVISION_CONFLICT', 'This memo changed elsewhere. Reload and reconcile your edits.', 409)
    db.flush()
    db.refresh(memo)
    service.save_revision(db, memo, user.id)
    db.commit()
    return service.serial(db, memo)


@router.get('/memos/{memo_id}/revisions')
def revisions(memo_id: str, user=Depends(current_user), db=Depends(session)):
    memo = get_memo(db, user, memo_id)
    service.verify_access(db, memo)
    rows = db.scalars(select(MemoRevision).where(MemoRevision.memo_id == memo_id)
                      .order_by(MemoRevision.number.desc()).limit(100)).all()
    items = []
    for r in rows:
        output = output_rights.memo_output(db, memo, body=r.body, title=r.title)
        items.append({'revision': r.number, **output, 'user_id': r.user_id, 'created_at': r.created_at})
    db.commit()
    return {'items': items}


@router.post('/memos/{memo_id}/reviews', status_code=201)
def review(memo_id: str, payload: ReviewCreate, user=Depends(current_user), db=Depends(session)):
    memo = get_memo(db, user, memo_id, 'review')
    service.verify_access(db, memo)
    if payload.expected_revision != memo.revision:
        fail('REVISION_CONFLICT', 'The memo changed before review was recorded.', 409)
    # Any edit by this person disqualifies an independent label on this revision lineage.
    contributed = db.scalar(select(MemoRevision).where(MemoRevision.memo_id == memo_id,
                                                      MemoRevision.user_id == user.id).limit(1))
    kind = 'self' if contributed or memo.created_by == user.id else 'independent'
    db.add(Review(memo_id=memo_id, revision=memo.revision, reviewer_id=user.id, kind=kind, note=payload.note))
    db.commit()
    return service.serial(db, memo)


@router.get('/memos/{memo_id}/export')
def export(memo_id: str, format: str = 'md', user=Depends(current_user), db=Depends(session)):
    if format not in {'md', 'html', 'docx', 'pdf'}:
        fail('EXPORT_FORMAT', 'Choose md, html, docx, or pdf.', 422)
    memo = get_memo(db, user, memo_id)
    service.verify_access(db, memo, 'export')
    content, mime = service.export_bytes(memo, format, db=db)
    db.commit()
    return Response(content, media_type=mime,
                    headers={'Content-Disposition': f'attachment; filename="accounting-memo-{memo.id[:8]}.{format}"',
                             'Cache-Control': 'no-store'})
