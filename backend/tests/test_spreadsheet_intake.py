"""Synthetic source spreadsheets; no live acquisition or professional approval."""
import pytest
from sqlalchemy import select, func
from app.intake_schemas import IntakeCreate
from app.models import Source, SourceArtifact, SourceExtraction
from app.services.storage import Storage
from app.sec_core.core import digest
from test_source_intake import payload, registered, fetch, parse, FakeGateway, ADMIN
from test_spreadsheet_parser import fixture, MIME


class SheetGateway(FakeGateway):
    def __init__(self, raw, mime):
        super().__init__(raw)
        self.mime = mime

    def get(self, url):
        return {**super().get(url), 'mime': self.mime}


@pytest.mark.parametrize('parser,mime,raw', [('xlsx', MIME, fixture()), ('csv', 'text/csv', b'Account,Amount\n00125,-1250.00\n')], ids=['xlsx','csv'])
def test_source_cells_preserve_provenance_and_stay_unreviewed(client, parser, mime, raw):
    work = registered(client, body=payload(parser=parser, allowed_mime=[mime]))
    artifact = fetch(client, work, SheetGateway(raw, mime))
    extraction = parse(client, artifact)
    assert extraction['parser_version'] == 'source-intake-1/spreadsheet-cells-3'
    assert parse(client, artifact)['id'] == extraction['id']
    response = client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN)
    assert response.status_code == 200, response.text
    staged = response.json()
    assert not staged['agent_eligible']
    with client.app.state.db.Session() as db:
        original = db.get(SourceArtifact, artifact['id'])
        assert Storage(client.app.state.settings).get(original.object_key) == raw
        rows = [db.get(Source, sid) for sid in staged['source_ids']]
        assert all(r.policy['intake_spreadsheet']['format'] == parser for r in rows)
        assert all(r.policy['content_sha256'] == digest(r.text) for r in rows)
        assert all(not r.reviewed and r.policy['technical_review_status'] == 'unreviewed' for r in rows)
        assert all(r.policy['intake_spreadsheet']['calculated'] is False for r in rows)
        cells = [c for r in rows for c in r.policy['intake_spreadsheet']['cells']]
        assert any(c['value'] == '00125' for c in cells)
        if parser == 'xlsx':
            assert any(c['cache_status'] == 'missing' for c in cells)
            assert any(c['formula'] and c['value'] == '-2500' for c in cells)


@pytest.mark.parametrize('parser,mimes,limit', [('xlsx',['text/plain'],1000), ('csv',[MIME],1000), ('text',['text/csv'],1000), ('xlsx',[MIME],12_000_001)])
def test_mime_and_limit_are_bound_to_parser(parser,mimes,limit):
    with pytest.raises(ValueError):
        IntakeCreate.model_validate(payload(parser=parser, allowed_mime=mimes, max_bytes=limit))


def test_unsafe_workbook_retains_raw_without_extraction(client):
    raw = fixture(extra={'xl/vbaProject.bin': b'not executable'})
    work = registered(client, body=payload(parser='xlsx', allowed_mime=[MIME]))
    artifact = fetch(client, work, SheetGateway(raw, MIME))
    response = client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN)
    assert response.status_code == 422
    assert 'SPREADSHEET_PARSE_BLOCKED' in response.text
    with client.app.state.db.Session() as db:
        assert db.get(SourceArtifact, artifact['id']) is not None
        assert db.scalar(select(func.count()).select_from(SourceExtraction)) == 0


def test_spreadsheet_review_packet_and_revocation(client):
    import base64
    body = payload(parser='xlsx', allowed_mime=[MIME])
    body['source']['policy']['export'] = True
    work = registered(client, body=body)
    raw = fixture()
    artifact = fetch(client, work, SheetGateway(raw, MIME))
    extraction = parse(client, artifact)
    url = '/api/v1/editorial/extractions/'+extraction['id']+'/packet'
    response = client.get(url, headers={'X-Dev-User': 'editor'})
    assert response.status_code == 200, response.text
    packet = response.json()['packet']
    assert base64.b64decode(packet['raw_base64']) == raw
    assert packet['passages'][1]['spreadsheet']['cells'][2]['formula']['text'] == 'B2*2'
    assert not packet['approval_granted']
    client.post('/api/v1/admin/sources/'+work['source_id']+'/disable', headers=ADMIN)
    assert client.get(url, headers={'X-Dev-User': 'editor'}).status_code == 403
    assert client.post('/api/v1/admin/intake/artifacts/'+artifact['id']+'/parse', headers=ADMIN).status_code == 403
    assert client.post('/api/v1/admin/intake/extractions/'+extraction['id']+'/stage', headers=ADMIN).status_code == 403


@pytest.mark.parametrize('raw,mime', [(fixture(), MIME), (b'Account,Amount\n00125,-1250.00\n', 'text/csv')], ids=['xlsx','csv'])
def test_gateway_accepts_declared_spreadsheet_mime_without_network(raw,mime):
    from types import SimpleNamespace
    from app.sec_core.fetch import Gateway
    from test_source_intake import Opener, Response
    gateway = Gateway('OSA tests maintainer@example.test', SimpleNamespace(reserve=lambda: None),
                      opener=Opener(Response(raw,mime)), resolver=lambda _: None)
    receipt = gateway.get('https://www.sec.gov/synthetic-sheet')
    assert receipt['mime'] == mime and receipt['raw'] == raw


def test_retrieval_retains_cell_locator_and_extraction_limits(client, monkeypatch):
    from types import SimpleNamespace
    from app.services import retrieval
    # Isolate the evidence formatter; real review/rights are tested separately, never granted here.
    monkeypatch.setattr(retrieval, 'allowed', lambda *a, **kw: True)
    monkeypatch.setattr(retrieval, 'applies', lambda *a, **kw: True)
    monkeypatch.setattr(retrieval, 'dependencies_allowed', lambda *a, **kw: True)
    with client.app.state.db.Session() as db:
        source = Source(id='synthetic-sheet-evidence', title='UniqueSheetTest', publisher='Test',
            canonical_url='https://www.sec.gov/synthetic', version_label='fixture', kind='guidance',
            text='UniqueSheetTest original value 1250', reviewed=True, created_by='admin',
            policy={'intake_locator': "'Trial balance'!A2:E2", 'intake_spreadsheet': {
                'format':'xlsx', 'date_system':'1900', 'calculated':False, 'display_rendered':False}})
        db.add(source);db.commit()
        run = SimpleNamespace(context={'framework':'BOTH'}, document_ids=[], workspace_id='synthetic')
        rows = retrieval.search(db, run, 'UniqueSheetTest')
        row = next(r for r in rows if r['source_id'] == source.id)
        assert row['locator'].startswith("'Trial balance'!A2:E2")
        assert row['spreadsheet_extraction']['calculated'] is False
        assert row['spreadsheet_extraction']['date_system'] == '1900'
