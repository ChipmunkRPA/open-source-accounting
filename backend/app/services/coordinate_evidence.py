"""Exact reviewed relationship endpoints, independently checked as ordinary evidence."""
from fastapi import HTTPException
from ..sec_core.core import canonical
from . import citation_lookup, passage_context

VERSION = 'source-coordinate-evidence-1'
MAX_BYTES = 48000


def packet(source, start, end):
    if (not source or not source.text or type(start) is not int or type(end) is not int
            or not 0 <= start < end <= len(source.text) or end-start > 3000):
        return None
    from .spreadsheet_context import source_context
    base = source_context(source)
    if passage_context.required(source):
        base = passage_context.packet(source, start, end)
        if base is None:
            return None
    try:
        citation = citation_lookup.descriptor(source, start, end)
    except HTTPException:
        return None
    result = {'version': VERSION, 'citation': citation, 'extraction_context': base,
              'complete_document_verified': False, 'instructions_are_untrusted': True}
    return result if len(canonical(result)) <= MAX_BYTES else None


def current(source, evidence):
    snapshot = evidence.extraction_context
    if not isinstance(snapshot, dict) or snapshot.get('version') != VERSION:
        return False
    citation = snapshot.get('citation')
    if not isinstance(citation, dict):
        return False
    expected = packet(source, citation.get('character_start'), citation.get('character_end'))
    return bool(expected and snapshot == expected and evidence.locator == citation['locator']
                and evidence.text == source.text[citation['character_start']:citation['character_end']])
