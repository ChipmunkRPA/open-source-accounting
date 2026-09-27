"""Resumable, permission-checked source intake. No acquisition or review happens on import."""
import json
import subprocess
import sys
from pathlib import Path
from sqlalchemy import select
from ..models import Source, IntakeWork, SourceArtifact, SourceExtraction, IntakeAttempt, Audit, now, uid
from ..errors import fail
from ..intake_schemas import IntakeCreate, IntakeManifest, https_url
from ..sec_core.core import canonical, digest, CoreError
from ..sec_core.fetch import Gateway, RateBudget, Blocked, reject_access_page
from . import rights
from .storage import Storage

PARSER_VERSION = 'source-intake-1/sec-core-0.7.0'


def families(settings):
    rows = json.loads((Path(settings.content_dir) / 'source_families.json').read_text())['families']
    return {row['id']: row for row in rows}


def register(db, settings, payload: IntakeCreate, actor_id):
    manifest = payload.manifest.canonical_metadata()
    if manifest['family_id'] not in families(settings):
        fail('UNKNOWN_FAMILY', 'Choose a registered source family.', 422)
    if db.scalar(select(IntakeWork).where(IntakeWork.family_id == manifest['family_id'],
            IntakeWork.work_id == manifest['work_id'], IntakeWork.edition == manifest['edition'])):
        fail('IMMUTABLE_EDITION', 'This edition already exists; inspect it or register a new edition.', 409)
    fingerprint = digest(canonical(manifest))
    data = payload.source.model_dump(mode='json')
    data.update(effective_from=manifest['effective_from'], effective_to=manifest['effective_to'])
    data['policy']['intake_manifest_sha256'] = fingerprint
    source = Source(**data, created_by=actor_id, reviewed=False)
    db.add(source)
    db.flush()
    work = IntakeWork(source_id=source.id, family_id=manifest['family_id'], work_id=manifest['work_id'],
                      edition=manifest['edition'], manifest=manifest, manifest_sha256=fingerprint)
    db.add(work)
    db.flush()
    db.add(Audit(actor_id=actor_id, action='intake.registered_metadata', target_id=work.id,
                 detail={'manifest_sha256': fingerprint}))
    db.commit()
    return work


def authorize(db, work_id, operations, *, lock=False):
    work = db.get(IntakeWork, work_id)
    if not work:
        fail('NOT_FOUND', 'Intake work not found.', 404)
    query = select(Source).where(Source.id == work.source_id)
    source = db.scalar(query.with_for_update() if lock else query)
    manifest = IntakeManifest.model_validate(work.manifest).canonical_metadata()
    if (digest(canonical(manifest)) != work.manifest_sha256
            or not source or source.policy.get('intake_manifest_sha256') != work.manifest_sha256):
        fail('INTAKE_REVISION', 'Intake metadata changed; register and review a new edition.', 409)
    if manifest['access_mode'] in {'reference_only', 'private'}:
        fail('SOURCE_POLICY_BLOCK', 'This intake record permits reference metadata only.', 403)
    context = {'route': manifest['route'], 'audience': 'internal_ingestion'}
    if not all(rights.allowed(source, operation, context=context) for operation in operations):
        fail('SOURCE_POLICY_BLOCK', 'Current reviewed permissions do not authorize this intake step.', 403)
    return work, source, manifest


def artifact_metadata(row):
    return {'id': row.id, 'work_id': row.work_id, 'raw_sha256': row.raw_sha256,
            'byte_count': row.byte_count, 'mime': row.mime, 'receipt': row.receipt,
            'status': 'acquired_not_reviewed', 'agent_eligible': False}


def manual_preflight(database, work_id, request_key):
    if not request_key or len(request_key) > 120:
        fail('IDEMPOTENCY_KEY', 'Supply an idempotency key of 1–120 characters.', 422)
    with database.Session() as db:
        work, source, manifest = authorize(db, work_id, ['acquire', 'store_raw'])
        if manifest['route'] != 'authorized_manual' or not manifest.get('manual_delivery'):
            fail('CONNECTOR_DISABLED', 'Register and independently review an exact manual delivery first.', 403)
        if work.family_id == 'PRIVATE_UPLOADS':
            fail('SOURCE_POLICY_BLOCK', 'Private uploads require the workspace pipeline.', 403)
        return {'manifest': manifest, 'rights_revision': rights.revision(source),
                'policy_version': source.policy_version}


def import_manual(database, settings, work_id, actor_id, request_key, raw, mime, preflight):
    """A completed body is bound to reviewed delivery evidence; never fetch or infer rights."""
    from datetime import datetime, timezone
    with database.Session() as db:
        work, source, manifest = authorize(db, work_id, ['acquire', 'store_raw'], lock=True)
        if (manifest != preflight['manifest'] or rights.revision(source) != preflight['rights_revision']
                or source.policy_version != preflight['policy_version']):
            fail('INTAKE_REVISION', 'Rights changed during import; repeat preview and review.', 409)
        if manifest['route'] != 'authorized_manual' or work.family_id == 'PRIVATE_UPLOADS':
            fail('SOURCE_POLICY_BLOCK', 'This record does not permit manual intake.', 403)
        delivery = manifest.get('manual_delivery')
        if (not delivery or len(raw) != delivery['byte_count'] or mime != delivery['mime']
                or digest(raw) != delivery['raw_sha256']):
            fail('ARTIFACT_INTEGRITY', 'File bytes, size and MIME must match the reviewed delivery.', 422)
        try:
            reject_access_page(raw)
        except Blocked:
            fail('INTAKE_BLOCKED', 'Access-control pages cannot be imported as source documents.', 422)
        if not request_key or len(request_key) > 120:
            fail('IDEMPOTENCY_KEY', 'Supply an idempotency key of 1–120 characters.', 422)
        attempt = db.scalar(select(IntakeAttempt).where(IntakeAttempt.work_id == work_id,
                                                        IntakeAttempt.request_key == request_key))
        if attempt:
            if attempt.state == 'acquired':
                return artifact_metadata(db.get(SourceArtifact, attempt.artifact_id))
            fail('INTAKE_BUSY', 'Inspect the existing attempt before resuming.', 409)
        attempt = IntakeAttempt(work_id=work_id, request_key=request_key, lease_owner=uid(), lease_until=0)
        db.add(attempt)
        db.flush()
        row = db.scalar(select(SourceArtifact).where(SourceArtifact.work_id == work_id,
                                                     SourceArtifact.raw_sha256 == delivery['raw_sha256']))
        if not row:
            key = f"sources/{work_id}/raw/{delivery['raw_sha256']}.bin"
            Storage(settings).put_immutable(key, raw, mime)
            # Storage can take time; expiry still applies at registration.
            authorize(db, work_id, ['acquire', 'store_raw'])
            receipt = {'requested_url': manifest['requested_url'], 'resolved_url': None,
                       'method': 'MANUAL_IMPORT', 'status': None, 'headers': {}, 'mime': mime,
                       'retrieved_at': None, 'imported_at': datetime.now(timezone.utc).isoformat(),
                       'manual_delivery': delivery, 'raw_sha256': delivery['raw_sha256'],
                       'manifest_sha256': work.manifest_sha256, 'rights_revision': rights.revision(source),
                       'policy_version': source.policy_version, 'operator_id': actor_id,
                       'attempt_id': attempt.id, 'acquisition_method': 'authorized_manual',
                       'source_dates': {k: manifest[k] for k in ('issued_at', 'publicly_available_at',
                           'effective_from', 'effective_to', 'date_notes', 'effective_conditions')},
                       'notices': manifest['notices'], 'redistribution_authorized': False}
            row = SourceArtifact(work_id=work_id, raw_sha256=delivery['raw_sha256'], object_key=key,
                                 byte_count=len(raw), mime=mime, receipt=receipt)
            db.add(row)
            db.flush()
        attempt.state, attempt.artifact_id = 'acquired', row.id
        db.add(Audit(actor_id=actor_id, action='intake.manual_import_unreviewed', target_id=row.id,
                     detail={'work_id': work_id, 'attempt_id': attempt.id, 'raw_sha256': row.raw_sha256}))
        db.commit()
        return artifact_metadata(row)


def make_gateway(settings, manifest):
    if not settings.source_fetch_enabled:
        fail('CONNECTOR_DISABLED', 'Explicitly configure approved intake before network access.', 403)
    urls = {manifest['requested_url'], *manifest['redirect_urls']}
    def validate(url):
        https_url(url)
        if url not in urls:
            raise CoreError('URL is outside the exact approved acquisition/redirect routes')
        return url
    location = settings.database_url
    if location.startswith('sqlite:///'):
        location = location.removeprefix('sqlite:///')
    budget = RateBudget(location)
    return Gateway(settings.sec_user_agent, budget, validator=validate, max_bytes=manifest['max_bytes'])


def acquire(database, settings, work_id, actor_id, request_key, *, gateway_factory=None):
    if not request_key or len(request_key) > 120:
        fail('IDEMPOTENCY_KEY', 'Supply an idempotency key of 1–120 characters.', 422)
    owner = uid()
    with database.Session() as db:
        work, source, manifest = authorize(db, work_id, ['acquire', 'store_raw'], lock=True)
        if manifest['route'] != 'official_http':
            fail('CONNECTOR_DISABLED', 'This record has no HTTP acquisition route.', 403)
        attempt = db.scalar(select(IntakeAttempt).where(IntakeAttempt.work_id == work_id,
                                                        IntakeAttempt.request_key == request_key))
        if attempt and attempt.state == 'acquired':
            return artifact_metadata(db.get(SourceArtifact, attempt.artifact_id))
        if attempt and attempt.state == 'blocked':
            fail('INTAKE_BLOCKED', 'Access was blocked; obtain operator review before a new attempt.', 409)
        if attempt and attempt.state == 'fetching' and attempt.lease_until > now():
            fail('INTAKE_BUSY', 'This attempt is already running; inspect it before retrying.', 409)
        if not attempt:
            attempt = IntakeAttempt(work_id=work_id, request_key=request_key, lease_owner=owner, lease_until=now()+180)
            db.add(attempt)
        else:
            attempt.lease_owner, attempt.lease_until, attempt.state = owner, now()+180, 'fetching'
            attempt.error_code = None
        db.flush()
        attempt_id = attempt.id
        policy_version, policy_revision = source.policy_version, rights.revision(source)
        db.add(Audit(actor_id=actor_id, action='intake.acquire_started', target_id=attempt_id,
                     detail={'work_id': work_id, 'policy_version': policy_version}))
        db.commit()
    try:
        gateway = (gateway_factory or make_gateway)(settings, manifest)
        result = gateway.get(manifest['requested_url'])
        if (result['requested_url'] != manifest['requested_url']
                or result['resolved_url'] not in {manifest['requested_url'], *manifest['redirect_urls']}
                or result['method'] != 'GET' or result['status'] != 200
                or result['mime'] not in manifest['allowed_mime'] or not result['raw']
                or len(result['raw']) > manifest['max_bytes']):
            raise CoreError('Unexpected or empty source content')
        raw_hash = digest(result['raw'])
        with database.Session() as db:
            work, source, manifest = authorize(db, work_id, ['acquire', 'store_raw'], lock=True)
            attempt = db.get(IntakeAttempt, attempt_id)
            if attempt.lease_owner != owner or attempt.lease_until <= now():
                fail('INTAKE_LEASE_LOST', 'Attempt lease expired; inspect and resume safely.', 409)
            if source.policy_version != policy_version or rights.revision(source) != policy_revision:
                fail('INTAKE_REVISION', 'Rights changed during acquisition; no artifact was registered.', 409)
            row = db.scalar(select(SourceArtifact).where(SourceArtifact.work_id == work_id, SourceArtifact.raw_sha256 == raw_hash))
            if not row:
                key = f'sources/{work_id}/raw/{raw_hash}.bin'
                Storage(settings).put_immutable(key, result['raw'], result['mime'])
                receipt = {k: result[k] for k in ('requested_url', 'resolved_url', 'mime', 'method', 'status', 'headers', 'retrieved_at')}
                receipt.update(raw_sha256=raw_hash, manifest_sha256=work.manifest_sha256,
                               rights_revision=policy_revision, policy_version=policy_version,
                               operator_id=actor_id, attempt_id=attempt_id, acquisition_method='direct_http',
                               source_dates={k: manifest[k] for k in ('issued_at', 'publicly_available_at', 'effective_from', 'effective_to', 'date_notes', 'effective_conditions')},
                               notices=manifest['notices'], redistribution_authorized=False)
                row = SourceArtifact(work_id=work_id, raw_sha256=raw_hash, object_key=key,
                                     byte_count=len(result['raw']), mime=result['mime'], receipt=receipt)
                db.add(row)
                db.flush()
            attempt.state, attempt.artifact_id = 'acquired', row.id
            db.add(Audit(actor_id=actor_id, action='intake.acquired_unreviewed', target_id=row.id,
                         detail={'raw_sha256': raw_hash, 'work_id': work_id}))
            db.commit()
            return artifact_metadata(row)
    except Exception as exc:
        # No URL credentials, source body, upstream exception text or legal advice enters the audit.
        with database.Session() as db:
            if isinstance(exc, Blocked):
                work = db.get(IntakeWork, work_id)
                source = db.scalar(select(Source).where(Source.id == work.source_id).with_for_update())
                source.enabled = False
                source.policy_version += 1
                db.add(Audit(actor_id=actor_id, action='intake.route_disabled_after_block', target_id=work_id))
            attempt = db.scalar(select(IntakeAttempt).where(IntakeAttempt.id == attempt_id).with_for_update())
            if attempt.lease_owner == owner:
                attempt.state = 'blocked' if isinstance(exc, Blocked) else 'failed'
                attempt.error_code = 'ACCESS_BLOCK' if isinstance(exc, Blocked) else 'ACQUISITION_FAILED'
                db.commit()
        if hasattr(exc, 'status_code'):
            raise
        fail('ACQUISITION_FAILED', 'Source acquisition failed; no approval or fallback route was granted.', 502)


def parse(db, settings, artifact_id, actor_id):
    artifact = db.get(SourceArtifact, artifact_id)
    if not artifact:
        fail('NOT_FOUND', 'Artifact not found.', 404)
    work, source, manifest = authorize(db, artifact.work_id, ['store_raw', 'extract', 'store_text'], lock=True)
    existing = db.scalar(select(SourceExtraction).where(SourceExtraction.artifact_id == artifact_id,
                                                       SourceExtraction.parser_version == PARSER_VERSION))
    if existing:
        return extraction_metadata(existing)
    raw = Storage(settings).get(artifact.object_key)
    if len(raw) != artifact.byte_count or digest(raw) != artifact.raw_sha256:
        fail('ARTIFACT_INTEGRITY', 'Raw artifact failed integrity verification.', 409)
    try:
        result = subprocess.run([sys.executable, '-m', 'app.intake_parse', manifest['parser'],
                                 manifest['parser_family'], source.title, manifest['cfr_title']],
                                input=raw, capture_output=True, timeout=25, cwd=Path(__file__).resolve().parents[2])
        if result.returncode or len(result.stdout) > 32_000_000:
            raise ValueError('Parser failed or output too large')
        passages = json.loads(result.stdout)
        if not passages or len(passages) > 10000 or any(digest(p['text']) != p['sha256'] or not p['locator'] for p in passages):
            raise ValueError('Invalid parser output')
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired):
        fail('PARSER_FAILED', 'Parsing failed; raw artifact retained, no text staged or approved.', 422)
    # Recheck time-based expiry after the bounded subprocess.
    authorize(db, work.id, ['store_raw', 'extract', 'store_text'])
    normalized = canonical(passages)
    checksum = digest(normalized)
    key = f'sources/{work.id}/parsed/{artifact.raw_sha256}-{checksum}.json'
    Storage(settings).put_immutable(key, normalized, 'application/json')
    row = SourceExtraction(artifact_id=artifact_id, parser_version=PARSER_VERSION,
                           normalized_sha256=checksum, object_key=key, passage_count=len(passages))
    db.add(row)
    db.flush()
    db.add(Audit(actor_id=actor_id, action='intake.parsed_unreviewed', target_id=row.id,
                 detail={'artifact_id': artifact_id, 'normalized_sha256': checksum, 'passages': len(passages)}))
    db.commit()
    return extraction_metadata(row)


def extraction_metadata(row):
    return {'id': row.id, 'artifact_id': row.artifact_id, 'parser_version': row.parser_version,
            'normalized_sha256': row.normalized_sha256, 'passage_count': row.passage_count,
            'status': 'parsed_not_reviewed', 'agent_eligible': False}


def stage(db, settings, extraction_id, actor_id):
    from uuid import uuid5, NAMESPACE_URL
    extraction = db.get(SourceExtraction, extraction_id)
    if not extraction:
        fail('NOT_FOUND', 'Extraction not found.', 404)
    artifact = db.get(SourceArtifact, extraction.artifact_id)
    work, parent, manifest = authorize(db, artifact.work_id, ['store_raw', 'extract', 'store_text'], lock=True)
    raw = Storage(settings).get(artifact.object_key)
    normalized = Storage(settings).get(extraction.object_key)
    if digest(raw) != artifact.raw_sha256 or digest(normalized) != extraction.normalized_sha256:
        fail('ARTIFACT_INTEGRITY', 'Raw or normalized artifact changed.', 409)
    passages = json.loads(normalized)
    ids = []
    for index, passage in enumerate(passages):
        sid = str(uuid5(NAMESPACE_URL, f'osa:{extraction.id}:{index}'))
        ids.append(sid)
        old = db.get(Source, sid)
        if old:
            if digest(old.text or '') != passage['sha256']:
                fail('ARTIFACT_INTEGRITY', 'An immutable staged passage changed.', 409)
            continue
        policy = {k: v for k, v in parent.policy.items() if not k.startswith('rights_review')}
        policy.update(requires_technical_review=True, technical_review_status='unreviewed',
                      content_sha256=passage['sha256'], content_reference_ids=[parent.id],
                      intake_parent_id=parent.id, intake_parent_policy_version=parent.policy_version,
                      intake_artifact_id=artifact.id, intake_extraction_id=extraction.id,
                      intake_locator=passage['locator'], applicability_review_status='pending')
        row = Source(id=sid, title=(parent.title+' — '+passage['locator'])[:250], publisher=parent.publisher,
                     canonical_url=parent.canonical_url, version_label=parent.version_label, kind=parent.kind,
                     framework=parent.framework, text=passage['text'], policy=policy, created_by=actor_id,
                     effective_from=manifest['effective_from'], effective_to=manifest['effective_to'],
                     reviewed=False)
        db.add(row)
    db.add(Audit(actor_id=actor_id, action='intake.staged_unapproved', target_id=extraction.id,
                 detail={'passages': len(ids)}))
    db.commit()
    return {'source_ids': ids, 'passages': len(ids), 'agent_eligible': False, 'status': 'independent_reviews_required'}
