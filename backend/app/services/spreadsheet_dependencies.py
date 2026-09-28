"""Separately authorized spreadsheet companions, each retained as ordinary evidence."""
from sqlalchemy import select
from ..models import Source, Evidence
from ..sec_core.core import canonical, digest
from . import spreadsheet_context, editorial

VERSION = 'spreadsheet-source-dependencies-1'
MAX_CANDIDATES = 200


def related(source, target):
    p, q = source.policy or {}, target.policy or {}
    if source.id == target.id or not all(p.get(k) and p.get(k) == q.get(k) for k in
            ('intake_extraction_id', 'intake_artifact_id', 'intake_parent_id')):
        return False
    a, b = p.get('intake_spreadsheet') or {}, q.get('intake_spreadsheet') or {}
    return bool(a and b and ((a.get('sheet') and a.get('sheet') == b.get('sheet') and
                            any(k in b for k in ('table', 'comment', 'header_footer')))
                           or 'defined_names' in b or 'calculation_properties' in b))


def binding(source):
    return {'source_id': source.id, 'policy_version': source.policy_version,
            'review_revision': editorial.revision(source),
            'locator': source.policy['intake_locator'], 'text_sha256': digest(source.text),
            'metadata_sha256': digest(canonical(source.policy['intake_spreadsheet']))}


def packet(source, bindings):
    result = spreadsheet_context.source_context(source)
    result.update(source_dependencies={'version': VERSION, 'bindings': bindings},
                  related_source_context='separate_evidence', context_partial=True,
                  warning='Bound companions are separately cited evidence, each with independent operation rights and review. Selection is bounded and does not establish complete workbook context.')
    return result


def admissible(source, run, context):
    from .rights import allowed
    from .applicability import applies
    from .dependencies import allowed as dependencies_allowed
    framework = run.context.get('framework', 'US_GAAP')
    period = run.context.get('period_end')
    if not source.enabled or not source.reviewed or not source.text or len(source.text) > 3000:
        return False
    if framework not in {'BOTH', 'UNKNOWN'} and source.framework not in {framework, 'BOTH', 'AUDIT'}:
        return False
    if period and ((source.effective_from and source.effective_from > period) or
                   (source.effective_to and source.effective_to < period)):
        return False
    return (all(allowed(source, op, context=context) for op in ('model_input', 'store_text', 'quote'))
            and applies(source, run.context)
            and dependencies_allowed(source, 'model_input', context=context, accounting_context=run.context))


def select_with_companions(db, run, pool, limit, *, context):
    """Preserve selected-document priority and the workflow's total evidence limit."""
    selected, seen = [], set()
    for original in pool:
        row = dict(original)
        key = (row['source_id'], row['document_id'], row['locator'])
        if key in seen:
            continue
        if len(selected) >= limit:
            break
        selected.append(row)
        seen.add(key)
        source = db.get(Source, row['source_id']) if row['source_id'] else None
        if not source or not row.get('text') or not (source.policy or {}).get('intake_spreadsheet'):
            continue
        extraction = source.policy.get('intake_extraction_id')
        if not extraction:
            continue
        candidates = db.scalars(select(Source).where(
            Source.policy['intake_extraction_id'].as_string() == extraction,
            Source.enabled.is_(True)).order_by(Source.id).limit(MAX_CANDIDATES)).all()
        bindings = []
        for target in candidates:
            if not related(source, target) or not admissible(target, run, context):
                continue
            locator = target.policy.get('intake_locator')
            if not locator:
                continue
            item = binding(target)
            proposal = packet(source, [*bindings, item])
            if (len(bindings) >= spreadsheet_context.MAX_RELATED or
                    len(canonical(proposal)) > spreadsheet_context.MAX_CONTEXT_CHARS):
                break
            companion_key = (target.id, None, locator)
            if companion_key not in seen:
                if len(selected) >= limit:
                    break
                selected.append({'source_id': target.id, 'document_id': None,
                    'title': target.title, 'locator': locator, 'text': target.text,
                    'access': 'primary_text_reviewed' if target.kind in {'standard', 'rule'} else 'secondary_text_reviewed',
                    'source_kind': target.kind, 'policy_version': target.policy_version,
                    'extraction_context': spreadsheet_context.source_context(target)})
                seen.add(companion_key)
            bindings.append(item)
        # No dependency packet is fabricated when no companion passes or capacity is exhausted.
        if bindings:
            row['extraction_context'] = packet(source, bindings)
    return selected


def current(db, evidence, source, *, action, context):
    """A dependency cannot disappear from the run or survive its independent gates."""
    from .rights import evidence_allowed
    declaration = (evidence.extraction_context or {}).get('source_dependencies', {})
    if not isinstance(declaration, dict):
        return False
    bindings = declaration.get('bindings')
    if declaration.get('version') != VERSION or not isinstance(bindings, list) or not 0 < len(bindings) <= spreadsheet_context.MAX_RELATED:
        return False
    if (len(canonical(evidence.extraction_context)) > spreadsheet_context.MAX_CONTEXT_CHARS
            or evidence.extraction_context != packet(source, bindings)):
        return False
    seen = set()
    for item in bindings:
        if (not isinstance(item, dict) or not isinstance(item.get('source_id'), str)
                or item['source_id'] in seen):
            return False
        seen.add(item.get('source_id'))
        target = db.get(Source, item.get('source_id')) if item.get('source_id') else None
        if not target or not related(source, target) or not target.text or not target.policy.get('intake_locator'):
            return False
        if binding(target) != item:
            return False
        rows = db.scalars(select(Evidence).where(Evidence.run_id == evidence.run_id,
            Evidence.source_id == target.id, Evidence.locator == item['locator']).limit(2)).all()
        # Companions must be leaf evidence. This also rejects cycles without recursion.
        if len(rows) != 1 or rows[0].text != target.text or rows[0].extraction_context != spreadsheet_context.source_context(target):
            return False
        if not evidence_allowed(db, rows[0], action, context=context):
            return False
    return True
