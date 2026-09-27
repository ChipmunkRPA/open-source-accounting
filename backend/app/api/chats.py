from fastapi import APIRouter, Depends, Request, Header, Response
from sqlalchemy import select, func
from ..auth import current_user, session, lock_user
from ..models import Chat, ChatMessage, Idempotency, now
from ..schemas import ChatCreate, ChatSend
from ..providers.gemini import get_model
from ..services.idempotency import begin
from ..errors import fail, ProviderError
from .common import get_chat

router = APIRouter(tags=['free-chat'])


@router.get('/chats')
def chats(user=Depends(current_user), db=Depends(session)):
    rows = db.scalars(select(Chat).where(Chat.user_id == user.id).order_by(Chat.created_at.desc()).limit(100)).all()
    return {'items': [{'id': c.id, 'title': c.title, 'created_at': c.created_at} for c in rows]}


@router.post('/chats', status_code=201)
def create_chat(payload: ChatCreate, user=Depends(current_user), db=Depends(session)):
    row = Chat(user_id=user.id, title=payload.title)
    db.add(row)
    db.commit()
    return {'id': row.id, 'title': row.title}


@router.get('/chats/{chat_id}')
def chat(chat_id: str, user=Depends(current_user), db=Depends(session)):
    row = get_chat(db, user, chat_id)
    messages = db.scalars(select(ChatMessage).where(ChatMessage.chat_id == chat_id).order_by(ChatMessage.sequence)).all()
    return {'id': row.id, 'title': row.title, 'messages': [{'role': m.role, 'body': m.body, 'id': m.id} for m in messages]}


@router.post('/chats/{chat_id}/messages')
def send(chat_id: str, payload: ChatSend, request: Request, idempotency_key: str = Header(default=''),
         user=Depends(current_user), db=Depends(session)):
    row = get_chat(db, user, chat_id)
    config = request.app.state.settings
    lock_user(db, user.id)
    record, repeat = begin(db, user.id, f'chat:{chat_id}', idempotency_key, payload.model_dump())
    if repeat:
        if record.response:
            if record.response.get('error'):
                fail('PREVIOUS_REQUEST_FAILED', 'Start a new attempt; the previous request failed.', 409)
            return record.response
        fail('REQUEST_PENDING', 'This message is still being processed.', 409)
    # Count admitted attempts, including provider failures, to cap external spend.
    recent = db.scalar(select(func.count()).select_from(Idempotency).where(
        Idempotency.user_id == user.id, Idempotency.scope.like('chat:%'), Idempotency.created_at >= now()-3600))
    if recent > config.chat_messages_per_hour:
        fail('CHAT_RATE_LIMIT', 'Free chat is temporarily rate-limited. No payment is required; try later.', 429)
    pending = db.scalar(select(func.count()).select_from(Idempotency).where(
        Idempotency.user_id == user.id, Idempotency.scope == f'chat:{chat_id}',
        Idempotency.response.is_(None), Idempotency.key != idempotency_key,
        Idempotency.created_at > now()-180))
    if pending:
        fail('CHAT_BUSY', 'Wait for the current reply before sending another message.', 409)
    history = db.scalars(select(ChatMessage).where(ChatMessage.chat_id == chat_id)
                         .order_by(ChatMessage.sequence.desc()).limit(20)).all()[::-1]
    messages = [{'role': m.role, 'body': m.body} for m in history] + [{'role': 'user', 'body': payload.message}]
    db.commit()
    try:
        reply = get_model(config).chat(messages)
    except ProviderError:
        record.response = {'error': 'MODEL_REQUEST_FAILED'}
        db.commit()
        fail('MODEL_REQUEST_FAILED', 'The model did not return a usable reply. Your chat remains free.', 502)
    sequence = db.scalar(select(func.max(ChatMessage.sequence)).where(ChatMessage.chat_id == chat_id)) or 0
    db.add(ChatMessage(chat_id=chat_id, role='user', body=payload.message, sequence=sequence+1))
    assistant = ChatMessage(chat_id=chat_id, role='assistant', body=reply, sequence=sequence+2)
    db.add(assistant)
    if row.title == 'New chat':
        row.title = payload.message[:100]
    db.flush()
    result = {'id': assistant.id, 'role': 'assistant', 'body': reply, 'model_id': config.model_id,
              'provider': config.model_provider, 'source_access': 'none'}
    record.response = result
    db.commit()
    return result


@router.delete('/chats/{chat_id}', status_code=204)
def delete_chat(chat_id: str, user=Depends(current_user), db=Depends(session)):
    from sqlalchemy import delete
    row = get_chat(db, user, chat_id)
    db.execute(delete(Idempotency).where(Idempotency.user_id == user.id, Idempotency.scope == f'chat:{chat_id}'))
    db.delete(row)
    db.commit()
    return Response(status_code=204)
