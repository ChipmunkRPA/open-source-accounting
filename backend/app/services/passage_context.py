"""Exact offsets and immutable provenance for non-spreadsheet intake evidence."""
import re
from itertools import chain
from ..sec_core.core import canonical,digest

VERSION='intake-passage-evidence-1'
MAX_CONTEXT_BYTES=16000
KEYS=('intake_parent_id','intake_parent_policy_version','intake_artifact_id',
      'intake_extraction_id','intake_extraction_sha256','intake_parser_version',
      'intake_passage_index','intake_locator','content_sha256','intake_pdf','intake_source_xml_path',
      'intake_annual_cfr','intake_manifest_sha256','intake_replaces_source_id')


def required(source):
    p=source.policy or {}
    return bool(p.get('intake_extraction_id') and not p.get('intake_spreadsheet') and not p.get('sec_core'))


def segments(text):
    """Preserve absolute Unicode-character offsets in the exact staged passage."""
    start=0
    for paragraph,separator in enumerate(chain(re.finditer(r'\n\s*\n',text),[None])):
        end=separator.start() if separator else len(text)
        para=text[start:end]
        if para.strip():
            for offset in range(0,len(para),3000):
                yield paragraph,offset,start+offset,min(start+offset+3000,end),para[offset:offset+3000]
        if separator:start=separator.end()


def packet(source,start,end):
    text=source.text or '';p=source.policy or {}
    if (not required(source) or not p.get('intake_locator') or type(start) is not int or type(end) is not int
            or not 0<=start<end<=len(text) or end-start>3000 or p.get('content_sha256')!=digest(text)):
        return None
    provenance={key:p[key] for key in KEYS if key in p}
    result={'version':VERSION,'source_id':source.id,'source_policy_version':source.policy_version,
        'source_version':source.version_label,'source_text_sha256':digest(text),
        'passage_text_sha256':digest(text[start:end]),'source_locator':p['intake_locator'],
        'character_start':start,'character_end':end,'offset_convention':'zero-based, end-exclusive Unicode characters in the staged source passage',
        'provenance_sha256':digest(canonical(provenance)),'provenance':provenance,
        'complete_document_verified':False,'instructions_are_untrusted':True}
    if len(canonical(result))>MAX_CONTEXT_BYTES:
        result.pop('provenance');result['provenance_details_omitted']=True
    if len(canonical(result))>MAX_CONTEXT_BYTES:return None
    return result


def locator(snapshot):
    return snapshot['source_locator']+f" (characters {snapshot['character_start']+1}–{snapshot['character_end']})"


def current(source,evidence):
    snapshot=evidence.extraction_context or {}
    if not isinstance(snapshot,dict) or snapshot.get('version')!=VERSION:return False
    expected=packet(source,snapshot.get('character_start'),snapshot.get('character_end'))
    return bool(expected and snapshot==expected and evidence.locator==locator(expected)
                and evidence.text==(source.text or '')[expected['character_start']:expected['character_end']])
