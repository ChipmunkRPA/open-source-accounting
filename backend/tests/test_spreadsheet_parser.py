"""Original synthetic spreadsheets only; no model execution or professional approval."""
import io
import zipfile
from types import SimpleNamespace
import pytest
from sqlalchemy import select, func
from app.spreadsheet_parser import parse_xlsx, parse_csv, SpreadsheetError, S, R, P, VERSION
from app.services.documents import parse_bytes, preflight
from app.models import Document
from app.agents.workflows import preprocess
from conftest import activate

CT='http://schemas.openxmlformats.org/package/2006/content-types'
MIME='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def fixture(cells=None, extra=None, sheet_extra='', date1904='0', state='visible'):
    cells=cells if cells is not None else '''<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>Amount (USD)</t></is></c></row>
    <row r="2" hidden="1"><c r="A2" t="inlineStr"><is><t>00125</t></is></c><c r="B2" s="0"><v>-1250.00</v></c><c r="D2"><f>B2*2</f><v>-2500</v></c><c r="E2"><f>SUM(B2:D2)</f></c></row>'''
    files={'[Content_Types].xml':f'<Types xmlns="{CT}"><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>',
      '_rels/.rels':f'<Relationships xmlns="{P}"><Relationship Id="r1" Type="{R}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
      'xl/workbook.xml':f'<workbook xmlns="{S}" xmlns:r="{R}"><workbookPr date1904="{date1904}"/><sheets><sheet name="Trial balance" sheetId="1" r:id="s1" state="{state}"/></sheets></workbook>',
      'xl/_rels/workbook.xml.rels':f'<Relationships xmlns="{P}"><Relationship Id="s1" Type="{R}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="ss" Type="{R}/sharedStrings" Target="sharedStrings.xml"/><Relationship Id="st" Type="{R}/styles" Target="styles.xml"/></Relationships>',
      'xl/worksheets/sheet1.xml':f'<worksheet xmlns="{S}"><cols><col min="3" max="3" hidden="1"/></cols><sheetData>{cells}</sheetData>{sheet_extra}</worksheet>',
      'xl/sharedStrings.xml':f'<sst xmlns="{S}"><si><t>Account code</t></si></sst>',
      'xl/styles.xml':f'<styleSheet xmlns="{S}"><numFmts><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts><cellXfs><xf numFmtId="164"/></cellXfs></styleSheet>'}
    files.update(extra or {})
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,text in files.items():z.writestr(name,text)
    return out.getvalue()


def test_cell_locations_values_formulas_cache_and_hidden_context():
    raw=fixture(sheet_extra='<mergeCells><mergeCell ref="A4:B4"/></mergeCells>')
    result=parse_xlsx(raw,100000)
    assert result==parse_xlsx(raw,100000)
    assert [c['locator'] for c in result]==["'Trial balance'!A1:B1","'Trial balance'!A2:E2"]
    a,b,d,e=result[1]['spreadsheet']['cells']
    assert a['value']=='00125' and b['value']=='-1250.00'
    assert b['number_format_code']=='#,##0.00'
    assert d['formula']['text']=='B2*2' and d['value']=='-2500' and d['cache_status']=='unverified_cached'
    assert e['cache_status']=='missing' and e['value'] is None
    m=result[1]['spreadsheet']
    assert m['row_hidden']=='1' and m['merged_ranges']==['A4:B4'] and m['column_properties'][0]['hidden']=='1'
    assert m['parser_version']==VERSION and not m['calculated'] and not m['display_rendered']


def test_dates_errors_booleans_empty_cache_and_shared_formulas():
    cells='''<row r="1"><c r="A1" t="d"><v>2026-09-27T00:00:00Z</v></c><c r="B1" t="b"><v>0</v></c><c r="C1" t="e"><v>#DIV/0!</v></c><c r="D1" t="str"><f>""</f><v/></c><c r="E1"><f t="shared" si="0"/><v>2</v></c><c r="F1" s="0"><v>60</v></c></row>'''
    result=parse_xlsx(fixture(cells,date1904='1',state='veryHidden'),10000)
    m=result[0]['spreadsheet'];a,b,c,d,e,f=m['cells']
    assert m['date_system']=='1904' and m['sheet_state']=='veryHidden'
    assert a['value'].endswith('Z') and b['value']=='0' and c['value']=='#DIV/0!'
    assert d['value']=='' and d['cache_status']=='unverified_cached'
    assert e['formula']=={'text':None,'attributes':{'t':'shared','si':'0'}}
    assert f['value']=='60'  # Never infer Excel's serial-60 date or render a number.


def test_empty_sheet_has_no_invented_cell():
    row=parse_xlsx(fixture(''),10000)[0]
    assert row['spreadsheet']['empty_sheet'] and row['spreadsheet']['cells']==[]
    assert 'A1' not in row['locator']


@pytest.mark.parametrize('cells,reason',[
 ('<row r="1"><c r="XFE1"><v>1</v></c></row>','cell_reference_out_of_range'),
 ('<row r="1"><c r="A2"><v>1</v></c></row>','ambiguous_cell_order'),
 ('<row r="1"><c r="A1"><v>1</v></c><c r="A1"><v>2</v></c></row>','ambiguous_cell_order'),
 ('<row r="1"><c r="A1" t="s"><v>999</v></c></row>','invalid_shared_string_index'),
 ('<row r="1"><c r="A1"><v>NaN</v></c></row>','nonfinite_numeric_value'),
 ('<row r="1"><c r="A1" t="d"><v>2026-02-30</v></c></row>','invalid_iso_date'),
 ('<row r="1"><c r="A1" s="99"><v>1</v></c></row>','invalid_cell_style'),
 ('<row r="1"><c r="A1" t="b"><v>2</v></c></row>','invalid_boolean_value'),
 ('<row r="1"><c r="A1"><v>1</v><v>2</v></c></row>','ambiguous_cell_content'),
 ])
def test_ambiguous_cells_fail_whole_workbook(cells,reason):
    with pytest.raises(SpreadsheetError,match=reason):parse_xlsx(fixture(cells),10000)


@pytest.mark.parametrize('part,content',[
 ('xl/vbaProject.bin',b'not executed'),('xl/externalLinks/externalLink1.xml','<externalLink/>'),
 ('xl/embeddings/object.bin',b'not executed'),
 ('../secret.xml','<secret/>'),
 ('xl/worksheets/sheet2.xml',f'<worksheet xmlns="{S}"><sheetData/></worksheet>'),
 ('xl/worksheets/_rels/sheet1.xml.rels',f'<Relationships xmlns="{P}"><Relationship Id="x" Type="{R}/hyperlink" Target="https://example.test/never-fetch" TargetMode="External"/></Relationships>'),
 ('xl/sharedStrings.xml','<!DOCTYPE x [<!ENTITY a "not expanded">]><sst/>'),
 ])
def test_unsafe_packages_and_orphan_content_are_blocked(part,content):
    with pytest.raises(SpreadsheetError):parse_xlsx(fixture(extra={part:content}),100000)


@pytest.mark.parametrize('node',['drawing','oleObjects','extLst','legacyDrawing'])
def test_graphics_and_extended_content_require_review(node):
    with pytest.raises(SpreadsheetError,match='requires_review'):parse_xlsx(fixture(sheet_extra=f'<{node}/>'),100000)


def test_invalid_epoch_duplicate_members_and_limits():
    with pytest.raises(SpreadsheetError,match='invalid_date_system'):parse_xlsx(fixture(date1904='maybe'),100000)
    with pytest.raises(SpreadsheetError,match='extraction_limit'):parse_xlsx(fixture(),10)
    data=io.BytesIO(fixture())
    with pytest.warns(UserWarning), zipfile.ZipFile(data,'a') as z:z.writestr('xl/workbook.xml','duplicate')
    with pytest.raises(SpreadsheetError,match='ambiguous_members'):parse_xlsx(data.getvalue(),100000)


def test_csv_literal_values_physical_lines_and_no_inference():
    raw=b'Code,Description,Amount\r\n00125,"two\nlines","(1,250.00)"\r\n=1+1,@literal,-2\r\n'
    result=parse_csv(raw,10000)
    assert result[1]['spreadsheet']['physical_lines']==[2,3]
    cells=result[1]['spreadsheet']['cells']
    assert [c['value'] for c in cells]==['00125','two\nlines','(1,250.00)']
    assert result[2]['spreadsheet']['cells'][0]['formula'] is None
    assert result[2]['spreadsheet']['cells'][0]['formula_like_literal']
    assert result[0]['locator']=="'CSV'!A1:C1"


@pytest.mark.parametrize('raw',[b'a,b\n1\n',b'"unterminated',b'a,\xff',b'a,\0',b''])
def test_csv_bad_shape_encoding_and_binary_reject(raw):
    with pytest.raises(SpreadsheetError):parse_csv(raw,10000)


def test_csv_blanks_and_bom():
    result=parse_csv(b'\xef\xbb\xbfa,b,\n,,\n',10000)
    assert [c['value'] for c in result[1]['spreadsheet']['cells']]==['','','']
    with pytest.raises(SpreadsheetError):parse_csv(b'a,b\n',5)


def test_upload_and_agent_limits_and_rejected_archive_not_stored(client):
    activate(client)
    result=client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file':('trial.xlsx',fixture(),MIME)},data={'authorization_basis':'own_original'})
    assert result.status_code==201,result.text
    doc_id=result.json()['id']
    with client.app.state.db.Session() as db:
        doc=db.get(Document,doc_id)
        assert doc.mime==MIME and doc.chunks[1]['spreadsheet']['cells'][0]['value']=='00125'
        run=SimpleNamespace(document_ids=[doc_id],workspace_id='demo-workspace',workflow='deep_research',inputs={},context={})
        limits=preprocess(db,run,{'min_documents':0,'guardrail':'Synthetic'})['document_extraction_limits'][0]
        assert limits['date_systems']==['1900'] and not limits['formula_caches_verified']
    bad=client.post('/api/v1/workspaces/demo-workspace/documents',files={'file':('bad.xlsx',fixture(sheet_extra='<drawing/>'),MIME)},data={'authorization_basis':'own_original'})
    assert bad.status_code==422 and bad.json()['error']['code']=='SPREADSHEET_PARSE_BLOCKED'
    with client.app.state.db.Session() as db:assert db.scalar(select(func.count()).select_from(Document))==1


def test_csv_upload_and_chunk_provenance(client):
    activate(client)
    result=client.post('/api/v1/workspaces/demo-workspace/documents',files={'file':('trial.csv',b'Code,Amount\n00125,-12.50\n','text/csv')},data={'authorization_basis':'own_original'})
    assert result.status_code==201,result.text
    chunks=parse_bytes(('A\n"'+'x'*4000+'"\n').encode(),'.csv',20000)
    assert chunks[-1]['spreadsheet']['character_range'][0]==3500
    assert preflight(fixture(),'trial.xlsx',SimpleNamespace(max_upload_mb=10))==MIME


def test_declarations_footer_units_and_unsupported_tables():
    book=f'<workbook xmlns="{S}" xmlns:r="{R}"><sheets><sheet name="Trial balance" sheetId="1" r:id="s1"/></sheets><definedNames><definedName name="Total">Sheet1!$B$2</definedName></definedNames><calcPr calcMode="manual"/></workbook>'
    result=parse_xlsx(fixture(extra={'xl/workbook.xml':book},sheet_extra='<headerFooter><oddFooter>Amounts in thousands</oddFooter></headerFooter>'),10000)
    assert result[0]['spreadsheet']['calculation_properties']['calcMode']=='manual'
    assert result[0]['spreadsheet']['defined_names'][0]['formula']=='Sheet1!$B$2'
    assert result[-1]['spreadsheet']['header_footer']['oddFooter']=='Amounts in thousands'
    with pytest.raises(SpreadsheetError,match='requires_review'):parse_xlsx(fixture(sheet_extra='<tableParts/>'),10000)


def test_workbook_type_and_inline_phonetic_text_do_not_silently_pass():
    with pytest.raises(SpreadsheetError,match='workbook_content_type'):
        parse_xlsx(fixture(extra={'[Content_Types].xml':f'<Types xmlns="{CT}"/>'}),10000)
    cells='<row r="1"><c r="A1" t="inlineStr"><is><t>Main text</t><rPh><t>Phonetic text</t></rPh></is></c></row>'
    with pytest.raises(SpreadsheetError,match='phonetic_text'):parse_xlsx(fixture(cells),10000)


def test_default_style_is_preserved_when_cell_style_index_is_omitted():
    cells='<row r="1"><c r="A1"><v>12.5</v></c></row>'
    assert parse_xlsx(fixture(cells),10000)[0]['spreadsheet']['cells'][0]['number_format_code']=='#,##0.00'


def test_nested_scalar_and_duplicate_footer_are_not_silently_dropped():
    with pytest.raises(SpreadsheetError,match='non_scalar_cell_value'):
        parse_xlsx(fixture('<row r="1"><c r="A1"><v><x>125</x></v></c></row>'),10000)
    with pytest.raises(SpreadsheetError,match='ambiguous_header_footer'):
        parse_xlsx(fixture(sheet_extra='<headerFooter><oddFooter>A</oddFooter><oddFooter>B</oddFooter></headerFooter>'),10000)
