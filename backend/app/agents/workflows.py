"""Workflow-specific deterministic preprocessing and task validation."""
from difflib import unified_diff
from ..models import Document, Memo
from ..errors import fail
from .calculations import allocate_revenue, lease_schedule, check_journal


def validate_inputs(db, run, task):
    docs = []
    for doc_id in run.document_ids:
        doc = db.get(Document, doc_id)
        if not doc or doc.workspace_id != run.workspace_id or doc.status != 'ready':
            fail('DOCUMENT_UNAVAILABLE', 'A selected document is missing, deleted, or outside this workspace.', 409)
        docs.append(doc)
    saved_memo = None
    if run.inputs.get('memo_id'):
        saved_memo = db.get(Memo, run.inputs['memo_id'])
        if not saved_memo or saved_memo.workspace_id != run.workspace_id:
            fail('NOT_FOUND', 'Memo not found in this workspace.', 404)
        from ..services.memos import verify_access
        verify_access(db, saved_memo, 'model_input')
    if len(docs) < task['min_documents'] and not (run.workflow == 'memo_review' and saved_memo):
        fail('DOCUMENT_REQUIRED', f'This task requires at least {task["min_documents"]} document(s).', 422)
    if run.workflow == 'framework_compare' and run.context.get('framework') != 'BOTH':
        fail('FRAMEWORK_REQUIRED', 'Select both frameworks for this comparison.', 422)
    if run.workflow == 'standards_watch':
        fail('USE_WATCH_SETUP', 'Configure an opt-in watch instead of starting a research run.', 422)
    return docs


def preprocess(db, run, task):
    docs = validate_inputs(db, run, task)
    result = {'workflow_guardrail': task['guardrail']}
    if run.workflow == 'memo_review' and run.inputs.get('memo_id'):
        memo = db.get(Memo, run.inputs['memo_id'])
        result['memo_under_review'] = {'title': memo.title, 'body': memo.body[:60000], 'revision': memo.revision, 'truncated': len(memo.body)>60000}
    if run.workflow == 'contract_compare':
        old, new = ['\n'.join(x['text'] for x in d.chunks) for d in docs[:2]]
        lines = list(unified_diff(old.splitlines(), new.splitlines(), fromfile=docs[0].name,
                                  tofile=docs[1].name, lineterm=''))
        result['comparison'] = {'diff': '\n'.join(lines)[:25000], 'truncated': sum(len(x)+1 for x in lines) > 25000,
                                'warning': 'Text differences do not themselves determine accounting modification treatment.'}
    if run.workflow == 'revenue_workpaper' and run.inputs.get('allocation'):
        result['allocation'] = allocate_revenue(run.inputs['allocation'])
    if run.workflow == 'lease_workpaper' and run.inputs.get('lease'):
        result['lease'] = lease_schedule(run.inputs['lease'])
    if run.inputs.get('journal'):
        result['journal_check'] = check_journal(run.inputs['journal'])
    return result
