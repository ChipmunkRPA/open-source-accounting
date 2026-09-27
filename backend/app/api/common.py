from sqlalchemy import select
from ..auth import workspace_access
from ..models import Run, Memo, Chat
from ..errors import fail
from ..services.rights import run_artifact_access
from ..services import output_rights


def get_run(db, user, run_id, action='read'):
    run = db.get(Run, run_id)
    if not run:
        fail('NOT_FOUND', 'Research run not found.', 404)
    workspace_access(db, user, run.workspace_id, action)
    return run


def get_memo(db, user, memo_id, action='read'):
    memo = db.get(Memo, memo_id)
    if not memo:
        fail('NOT_FOUND', 'Memo not found.', 404)
    workspace_access(db, user, memo.workspace_id, action)
    return memo


def get_chat(db, user, chat_id):
    chat = db.get(Chat, chat_id)
    if not chat or chat.user_id != user.id:
        fail('NOT_FOUND', 'Chat not found.', 404)
    return chat


def run_json(db, run):
    blocked = False
    result = run.result
    if run.result:
        try:
            run_artifact_access(db, run)
            result = output_rights.run_output(db, run)
            db.commit()
        except Exception:
            db.rollback()
            blocked = True
    return {'id': run.id, 'workspace_id': run.workspace_id, 'workflow': run.workflow,
            'question': run.question, 'context': run.context, 'facts': run.facts,
            'document_ids': run.document_ids, 'inputs': run.inputs,
            'state': run.state, 'revision': run.revision, 'parent_id': run.parent_id,
            'plan': run.plan, 'result': None if blocked else result,
            'access_blocked': blocked, 'error_code': run.error_code,
            'usage_status': run.usage_status, 'created_at': run.created_at,
            'updated_at': run.updated_at, 'model_id': run.model_id, 'token_usage': run.token_usage,
            'memo_id': db.scalar(select(Memo.id).where(Memo.run_id == run.id))}
