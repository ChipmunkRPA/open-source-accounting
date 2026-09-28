"""Original legacy-note fixtures, not evidence of real authorship or approval."""
import pytest
from app.spreadsheet_parser import parse_xlsx, SpreadsheetError, S, R, P
from test_spreadsheet_parser import fixture, MIME
from test_spreadsheet_intake import SheetGateway
from test_source_intake import registered, payload, fetch, parse, ADMIN

COMMENT=f'''<comments xmlns="{S}"><authors><author>Fixture reviewer</author></authors><commentList>
<comment ref="C4" authorId="0"><text><r><rPr><b/></rPr><t>Check units: </t></r><r><t>USD, not thousands.\nUnreviewed note.</t></r></text></comment>
</commentList></comments>'''
VML='''<xml xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
<o:shapelayout v:ext="edit"><o:idmap v:ext="edit" data="1"/></o:shapelayout>
<v:shapetype id="_x0000_t202" coordsize="21600,21600" o:spt="202" path="m,l,21600r21600,l21600,xe"><v:stroke joinstyle="miter"/><v:path gradientshapeok="t" o:connecttype="rect"/></v:shapetype>
<v:shape id="_x0000_s1025" type="#_x0000_t202" style="position:absolute;visibility:hidden"><v:fill color2="#ffffe1"/><v:shadow on="t" obscured="t"/><v:path o:connecttype="none"/><v:textbox style="mso-direction-alt:auto"><div style="text-align:left"/></v:textbox><x:ClientData ObjectType="Note"><x:MoveWithCells/><x:SizeWithCells/><x:Anchor>3, 15, 3, 2, 5, 31, 7, 1</x:Anchor><x:AutoFill>False</x:AutoFill><x:Row>3</x:Row><x:Column>2</x:Column></x:ClientData></v:shape></xml>'''


def workbook(comment=COMMENT,vml=VML):
    relationships=f'<Relationship Id="c1" Type="{R}/comments" Target="../comments/comment1.xml"/>'
    extra={'xl/comments/comment1.xml':comment}
    binding=''
    if vml is not None:
        relationships+=f'<Relationship Id="v1" Type="{R}/vmlDrawing" Target="../drawings/vml1.vml"/>'
        extra['xl/drawings/vml1.vml']=vml
        binding=f'<legacyDrawing xmlns:r="{R}" r:id="v1"/>'
    extra['xl/worksheets/_rels/sheet1.xml.rels']=f'<Relationships xmlns="{P}">{relationships}</Relationships>'
    return fixture(extra=extra,sheet_extra=binding)


@pytest.mark.parametrize('vml',[VML,None],ids=['with-note-drawing','without-drawing'])
def test_comment_text_author_and_missing_cell_preserved(vml):
    rows=parse_xlsx(workbook(vml=vml),100000)
    note=rows[0]['spreadsheet']['comment']
    assert note['text']=='Check units: USD, not thousands.\nUnreviewed note.'
    assert note['author']=='Fixture reviewer' and not note['author_verified']
    assert note['source_xml_path']=='/comments/commentList/comment[1]'
    assert rows[0]['locator']=="'Trial balance'!C4 comment"
    assert all(c['ref']!='C4' for row in rows for c in row['spreadsheet']['cells'])
    assert parse_xlsx(workbook(vml=vml),100000)==rows
    if vml:
        drawing=rows[1]['spreadsheet']['note_drawing']
        assert drawing['note_cells']==['C4'] and not drawing['visual_layout_verified']
        assert 'visibility:hidden' in str(drawing)


@pytest.mark.parametrize('old,new,reason',[
 ('authorId="0"','authorId="1"','invalid_comment'),
 ('ref="C4"','ref="C0"','invalid_cell_reference'),
 ('</commentList>','<comment ref="C4" authorId="0"><text><t>Duplicate</t></text></comment></commentList>','invalid_comment'),
 ('<b/>','<rPh/>','unsupported_comment_rich_text'),
 ('</comments>','<extLst/></comments>','unsupported_comment_structure'),
])
def test_invalid_comments_reject_whole_workbook(old,new,reason):
    with pytest.raises(SpreadsheetError,match=reason):parse_xlsx(workbook(COMMENT.replace(old,new)),100000)


@pytest.mark.parametrize('old,new,reason',[
 ('ObjectType="Note"','ObjectType="Button"','non_note_drawing'),
 ('<x:Row>3','<x:Row>4','note_anchor_comment_mismatch'),
 ('<x:Row>3','<x:Row>-1','invalid_note_anchor'),
 ('<x:Row>3','<x:Row>1048576','invalid_note_anchor'),
 ('<v:fill','<script/><v:fill','non_note_drawing'),
 ('<v:fill','<v:fill href="https://example.test/"','active_note_drawing'),
 ('<x:Row>3</x:Row>','<x:Row>3</x:Row><x:Row>3</x:Row>','ambiguous_note_anchor'),
])
def test_non_note_or_unsafe_drawing_rejected(old,new,reason):
    with pytest.raises(SpreadsheetError,match=reason):parse_xlsx(workbook(vml=VML.replace(old,new)),100000)


def test_orphan_comments_and_drawing_are_not_dropped():
    for extra in ({'xl/comments/comment1.xml':COMMENT},{'xl/drawings/vml1.vml':VML}):
        with pytest.raises(SpreadsheetError,match='unbound_or_unsupported_comment_part'):
            parse_xlsx(fixture(extra=extra),100000)


def test_comment_budget_and_xml_safety():
    with pytest.raises(SpreadsheetError,match='spreadsheet_extraction_limit'):parse_xlsx(workbook(),100)
    with pytest.raises(SpreadsheetError,match='unsafe_xml'):parse_xlsx(workbook(vml='<!DOCTYPE xml>'+VML),100000)


def test_comment_intake_review_packet_is_unapproved(client):
    body=payload(parser='xlsx',allowed_mime=[MIME]);body['source']['policy']['export']=True
    work=registered(client,body=body)
    extraction=parse(client,fetch(client,work,SheetGateway(workbook(),MIME)))
    staged=client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage',headers=ADMIN)
    assert staged.status_code==200 and not staged.json()['agent_eligible']
    response=client.get('/api/v1/editorial/extractions/'+extraction['id']+'/packet',headers={'X-Dev-User':'editor'})
    assert response.status_code==200
    packet=response.json()['packet']
    assert packet['passages'][0]['spreadsheet']['comment']['cell']=='C4'
    assert not packet['approval_granted']


def test_threaded_comment_content_is_explicitly_unsupported():
    rel=f'<Relationships xmlns="{P}"><Relationship Id="t1" Type="http://schemas.microsoft.com/office/2017/10/relationships/threadedComment" Target="../threadedComments/thread1.xml"/></Relationships>'
    extra={'xl/worksheets/_rels/sheet1.xml.rels':rel,'xl/threadedComments/thread1.xml':'<ThreadedComments xmlns="http://schemas.microsoft.com/office/spreadsheetml/2018/threadedcomments"/>'}
    with pytest.raises(SpreadsheetError,match='threaded_comments_require_review'):
        parse_xlsx(fixture(extra=extra),100000)


def test_comment_rich_text_is_data_not_formula_execution():
    comment=COMMENT.replace('Check units: ', '=HYPERLINK(&quot;https://example.test&quot;) ')
    note=parse_xlsx(workbook(comment),100000)[0]['spreadsheet']['comment']
    assert note['text'].startswith('=HYPERLINK(')
    assert not note['author_verified']
