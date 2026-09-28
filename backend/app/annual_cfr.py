"""Bounded annual CFR XML normalization. No rights, authenticity or completeness approval.

Unrecognized structures fail the entire parse; a successful parse covers supported XML
text, not missing images or the publisher's entire legal publication.
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from .sec_core.parsers import MAX_BYTES, clean, passage

VERSION = 'source-intake-annual-cfr-1'


class AnnualCfrError(ValueError):
    def __init__(self, code, path='/'):
        self.code, self.path = code, path[:1000]
        super().__init__(code)


# Structural containers and textual metadata in the publisher's CFR XML vocabulary.
# Unknown tags never disappear into generic itertext() output.
WRAPPERS = set('CFRDOC FMTR BMTR TITLE CFRTITLE SUBTITLE CHAPTER SUBCHAP PART SUBPART SECTION '
               'SUBJGRP APPENDIX APP REGTEXT EXTRACT BIBINF TOC CONTENTS CITE EXPLA THISTITL '
               'FAIDS ALPHLIST INCORP TOCTAC LSA REDES ANCIL'.split())
TEXT = set('P FP HD HEAD SUBJECT SECTNO AUTH SOURCE CITA FTNT TNOTE EDNOTE EFFDNOTP '
           'AMDDATE DATE PUBYEAR VOL BTI BTISB BTICT BSUBTI BSUBTISB BSUBTICT BCH BCHSB BCHCT '
           'BSUBCH BSUBCHSB BSUBCHCT BPT BPTSB BPTCT BIBSRT BSUBPT BSUBPTSB BSUBPTCT BSUBGP '
           'BSUBGPSB BSUBGPCT BSEC BSECSB BSECCT BAPP BAPPSB BAPPCT BFRPAGE BEFFDATE BID BREGHD '
           'TITLEHD TITLENO CFRHD CFRNO CHAPNO CHAPTI SUBTI SUBTI2 SUBTITL PTHD PGHD TOCHD '
           'SECHD REV REVTXT LRH RRH PG AGENCY NAME POSITION OFFICE SIG PUB SPECED BTITLE '
           'OWNER ADDR PUBLI ONOTE RESERVED STARS TXT LI ENTRY AGHD CFRID ABBREV'.split())
INLINE = {'E', 'I', 'B', 'FTREF', 'SU', 'SUP', 'SUB', 'PRTPAGE'}


def parse(raw, title, edition):
    def reject(code, path='/'):
        raise AnnualCfrError(code, path)

    if len(raw) > MAX_BYTES:
        reject('size_limit')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        reject('unsupported_encoding')
    if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        reject('unsafe_xml')
    declaration = re.match(r'\s*<\?xml\s+[^?]*encoding=[\"\']([^\"\']+)', text)
    if declaration and declaration[1].lower() not in {'utf-8', 'us-ascii'}:
        reject('unsupported_encoding')
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError):
        reject('invalid_xml')
    if root.tag != 'CFRDOC':
        reject('wrong_document_type')
    paths, nodes = {}, []

    def inventory(node, path, depth):
        if depth > 80 or len(nodes) >= 100000:
            reject('structure_limit', path)
        if not re.fullmatch('[A-Z][A-Z0-9]*', node.tag):
            reject('unsupported_tag', path)
        if node.tag == "PRTPAGE" and (set(node.attrib) != {"P"} or not node.get("P") or len(node) or (node.text and node.text.strip())):
            reject("unsupported_page_marker", path)
        paths[node] = path
        nodes.append(node)
        counts = Counter()
        for child in node:
            counts[child.tag] += 1
            inventory(child, path+'/'+child.tag+'['+str(counts[child.tag])+']', depth+1)
    inventory(root, '/CFRDOC[1]', 0)
    # Obvious identity contradictions block. Missing/unrecognized header fields remain
    # explicit observations requiring review, never inferred from the fetch timestamp.
    observations = {k: [clean(''.join(n.itertext())) for n in nodes if n.tag == k]
                    for k in ('PUBYEAR', 'VOL', 'BTI', 'AMDDATE')}
    if any(len(values) > 100 or sum(map(len, values)) > 8000 for values in observations.values()):
        reject('metadata_limit')
    for tag, expected in [('PUBYEAR', str(edition['year'])), ('VOL', str(edition['volume'])), ('BTI', str(title))]:
        for value in observations[tag]:
            m = re.fullmatch(r'(?:Title |Volume )?(\d+)', value, re.I)
            if m and int(m[1]) != int(expected):
                reject('edition_identity_mismatch')
    context = {'year': edition['year'], 'volume': edition['volume'], 'title': str(title),
               'revised_as_of': edition.get('revised_as_of'),
               'identity_basis': 'declared_manifest_with_observed_xml_headers_not_independent_verification',
               'xml_header_observations': observations, 'root_attributes': dict(root.attrib),
               'legal_effective_date_inferred': False, 'publisher_completeness_verified': False}
    seen = set()
    section_numbers = {}
    for n in nodes:
        if n.tag == 'SECTION':
            numbers = n.findall('SECTNO')
            number = clean(''.join(numbers[0].itertext())).removeprefix('§').strip() if len(numbers) == 1 else ''
            if not re.fullmatch(r'\d+\.[\dA-Za-z-]+', number) or number in seen:
                reject('invalid_or_duplicate_section', paths[n])
            seen.add(number)
            section_numbers[n] = number
    if not seen:
        reject('no_sections')

    def inline(n):
        value = n.text or ''
        for child in n:
            if child.tag not in INLINE and not (n.tag in {'FTNT', 'TNOTE'} and child.tag == 'P'):
                reject('unsupported_inline_structure', paths[child])
            part = inline(child)
            if child.tag in {'SU', 'SUP'}: part = '[superscript: '+part+']'
            elif child.tag == 'SUB': part = '[subscript: '+part+']'
            elif child.tag == 'FTREF': part = '[footnote reference: '+part+']'
            value += part+(child.tail or '')
        return clean(value)

    def table(n):
        def structural_text(node):
            if (node.text and node.text.strip()) or any(c.tail and c.tail.strip() for c in node):
                reject('unsupported_mixed_table', paths[node])
        structural_text(n)
        if set(n.attrib)-{'COLS', 'CDEF', 'OPTS', 'ID'}:
            reject('unsupported_table_layout', paths[n])
        try: columns = int(n.attrib['COLS'])
        except (KeyError, ValueError): reject('invalid_table_columns', paths[n])
        if not 1 <= columns <= 100: reject('invalid_table_columns', paths[n])
        rows, captions, notes = [], [], []
        headers = 0
        for child in n:
            if child.tag in {'BOXHD', 'ROW'}:
                structural_text(child)
                header = child.tag == 'BOXHD'
                headers += header
                if headers > 1 or (header and rows) or child.attrib:
                    reject('unsupported_table_layout', paths[child])
                cells, cell_metadata = [], []
                for c in child:
                    if c.tag == 'PRTPAGE': continue
                    if c.tag != ('CHED' if header else 'ENT'):
                        reject('unsupported_table_layout', paths[c])
                    if (header and (set(c.attrib)-{'H'} or c.get('H', '1') != '1')
                            or not header and set(c.attrib)-{'I'}):
                        reject('unsupported_table_span_or_alignment', paths[c])
                    cells.append(inline(c))
                    cell_metadata.append({"attributes": dict(c.attrib), "source_xml_path": paths[c]})
                if len(cells) != columns:
                    reject('inconsistent_table_columns', paths[child])
                rows.append({'kind': 'header' if header else 'data', 'cells': cells,
                             'source_xml_path': paths[child], 'cell_metadata': cell_metadata})
            elif child.tag in {'TTITLE', 'TDESC', 'TNOTE'}:
                (notes if child.tag == 'TNOTE' else captions).append(inline(child))
            elif child.tag != 'PRTPAGE':
                reject('unsupported_table_structure', paths[child])
        if not any(r['kind'] == 'data' for r in rows): reject('empty_table', paths[n])
        rendered = ['Caption: '+v for v in captions]
        rendered += [('Header: ' if r['kind'] == 'header' else '')+' | '.join(v.replace('|', '\\|') for v in r['cells']) for r in rows]
        rendered += ['Note: '+v for v in notes]
        return '\n'.join(rendered), {'columns': columns, 'attributes': dict(n.attrib), 'rows': rows, 'captions': captions, 'notes': notes}

    output, page = [], None

    def emit(n, value, kind, number, extra=None):
        if not value: return
        if len(output) >= 10000: reject('passage_limit', paths[n])
        base = f'{title} CFR {number}' if number else f'{title} CFR annual volume metadata'
        label = f'{base} — {edition["year"]} annual edition, volume {edition["volume"]} — XML {paths[n]}'
        item = passage(label, value, kind, n.get('ID'))
        item.update(annual_cfr=context, source_xml_path=paths[n], printed_page_at_start=page,
                    printed_page_markers=[c.get('P') for c in n.iter('PRTPAGE')])
        if extra: item.update(extra)
        output.append(item)

    def visit(n, number=None):
        nonlocal page
        if n.tag == 'PRTPAGE':
            page = n.get('P')
            return
        number = section_numbers.get(n, number)
        if n.tag == 'GPOTABLE':
            value, structure = table(n)
            emit(n, value, 'annual_cfr_table_unreviewed', number, {'table': structure})
        elif n.tag in TEXT:
            emit(n, inline(n), 'annual_cfr_xml_text_unreviewed', number)
        elif n.tag in WRAPPERS:
            if n.text and n.text.strip(): emit(n, clean(n.text), 'annual_cfr_xml_text_unreviewed', number)
            for child in n:
                visit(child, number)
                if child.tail and child.tail.strip():
                    # Mixed structural containers have ambiguous citation boundaries.
                    reject('unsupported_mixed_container', paths[child])
        else:
            reject('unsupported_structure', paths[n])
        # A page marker inside a block also governs following sibling blocks.
        for c in n.iter('PRTPAGE'):
            page = c.get('P')
    visit(root)
    if not output: reject('no_text')
    return output
