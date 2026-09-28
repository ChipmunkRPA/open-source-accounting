"""Bounded DOCX body-order extraction. No revision acceptance or layout approval."""
import io
import re
import posixpath
from urllib.parse import unquote, urlsplit
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import PurePosixPath
from .sec_core.core import digest

VERSION = 'docx-body-order-2'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'w': W}


class DocxError(ValueError):
    def __init__(self, code, part='word/document.xml', path='/'):
        self.code, self.part, self.path = code, part[:200], path[:1000]
        super().__init__(code)


def parse(raw, character_limit):
    def reject(code, part='word/document.xml', path='/'):
        raise DocxError(code, part, path)

    if len(raw) > 12 * 1024 * 1024: reject('size_limit')
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        with archive:
            members = archive.infolist()
            names = [m.filename for m in members]
            if (len(members) > 2000 or len(set(names)) != len(names)
                    or sum(m.file_size for m in members) > 40 * 1024 * 1024
                    or any(m.flag_bits & 1 or m.file_size > 1000 * max(1, m.compress_size) for m in members)):
                reject('archive_limit_or_ambiguous_members')
            if any(n.startswith('/') or '\\' in n or '..' in PurePosixPath(n).parts for n in names): reject('unsafe_archive_path')
            if any('vbaproject' in n.lower() or n.startswith('word/embeddings/') for n in names): reject('active_or_embedded_content')
            if 'word/document.xml' not in names: reject('missing_document')
            roots, paths, nodes = {}, {}, 0
            for name in names:
                if not name.endswith(('.xml', '.rels')): continue
                try: text = archive.read(name).decode('utf-8-sig')
                except UnicodeDecodeError: reject('unsupported_xml_encoding', name)
                if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): reject('unsafe_xml', name)
                try: root = ET.fromstring(text)
                except (ET.ParseError, ValueError): reject('invalid_xml', name)
                roots[name] = root
                def walk(n, path, depth):
                    nonlocal nodes
                    nodes += 1
                    paths[n] = path
                    if depth > 80 or nodes > 200000: reject('xml_structure_limit', name, path)
                    local = n.tag.rsplit('}', 1)[-1]
                    if n.tag.startswith('{'+W+'}'):
                        if local in {'ins', 'del', 'moveFrom', 'moveTo', 'moveFromRangeStart', 'moveToRangeStart', 'cellIns', 'cellDel', 'cellMerge', 'numberingChange'} or local.endswith('Change'):
                            reject('tracked_revisions_require_resolution', name, path)
                        if local in {'comment', 'commentRangeStart', 'commentRangeEnd', 'commentReference'}: reject('comments_require_review', name, path)
                        if local in {'drawing', 'pict', 'object', 'altChunk'}: reject('unsupported_visual_or_embedded_content', name, path)
                        if local in {'fldChar', 'fldSimple', 'instrText'}: reject('fields_require_review', name, path)
                        if local in {'vanish', 'webHidden'} and n.get('{'+W+'}val', 'true') not in {'0', 'false', 'off'}:
                            reject('hidden_text_requires_review', name, path)
                    counts = Counter()
                    for child in n:
                        counts[child.tag] += 1
                        label = ('w:' if child.tag.startswith('{'+W+'}') else '')+child.tag.rsplit('}', 1)[-1]
                        walk(child, path+'/'+label+'['+str(counts[child.tag])+']', depth+1)
                root_label = ('w:' if root.tag.startswith('{'+W+'}') else '')+root.tag.rsplit('}', 1)[-1]
                walk(root, '/'+root_label+'[1]', 0)
            links = {}
            main_targets = []
            for name, root in roots.items():
                if name.endswith('.rels'):
                    relationship_ids = set()
                    for rel in root:
                        rid = rel.get('Id')
                        if not rid or rid in relationship_ids: reject('ambiguous_relationship', name)
                        relationship_ids.add(rid)
                        kind, target = rel.get('Type', ''), rel.get('Target', '')
                        if any(s in kind.lower() for s in ('oleobject', 'attachedtemplate', 'afchunk', 'vbaproject')): reject('active_or_embedded_content', name)
                        if rel.get('TargetMode') == 'External' and not kind.endswith('/hyperlink'): reject('external_relationship', name)
                        if rel.get('TargetMode') != 'External':
                            uri = urlsplit(target)
                            if uri.scheme or uri.netloc or uri.query: reject('invalid_internal_relationship', name)
                            target_path = unquote(uri.path)
                            base = posixpath.dirname(posixpath.dirname(name))
                            resolved = posixpath.normpath(target_path.lstrip('/') if target_path.startswith('/') else posixpath.join(base, target_path))
                            if resolved.startswith('../') or resolved not in names: reject('missing_relationship_part', name)
                            if name == '_rels/.rels' and kind.endswith('/officeDocument'):
                                main_targets.append(resolved)
                        if name == 'word/_rels/document.xml.rels' and kind.endswith('/hyperlink'):
                            links[rel.get('Id')] = {'target': target, 'external': rel.get('TargetMode') == 'External'}
                if re.fullmatch(r'word/(header\d*|footer\d*|footnotes|endnotes)\.xml', name):
                    if any(n.tag == '{'+W+'}t' and (n.text or '').strip() for n in root.iter()):
                        reject('supplemental_story_requires_review', name)
    except DocxError:
        raise
    except (zipfile.BadZipFile, KeyError, RuntimeError, OSError):
        reject('invalid_archive')
    if main_targets != ['word/document.xml']: reject('unsupported_main_document_relationship')
    root = roots['word/document.xml']
    bodies = root.findall('w:body', NS)
    if root.tag != '{'+W+'}document' or len(bodies) != 1: reject('invalid_document_body')
    body = bodies[0]
    output, total, paragraph_number, table_number = [], 0, 0, 0
    has_content = False

    def local(n):
        if not n.tag.startswith('{'+W+'}'): reject('unsupported_namespace', path=paths[n])
        return n.tag.rsplit('}', 1)[-1]

    def paragraph(n):
        hyperlinks = []
        def text_of(node):
            tag = local(node)
            if tag == 't':
                if len(node): reject('unsupported_text_structure', path=paths[node])
                return node.text or ''
            if tag in {'tab'}: return '\t'
            if tag in {'br', 'cr'}: return '\n'
            if tag in {'pPr', 'rPr', 'bookmarkStart', 'bookmarkEnd', 'proofErr', 'lastRenderedPageBreak'}: return ''
            if (node.text and node.text.strip()) or any(c.tail and c.tail.strip() for c in node):
                reject('unsupported_mixed_text', path=paths[node])
            if tag not in {'p', 'r', 'hyperlink'}: reject('unsupported_paragraph_structure', path=paths[node])
            if tag == 'hyperlink':
                rid = node.get('{'+R+'}id')
                if rid and rid not in links: reject('unresolved_hyperlink', path=paths[node])
                hyperlinks.append({'source_xml_path': paths[node], 'relationship_id': rid,
                                   'anchor': node.get('{'+W+'}anchor'), **links.get(rid, {})})
            return ''.join(text_of(child) for child in node)
        text = text_of(n).strip()
        num = n.find('w:pPr/w:numPr', NS)
        numbering = None if num is None else {c.tag.rsplit('}', 1)[-1]: c.get('{'+W+'}val') for c in num}
        return text, {'hyperlinks': hyperlinks, 'declared_numbering': numbering, 'numbering_rendered': False}

    def emit(locator, text, n, metadata):
        nonlocal total
        if not text: return
        total += len(text)
        if total > character_limit or len(output) >= 10000: reject('extraction_limit', path=paths[n])
        output.append({'locator': locator, 'text': text, 'docx': {
            'parser_version': VERSION, 'source_part': 'word/document.xml', 'source_xml_path': paths[n],
            'block_text_sha256': digest(text), 'revision_handling': 'no_tracked_revisions_detected',
            'layout_review_status': 'not_reviewed', 'complete_document_verified': False, **metadata}})

    for node in body:
        tag = local(node)
        if tag == 'sectPr': continue
        if tag == 'p':
            paragraph_number += 1
            text, metadata = paragraph(node)
            has_content = has_content or bool(text.strip())
            emit(f'Paragraph {paragraph_number}', text, node, metadata)
        elif tag == 'tbl':
            table_number += 1
            if any(local(c) not in {'tblPr', 'tblGrid', 'tr'} for c in node): reject('unsupported_table_structure', path=paths[node])
            columns = len(node.findall('w:tblGrid/w:gridCol', NS))
            if not 1 <= columns <= 100: reject('unsupported_table_grid', path=paths[node])
            for row_number, row in enumerate(node.findall('w:tr', NS), 1):
                if any(local(c) not in {'trPr', 'tc'} for c in row): reject('unsupported_table_structure', path=paths[row])
                cells = row.findall('w:tc', NS)
                for cell in cells:
                    if cell.find('w:tcPr/w:vMerge', NS) is not None or cell.find('w:tcPr/w:gridSpan', NS) is not None:
                        reject('merged_cells_require_review', path=paths[cell])
                if len(cells) != columns: reject('inconsistent_table_grid', path=paths[row])
                mapped = []
                for index, cell in enumerate(cells, 1):
                    if any(local(c) not in {'tcPr', 'p'} for c in cell): reject('unsupported_cell_structure', path=paths[cell])
                    paragraphs = []
                    for p in cell.findall('w:p', NS):
                        value, info = paragraph(p)
                        paragraphs.append({'text': value, 'source_xml_path': paths[p], **info})
                    mapped.append({'column': index, 'text': '\n'.join(p['text'] for p in paragraphs), 'source_xml_path': paths[cell], 'paragraphs': paragraphs})
                has_content = has_content or any(c['text'].strip() for c in mapped)
                header = row.find('w:trPr/w:tblHeader', NS)
                text = ' | '.join(c['text'].replace('|', '\\|').replace('\n', '\\n') for c in mapped)
                emit(f'Table {table_number}, row {row_number}', text, row,
                     {'table_number': table_number, 'row_number': row_number, 'cells': mapped,
                      'declared_header_row': header is not None and header.get('{'+W+'}val', 'true') not in {'0', 'false', 'off'}})
        else: reject('unsupported_body_structure', path=paths[node])
    if not has_content: reject('no_text')
    return output
