"""Public educational drafts. This router does not charge, crawl, or call a model."""
import hashlib
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from ..auth import fresh_user, settings, session, current_user
from ..content import Library, ContentError
from ..applicability_schemas import ApplicabilityDecision
from ..editorial_schemas import EditorialDecision, ParserDecision, RevisionComparison
from ..models import Source, EditorialReview
from ..errors import fail
from ..services import rights, output_rights, editorial

router = APIRouter(tags=['open library'])


def get_library(config=Depends(settings)):
    try:
        return Library(config.content_dir)
    except (ValueError, OSError, ContentError):
        fail('CONTENT_LIBRARY_UNAVAILABLE', 'The content library is missing or failed its integrity check.', 503)


@router.get('/library')
def library(q: str = Query('', max_length=200), topic: str = Query('', max_length=60),
            kind: str = Query('', max_length=40), offset: int = Query(0, ge=0),
            limit: int = Query(24, ge=1, le=100), pack=Depends(get_library)):
    return pack.search(q, topic, kind, offset, limit)


@router.get('/library/{item_id}')
def library_item(item_id: str, pack=Depends(get_library)):
    result = pack.get(item_id)
    if result is None:
        fail('NOT_FOUND', 'Library item not found.', 404)
    return result


def require_editor(user):
    if user.role != 'technical_reviewer':
        fail('FORBIDDEN', 'An assigned technical reviewer is required.', 403)


@router.get('/editorial/sources')
def editorial_sources(user=Depends(current_user), db=Depends(session)):
    require_editor(user)
    rows = db.scalars(select(Source).where(Source.enabled.is_(True)).order_by(Source.created_at.desc()).limit(2000))
    items, releases = [], []
    for s in rows:
        if not (s.policy or {}).get('requires_technical_review'): continue
        text = s.text if rights.allowed(s, 'display_full') else None
        notes = output_rights.notices(db, [s])
        if text: releases.append(([s], {'text': text, 'source_attributions': notes}))
        items.append({**rights.metadata(s), 'policy': s.policy, 'text': text,
                      'content_sha256': hashlib.sha256((s.text or '').encode()).hexdigest(),
                      'source_attributions': notes, 'created_by': s.created_by,
                      'review_revision': editorial.revision(s), 'technical_review_current': editorial.current(s)})
    output_rights.release_batch(db, releases)
    db.commit()
    return {'items': items}


@router.post('/editorial/sources/{source_id}/review')
def editorial_review(source_id: str, payload: EditorialDecision,
                     user=Depends(fresh_user), db=Depends(session)):
    require_editor(user)
    ids = sorted({source_id, *(b.source_id for b in payload.reference_bindings)})
    locked = {s.id: s for s in db.scalars(select(Source).where(Source.id.in_(ids)).order_by(Source.id).with_for_update())}
    source = locked.get(source_id)
    if not source or not (source.policy or {}).get('requires_technical_review'):
        fail('NOT_FOUND', 'Reviewable library source not found.', 404)
    row = editorial.record(db, source, payload, user.id)
    return {**rights.metadata(source), 'review_record_id': row.id,
            'review_revision': editorial.revision(source), 'technical_review_current': editorial.current(source)}


@router.get('/editorial/sources/{source_id}/reviews')
def review_history(source_id: str, user=Depends(current_user), db=Depends(session)):
    require_editor(user)
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if not source or not rights.allowed(source, 'display_full'):
        fail('SOURCE_POLICY_BLOCK', 'Current source display permission is required to read review findings.', 403)
    rows = db.scalars(select(EditorialReview).where(EditorialReview.source_id == source_id)
                      .order_by(EditorialReview.created_at.desc(), EditorialReview.id).limit(100)).all()
    supporting = output_rights.history_sources(db,source)
    result = {'source_attributions': output_rights.notices(db,supporting), 'source_id': source_id, 'current_record_id': source.policy.get('technical_review_record_id'),
              'current': editorial.current(source), 'items': [{'id': row.id, 'created_at': row.created_at,
              'payload_sha256': row.payload_sha256, 'payload': row.payload} for row in rows]}
    # Findings may contain source-derived text; normal output budgets still apply.
    output_rights.release(db, supporting, result)
    db.commit()
    return result


@router.get('/editorial/sources/{source_id}/packet')
def review_packet(source_id: str,
                  expected_review_revision: str = Query(pattern=r'^[a-f0-9]{64}$'),
                  expected_policy_version: int = Query(ge=1),
                  user=Depends(current_user), db=Depends(session)):
    require_editor(user)
    source = db.scalar(select(Source).where(Source.id == source_id).with_for_update())
    if not source or not (source.policy or {}).get('requires_technical_review'):
        fail('NOT_FOUND', 'Reviewable source not found.', 404)
    if (expected_review_revision != editorial.revision(source)
            or expected_policy_version != source.policy_version):
        fail('REVISION_CONFLICT', 'Reload the source before exporting this review packet.', 409)
    result = editorial.packet(db, source)
    db.commit()
    return result


@router.get('/editorial/extractions/{extraction_id}/packet')
def parser_packet(extraction_id: str, config=Depends(settings), user=Depends(current_user), db=Depends(session)):
    from ..services import parser_review
    require_editor(user)
    return parser_review.packet(db, config, extraction_id)


@router.post('/editorial/extractions/{extraction_id}/review')
def parser_decision(extraction_id: str, payload: ParserDecision, config=Depends(settings),
                    user=Depends(fresh_user), db=Depends(session)):
    from ..services import parser_review
    require_editor(user)
    return parser_review.record(db, config, extraction_id, payload, user.id)


@router.get('/editorial/extractions/{extraction_id}/reviews')
def parser_history(extraction_id: str, config=Depends(settings), user=Depends(current_user), db=Depends(session)):
    from ..services import parser_review
    require_editor(user)
    return parser_review.history(db, config, extraction_id)


@router.get('/editorial/extractions')
def parser_extractions(offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100),
                       user=Depends(current_user), db=Depends(session)):
    from ..models import SourceExtraction, SourceArtifact, IntakeWork
    from ..services import parser_review
    require_editor(user)
    rows = db.execute(select(SourceExtraction, SourceArtifact, IntakeWork, Source)
        .join(SourceArtifact, SourceArtifact.id == SourceExtraction.artifact_id)
        .join(IntakeWork, IntakeWork.id == SourceArtifact.work_id)
        .join(Source, Source.id == IntakeWork.source_id)
        .order_by(SourceExtraction.parsed_at.desc(), SourceExtraction.id)
        .offset(offset).limit(limit+1)).all()
    items = []
    for ex, artifact, work, source in rows[:limit]:
        last = parser_review.latest(db, ex.id)
        context = {'route':work.manifest['route'], 'audience':'internal_ingestion'}
        items.append({'id':ex.id, 'title':source.title, 'edition':source.version_label,
            'family_id':work.family_id, 'parser_version':ex.parser_version,
            'passage_count':ex.passage_count, 'parsed_at':ex.parsed_at,
            'review_sequence':last.sequence if last else 0,
            'last_decision':last.payload.get('decision') if last else None,
            'review_expires_at':last.payload.get('expires_at') if last else None,
            'packet_permitted':all(rights.allowed(source, op, context=context)
                for op in ('store_raw','store_text','display_full','export'))})
    return {'items':items, 'offset':offset, 'next_offset':offset+limit if len(rows)>limit else None}


@router.post('/editorial/compare')
def compare_revisions(payload: RevisionComparison, user=Depends(current_user), db=Depends(session)):
    from ..services import review_comparison
    require_editor(user)
    return review_comparison.compare(db, payload)


@router.post('/editorial/sources/{source_id}/applicability')
def applicability_decision(source_id: str, payload: ApplicabilityDecision,
                           user=Depends(fresh_user), db=Depends(session)):
    from ..services import applicability
    require_editor(user)
    source=db.scalar(select(Source).where(Source.id==source_id).with_for_update())
    if not source or not source.policy.get('requires_technical_review'):
        fail('NOT_FOUND','Reviewable source not found.',404)
    return applicability.record(db,source,payload,user.id)


@router.get('/editorial/sources/{source_id}/applicability')
def applicability_history(source_id: str, user=Depends(current_user), db=Depends(session)):
    from ..services import applicability
    require_editor(user)
    source=db.scalar(select(Source).where(Source.id==source_id).with_for_update())
    if not source:fail('NOT_FOUND','Source not found.',404)
    return applicability.history(db,source)
