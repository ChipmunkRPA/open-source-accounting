"""Original table fixtures; declarations are not verified calculations."""
import pytest
from app.spreadsheet_parser import parse_xlsx, SpreadsheetError, S, R, P
from test_spreadsheet_parser import fixture, MIME
from test_spreadsheet_intake import SheetGateway
from test_source_intake import registered, payload, fetch, parse, ADMIN

TABLE=f'''<table xmlns="{S}" id="1" name="Amounts" displayName="Amounts" ref="A1:B3" totalsRowCount="1">
<autoFilter ref="A1:B2"><filterColumn colId="1"><filters><filter val="-1250.00"/></filters></filterColumn></autoFilter>
<tableColumns count="2"><tableColumn id="1" name="Account" totalsRowLabel="Total"/>
<tableColumn id="2" name="Amount" totalsRowFunction="custom"><calculatedColumnFormula>[@Amount]*2</calculatedColumnFormula><totalsRowFormula>SUM(Amounts[Amount])</totalsRowFormula></tableColumn></tableColumns>
<tableStyleInfo name="TableStyleMedium2" showRowStripes="1"/></table>'''


def workbook(table=TABLE, binding=None, extra=None):
    entries={'xl/tables/table1.xml':table,
             'xl/worksheets/_rels/sheet1.xml.rels':f'<Relationships xmlns="{P}"><Relationship Id="t1" Type="{R}/table" Target="../tables/table1.xml"/></Relationships>'}
    entries.update(extra or {})
    return fixture(extra=entries, sheet_extra=binding if binding is not None else f'<tableParts count="1" xmlns:r="{R}"><tablePart r:id="t1"/></tableParts>')


def test_table_preserves_declarations_and_stored_values():
    rows=parse_xlsx(workbook(),100000)
    table=rows[0]['spreadsheet']['table']
    assert rows[0]['locator']=="'Trial balance'!A1:B3 table Amounts"
    assert table['columns'][1]['children'][0]['text']=='[@Amount]*2'
    assert table['columns'][1]['children'][1]['text']=='SUM(Amounts[Amount])'
    assert not table['filters_applied'] and not table['formulas_calculated']
    assert not table['header_values_verified']
    assert rows[2]['spreadsheet']['cells'][1]['value']=='-1250.00'
    assert rows[2]['spreadsheet']['tables'][0]['range']=='A1:B3'
    assert parse_xlsx(workbook(),100000)==rows


@pytest.mark.parametrize('old,new,reason',[
 ('ref="A1:B3"','ref="B3:A1"','invalid_table_range'),
 ('count="2"','count="3"','table_column_count_mismatch'),
 ('id="2" name="Amount"','id="1" name="Amount"','ambiguous_table_column'),
 ('name="Amount"','name="ACCOUNT"','ambiguous_table_column'),
 ('colId="1"','colId="2"','invalid_table_filter_column'),
 ('ref="A1:B2"','ref="A1:C2"','table_filter_range_mismatch'),
 ('<tableStyleInfo','<extLst/><tableStyleInfo','requires_review'),
 ('totalsRowCount="1"','totalsRowCount="3"','unsupported_table_row_counts'),
 ('totalsRowCount="1"','totalsRowCount="1" tableType="queryTable"','external_table'),
])
def test_invalid_tables_fail_whole_extraction(old,new,reason):
    with pytest.raises(SpreadsheetError,match=reason):
        parse_xlsx(workbook(TABLE.replace(old,new)),100000)


def test_orphan_and_duplicate_binding_rejected():
    with pytest.raises(SpreadsheetError,match='unbound_table_relationship'):
        parse_xlsx(workbook(binding=''),100000)
    with pytest.raises(SpreadsheetError,match='ambiguous_table_binding'):
        parse_xlsx(workbook(binding=f'<tableParts count="2" xmlns:r="{R}"><tablePart r:id="t1"/><tablePart r:id="t1"/></tableParts>'),100000)
    with pytest.raises(SpreadsheetError,match='unbound_table_part'):
        parse_xlsx(fixture(extra={'xl/tables/table1.xml':TABLE}),100000)


def test_table_declarations_obey_extraction_budget():
    with pytest.raises(SpreadsheetError,match='spreadsheet_extraction_limit'):
        parse_xlsx(workbook(),100)


def test_table_context_survives_intake_and_review_packet(client):
    body=payload(parser='xlsx',allowed_mime=[MIME]);body['source']['policy']['export']=True
    work=registered(client,body=body)
    extraction=parse(client,fetch(client,work,SheetGateway(workbook(),MIME)))
    staged=client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage',headers=ADMIN)
    assert staged.status_code==200 and not staged.json()['agent_eligible']
    response=client.get('/api/v1/editorial/extractions/'+extraction['id']+'/packet',headers={'X-Dev-User':'editor'})
    assert response.status_code==200
    packet=response.json()['packet']
    assert packet['passages'][0]['spreadsheet']['table']['columns'][1]['attributes']['name']=='Amount'
    assert not packet['approval_granted']


@pytest.mark.parametrize('second,reason', [
    (TABLE.replace('id="1" name="Amounts" displayName="Amounts"', 'id="2" name="Other" displayName="Other"'), 'overlapping_table_ranges'),
    (TABLE.replace('ref="A1:B3"', 'ref="D1:E3"').replace('ref="A1:B2"', 'ref="D1:E2"'), 'duplicate_table_identity')])
def test_multiple_tables_reject_overlap_or_duplicate_identity(second,reason):
    rel=f'<Relationships xmlns="{P}"><Relationship Id="t1" Type="{R}/table" Target="../tables/table1.xml"/><Relationship Id="t2" Type="{R}/table" Target="../tables/table2.xml"/></Relationships>'
    binding=f'<tableParts count="2" xmlns:r="{R}"><tablePart r:id="t1"/><tablePart r:id="t2"/></tableParts>'
    with pytest.raises(SpreadsheetError,match=reason):
        parse_xlsx(workbook(binding=binding,extra={'xl/tables/table2.xml':second,'xl/worksheets/_rels/sheet1.xml.rels':rel}),100000)


def test_no_header_and_no_totals_declaration_preserved():
    table=TABLE.replace('totalsRowCount="1"','totalsRowCount="0" headerRowCount="0"')
    metadata=parse_xlsx(workbook(table),100000)[0]['spreadsheet']['table']
    assert metadata['declaration']['attributes']['headerRowCount']=='0'
    assert metadata['declaration']['attributes']['totalsRowCount']=='0'
