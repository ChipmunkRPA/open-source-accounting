"""Generated original PDFs only; no real accounting evidence or reviewer approval."""
import io
import pytest
from sqlalchemy import select, func
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject
from reportlab.pdfgen import canvas
from app.pdf_parser import parse, PdfError, VERSION
from app.services.documents import parse_bytes
from app.services.storage import Storage
from app.models import Document, SourceArtifact, SourceExtraction, Source
from app.sec_core.core import digest
from test_source_intake import FakeGateway, payload, registered, fetch, ADMIN, parse as api_parse
from conftest import activate


def pdf(pages=('Original fictional subscription agreement.',), labels=False):
    stream = io.BytesIO(); c = canvas.Canvas(stream)
    for text in pages:
        if text: c.drawString(40, 700, text)
        c.showPage()
    c.save()
    if not labels: return stream.getvalue()
    writer = PdfWriter(); writer.append(PdfReader(io.BytesIO(stream.getvalue())))
    writer.set_page_label(0, len(pages)-1, prefix='Appendix-', style='/r', start=1)
    out = io.BytesIO(); writer.write(out); return out.getvalue()


def test_physical_pages_and_declared_labels_remain_separate():
    result = parse(pdf(('Original first page.', 'Original second page.'), labels=True))
    assert [x['pdf']['physical_page'] for x in result] == [1, 2]
    assert [x['pdf']['declared_page_label'] for x in result] == ['Appendix-i', 'Appendix-ii']
    for item in result:
        m = item['pdf']
        assert m['physical_page_count'] == 2 and m['parser_version'] == VERSION
        assert m['page_text_sha256'] == digest(item['text'])
        assert not m['page_label_verified_against_print'] and not m['ocr_performed']
        assert m['layout_review_status'] == m['table_review_status'] == m['graphics_review_status'] == 'not_reviewed'
        assert not m['complete_publication_verified']
    assert parse(pdf())[0]['pdf']['declared_page_label'] is None


def test_private_chunks_preserve_page_hash_and_character_ranges():
    raw = pdf(('Original ' + 'fictional ' * 850,))
    chunks = parse_bytes(raw, '.pdf', 20000)
    whole = parse(raw)[0]['text']
    assert len(chunks) > 1 and ''.join(c['text'] for c in chunks) == whole
    assert chunks[0]['locator'] == 'Page 1' and chunks[1]['locator'] == 'Page 1, part 2'
    for chunk in chunks:
        a, b = chunk['pdf']['character_range']
        assert chunk['text'] == whole[a:b] and chunk['pdf']['page_text_sha256'] == digest(whole)
        assert chunk['pdf']['physical_page'] == 1


@pytest.mark.parametrize('pages,page', [
    (('Original text page.', ''), 2), (('', 'Original text page.'), 1), (('',), 1),
])
def test_mixed_text_and_textless_pages_fail_atomically(pages, page):
    raw = pdf(pages)
    for parser in (parse, lambda raw: parse_bytes(raw, '.pdf', 10000)):
        with pytest.raises(PdfError) as exc: parser(raw)
        assert exc.value.code == 'page_without_extractable_text' and exc.value.page == page


def changed_pdf(change):
    writer = PdfWriter(); writer.append(PdfReader(io.BytesIO(pdf())))
    change(writer)
    out = io.BytesIO(); writer.write(out); return out.getvalue()


def root_action(writer):
    writer._root_object[NameObject('/OpenAction')] = DictionaryObject({NameObject('/S'): NameObject('/JavaScript'), NameObject('/JS'): TextStringObject('synthetic inert fixture')})


def annotation_action(writer):
    action = DictionaryObject({NameObject('/S'): NameObject('/Launch'), NameObject('/F'): TextStringObject('synthetic-no-execution')})
    writer.pages[0][NameObject('/Annots')] = ArrayObject([DictionaryObject({NameObject('/Subtype'): NameObject('/Link'), NameObject('/A'): action})])


def embedded(writer):
    writer.add_attachment('synthetic.txt', b'Original test attachment')


@pytest.mark.parametrize('change', [root_action, annotation_action, embedded])
def test_reachable_active_or_embedded_content_is_rejected(change):
    with pytest.raises(PdfError) as exc: parse(changed_pdf(change))
    assert exc.value.code == 'active_or_embedded_content'


def test_encryption_page_and_character_limits():
    raw = changed_pdf(lambda w: w.encrypt('synthetic-test-password'))
    with pytest.raises(PdfError, match='encrypted_pdf'): parse(raw)
    with pytest.raises(PdfError, match='page_limit'): parse(pdf(('Page one.', 'Page two.')), page_limit=1)
    with pytest.raises(PdfError, match='character_limit'): parse(pdf(), character_limit=5)
    with pytest.raises(PdfError, match='invalid_or_oversized_pdf'): parse(b'not pdf')


def test_private_upload_failure_stores_no_document(client):
    activate(client)
    response = client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file': ('mixed.pdf', pdf(('Original text.', '')), 'application/pdf')},
        data={'authorization_basis': 'own_original'})
    assert response.status_code == 422, response.text
    error = response.json()['error']
    assert error['code'] == 'PDF_PARSE_BLOCKED' and error['physical_page'] == 2
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 0


def test_private_upload_exposes_coverage_to_authorized_reader(client):
    activate(client)
    response = client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file': ('original.pdf', pdf(labels=True), 'application/pdf')},
        data={'authorization_basis': 'own_original'})
    assert response.status_code == 201, response.text
    detail = client.get('/api/v1/documents/'+response.json()['id']).json()
    assert detail['chunks'][0]['pdf']['declared_page_label'] == 'Appendix-i'
    assert detail['chunks'][0]['pdf']['table_review_status'] == 'not_reviewed'


class PdfGateway(FakeGateway):
    def get(self, url):
        return {**super().get(url), 'mime': 'application/pdf'}


def pdf_work(client):
    return registered(client, body=payload(parser='pdf', requested_url='https://www.sec.gov/synthetic.pdf', allowed_mime=['application/pdf']))


def test_intake_failure_retains_raw_and_no_partial_extraction(client):
    raw = pdf(('Original text.', ''))
    artifact = fetch(client, pdf_work(client), PdfGateway(raw))
    response = client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN)
    assert response.status_code == 422, response.text
    assert response.json()['error']['physical_page'] == 2
    with client.app.state.db.Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0
        row = db.get(SourceArtifact, artifact['id'])
        assert Storage(client.app.state.settings)._path(row.object_key).read_bytes() == raw


def test_intake_pdf_version_stage_and_review_are_separate(client):
    artifact = fetch(client, pdf_work(client), PdfGateway(pdf(labels=True)))
    extraction = api_parse(client, artifact)
    assert extraction['parser_version'] == VERSION
    assert api_parse(client, artifact)['id'] == extraction['id']
    response = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN)
    assert response.status_code == 200, response.text
    with client.app.state.db.Session() as db:
        row = db.get(Source, response.json()['source_ids'][0])
        assert not row.reviewed and row.effective_from is None
        assert row.policy['intake_pdf']['declared_page_label'] == 'Appendix-i'
        assert row.policy['intake_pdf']['layout_review_status'] == 'not_reviewed'


def test_workflow_carries_pdf_limits_and_legacy_unknown_coverage(client):
    from types import SimpleNamespace
    from app.agents.workflows import preprocess
    activate(client)
    response = client.post('/api/v1/workspaces/demo-workspace/documents',
        files={'file': ('original.pdf', pdf(), 'application/pdf')},
        data={'authorization_basis': 'own_original'})
    assert response.status_code == 201
    did = response.json()['id']
    run = SimpleNamespace(document_ids=[did], workspace_id='demo-workspace', inputs={}, workflow='document_gaap', context={})
    task = {'min_documents': 1, 'guardrail': 'Synthetic task'}
    with client.app.state.db.Session() as db:
        limits = preprocess(db, run, task)['document_extraction_limits'][0]
        assert limits['physical_pages_with_text'] == [1] and limits['parser_versions'] == [VERSION]
        assert not limits['complete_document_verified'] and not limits['layout_tables_graphics_reviewed']
        doc = db.get(Document, did)
        doc.chunks = [{'locator': 'Page 1', 'text': 'Original legacy fixture text.'}]
        db.flush()
        legacy = preprocess(db, run, task)['document_extraction_limits'][0]
        assert legacy['page_coverage_metadata'] == 'unknown_legacy_extraction'
        assert not legacy['physical_pages_with_text']


def test_image_only_page_is_not_hidden_by_text_on_another_page():
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    stream = io.BytesIO(); c = canvas.Canvas(stream)
    c.drawString(40, 700, 'Original first page with text.'); c.showPage()
    c.drawImage(ImageReader(Image.new('RGB', (8, 8), 'black')), 40, 600, width=80, height=80)
    c.showPage(); c.save()
    with pytest.raises(PdfError) as exc: parse(stream.getvalue())
    assert exc.value.code == 'page_without_extractable_text' and exc.value.page == 2
