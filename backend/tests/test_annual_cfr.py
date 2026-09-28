"""Original synthetic annual XML only; no real regulation or professional approval."""
import pytest
from sqlalchemy import select, func
from app.annual_cfr import parse, AnnualCfrError, VERSION
from app.intake_schemas import IntakeCreate
from app.models import Source, SourceArtifact, SourceExtraction
from app.sec_core.core import digest
from app.services import rights
from app.services.storage import Storage
from test_source_intake import ADMIN, payload, registered, fetch, FakeGateway, parse as api_parse

EDITION = {'year': 2025, 'volume': 3, 'revised_as_of': '2025-04-01'}
URL = 'https://www.govinfo.gov/bulkdata/CFR/2025/title-17/CFR-2025-title17-vol3.xml'
RAW = b'''<CFRDOC REV="synthetic"><TITLE><BIBINF><BTI>Title 17</BTI><PUBYEAR>2025</PUBYEAR><VOL>3</VOL></BIBINF>
<SECTION><SECTNO>\xc2\xa7 999.1</SECTNO><SUBJECT>Original test only</SUBJECT><PRTPAGE P="10"/>
<P ID="a">Amount <SU>2</SU> and note <FTREF>1</FTREF>.</P>
<GPOTABLE COLS="2" CDEF="s20,20"><TTITLE>Synthetic balances</TTITLE><BOXHD><CHED H="1">Year</CHED><CHED H="1">Amount</CHED></BOXHD>
<ROW><ENT I="1">2025</ENT><ENT>(1,250.00)</ENT></ROW><ROW><ENT>2024</ENT><ENT></ENT></ROW>
<TNOTE><P>1. Original example only.</P></TNOTE><PRTPAGE P="11"/></GPOTABLE><P>After table.</P></SECTION></TITLE></CFRDOC>'''


def annual_payload(**changes):
    return payload(parser='annual_cfr_xml', requested_url=URL, edition='2025', annual_cfr=EDITION, **changes)


def test_exact_table_headers_numbers_empty_cells_notes_and_paths():
    result = parse(RAW, '17', EDITION)
    assert result == parse(RAW, '17', EDITION)
    table = next(p for p in result if 'table' in p)
    assert table['table']['rows'][0]['cells'] == ['Year', 'Amount']
    assert table['table']['rows'][1]['cells'] == ['2025', '(1,250.00)']
    assert table['table']['rows'][2]['cells'] == ['2024', '']
    assert table['table']['rows'][1]['cell_metadata'][0]['attributes'] == {'I': '1'}
    assert table['table']['notes'] == ['1. Original example only.']
    assert table['source_xml_path'] == '/CFRDOC[1]/TITLE[1]/SECTION[1]/GPOTABLE[1]'
    assert table['printed_page_at_start'] == '10' and table['printed_page_markers'] == ['11']
    assert result[-1]['printed_page_at_start'] == '11'
    assert '17 CFR 999.1' in table['locator'] and '2025 annual edition, volume 3' in table['locator']
    assert not table['annual_cfr']['legal_effective_date_inferred']
    assert not table['annual_cfr']['publisher_completeness_verified']
    assert '[superscript: 2]' in result[5]['text']
    assert all(p['sha256'] == digest(p['text'].encode()) for p in result)


@pytest.mark.parametrize('before,after,code', [
    (b'<PUBYEAR>2025', b'<PUBYEAR>2024', 'edition_identity_mismatch'),
    (b'<VOL>3', b'<VOL>4', 'edition_identity_mismatch'),
    (b'Title 17', b'Title 12', 'edition_identity_mismatch'),
    (b'<P>After table.</P>', b'<GPH/>', 'unsupported_structure'),
    (b'<ENT>(1,250.00)</ENT>', b'', 'inconsistent_table_columns'),
    (b'<CHED H="1">Year', b'<CHED H="2">Year', 'unsupported_table_span_or_alignment'),
    (b'<ENT I="1">', b'<ENT O="2">', 'unsupported_table_span_or_alignment'),
    (b'<ROW>', b'<ROW>discarded?', 'unsupported_mixed_table'),
    (b'<SU>2</SU>', b'<FR>2</FR>', 'unsupported_inline_structure'),
    (b'<PRTPAGE P="10"/>', b'<PRTPAGE P="10">lost text</PRTPAGE>', 'unsupported_page_marker'),
    (b'<P>After table.</P>', b'<SECTION><SECTNO>999.1</SECTNO></SECTION>', 'invalid_or_duplicate_section'),
])
def test_unsupported_content_fails_entire_parse(before, after, code):
    with pytest.raises(AnnualCfrError) as error:
        parse(RAW.replace(before, after), '17', EDITION)
    assert error.value.code == code


@pytest.mark.parametrize('raw,code', [
    (b'<!DOCTYPE CFRDOC [<!ENTITY x "bad">]>'+RAW, 'unsafe_xml'),
    (RAW.decode().encode('utf-16'), 'unsupported_encoding'),
    (b'<CFRDOC>', 'invalid_xml'),
    (b'<ECFR/>', 'wrong_document_type'),
    (b'<CFRDOC/>', 'no_sections'),
    (b'<CFRDOC>'+b'<PART>'*81+b'</PART>'*81+b'</CFRDOC>', 'structure_limit'),
])
def test_unsafe_or_wrong_documents(raw, code):
    with pytest.raises(AnnualCfrError) as error:
        parse(raw, '17', EDITION)
    assert error.value.code == code


@pytest.mark.parametrize('field,value', [
    ('annual_cfr', None), ('annual_cfr', {'year': True, 'volume': 3}),
    ('edition', '2024'), ('requested_url', URL+'?mirror=1'),
    ('redirect_urls', [URL]), ('allowed_mime', ['text/html']),
    ('annual_cfr', {**EDITION, 'revised_as_of': '2024-04-01'}),
])
def test_manifest_identity_must_match(field, value):
    body = annual_payload(); body['manifest'][field] = value
    with pytest.raises(ValueError): IntakeCreate.model_validate(body)


def test_legacy_manifest_hash_contract_and_distinct_version():
    old = IntakeCreate.model_validate(payload()).manifest.canonical_metadata()
    assert 'annual_cfr' not in old and 'manual_delivery' not in old
    new = IntakeCreate.model_validate(annual_payload()).manifest.canonical_metadata()
    assert new['annual_cfr'] == EDITION
    from app.services.intake import parser_version, PARSER_VERSION
    from app.ecfr_parser import VERSION as ECFR_VERSION
    assert parser_version(old) == ECFR_VERSION
    assert parser_version({**old, 'parser': 'text'}) == PARSER_VERSION
    assert parser_version(new) == VERSION != PARSER_VERSION


def test_api_isolated_parse_retry_and_separate_review(client):
    work = registered(client, body=annual_payload())
    artifact = fetch(client, work, FakeGateway(RAW))
    extraction = api_parse(client, artifact)
    assert extraction['parser_version'] == VERSION
    assert api_parse(client, artifact)['id'] == extraction['id']
    response = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN)
    assert response.status_code == 200, response.text
    with client.app.state.db.Session() as db:
        for sid in response.json()['source_ids']:
            source = db.get(Source, sid)
            assert not source.reviewed and not rights.allowed(source, 'model_input')
            assert source.effective_from is None
            assert source.policy['intake_annual_cfr']['year'] == 2025
            assert source.policy['intake_source_xml_path'].startswith('/CFRDOC[1]')


def test_api_failure_retains_raw_and_creates_no_partial_extraction(client):
    raw = RAW.replace(b'<P>After table.</P>', b'<GPH/>')
    artifact = fetch(client, registered(client, body=annual_payload()), FakeGateway(raw))
    response = client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN)
    assert response.status_code == 422, response.text
    assert 'ANNUAL_CFR_PARSE_BLOCKED' in response.text and 'unsupported_structure' in response.text
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0
        stored = db.get(SourceArtifact, artifact['id'])
        assert Storage(client.app.state.settings)._path(stored.object_key).read_bytes() == raw


def test_annual_parse_does_not_bypass_operation_permission(client):
    body = annual_payload(); body['source']['policy']['extract'] = False
    artifact = fetch(client, registered(client, body=body), FakeGateway(RAW))
    response = client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN)
    assert response.status_code == 403
