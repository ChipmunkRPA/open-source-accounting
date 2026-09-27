"""Bounded exact-version comparison. Never infer equivalence or transfer approval."""
from difflib import SequenceMatcher
from sqlalchemy import select
from ..models import Source, SourceExtraction, SourceArtifact, IntakeWork
from ..errors import fail
from ..sec_core.core import canonical, digest
from . import editorial, rights, output_rights

MAX_CHARACTERS = 200_000
MAX_LINES = 2_000


def logical_unit(db, source):
    policy = source.policy or {}
    if policy.get('content_item_id'):
        return ('original_item', policy['content_item_id'])
    if policy.get('intake_extraction_id'):
        ex = db.get(SourceExtraction, policy['intake_extraction_id'])
        artifact = db.get(SourceArtifact, ex.artifact_id) if ex else None
        work = db.get(IntakeWork, artifact.work_id) if artifact else None
        if work and work.source_id == policy.get('intake_parent_id') and policy.get('intake_locator'):
            return ('intake_passage', work.family_id, work.work_id, policy['intake_locator'])
    sec = policy.get('sec_core', {})
    if sec.get('source_id') and sec.get('passage_id'):
        return ('sec_excerpt', sec['source_id'], sec['passage_id'])
    return None


def metadata(source):
    policy = source.policy or {}
    sec = policy.get('sec_core', {})
    return {'title':source.title, 'publisher':source.publisher, 'url':source.canonical_url,
            'edition':source.version_label, 'kind':source.kind, 'framework':source.framework,
            'reference_ids':policy.get('content_reference_ids', []),
            'reference_metadata':policy.get('content_reference_snapshot'),
            'reference_metadata_sha256':policy.get('content_references_sha256'),
            'intake':{k:policy.get(k) for k in ('intake_locator','intake_artifact_id','intake_extraction_id',
                'intake_extraction_sha256','intake_parser_version','intake_passage_index')},
            'sec_citation':{k:sec.get(k) for k in ('source_id','passage_id','locator','snapshot_id',
                'source_as_of','retrieved_at','authority_type','coverage','acquisition_method')},
            'date_claims':{'effective_from':source.effective_from,'effective_to':source.effective_to,
                'public_available_at':sec.get('public_available_at')}}


def compare(db, request):
    if request.before_source_id == request.after_source_id:
        fail('COMPARISON_SCOPE', 'Choose two distinct staged versions.', 422)
    sources = {}
    for sid in sorted([request.before_source_id, request.after_source_id]):
        source = db.scalar(select(Source).where(Source.id == sid).with_for_update())
        if not source or not source.policy.get('requires_technical_review'):
            fail('NOT_FOUND', 'Reviewable version not found.', 404)
        rights.require(source, 'display_full')
        sources[sid] = source
    before, after = sources[request.before_source_id], sources[request.after_source_id]
    for source, expected_revision, expected_policy in (
        (before,request.before_revision,request.before_policy_version),
        (after,request.after_revision,request.after_policy_version)):
        if editorial.revision(source) != expected_revision or source.policy_version != expected_policy:
            fail('REVISION_CONFLICT', 'Reload both versions before comparing them.', 409)
    unit = logical_unit(db, before)
    if unit is None or logical_unit(db, after) != unit:
        fail('COMPARISON_SCOPE', 'Versions must share an explicit item or work/passage identity; renumbered passages need separate reconciliation.', 422)
    texts = [s.text or '' for s in (before,after)]
    lines = [text.splitlines(keepends=True) for text in texts]
    if any(len(t)>MAX_CHARACTERS for t in texts) or any(len(value)>MAX_LINES for value in lines):
        fail('COMPARISON_LIMIT', 'Comparison supports 200,000 characters and 2,000 lines per version. Review narrower source units; no diff was truncated.', 422)
    changes = []
    for operation, start_a, end_a, start_b, end_b in SequenceMatcher(None,*lines,autojunk=False).get_opcodes():
        if operation == 'equal': continue
        changes.append({'operation':operation, 'before_start_line':start_a+1, 'after_start_line':start_b+1,
                        'before_lines':lines[0][start_a:end_a], 'after_lines':lines[1][start_b:end_b]})
    left, right = metadata(before), metadata(after)
    packet = {'schema_version':1, 'logical_unit':list(unit),
        'before':{'source_id':before.id, 'review_revision':request.before_revision,
                  'policy_version':before.policy_version, 'body_sha256':digest(texts[0]), 'metadata':left},
        'after':{'source_id':after.id, 'review_revision':request.after_revision,
                 'policy_version':after.policy_version, 'body_sha256':digest(texts[1]), 'metadata':right},
        'body_changed':texts[0]!=texts[1], 'line_changes':changes,
        'metadata_changes':[{'field':key, 'before':left[key], 'after':right[key]} for key in left if left[key]!=right[key]],
        'source_attributions':output_rights.notices(db,[before,after]), 'approval_transferred':False,
        'notice':'Exact text/metadata differences are review inputs. Identical wording does not establish unchanged authority, rights or applicability. Date fields are claims, not new reviews.'}
    result = {'comparison_sha256':digest(canonical(packet)), 'comparison':packet}
    # Both versions contribute source-derived output; both shared-work limits apply.
    output_rights.release(db,[before,after],result)
    db.commit()
    return result
