from pathlib import Path
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, Response
from sqlalchemy import select, func, delete
from ..auth import fresh_user, current_user, session, workspace_access, lock_user
from ..schemas import WorkspaceCreate, MemberAdd
from ..models import Workspace, Membership, User, Document, Run, Evidence, Memo, MemoRevision, Audit, now, uid
from ..errors import fail
from ..services.entitlements import require_agent, ACTIVE_STATES
from ..services import documents
from ..services.storage import Storage

router = APIRouter(tags=['workspaces'])


@router.get('/workspaces')
def workspaces(user=Depends(current_user), db=Depends(session)):
    rows = db.execute(select(Workspace, Membership.role).join(Membership)
                      .where(Membership.user_id == user.id).order_by(Workspace.created_at.desc())).all()
    return {'items': [{'id': r.id, 'name': r.name, 'role': role, 'created_at': r.created_at} for r, role in rows]}


@router.post('/workspaces', status_code=201)
def create_workspace(payload: WorkspaceCreate, user=Depends(current_user), db=Depends(session)):
    count = db.scalar(select(func.count()).select_from(Workspace).where(Workspace.owner_id == user.id))
    if count >= 20:
        fail('WORKSPACE_LIMIT', 'The workspace limit has been reached.', 429)
    row = Workspace(name=payload.name, owner_id=user.id)
    db.add(row)
    db.flush()
    db.add(Membership(workspace_id=row.id, user_id=user.id, role='owner'))
    db.commit()
    return {'id': row.id, 'name': row.name, 'role': 'owner'}


@router.get('/workspaces/{workspace_id}/members')
def members(workspace_id: str, user=Depends(current_user), db=Depends(session)):
    workspace_access(db, user, workspace_id)
    rows = db.execute(select(User, Membership.role).join(Membership)
                      .where(Membership.workspace_id == workspace_id)).all()
    return {'items': [{'user_id': row.id, 'email': row.email, 'name': row.name, 'role': role} for row, role in rows]}


@router.post('/workspaces/{workspace_id}/members', status_code=201)
def add_member(workspace_id: str, payload: MemberAdd, user=Depends(fresh_user), db=Depends(session)):
    workspace_access(db, user, workspace_id, 'owner')
    target = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if not target:
        fail('MEMBER_NOT_REGISTERED', 'The collaborator must create an account before being added. No invitation email is sent.', 422)
    if db.get(Membership, (workspace_id, target.id)):
        fail('ALREADY_MEMBER', 'This account is already a member.', 409)
    db.add(Membership(workspace_id=workspace_id, user_id=target.id, role=payload.role))
    db.add(Audit(actor_id=user.id, action='workspace.member_added', target_id=workspace_id,
                 detail={'member_id': target.id, 'role': payload.role}))
    db.commit()
    return {'user_id': target.id, 'role': payload.role}


@router.delete('/workspaces/{workspace_id}/members/{user_id}', status_code=204)
def remove_member(workspace_id: str, user_id: str, user=Depends(fresh_user), db=Depends(session)):
    workspace_access(db, user, workspace_id, 'owner')
    member = db.get(Membership, (workspace_id, user_id))
    if not member or member.role == 'owner':
        fail('INVALID_MEMBER', 'The workspace owner cannot be removed here.', 409)
    db.delete(member)
    db.commit()
    return Response(status_code=204)


def doc_json(row):
    return {'id': row.id, 'name': row.name, 'mime': row.mime, 'size': row.size, 'status': row.status,
            'scan_status': row.scan_status, 'created_at': row.created_at, 'chunk_count': len(row.chunks)}


@router.get('/workspaces/{workspace_id}/documents')
def list_documents(workspace_id: str, user=Depends(current_user), db=Depends(session)):
    workspace_access(db, user, workspace_id)
    docs = db.scalars(select(Document).where(Document.workspace_id == workspace_id, Document.status != 'deleted')
                      .order_by(Document.created_at.desc())).all()
    return {'items': [doc_json(r) for r in docs]}


@router.post('/workspaces/{workspace_id}/documents', status_code=201)
def upload_document(workspace_id: str, request: Request, file: UploadFile = File(...),
                    authorization_basis: str = Form(...), user=Depends(current_user), db=Depends(session)):
    config = request.app.state.settings
    workspace_access(db, user, workspace_id, 'edit')
    lock_user(db, user.id)
    require_agent(db, user, config)
    if authorization_basis not in {'own_original', 'licensed_for_this_service'}:
        fail('DOCUMENT_AUTHORIZATION', 'Confirm a compatible authorization basis for processing this document.', 422)
    count = db.scalar(select(func.count()).select_from(Document).where(Document.workspace_id == workspace_id, Document.status != 'deleted'))
    if count >= config.max_documents_per_workspace:
        fail('DOCUMENT_LIMIT', 'Delete unused documents before uploading more.', 429)
    data = file.file.read(config.max_upload_mb * 1024 * 1024 + 1)
    name = documents.safe_filename(file.filename or 'document.txt')
    mime = documents.preflight(data, name, config)
    scan_status = documents.scan(data, config)
    chunks = documents.parse_isolated(data, Path(name).suffix.lower(), config.max_document_characters)
    key = f'{workspace_id}/{uid()}'
    storage = Storage(config)
    storage.put(key, data, mime)
    try:
        row = Document(workspace_id=workspace_id, uploaded_by=user.id, name=name, mime=mime,
                       size=len(data), checksum=documents.checksum(data), object_key=key, chunks=chunks,
                       authorization_basis=authorization_basis, scan_status=scan_status)
        db.add(row)
        db.commit()
    except Exception:
        storage.delete(key)
        raise
    return doc_json(row)


@router.get('/documents/{document_id}')
def get_document(document_id: str, user=Depends(current_user), db=Depends(session)):
    row = db.get(Document, document_id)
    if not row:
        fail('NOT_FOUND', 'Document not found.', 404)
    workspace_access(db, user, row.workspace_id)
    if row.status != 'ready':
        fail('DOCUMENT_UNAVAILABLE', 'Document is unavailable.', 410)
    return {**doc_json(row), 'chunks': row.chunks}


@router.delete('/documents/{document_id}', status_code=204)
def delete_document(document_id: str, request: Request, user=Depends(fresh_user), db=Depends(session)):
    row = db.get(Document, document_id)
    if not row:
        fail('NOT_FOUND', 'Document not found.', 404)
    workspace_access(db, user, row.workspace_id, 'edit')
    runs = db.scalars(select(Run).where(Run.workspace_id == row.workspace_id)).all()
    affected = [r for r in runs if document_id in r.document_ids]
    if any(r.state in ACTIVE_STATES for r in affected):
        fail('DOCUMENT_IN_USE', 'Cancel or finish dependent tasks before deleting this document.', 409)
    Storage(request.app.state.settings).delete(row.object_key)
    row.chunks, row.status = [], 'deleted'
    for run in affected:
        run.result = None
        run.state = 'blocked'
        run.error_code = 'DOCUMENT_DELETED'
        for evidence in db.scalars(select(Evidence).where(Evidence.run_id == run.id)):
            evidence.text = None
        for memo in db.scalars(select(Memo).where(Memo.run_id == run.id)):
            memo.body = 'Content removed because a supporting document was deleted.'
            memo.revision += 1
            db.execute(delete(MemoRevision).where(MemoRevision.memo_id == memo.id))
    db.add(Audit(actor_id=user.id, action='document.deleted', target_id=document_id,
                 detail={'dependent_runs': len(affected)}))
    db.commit()
    return Response(status_code=204)
