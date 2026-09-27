"""Operation-level rights, independent of payment. Fail closed on unknown sources."""
import hashlib
import json
from ..models import Source, Document, Evidence, now
from ..errors import fail


# Metadata fields can never become operations merely because their value is truthy.
OPERATIONS = frozenset({'acquire', 'store_raw', 'extract', 'store_text', 'embed',
                        'model_input', 'display_full', 'quote', 'export', 'redistribute', 'train'})
RIGHTS_FIELDS = OPERATIONS | {'basis', 'commercial_use', 'effective_at', 'expires_at',
    'license_evidence_ref', 'scope', 'attribution', 'output_control', 'requires_technical_review',
    'intake_manifest_sha256', 'intake_parent_id', 'intake_parent_policy_version'}


def revision(source: Source) -> str:
    """Bind rights to work/version/body and grants, independently of editorial annotations."""
    payload = {'title': source.title, 'publisher': source.publisher, 'url': source.canonical_url,
               'version': source.version_label, 'text_sha256': hashlib.sha256((source.text or '').encode()).hexdigest(),
               'rights': {k: (source.policy or {}).get(k) for k in sorted(RIGHTS_FIELDS)}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def record_approval(source: Source, reviewer_id: str) -> None:
    """Called only after server authorization; this function does not assert legal correctness."""
    source.policy = {**source.policy, 'rights_reviewed_revision': revision(source),
                     'rights_reviewed_at': now(), 'rights_reviewer_id': reviewer_id}


def allowed(source: Source, action: str, *, context: dict | None = None, _visited=None) -> bool:
    if action not in OPERATIONS or source.enabled is not True or source.reviewed is not True:
        return False
    policy = source.policy or {}
    if policy.get('basis') not in {'original', 'government_work', 'license', 'reviewed_use',
                                  'government_source_excerpt_pending_review'}:
        return False
    if policy.get('commercial_use') is not True or policy.get(action) is not True:
        return False
    if policy.get('rights_reviewed_revision') != revision(source):
        return False
    if policy.get('intake_parent_id'):
        from sqlalchemy.orm import object_session
        db = object_session(source)
        visited = set(_visited or ())
        if not db or source.id in visited or len(visited) >= 10:
            return False
        visited.add(source.id)
        parent = db.get(Source, policy['intake_parent_id'])
        if (not parent or parent.policy_version != policy.get('intake_parent_policy_version')
                or not allowed(parent, action, context=context, _visited=visited)):
            return False
    current = now()
    for key in ('effective_at', 'expires_at'):
        value = policy.get(key)
        if value is not None and (type(value) is not int or value < 0):
            return False
    if policy.get('effective_at') is not None and current < policy['effective_at']:
        return False
    if policy.get('expires_at') is not None and current >= policy['expires_at']:
        return False
    if policy.get('basis') in {'license', 'reviewed_use'} and not policy.get('license_evidence_ref'):
        return False
    if action in {'quote', 'display_full', 'export', 'model_input'}:
        control = policy.get('output_control')
        if policy.get('basis') in {'license', 'reviewed_use'} and not control:
            return False
        if control is not None:
            from ..schemas import OutputControl
            try:
                normalized = OutputControl.model_validate(control).model_dump(mode='json')
                from .output_rights import policy_current
                if not policy_current(source, normalized):
                    return False
            except ValueError:
                return False
    if policy.get('basis') == 'reviewed_use':
        from .counsel import permitted
        if not permitted(source, action):
            return False
    # Missing context denies a scoped grant. A paid plan cannot satisfy source seat rights.
    scope = policy.get('scope', {})
    if not isinstance(scope, dict):
        return False
    from .source_scopes import PROTECTED, resolve
    if set(scope) & PROTECTED:
        context = resolve(source, action, context)
        if context is None:
            return False
    supported = {'route', 'workspace_id', 'seat_id', 'audience', 'provider', 'region', 'retention', 'jurisdiction'}
    for key, values in scope.items():
        if key not in supported or not isinstance(values, list) or not values:
            return False
        if not all(isinstance(v, str) and v for v in values) or (context or {}).get(key) not in values:
            return False
    if action in {'model_input', 'embed', 'train'} and (policy.get('intake_extraction_id') or policy.get('applicability_record_id')):
        from .applicability import current as applicability_current
        if applicability_current(source) is None:
            return False
    if action in {'model_input', 'embed', 'train'} and policy.get('intake_extraction_id'):
        from .parser_review import current
        if not current(source):
            return False
    if action in {'model_input', 'embed', 'train'} and policy.get('requires_technical_review'):
        from .editorial import current
        digest = hashlib.sha256((source.text or '').encode()).hexdigest()
        if (policy.get('technical_review_status') != 'approved'
                or policy.get('technical_reviewed_sha256') != digest or not current(source)):
            return False
    return True


def require(source, action):
    if not source or not allowed(source, action):
        fail('SOURCE_POLICY_BLOCK', 'The current source policy does not permit this operation.', 403)


def runtime_context(db, run, settings=None, *, actor_id=None, require_edit=False):
    """Only server-owned scope values; never merge run.context, prompts or client inputs.

    A workspace member is not automatically a licensed publisher seat. Protected
    scope values are resolved per source/operation from fresh verified records.
    """
    from .source_scopes import RuntimeContext, member
    if not run:
        fail('SOURCE_CHANGED', 'The source execution is unavailable.', 409)
    actor_id = actor_id or db.info.get('rights_actor_id') or run.user_id
    settings = settings or db.info.get('rights_settings')
    membership = member(db, run.workspace_id, actor_id)
    if not membership or (require_edit and membership.role not in {'owner', 'editor'}):
        fail('WORKSPACE_ACCESS_REVOKED', 'Current workspace membership is required.', 403)
    context = {'workspace_id': run.workspace_id, 'route': 'hosted_agent', 'audience': 'workspace'}
    if settings is not None:
        context.update(provider=settings.model_provider, region=settings.model_location)
    return RuntimeContext(context, db, actor_id, settings, require_edit)


def evidence_allowed(db, evidence: Evidence, action='model_input', *, context=None):
    from ..models import Run
    from .parser_review import current as parser_current
    from .applicability import applies
    run = db.get(Run, evidence.run_id)
    if not run:
        return False
    context = context or runtime_context(db, run)
    if context.get('workspace_id') != run.workspace_id:
        return False
    if evidence.source_id:
        source = db.get(Source, evidence.source_id)
        if evidence.access == 'reference_only':
            return bool(source and source.enabled and not evidence.text)
        return bool(source and source.policy_version == evidence.policy_version
                    and evidence.text and evidence.text in (source.text or '')
                    and allowed(source, action, context=context) and applies(source, run.context)
                    and (not source.policy.get('intake_extraction_id')
                         or parser_current(source)))
    if evidence.document_id:
        doc = db.get(Document, evidence.document_id)
        return bool(doc and doc.status == 'ready' and doc.workspace_id == run.workspace_id
                    and doc.id in run.document_ids and any(
                        part.get('locator') == evidence.locator and part.get('text') == evidence.text
                        for part in doc.chunks))
    return False


def run_artifact_access(db, run, action='quote', _visited=None, *, context=None):
    """Conservative: hide dependent generated content after a rights or deletion change.

    This does not pretend to remove already downloaded exports from users' devices.
    """
    from sqlalchemy import select
    from ..models import Memo, Run
    if not run:
        fail('SOURCE_CHANGED', 'The source execution is unavailable.', 409)
    context = context or runtime_context(db, run)
    if context.get('workspace_id') != run.workspace_id:
        fail('SOURCE_CHANGED', 'Cross-workspace source dependency is unavailable.', 409)
    # Deterministic preprocessing can include a selected file absent from the retrieval subset.
    for document_id in run.document_ids:
        document = db.get(Document, document_id)
        if not document or document.status != 'ready' or document.workspace_id != run.workspace_id:
            fail('SOURCE_CHANGED', 'A selected document is no longer available.', 409)
    visited = set() if _visited is None else set(_visited)
    if run.id in visited or len(visited) >= 20:
        fail('DEPENDENCY_CYCLE', 'Artifact dependency chain requires review.', 409)
    visited.add(run.id)
    memo_id = (run.inputs or {}).get('memo_id')
    if memo_id:
        memo = db.get(Memo, memo_id)
        if not memo or memo.workspace_id != run.workspace_id:
            fail('SOURCE_CHANGED', 'The input memo is no longer available.', 409)
        if memo.run_id:
            parent = db.get(Run, memo.run_id)
            if not parent:
                fail('SOURCE_CHANGED', 'The input memo evidence is no longer available.', 409)
            run_artifact_access(db, parent, action, visited, context=context)
    items = db.scalars(select(Evidence).where(Evidence.run_id == run.id)).all()
    if any(not evidence_allowed(db, item, action, context=context) for item in items):
        fail('SOURCE_CHANGED', 'A source was disabled, changed, or deleted. This artifact requires review.', 409)


def metadata(source):
    return {'id': source.id, 'title': source.title, 'publisher': source.publisher,
            'url': source.canonical_url, 'kind': source.kind, 'framework': source.framework,
            'version': source.version_label, 'effective_from': source.effective_from,
            'effective_to': source.effective_to, 'enabled': source.enabled,
            'access': 'text_available' if allowed(source, 'display_full') else 'reference_only',
            'reviewed': source.reviewed, 'rights_reviewed': source.reviewed,
            'editorial_status': (source.policy or {}).get('technical_review_status', 'not_recorded'),
            'content_item_id': (source.policy or {}).get('content_item_id'),
            'policy_version': source.policy_version,
            'attribution': (source.policy or {}).get('attribution', ''),
            'source_provenance': (source.policy or {}).get('sec_core')}
