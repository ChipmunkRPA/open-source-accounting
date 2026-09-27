"""Operation-level rights, independent of payment. Fail closed on unknown sources."""
import hashlib
import json
from ..models import Source, Document, Evidence, now
from ..errors import fail


# Metadata fields can never become operations merely because their value is truthy.
OPERATIONS = frozenset({'acquire', 'store_raw', 'extract', 'store_text', 'embed',
                        'model_input', 'display_full', 'quote', 'export', 'redistribute', 'train'})
RIGHTS_FIELDS = OPERATIONS | {'basis', 'commercial_use', 'effective_at', 'expires_at',
    'license_evidence_ref', 'scope', 'attribution', 'requires_technical_review'}


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


def allowed(source: Source, action: str, *, context: dict | None = None) -> bool:
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
    # Missing context denies a scoped grant. A paid plan cannot satisfy source seat rights.
    scope = policy.get('scope', {})
    if not isinstance(scope, dict):
        return False
    supported = {'route', 'workspace_id', 'seat_id', 'audience', 'provider', 'region', 'retention', 'jurisdiction'}
    for key, values in scope.items():
        if key not in supported or not isinstance(values, list) or not values:
            return False
        if not all(isinstance(v, str) and v for v in values) or (context or {}).get(key) not in values:
            return False
    if action in {'model_input', 'embed', 'train'} and policy.get('requires_technical_review'):
        digest = hashlib.sha256((source.text or '').encode()).hexdigest()
        if (policy.get('technical_review_status') != 'approved'
                or policy.get('technical_reviewed_sha256') != digest):
            return False
    return True


def require(source, action):
    if not source or not allowed(source, action):
        fail('SOURCE_POLICY_BLOCK', 'The current source policy does not permit this operation.', 403)


def evidence_allowed(db, evidence: Evidence, action='model_input'):
    if evidence.source_id:
        source = db.get(Source, evidence.source_id)
        if evidence.access == 'reference_only':
            return bool(source and source.enabled)
        return bool(source and source.policy_version == evidence.policy_version and allowed(source, action))
    if evidence.document_id:
        doc = db.get(Document, evidence.document_id)
        return bool(doc and doc.status == 'ready')
    return False


def run_artifact_access(db, run, action='quote', _visited=None):
    """Conservative: hide dependent generated content after a rights or deletion change.

    This does not pretend to remove already downloaded exports from users' devices.
    """
    from sqlalchemy import select
    from ..models import Memo, Run
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
            run_artifact_access(db, parent, action, visited)
    items = db.scalars(select(Evidence).where(Evidence.run_id == run.id)).all()
    if any(not evidence_allowed(db, item, action) for item in items):
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
            'source_provenance': (source.policy or {}).get('sec_core')}
