"""Synthetic linkage tests; parser/applicability stubs are not real source approvals."""
import pytest
from sqlalchemy import select
from app.models import Source, Run, Evidence
from app.services import spreadsheet_dependencies as deps, spreadsheet_context as ctx, rights
from app.services.output_rights import run_sources


@pytest.fixture
def corpus(client, monkeypatch):
    from app.services import applicability, parser_review, retrieval
    # Isolate dependency/operation checks. Actual immutable reviews have their own regression suites.
    original_current, original_applies = applicability.current, applicability.applies
    monkeypatch.setattr(applicability, 'current', lambda source: {'synthetic': True} if source.id.startswith('companion-') else original_current(source))
    monkeypatch.setattr(applicability, 'applies', lambda source, context: True if source.id.startswith('companion-') else original_applies(source,context))
    monkeypatch.setattr(retrieval, 'applies', applicability.applies)
    monkeypatch.setattr(parser_review, 'current', lambda source: True)
    with client.app.state.db.Session() as db:
        parent = Source(id='companion-parent', title='Synthetic workbook', publisher='Tests',
            canonical_url='https://example.test/book', version_label='fixture', kind='guidance',
            text='Original synthetic workbook', reviewed=True, created_by='admin',
            policy={'basis':'original','commercial_use':True, **{op:True for op in rights.OPERATIONS}})
        db.add(parent); db.flush(); rights.record_approval(parent, 'synthetic')
        sources = []
        for sid, sheet, meta, text in [
            ('root','S',{'cells':[{'cell':'A1','value':'1250'}]},'Amount 1250'),
            ('note','S',{'comment':{'cell':'A1'}},'Amounts exclude disputed balances.'),
            ('other','T',{'comment':{'cell':'A1'}},'Other-sheet information'),
            ('table','S',{'table':{'range':'A1:B5'}},'Amounts in USD thousands')]:
            source = Source(id='companion-'+sid, title=sid, publisher='Tests',
                canonical_url='https://example.test/book', version_label='fixture', kind='guidance',
                text=text, reviewed=True, created_by='admin', policy={
                    'basis':'original','commercial_use':True, **{op:True for op in rights.OPERATIONS},
                    'intake_parent_id':parent.id,'intake_parent_policy_version':parent.policy_version,
                    'intake_extraction_id':'synthetic-extraction','intake_artifact_id':'synthetic-artifact',
                    'intake_locator':sheet+'!A1 '+sid,
                    'intake_spreadsheet':{'format':'xlsx','sheet':sheet,**meta}})
            db.add(source);db.flush();rights.record_approval(source,'synthetic');sources.append(source)
        run=Run(workspace_id='demo-workspace',user_id='demo',workflow='deep_research',
                question='Synthetic amount',context={'framework':'US_GAAP'},document_ids=[])
        db.add(run);db.commit()
        yield db,run,sources


def row(source):
    return {'source_id':source.id,'document_id':None,'title':source.title,
        'locator':source.policy['intake_locator']+' paragraph 1','text':source.text,
        'access':'secondary_text_reviewed','source_kind':source.kind,'policy_version':source.policy_version,
        'extraction_context':ctx.source_context(source)}


def selected(db,run,sources,limit=12):
    return deps.select_with_companions(db,run,[row(sources[0])],limit,context=rights.runtime_context(db,run))


def persisted(db,run,rows):
    records=[Evidence(run_id=run.id,**r) for r in rows]
    db.add_all(records);db.commit()
    return records


def test_separate_citations_and_output_lineage(corpus):
    db,run,sources=corpus
    rows=selected(db,run,sources)
    assert [r['source_id'] for r in rows]==['companion-root','companion-note','companion-table']
    assert rows[0]['extraction_context']['context_partial']
    assert 'Amounts exclude' not in str(rows[0]['extraction_context'])
    records=persisted(db,run,rows)
    assert all(rights.evidence_allowed(db,e) for e in records)
    assert {'companion-parent','companion-root','companion-note','companion-table'} <= {s.id for s in run_sources(db,run)}


@pytest.mark.parametrize('change',['rights','disable','delete_evidence','text','locator','metadata','review','cycle'])
def test_companion_changes_invalidate_root(corpus,change):
    db,run,sources=corpus
    records=persisted(db,run,selected(db,run,sources))
    root,note=records[:2];target=sources[1]
    assert rights.evidence_allowed(db,root,'export')
    if change=='rights':
        target.policy={**target.policy,'export':False};rights.record_approval(target,'synthetic')
    elif change=='disable':target.enabled=False
    elif change=='delete_evidence':db.delete(note)
    elif change=='text':target.text='Different qualification'
    elif change=='locator':target.policy={**target.policy,'intake_locator':'changed'}
    elif change=='metadata':target.policy={**target.policy,'intake_spreadsheet':{'format':'xlsx','sheet':'T','comment':{}}}
    elif change=='review':target.policy_version+=1
    elif change=='cycle':note.extraction_context=deps.packet(target,[deps.binding(sources[0])])
    db.commit()
    assert not rights.evidence_allowed(db,root,'export')


@pytest.mark.parametrize('gate',['rights','reviewed','parser','applicability','scope','extraction','artifact','parent','oversize'])
def test_companions_require_independent_gates(corpus,monkeypatch,gate):
    from app.services import parser_review, applicability
    db,run,sources=corpus
    note=sources[1]
    if gate=='rights':note.policy={**note.policy,'model_input':False};rights.record_approval(note,'synthetic')
    elif gate=='reviewed':note.reviewed=False
    elif gate=='parser':monkeypatch.setattr(parser_review,'current',lambda s:s.id!=note.id)
    elif gate=='applicability':monkeypatch.setattr(applicability,'applies',lambda s,c:s.id!=note.id)
    elif gate=='scope':note.policy={**note.policy,'scope':{'region':['unapproved']}};rights.record_approval(note,'synthetic')
    elif gate in {'extraction','artifact','parent'}:note.policy={**note.policy,'intake_'+gate+'_id':'other'}
    elif gate=='oversize':note.text='q'*3001;rights.record_approval(note,'synthetic')
    db.commit()
    rows=selected(db,run,sources)
    assert note.id not in {r['source_id'] for r in rows}
    assert note.id not in str(rows[0]['extraction_context'])


def test_total_budget_and_document_priority(corpus):
    db,run,sources=corpus
    doc={'source_id':None,'document_id':'selected-private-document','locator':'p1','text':'private'}
    rows=deps.select_with_companions(db,run,[doc,row(sources[0])],3,context=rights.runtime_context(db,run))
    assert len(rows)==3 and rows[0]==doc
    assert rows[1]['extraction_context']['context_partial']
    assert len(rows[1]['extraction_context']['source_dependencies']['bindings'])==1
    rows=selected(db,run,sources,1)
    assert len(rows)==1 and 'source_dependencies' not in rows[0]['extraction_context']


def test_duplicate_companion_evidence_is_ambiguous(corpus):
    db,run,sources=corpus
    rows=selected(db,run,sources);records=persisted(db,run,rows)
    db.add(Evidence(run_id=run.id,**rows[1]));db.commit()
    assert not rights.evidence_allowed(db,records[0])


def test_context_packet_budget(corpus,monkeypatch):
    db,run,sources=corpus
    from app.sec_core.core import canonical
    monkeypatch.setattr(ctx,'MAX_CONTEXT_CHARS',1000)
    rows=selected(db,run,sources)
    assert len(rows)==2
    assert len(canonical(rows[0]['extraction_context']))<=1000
    assert rows[0]['extraction_context']['context_partial']


def test_mock_agent_retains_companions_and_revocation_blocks_artifact(client,corpus):
    from conftest import complete_run
    from fastapi import HTTPException
    db,_,sources=corpus
    result=complete_run(client,question='Research Amount 1250 in the synthetic workbook.')
    db.expire_all()
    run=db.get(Run,result['id'])
    records=list(db.scalars(select(Evidence).where(Evidence.run_id==run.id)))
    root=next(e for e in records if e.source_id==sources[0].id and e.extraction_context.get('source_dependencies'))
    assert rights.evidence_allowed(db,root)
    target=db.get(Source,'companion-note');target.enabled=False;db.commit()
    with pytest.raises(HTTPException) as exc:
        rights.run_artifact_access(db,run,'export')
    assert exc.value.status_code==409


@pytest.mark.parametrize('value',[None, [], {'version':deps.VERSION,'bindings':[{'source_id':[]}]}])
def test_malformed_dependency_snapshots_fail_closed(corpus,value):
    db,run,sources=corpus
    records=persisted(db,run,selected(db,run,sources))
    root=records[0]
    root.extraction_context={**root.extraction_context,'source_dependencies':value};db.commit()
    assert not rights.evidence_allowed(db,root)
