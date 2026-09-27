"""Conservative structural parsers. Parsing never grants rights or applicability.

XML/HTML raw bytes remain the canonical acquired artifact. Paragraph locators that
are not legal subsection identifiers are explicitly described as local block IDs.
PDF page locators are physical 1-based PDF pages, not printed page numbers.
"""
from __future__ import annotations
import io
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from .core import CoreError, digest

MAX_BYTES = 16 * 1024 * 1024


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


def passage(locator, text, kind='paragraph', anchor=None):
    text = text.strip()
    return {'locator': locator, 'text': text, 'kind': kind, 'anchor': anchor,
            'sha256': digest(text), 'review_status': 'pending'}


def ecfr_xml(raw: bytes, title='17'):
    if len(raw) > MAX_BYTES or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise CoreError('Oversized or unsafe XML')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CoreError('Invalid eCFR XML') from exc
    sections = [n for n in root.iter() if n.attrib.get('TYPE') == 'SECTION' or n.tag == 'SECTION']
    output = []
    for section in sections:
        number = section.attrib.get('N') or clean(section.findtext('SECTNO', ''))
        number = number.removeprefix('§').strip()
        if not re.fullmatch(r'\d+\.[\dA-Za-z-]+', number):
            raise CoreError('Section lacks a valid CFR locator; no fabricated citation')
        base = f'{title} CFR {number}'
        block = 0
        for n in section.iter():
            tag = n.tag.upper()
            if tag not in {'P', 'TABLE', 'GPOTABLE', 'FTNT', 'AUTH', 'SOURCE', 'CITA'}:
                continue
            # Nested table/footnote paragraphs are emitted with their enclosing structure once.
            if any(n in list(x.iter())[1:] for x in section.iter() if x.tag.upper() in {'TABLE', 'GPOTABLE', 'FTNT'}):
                continue
            block += 1
            if tag in {'TABLE', 'GPOTABLE'}:
                rows = []
                for tr in n.iter():
                    if tr.tag.upper() in {'TR', 'ROW'}:
                        cells = [clean(''.join(c.itertext())) for c in tr if c.tag.upper() in {'TD', 'TH', 'ENT'}]
                        if cells:
                            rows.append(' | '.join(cells))
                text = '\n'.join(rows) or clean(''.join(n.itertext()))
                kind = 'table_linearized'
            else:
                text, kind = clean(''.join(n.itertext())), 'footnote' if tag == 'FTNT' else 'paragraph'
            if text:
                output.append(passage(f'{base} — source block {block}', text, kind, n.attrib.get('ID')))
    if not output:
        raise CoreError('No CFR sections extracted')
    return output


class Node:
    def __init__(self, tag='root', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self):
        if self.tag in {'script', 'style', 'nav', 'iframe'}:
            return ''
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children)


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'wbr'}:
            self.stack.append(n)
        elif tag == 'br':
            self.stack[-1].children.append('\n')
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
    def handle_data(self, data):
        self.stack[-1].children.append(data)


def walk(n):
    yield n
    for c in n.children:
        if isinstance(c, Node):
            yield from walk(c)


def html(raw: bytes, family: str, title: str):
    if len(raw) > MAX_BYTES:
        raise CoreError('Oversized HTML')
    parser = DOM()
    parser.feed(raw.decode('utf-8', errors='strict'))
    nodes = list(walk(parser.root))
    root = next((n for n in nodes if n.tag == 'main'), None)
    root = root or next((n for n in nodes if n.tag == 'article'), None)
    if root is None:
        raise CoreError('Unrecognized HTML body; require a reviewed selector, not entire navigation text')
    blocks = []
    def visit(n):
        if n.tag in {'script', 'style', 'nav', 'header', 'footer', 'noscript', 'form', 'iframe'}:
            return
        if n.tag == 'table':
            rows = []
            for tr in walk(n):
                if tr.tag == 'tr':
                    rows.append(' | '.join(clean(c.text()) for c in tr.children
                                           if isinstance(c, Node) and c.tag in {'td', 'th'}))
            blocks.append(('table_linearized', '\n'.join(rows), n.attrs.get('id')))
            return
        if n.tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote'}:
            text = clean(n.text())
            if text:
                blocks.append((n.tag, text, n.attrs.get('id')))
            return
        for c in n.children:
            if isinstance(c, Node):
                visit(c)
    visit(root)
    output, heading, pending, current = [], title, [], None
    def flush():
        nonlocal pending
        if pending:
            output.append(passage(current, '\n\n'.join(pending), 'question_and_answer'))
            pending = []
    for i, (kind, text, anchor) in enumerate(blocks, 1):
        match = re.match(r'^Question\s+(\d{3}\.\d{2}(?:\([a-z]\))?)(?=\s|:|$)', text)
        if match and family == 'cfi':
            flush()
            current = f'CFI {match.group(1)}'
            pending = [text]
            continue
        if current:
            if kind.startswith('h') and re.match(r'^(?:Section|QUESTIONS)', text):
                flush(); current = None
            else:
                pending.append(text)
                continue
        if kind.startswith('h'):
            heading = text
        if family == 'frm' and re.match(r'^\d{4,5}(?:\.\d+)?\s', text):
            heading = 'FRM ' + re.match(r'^(\d{4,5}(?:\.\d+)?)', text).group(1)
        output.append(passage(f'{heading[:95]} — source block {i}', text,
                              'table_linearized' if kind == 'table_linearized' else 'paragraph', anchor))
    flush()
    if not output:
        raise CoreError('No body passages')
    return output


def pdf(raw: bytes):
    if len(raw) > MAX_BYTES or not raw.startswith(b'%PDF-'):
        raise CoreError('Invalid/oversized PDF')
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted or len(reader.pages) > 600:
        raise CoreError('Encrypted or oversized PDF')
    result = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or '').strip()
        if not text:
            raise CoreError(f'Page {i} has no extractable text; OCR/manual handling is required')
        result.append(passage(f'PDF page {i}', text, 'pdf_page_unreviewed_layout'))
    return result
