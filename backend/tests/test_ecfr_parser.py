"""Original fixtures; no actual source acquisition or professional review."""
import pytest
from sqlalchemy import select, func
from app.ecfr_parser import parse, EcfrError, VERSION
from app.sec_core import parsers
from app.sec_core.core import canonical, digest
from app.models import SourceExtraction, SourceArtifact, Source
from app.services.storage import Storage
from app.services.intake import PARSER_VERSION
from test_source_intake import registered, fetch, FakeGateway, ADMIN, RAW, parse as api_parse

TABLE = b'''<GPOTABLE COLS="2" CDEF="s20,20"><TTITLE>Original test</TTITLE><BOXHD><CHED H="1">Year</CHED><CHED H="1">Amount</CHED></BOXHD><ROW><ENT>2025</ENT><ENT>(1,250)</ENT></ROW><ROW><ENT>2024</ENT><ENT/></ROW><TNOTE><P>Note <FTREF>1</FTREF>.</P></TNOTE></GPOTABLE>'''


def document(table=TABLE):
    return b'<ECFR><DIV8 TYPE="SECTION" N="999.1"><HEAD>Synthetic title</HEAD><PRTPAGE P="12"/>'+table+b'<P>After.</P></DIV8></ECFR>'


def test_gpo_headers_cells_notes_paths_and_hashes():
    result = parse(document())
    assert result == parse(document())
    assert result[0]['text'] == 'Synthetic title'
    p = result[1]
    assert p['table']['rows'][0]['cells'] == ['Year', 'Amount']
    assert p['table']['rows'][1]['cells'] == ['2025', '(1,250)']
    assert p['table']['rows'][2]['cells'] == ['2024', '']
    assert p['table']['notes'][0]['text'] == 'Note [footnote reference: 1].'
    assert p['table']['rows'][1]['cell_metadata'][1]['source_xml_path'].endswith('/ROW[1]/ENT[2]')
    assert p['source_xml_path'] == '/ECFR[1]/DIV8[1]/GPOTABLE[1]'
    assert p['printed_page_at_start'] == '12'
    assert all(x['sha256'] == digest(x['text']) and x['review_status'] == 'pending' for x in result)
    assert 'Year' not in parsers.ecfr_xml(document())[0]['text']  # retained legacy replay behavior


def test_html_table_sections_preserve_headers_row_headers_and_empty_cells():
    xml = b'<TABLE><CAPTION>Test</CAPTION><THEAD><TR><TH>Period</TH><TH>Value</TH></TR></THEAD><TBODY><TR><TH SCOPE="row">2025</TH><TD>-10.50</TD></TR><TR><TD>2024</TD><TD/></TR></TBODY></TABLE>'
    p = parse(document(xml))[1]
    assert [r['cells'] for r in p['table']['rows']] == [['Period', 'Value'], ['2025', '-10.50'], ['2024', '']]
    assert p['table']['rows'][1]['cell_metadata'][0]['attributes']['SCOPE'] == 'row'
    assert 'Header: Period | Value' in p['text']


@pytest.mark.parametrize('table,code', [
    (TABLE.replace(b'H="1"', b'H="2"'), 'unsupported_table_span_or_alignment'),
    (TABLE.replace(b'<ENT/>', b''), 'inconsistent_table_columns'),
    (TABLE.replace(b'<ROW>', b'<ROW>lost'), 'unsupported_mixed_table'),
    (TABLE.replace(b'<ENT>2025', b'<ENT O="1">2025'), 'unsupported_table_span_or_alignment'),
    (TABLE.replace(b'</BOXHD>', b'</BOXHD><BOXHD><CHED>Extra</CHED><CHED>Header</CHED></BOXHD>'), 'unsupported_multirow_or_late_header'),
    (b'<TABLE><TR><TD COLSPAN="2">x</TD></TR></TABLE>', 'unsupported_table_span_or_alignment'),
    (b'<TABLE><TR><TD><TABLE/></TD></TR></TABLE>', 'unsupported_inline_structure'),
    (b'<GPOTABLE COLS="0"/>', 'invalid_table_columns'),
    (b'<GPH/>', 'unsupported_structure'),
    (b'<P>formula <FR>x/y</FR></P>', 'unsupported_inline_structure'),
])
def test_no_partial_or_silently_flattened_layouts(table, code):
    with pytest.raises(EcfrError) as exc: parse(document(table))
    assert exc.value.code == code and exc.value.path.startswith('/ECFR[1]')


@pytest.mark.parametrize('raw,code', [
    (b'<!DOCTYPE ECFR [<!ENTITY x "boom">]>'+document(), 'unsafe_xml'),
    (document().decode().encode('utf-16'), 'unsupported_encoding'),
    (b'<CFRDOC/>', 'wrong_document_type'),
    (b'<ECFR/>', 'no_sections'),
    (b'<ECFR><SECTION N="1.1"><SECTION N="1.2"><P>x</P></SECTION></SECTION></ECFR>', 'nested_section'),
    (b'<ECFR><SECTION N="1.1"/><SECTION N="1.1"/></ECFR>', 'invalid_or_duplicate_section'),
    (document(b'<PRTPAGE P="1">lost</PRTPAGE>'), 'unsupported_page_marker'),
    (b'<ECFR>'+b'<PART>'*81+b'</PART>'*81+b'</ECFR>', 'structure_limit'),
])
def test_unsafe_ambiguous_inputs(raw, code):
    with pytest.raises(EcfrError) as exc: parse(raw)
    assert exc.value.code == code


def test_old_extraction_is_preserved_but_new_parse_uses_new_version(client):
    artifact = fetch(client, registered(client), FakeGateway(RAW))
    old_bytes = canonical(parsers.ecfr_xml(RAW))
    old_hash = digest(old_bytes)
    key = 'sources/synthetic-legacy-replay.json'
    Storage(client.app.state.settings).put_immutable(key, old_bytes, 'application/json')
    with client.app.state.db.Session() as db:
        old = SourceExtraction(artifact_id=artifact['id'], parser_version=PARSER_VERSION,
                               normalized_sha256=old_hash, object_key=key, passage_count=1)
        db.add(old); db.commit(); old_id = old.id
    new = api_parse(client, artifact)
    assert new['id'] != old_id and new['parser_version'] == VERSION
    assert api_parse(client, artifact)['id'] == new['id']
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 2
        assert db.get(SourceExtraction, old_id).normalized_sha256 == old_hash
        assert Storage(client.app.state.settings)._path(key).read_bytes() == old_bytes
    staged = client.post('/api/v1/admin/intake/extractions/'+new['id']+'/stage', headers=ADMIN)
    assert staged.status_code == 200, staged.text
    with client.app.state.db.Session() as db:
        source = db.get(Source, staged.json()['source_ids'][0])
        assert source.policy['intake_parser_version'] == VERSION and not source.reviewed
        assert source.policy['intake_source_xml_path'] == '/ECFR[1]/SECTION[1]/P[1]'


def test_failure_keeps_raw_without_extraction(client):
    raw = document(b'<GPH/>')
    artifact = fetch(client, registered(client), FakeGateway(raw))
    response = client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN)
    assert response.status_code == 422 and 'ECFR_PARSE_BLOCKED' in response.text
    assert 'unsupported_structure' in response.text
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0
        saved = db.get(SourceArtifact, artifact['id'])
        assert Storage(client.app.state.settings)._path(saved.object_key).read_bytes() == raw
