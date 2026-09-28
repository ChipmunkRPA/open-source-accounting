"""Bounded PDF text extraction with explicit page coverage, never layout approval."""
import io
from .sec_core.core import digest

VERSION = 'pdf-text-pages-2'
MAX_BYTES = 16 * 1024 * 1024


class PdfError(ValueError):
    def __init__(self, code, page=None):
        self.code, self.page = code, page
        super().__init__(code)


def parse(raw, *, page_limit=600, character_limit=2_000_000):
    from pypdf import PdfReader, __version__ as engine_version
    from pypdf.generic import DictionaryObject, ArrayObject, IndirectObject
    if not raw.startswith(b'%PDF-') or len(raw) > MAX_BYTES:
        raise PdfError('invalid_or_oversized_pdf')
    try:
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted: raise PdfError('encrypted_pdf')
        count = len(reader.pages)
        if not 1 <= count <= page_limit: raise PdfError('page_limit')
        seen, references = set(), set()
        # Inspect reachable object dictionaries without executing actions or decoding
        # image streams. Repeated/cyclic page references are visited once.
        def inspect(obj, depth=0):
            if isinstance(obj, IndirectObject):
                key = (obj.idnum, obj.generation)
                if key in references: return
                references.add(key)
                obj = obj.get_object()
            if not isinstance(obj, (DictionaryObject, ArrayObject)): return
            key = id(obj)
            if key in seen: return
            seen.add(key)
            if depth > 80 or len(seen) > 100000: raise PdfError('object_graph_limit')
            if isinstance(obj, DictionaryObject):
                if any(k in obj for k in ('/OpenAction', '/AA', '/JS', '/JavaScript', '/EmbeddedFiles', '/XFA', '/RichMediaContent')):
                    raise PdfError('active_or_embedded_content')
                if obj.get('/S') in {'/JavaScript', '/Launch', '/GoToR', '/GoToE', '/SubmitForm', '/ImportData', '/Rendition', '/Sound', '/Movie'}:
                    raise PdfError('active_or_embedded_content')
                if obj.get('/Subtype') in {'/FileAttachment', '/RichMedia', '/Movie', '/Sound', '/Screen'}:
                    raise PdfError('active_or_embedded_content')
                children = obj.values()
            else: children = obj
            for child in children: inspect(child, depth+1)
        inspect(reader.trailer['/Root'])
        declared_labels = '/PageLabels' in reader.trailer['/Root']
        labels = reader.page_labels if declared_labels else [None] * count
        if len(labels) != count or any(x is not None and (not isinstance(x, str) or len(x) > 200) for x in labels):
            raise PdfError('invalid_page_labels')
        output, total = [], 0
        for i, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or '').strip()
            if not text:
                # Even a legitimately blank page needs explicit handling, not silent
                # disappearance from a file otherwise treated as fully extracted.
                raise PdfError('page_without_extractable_text', i)
            total += len(text)
            if total > character_limit: raise PdfError('character_limit', i)
            output.append({'text': text, 'pdf': {
                'parser_version': VERSION, 'engine': 'pypdf', 'engine_version': engine_version,
                'physical_page': i, 'physical_page_count': count,
                'declared_page_label': labels[i-1], 'page_label_verified_against_print': False,
                'page_text_sha256': digest(text), 'page_character_count': len(text),
                'text_extraction_status': 'text_extracted',
                'layout_review_status': 'not_reviewed', 'table_review_status': 'not_reviewed',
                'graphics_review_status': 'not_reviewed', 'ocr_performed': False,
                'complete_publication_verified': False,
            }})
        return output
    except PdfError:
        raise
    except Exception as exc:
        # Parser details/raw data are not API diagnostics.
        raise PdfError('invalid_or_unsupported_pdf') from exc
