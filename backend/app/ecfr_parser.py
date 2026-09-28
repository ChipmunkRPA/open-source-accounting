"""Versioned eCFR normalization; originals and all review gates remain separate."""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from .sec_core.parsers import MAX_BYTES, clean, passage

VERSION = 'source-intake-ecfr-2'


class EcfrError(ValueError):
    def __init__(self, code, path='/'):
        self.code, self.path = code, path[:1000]
        super().__init__(code)


INLINE = {'E', 'I', 'B', 'EM', 'STRONG', 'SU', 'SUP', 'SUB', 'FTREF', 'PRTPAGE'}
BLOCKS = {'P', 'FP', 'HEAD', 'HD', 'SUBJECT', 'SECTNO', 'FTNT', 'AUTH', 'SOURCE', 'CITA', 'EDNOTE', 'EFFDNOTP'}
CONTAINERS = {'ECFR', 'DLPSTEXTCLASS', 'TEXT', 'BODY', 'TITLE', 'CHAPTER', 'SUBCHAP', 'PART', 'SUBPART', 'SECTION', 'APPENDIX'} | {'DIV'+str(i) for i in range(1, 10)}


def parse(raw, title='17'):
    def reject(code, node=None):
        raise EcfrError(code, paths.get(node, '/'))

    paths = {}
    if len(raw) > MAX_BYTES: reject('size_limit')
    try: text = raw.decode('utf-8-sig')
    except UnicodeDecodeError: reject('unsupported_encoding')
    if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): reject('unsafe_xml')
    declaration = re.match(r'\s*<\?xml\s+[^?]*encoding=[\"\']([^\"\']+)', text)
    if declaration and declaration[1].lower() not in {'utf-8', 'us-ascii'}: reject('unsupported_encoding')
    try: root = ET.fromstring(text)
    except (ET.ParseError, ValueError): reject('invalid_xml')
    if root.tag not in CONTAINERS: reject('wrong_document_type')
    nodes = []

    def inventory(n, path, depth):
        paths[n] = path
        if depth > 80 or len(nodes) >= 100000: reject('structure_limit', n)
        if not re.fullmatch('[A-Z][A-Z0-9]*', n.tag): reject('unsupported_tag', n)
        if n.tag == 'PRTPAGE' and (set(n.attrib) != {'P'} or not n.get('P') or len(n) or (n.text and n.text.strip())):
            reject('unsupported_page_marker', n)
        nodes.append(n)
        counts = Counter()
        for child in n:
            counts[child.tag] += 1
            inventory(child, path+'/'+child.tag+'['+str(counts[child.tag])+']', depth+1)
    inventory(root, '/'+root.tag+'[1]', 0)
    numbers, seen = {}, set()
    for n in nodes:
        if n.tag == 'SECTION' or n.get('TYPE') == 'SECTION':
            number = clean(n.get('N') or n.findtext('SECTNO', '')).removeprefix('§').strip()
            if not re.fullmatch(r'\d+\.[\dA-Za-z-]+', number) or number in seen: reject('invalid_or_duplicate_section', n)
            numbers[n] = number
            seen.add(number)
    if not seen: reject('no_sections')

    def inline(n):
        text = n.text or ''
        for c in n:
            if c.tag not in INLINE and not (n.tag in {'FTNT', 'TNOTE', 'TD', 'TH'} and c.tag == 'P'):
                reject('unsupported_inline_structure', c)
            value = inline(c)
            if c.tag in {'SU', 'SUP'}: value = '[superscript: '+value+']'
            elif c.tag == 'SUB': value = '[subscript: '+value+']'
            elif c.tag == 'FTREF': value = '[footnote reference: '+value+']'
            text += value+(c.tail or '')
        return clean(text)

    def structural(n):
        if (n.text and n.text.strip()) or any(c.tail and c.tail.strip() for c in n): reject('unsupported_mixed_table', n)

    def table(n):
        structural(n)
        gpo = n.tag == 'GPOTABLE'
        if set(n.attrib) - ({'COLS', 'CDEF', 'OPTS', 'ID'} if gpo else {'ID'}): reject('unsupported_table_layout', n)
        columns = None
        if gpo:
            try: columns = int(n.attrib['COLS'])
            except (KeyError, ValueError): reject('invalid_table_columns', n)
            if not 1 <= columns <= 100: reject('invalid_table_columns', n)
        rows, captions, notes = [], [], []

        def row(c, group=None):
            nonlocal columns
            structural(c)
            if c.attrib: reject('unsupported_table_layout', c)
            cells, metadata = [], []
            header = c.tag == 'BOXHD' or group == 'THEAD'
            for cell in c:
                if cell.tag == 'PRTPAGE': continue
                allowed = {'CHED'} if c.tag == 'BOXHD' else {'ENT'} if gpo else {'TH', 'TD'}
                if cell.tag not in allowed: reject('unsupported_table_layout', cell)
                attrs = cell.attrib
                if gpo:
                    if (cell.tag == 'CHED' and (set(attrs)-{'H'} or cell.get('H', '1') != '1')
                            or cell.tag == 'ENT' and set(attrs)-{'I'}): reject('unsupported_table_span_or_alignment', cell)
                elif set(attrs)-{'ROWSPAN', 'COLSPAN', 'SCOPE', 'ID'} or any(attrs.get(k, '1') != '1' for k in ('ROWSPAN', 'COLSPAN')):
                    reject('unsupported_table_span_or_alignment', cell)
                cells.append(inline(cell))
                metadata.append({'tag': cell.tag, 'attributes': dict(attrs), 'source_xml_path': paths[cell]})
            if columns is None: columns = len(cells)
            if not columns or columns > 100 or len(cells) != columns: reject('inconsistent_table_columns', c)
            if not gpo and metadata and all(m['tag'] == 'TH' for m in metadata): header = True
            if header and rows: reject('unsupported_multirow_or_late_header', c)
            rows.append({'kind': 'header' if header else 'data', 'cells': cells,
                         'source_xml_path': paths[c], 'cell_metadata': metadata})

        for c in n:
            if c.tag in ({'BOXHD', 'ROW'} if gpo else {'TR'}): row(c)
            elif not gpo and c.tag in {'THEAD', 'TBODY', 'TFOOT'}:
                structural(c)
                if c.attrib: reject('unsupported_table_layout', c)
                for child in c:
                    if child.tag != 'TR': reject('unsupported_table_structure', child)
                    row(child, c.tag)
            elif c.tag in ({'TTITLE', 'TDESC', 'TNOTE'} if gpo else {'CAPTION'}):
                item = {'text': inline(c), 'source_xml_path': paths[c]}
                (notes if c.tag == 'TNOTE' else captions).append(item)
            elif c.tag != 'PRTPAGE': reject('unsupported_table_structure', c)
        if not any(r['kind'] == 'data' for r in rows): reject('empty_table', n)
        rendered = ['Caption: '+x['text'] for x in captions]
        rendered += [('Header: ' if r['kind'] == 'header' else '')+' | '.join(x.replace('|', '\\|') for x in r['cells']) for r in rows]
        rendered += ['Note: '+x['text'] for x in notes]
        return '\n'.join(rendered), {'columns': columns, 'attributes': dict(n.attrib), 'rows': rows, 'captions': captions, 'notes': notes}

    output, counters, page = [], Counter(), None

    def visit(n, number=None):
        nonlocal page
        if n in numbers and number: reject('nested_section', n)
        number = numbers.get(n, number)
        extra = {}
        if n.tag == 'PRTPAGE':
            page = n.get('P')
            return
        if n.tag in {'TABLE', 'GPOTABLE'}:
            value, extra['table'] = table(n)
            kind = 'ecfr_table_unreviewed'
        elif n.tag in BLOCKS:
            value, kind = inline(n), 'footnote' if n.tag == 'FTNT' else 'paragraph'
        elif n.tag in CONTAINERS:
            if n.text and n.text.strip(): reject('unsupported_mixed_container', n)
            for c in n:
                visit(c, number)
                if c.tail and c.tail.strip(): reject('unsupported_mixed_container', c)
            return
        else: reject('unsupported_structure', n)
        if value:
            if len(output) >= 10000: reject('passage_limit', n)
            counters[number] += 1
            base = f'{title} CFR {number}' if number else f'{title} CFR document metadata'
            item = passage(f'{base} — source block {counters[number]}', value, kind, n.get('ID'))
            item.update(source_xml_path=paths[n], printed_page_at_start=page,
                        printed_page_markers=[c.get('P') for c in n.iter('PRTPAGE')], **extra)
            output.append(item)
        for c in n.iter('PRTPAGE'): page = c.get('P')
    visit(root)
    if not output: reject('no_text')
    return output
