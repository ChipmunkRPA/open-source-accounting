"""Literal CSV and XLSX cell extraction. No calculation, rendering, macros or network."""
import csv
import io
import json
import re
import posixpath
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import PurePosixPath
from .sec_core.core import digest

VERSION = 'spreadsheet-cells-1'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P = 'http://schemas.openxmlformats.org/package/2006/relationships'
MAX_CELLS = 50000


class SpreadsheetError(ValueError):
    def __init__(self, code, part='', locator=''):
        self.code, self.part, self.locator = code, part[:200], locator[:200]
        super().__init__(code)


def reject(code, part='', locator=''):
    raise SpreadsheetError(code, part, locator)


def column(n):
    result=''
    while n:
        n,r=divmod(n-1,26);result=chr(65+r)+result
    return result


def coordinate(ref):
    m=re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,6})',ref)
    if not m:reject('invalid_cell_reference',locator=ref)
    col=0
    for c in m[1]:col=col*26+ord(c)-64
    row=int(m[2])
    if col>16384 or row>1048576:reject('cell_reference_out_of_range',locator=ref)
    return row,col


def chunk(sheet, cells, **meta):
    text='\n'.join(c['ref']+' '+json.dumps({k:v for k,v in c.items() if k in {'value','value_type','formula','cache_status','formula_like_literal','number_format_id','number_format_code'}},ensure_ascii=False,sort_keys=True) for c in cells)
    return {'locator':"'"+sheet.replace("'","''")+"'!"+cells[0]['ref']+(':'+cells[-1]['ref'] if len(cells)>1 else ''),
            'text':text,'spreadsheet':{'parser_version':VERSION,'sheet':sheet,'cells':cells,
                'content_sha256':digest(text),'calculated':False,'display_rendered':False,
                'units_verified':False,'professional_review':'unreviewed',**meta}}


def parse_csv(raw, limit):
    try:text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:reject('csv_requires_utf8')
    if '\0' in text:reject('binary_csv')
    # Deliberate comma contract, no locale/delimiter or numeric/date guessing.
    csv.field_size_limit(min(limit,100000))
    reader=csv.reader(io.StringIO(text,newline=''),strict=True)
    output=[];total=count=0;previous_line=0;width=None
    try:
        for n,row in enumerate(reader,1):
            if n>100000 or len(row)>16384:reject('csv_shape_limit')
            if not row:row=['']  # Preserve an actual empty physical record.
            if width is None:width=len(row)
            if len(row)!=width:reject('csv_uneven_rows',locator=f'row {n}')
            cells=[{'ref':f'{column(i+1)}{n}','value':value,'value_type':'text',
                    'formula':None,'formula_like_literal':bool(value.lstrip().startswith(('=','+','-','@')))} for i,value in enumerate(row)]
            count+=len(cells)
            item=chunk('CSV',cells,format='csv',record=n,physical_lines=[previous_line+1,reader.line_num],
                       delimiter=',',header_inferred=False,date_system=None)
            previous_line=reader.line_num;total+=len(item['text'])
            if count>MAX_CELLS or total>limit:reject('spreadsheet_extraction_limit')
            output.append(item)
    except csv.Error:reject('invalid_csv')
    if not output:reject('empty_spreadsheet')
    return output


def parse_xlsx(raw, limit):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members=archive.infolist();names=[x.filename for x in members]
            if (len(names)>2000 or len(set(names))!=len(names) or sum(x.file_size for x in members)>40*1024*1024
                    or any(x.flag_bits&1 or x.file_size>1000*max(1,x.compress_size) for x in members)):
                reject('archive_limit_or_ambiguous_members')
            if any(n.startswith('/') or '\\' in n or '..' in PurePosixPath(n).parts for n in names):reject('unsafe_archive_path')
            if any(any(x in n.lower() for x in ('vbaproject','embeddings/','externallinks/','connections.xml','querytables/','macrosheets/','.bin')) for n in names):
                reject('active_or_external_content')
            roots={};nodes=0
            for name in names:
                if not name.endswith(('.xml','.rels')):continue
                try:xml=archive.read(name).decode('utf-8-sig')
                except UnicodeDecodeError:reject('unsupported_xml_encoding',name)
                if '\0' in xml or '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():reject('unsafe_xml',name)
                try:root=ET.fromstring(xml)
                except ET.ParseError:reject('invalid_xml',name)
                todo=[(root,0)]
                while todo:
                    node,depth=todo.pop();nodes+=1
                    if depth>60 or nodes>250000:reject('xml_structure_limit',name)
                    todo.extend((c,depth+1) for c in node)
                roots[name]=root
            def rels(part):
                filename=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels') if part else '_rels/.rels'
                root=roots.get(filename)
                if root is None:return {}
                if root.tag!='{'+P+'}Relationships':reject('invalid_relationships',filename)
                result={}
                for rel in root:
                    rid,target,kind=rel.get('Id'),rel.get('Target',''),rel.get('Type','')
                    if rel.tag!='{'+P+'}Relationship' or not rid or rid in result:reject('ambiguous_relationship',filename)
                    if any(x in kind.lower() for x in ('vbaproject','oleobject','externallink','connection','attachedtemplate')):reject('active_or_external_content',filename)
                    if rel.get('TargetMode')=='External':reject('external_relationship',filename)
                    if not target or any(c in target for c in ('%',':','?','#','\\')):reject('unsafe_relationship',filename)
                    resolved=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(posixpath.dirname(part),target))
                    if resolved.startswith('../') or resolved not in names:reject('missing_relationship_part',filename)
                    result[rid]=(kind,resolved)
                return result
            # Validate every relationship, even those on hidden/unselected sheets.
            for name in names:
                if name.endswith('.rels'):
                    part='' if name=='_rels/.rels' else posixpath.join(posixpath.dirname(posixpath.dirname(name)),posixpath.basename(name)[:-5])
                    rels(part)
            mains=[v for v in rels('').values() if v[0]==R+'/officeDocument']
            if len(mains)!=1 or mains[0][1]!='xl/workbook.xml':reject('missing_or_ambiguous_workbook')
            book=roots.get('xl/workbook.xml')
            if book is None or book.tag!='{'+S+'}workbook':reject('unsupported_workbook')
            content_types=roots.get('[Content_Types].xml')
            ct='http://schemas.openxmlformats.org/package/2006/content-types'
            if content_types is None or content_types.tag!='{'+ct+'}Types' or any('macroenabled' in v.lower() for n in content_types for v in n.attrib.values()):reject('active_or_invalid_content_types')
            declared=[n.get('ContentType') for n in content_types if n.get('PartName')=='/xl/workbook.xml']
            if declared!=['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml']:reject('unsupported_workbook_content_type')
            links=rels('xl/workbook.xml')
            props=book.find('{'+S+'}workbookPr')
            if props is not None and props.get('date1904','0') not in {'0','1','true','false'}:reject('invalid_date_system')
            epoch='1904' if props is not None and props.get('date1904') in {'1','true'} else '1900'
            strings=[]
            shared=[path for kind,path in links.values() if kind==R+'/sharedStrings']
            if len(shared)>1:reject('ambiguous_shared_strings')
            if shared:
                for si in roots[shared[0]]:
                    if si.tag!='{'+S+'}si':reject('unsupported_shared_string',shared[0])
                    if any(n.tag=='{'+S+'}rPh' for n in si.iter()):reject('phonetic_text_requires_review',shared[0])
                    strings.append(''.join(t.text or '' for t in si.iter('{'+S+'}t')))
            styles=[path for kind,path in links.values() if kind==R+'/styles']
            if len(styles)>1:reject('ambiguous_styles')
            formats={};xfs=[]
            if styles:
                sr=roots[styles[0]]
                for nf in sr.findall('./{'+S+'}numFmts/{'+S+'}numFmt'):
                    key=nf.get('numFmtId')
                    if not key or key in formats:reject('ambiguous_number_format')
                    formats[key]=nf.get('formatCode')
                xfs=[dict(x.attrib) for x in sr.findall('./{'+S+'}cellXfs/{'+S+'}xf')]
            sheets=book.find('{'+S+'}sheets')
            if sheets is None or not 1<=len(sheets)<=100:reject('sheet_count_limit')
            seen_names=set();seen_parts=set();output=[];count=total=0
            declared_names=[{'attributes':dict(n.attrib),'formula':n.text or ''}
                            for n in book.findall('./{'+S+'}definedNames/{'+S+'}definedName')]
            calculation=book.find('{'+S+'}calcPr')
            if declared_names or calculation is not None:
                declarations={'defined_names':declared_names,'calculation_properties':dict(calculation.attrib) if calculation is not None else {},'date_system':epoch}
                description=json.dumps(declarations,ensure_ascii=False,sort_keys=True)
                total+=len(description)
                output.append({'locator':'Workbook declarations','text':description,
                    'spreadsheet':{'parser_version':VERSION,'format':'xlsx','source_part':'xl/workbook.xml',
                        'date_system':epoch,'cells':[],'calculated':False,'display_rendered':False,
                        'units_verified':False,'professional_review':'unreviewed',**declarations}})

            for sh in sheets:
                name=sh.get('name','');rid=sh.get('{'+R+'}id');link=links.get(rid)
                if not name or name.casefold() in seen_names or not link or link[0]!=R+'/worksheet':reject('unsupported_or_ambiguous_sheet')
                if sh.get('state','visible') not in {'visible','hidden','veryHidden'}:reject('invalid_sheet_visibility')
                seen_names.add(name.casefold());part=link[1]
                if part in seen_parts:reject('duplicate_worksheet_binding',part)
                seen_parts.add(part);sheet=roots.get(part)
                if sheet is None or sheet.tag!='{'+S+'}worksheet':reject('invalid_worksheet',part)
                unsupported={'drawing','legacyDrawing','legacyDrawingHF','oleObjects','controls','extLst','pivotTable','picture','tableParts','pivotTableParts'}
                if any(n.tag.rsplit('}',1)[-1] in unsupported for n in sheet.iter()):reject('visual_or_extended_content_requires_review',part)
                if any('/comments' in kind or '/threadedComment' in kind for kind,_ in rels(part).values()):reject('comments_require_review',part)
                merges=[m.get('ref','') for m in sheet.findall('./{'+S+'}mergeCells/{'+S+'}mergeCell')]
                for merge in merges:
                    refs=merge.split(':')
                    if len(refs)!=2:reject('invalid_merge_range',part)
                    a,b=map(coordinate,refs)
                    if a[0]>b[0] or a[1]>b[1]:reject('invalid_merge_range',part)
                sd=sheet.find('{'+S+'}sheetData')
                if sd is None:reject('missing_sheet_data',part)
                seen_cells=set();last_row=0;sheet_items=0
                for row in sd:
                    try:rn=int(row.get('r',''))
                    except ValueError:reject('invalid_row_number',part)
                    if row.tag!='{'+S+'}row' or not last_row<rn<=1048576:reject('ambiguous_row_order',part)
                    last_row=rn;cells=[];last_col=0
                    for c in row:
                        ref=c.get('r','');rr,cc=coordinate(ref)
                        if c.tag!='{'+S+'}c' or rr!=rn or cc<=last_col or ref in seen_cells:reject('ambiguous_cell_order',part,ref)
                        last_col=cc;seen_cells.add(ref);count+=1
                        if count>MAX_CELLS:reject('cell_count_limit',part)
                        if set(n.tag for n in c)-{'{'+S+'}v','{'+S+'}f','{'+S+'}is'}:reject('unsupported_cell_content',part,ref)
                        if any(len(c.findall('{'+S+'}'+n))>1 for n in ('v','f','is')):reject('ambiguous_cell_content',part,ref)
                        v=c.find('{'+S+'}v');f=c.find('{'+S+'}f');inline=c.find('{'+S+'}is')
                        if (v is not None and len(v)) or (f is not None and len(f)):reject('non_scalar_cell_value',part,ref)
                        rawvalue=v.text if v is not None else None;typ=c.get('t','n');value=rawvalue
                        if typ=='s':
                            try:value=strings[int(rawvalue)] if rawvalue is not None and rawvalue.isdigit() else None
                            except (ValueError,IndexError):reject('invalid_shared_string_index',part,ref)
                            if value is None:reject('invalid_shared_string_index',part,ref)
                        elif typ=='inlineStr':
                            if inline is None or v is not None or f is not None:reject('invalid_inline_string',part,ref)
                            if any(n.tag=='{'+S+'}rPh' for n in inline.iter()):reject('phonetic_text_requires_review',part,ref)
                            value=''.join(t.text or '' for t in inline.iter('{'+S+'}t'))
                        elif typ=='n' and rawvalue is not None:
                            try:
                                if not Decimal(rawvalue).is_finite():reject('nonfinite_numeric_value',part,ref)
                            except InvalidOperation:reject('invalid_numeric_value',part,ref)
                        elif typ=='b' and rawvalue not in {None,'0','1'}:reject('invalid_boolean_value',part,ref)
                        elif typ=='d' and rawvalue is not None:
                            try:
                                if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(T.+)?',rawvalue):raise ValueError()
                                datetime.fromisoformat(rawvalue.replace('Z','+00:00'))
                            except ValueError:reject('invalid_iso_date',part,ref)
                        elif typ not in {'n','b','str','e','d'}:reject('unsupported_cell_type',part,ref)
                        if typ!='inlineStr' and inline is not None:reject('ambiguous_cell_content',part,ref)
                        style=c.get('s');style_meta=xfs[0] if xfs else {}
                        if style is not None:
                            if not style.isdigit() or int(style)>=len(xfs):reject('invalid_cell_style',part,ref)
                            style_meta=xfs[int(style)]
                        if typ=='str' and v is not None and rawvalue is None:value=''
                        format_id=style_meta.get('numFmtId','0')
                        formula=None if f is None else {'text':f.text,'attributes':dict(f.attrib)}
                        cells.append({'ref':ref,'value':value,'raw_value':rawvalue,'value_type':typ,
                            'formula':formula,'cache_status':'not_formula' if f is None else 'missing' if v is None or (rawvalue is None and typ!='str') else 'unverified_cached',
                            'style_index':style,'style':style_meta,'number_format_id':format_id,
                            'number_format_code':formats.get(format_id)})
                    if not cells:continue
                    item=chunk(name,cells,format='xlsx',source_part=part,row=rn,sheet_state=sh.get('state','visible'),
                        row_hidden=row.get('hidden','0'),date_system=epoch,merged_ranges=merges,
                        column_properties=[dict(n.attrib) for n in sheet.findall('./{'+S+'}cols/{'+S+'}col')],
                        warning='Literal stored cells and formula caches only. Caches may be absent or stale. No formula translation/recalculation, number/date rendering, inferred units or visual review.')
                    total+=len(item['text']);sheet_items+=1
                    if total>limit:reject('spreadsheet_extraction_limit',part)
                    output.append(item)
                header_footer=sheet.find('{'+S+'}headerFooter')
                if header_footer is not None:
                    tags=[n.tag for n in header_footer]
                    if len(tags)!=len(set(tags)) or any(t not in {'{'+S+'}'+n for n in ('oddHeader','oddFooter','evenHeader','evenFooter','firstHeader','firstFooter')} for t in tags):reject('ambiguous_header_footer',part)
                    contents={n.tag.rsplit('}',1)[-1]:n.text or '' for n in header_footer}
                    description=json.dumps(contents,ensure_ascii=False,sort_keys=True)
                    total+=len(description)
                    output.append({'locator':"'"+name.replace("'","''")+"' header/footer",'text':description,
                        'spreadsheet':{'parser_version':VERSION,'format':'xlsx','source_part':part,
                            'sheet':name,'date_system':epoch,'cells':[],'header_footer':contents,
                            'calculated':False,'display_rendered':False,'units_verified':False,
                            'professional_review':'unreviewed'}})
                if total>limit:reject('spreadsheet_extraction_limit',part)
                if not sheet_items:
                    output.append({'locator':"'"+name.replace("'","''")+"' (empty worksheet)",
                        'text':'Worksheet contains no stored cells.',
                        'spreadsheet':{'parser_version':VERSION,'format':'xlsx','sheet':name,'source_part':part,
                            'sheet_state':sh.get('state','visible'),'date_system':epoch,'empty_sheet':True,
                            'cells':[],'calculated':False,'display_rendered':False,'units_verified':False,
                            'professional_review':'unreviewed'}})
            if any(n.startswith('xl/worksheets/') and n.endswith('.xml') and n not in seen_parts for n in names):
                reject('unbound_worksheet_part')
            return output
    except zipfile.BadZipFile:reject('invalid_xlsx_archive')
