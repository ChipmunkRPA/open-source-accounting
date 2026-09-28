"""Exact public reading coordinates; resolution never grants Agent admission."""
from ..errors import fail
from ..sec_core.core import canonical, digest
from . import rights, editorial, output_rights

VERSION = 'source-citation-lookup-1'
PASSAGE_CHARS = 3000


def revision(source):
    return digest(canonical({'version': VERSION, 'source_id': source.id,
        'policy_version': source.policy_version, 'rights': rights.revision(source),
        'editorial': editorial.revision(source), 'policy_sha256': digest(canonical(source.policy or {})),
        'effective_from': source.effective_from, 'effective_to': source.effective_to}))


def authorize(source):
    if not source or not source.enabled or not source.reviewed:
        fail('NOT_FOUND', 'Source not found.', 404)
    # No caller-provided tenant/provider context can turn this public route into a private reader.
    rights.require(source, 'display_full')
    if not source.text:
        fail('CITATION_UNAVAILABLE', 'No retained source text is available.', 409)
    p = source.policy or {}
    if p.get('intake_extraction_id') and p.get('content_sha256') != digest(source.text):
        fail('SOURCE_CHANGED', 'The retained intake body requires integrity review.', 409)


def descriptor(source, start, end, *, binding=None):
    p = source.policy or {}
    retained = p.get('intake_locator') or (p.get('sec_core') or {}).get('locator')
    base = retained or source.canonical_url or 'source:' + source.id
    if len(base) > 15000:
        fail('CITATION_UNAVAILABLE', 'The exact locator exceeds the supported citation size.', 422)
    return {'source_id': source.id, 'revision': binding or revision(source),
        'source_version': source.version_label, 'policy_version': source.policy_version,
        'source_kind': source.kind, 'source_locator': base,
        'locator_kind': 'retained_locator' if retained else 'source_record',
        'locator': base + f' (characters {start+1}–{end})',
        'character_start': start, 'character_end': end,
        'offset_convention': 'zero-based, end-exclusive Unicode characters in the retained source text',
        'source_text_sha256': digest(source.text), 'passage_text_sha256': digest(source.text[start:end])}


def release(db, source, response):
    # Every response, including locator inventories, retains notices and cumulative accounting.
    expected = revision(source)
    response['source_attributions'] = output_rights.notices(db, [source])
    response.update(lookup_version=VERSION, purpose='public_source_reading',
        agent_admission_granted=False, claim_support_verified=False, complete_document_verified=False)
    output_rights.release(db, [source], response)
    # The release locks refresh the source: retain exact citation identity across that boundary.
    if revision(source) != expected:
        fail('REVISION_CONFLICT', 'The citation changed before output release.', 409)
    authorize(source)
    return response


def inventory(db, source, start, limit):
    authorize(source)
    if start < 0 or start >= len(source.text):
        fail('CITATION_RANGE', 'Choose a character offset inside the retained text.', 422)
    binding = revision(source)
    items = [descriptor(source, offset, min(offset + PASSAGE_CHARS, len(source.text)), binding=binding)
             for offset in range(start, min(start + limit * PASSAGE_CHARS, len(source.text)), PASSAGE_CHARS)]
    end = items[-1]['character_end']
    return release(db, source, {'items': items, 'retained_characters': len(source.text),
        'next_start': end if end < len(source.text) else None})


def resolve(db, source, payload):
    authorize(source)
    if payload.expected_revision != revision(source):
        fail('REVISION_CONFLICT', 'Reload the exact citation: the source revision changed.', 409)
    start, end = payload.character_start, payload.character_end
    if not 0 <= start < end <= len(source.text) or end-start > PASSAGE_CHARS:
        fail('CITATION_RANGE', 'Resolve at most 3,000 characters inside the retained text.', 422)
    item = descriptor(source, start, end)
    if item['locator'] != payload.locator or item['passage_text_sha256'] != payload.passage_text_sha256:
        fail('CITATION_MISMATCH', 'The exact locator or passage hash does not match.', 409)
    return release(db, source, {'citation': item, 'text': source.text[start:end]})
