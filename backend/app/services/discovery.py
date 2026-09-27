"""Authorized offline discovery is separate from acquiring or approving linked works."""
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from sqlalchemy import select
from ..errors import fail
from ..models import SourceArtifact, SourceDiscovery, Audit
from ..source_discovery import VERSION
from ..sec_core.core import canonical, digest
from . import intake, rights
from .storage import Storage


def metadata(row):
    return {'id': row.id, 'artifact_id': row.artifact_id, 'adapter_version': row.adapter_version,
            'recipe_sha256': row.recipe_sha256, 'normalized_sha256': row.normalized_sha256,
            'candidate_count': row.candidate_count, 'status': 'discovered_not_reviewed',
            'agent_eligible': False, 'network_requests': 0}


def discover(db, settings, artifact_id, actor_id):
    artifact = db.get(SourceArtifact, artifact_id)
    if not artifact:
        fail('NOT_FOUND', 'Index artifact not found.', 404)
    work, source, manifest = intake.authorize(db, artifact.work_id, ['store_raw', 'extract', 'store_text'], lock=True)
    if artifact.mime != 'text/html':
        fail('DISCOVERY_ADAPTER', 'This adapter requires an authorized HTML index; API/XML adapters are separate.', 422)
    recipe = intake.families(settings)[work.family_id]
    recipe_hash = digest(canonical(recipe))
    hosts = sorted({urlsplit(url).hostname for url in recipe['seed_urls'] if urlsplit(url).scheme == 'https'})
    base_url = artifact.receipt.get('resolved_url') or manifest['requested_url']
    if urlsplit(base_url).hostname not in hosts:
        fail('DISCOVERY_ROUTE', 'Index host is outside the family discovery recipe.', 422)
    existing = db.scalar(select(SourceDiscovery).where(SourceDiscovery.artifact_id == artifact.id,
        SourceDiscovery.adapter_version == VERSION, SourceDiscovery.recipe_sha256 == recipe_hash))
    if existing:
        return metadata(existing)
    raw = Storage(settings).get(artifact.object_key)
    if len(raw) != artifact.byte_count or digest(raw) != artifact.raw_sha256:
        fail('ARTIFACT_INTEGRITY', 'Index artifact failed integrity verification.', 409)
    try:
        result = subprocess.run([sys.executable, '-m', 'app.source_discovery', base_url, json.dumps(hosts)],
            input=raw, capture_output=True, timeout=25, cwd=Path(__file__).resolve().parents[2])
        if result.returncode or len(result.stdout) > 32_000_000:
            raise ValueError('Discovery subprocess failed')
        output = json.loads(result.stdout)
        if output['raw_sha256'] != artifact.raw_sha256 or output['adapter_version'] != VERSION:
            raise ValueError('Invalid discovery provenance')
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired):
        fail('DISCOVERY_FAILED', 'Index requires review or a different adapter; no partial candidates saved.', 422)
    intake.authorize(db, work.id, ['store_raw', 'extract', 'store_text'])
    output.update(artifact_id=artifact.id, family_id=work.family_id, recipe_sha256=recipe_hash,
                  recipe=recipe,
                  manifest_sha256=work.manifest_sha256, rights_revision=rights.revision(source),
                  source_dates=artifact.receipt['source_dates'], notices=manifest['notices'])
    normalized = canonical(output)
    checksum = digest(normalized)
    key = f'sources/{work.id}/discovery/{artifact.raw_sha256}-{checksum}.json'
    Storage(settings).put_immutable(key, normalized, 'application/json')
    intake.authorize(db, work.id, ['store_raw', 'extract', 'store_text'])
    row = SourceDiscovery(artifact_id=artifact.id, adapter_version=VERSION, recipe_sha256=recipe_hash,
                          normalized_sha256=checksum, object_key=key, candidate_count=len(output['items']))
    db.add(row)
    db.flush()
    db.add(Audit(actor_id=actor_id, action='intake.discovered_unreviewed', target_id=row.id,
                 detail={'artifact_id': artifact.id, 'normalized_sha256': checksum,
                         'candidate_count': row.candidate_count}))
    db.commit()
    return metadata(row)


def read(db, settings, discovery_id):
    row = db.get(SourceDiscovery, discovery_id)
    if not row:
        fail('NOT_FOUND', 'Discovery not found.', 404)
    artifact = db.get(SourceArtifact, row.artifact_id)
    intake.authorize(db, artifact.work_id, ['store_text', 'display_full'], lock=True)
    normalized = Storage(settings).get(row.object_key)
    if digest(normalized) != row.normalized_sha256:
        fail('ARTIFACT_INTEGRITY', 'Discovery failed integrity verification.', 409)
    intake.authorize(db, artifact.work_id, ['store_text', 'display_full'])
    return {**metadata(row), 'discovery': json.loads(normalized)}
