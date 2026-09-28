"""Execute actual retrieval in isolated SQLite or an explicitly confirmed empty local PostgreSQL test database."""
import json
import tempfile
import time
import sys
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from ..db import Database
from ..models import User, Workspace, Membership, Source, Document, Run, Evidence, now
from ..sec_core.core import canonical, digest
from ..editorial_schemas import EditorialDecision
from ..applicability_schemas import ApplicabilityDecision
from ..authority_schemas import RelationshipProposal, RelationshipDecision
from ..services import rights, editorial, applicability, authority, citation_lookup, retrieval, authority_evidence, source_search
from .schema import Corpus

VERSION = 'retrieval-evaluation-2'
NOTICE = 'Original fictional engineering fixture. Simulated review only; no actual professional approval.'


def load(path):
    raw = Path(path).read_bytes()
    if len(raw)>2000000:raise ValueError('Evaluation corpus exceeds 2 MB')
    return Corpus.model_validate_json(raw)


def endpoint(source):
    c=citation_lookup.descriptor(source,0,len(source.text))
    return {k:c[k] for k in ('source_id','revision','locator','character_start','character_end','passage_text_sha256')}


def prepare(db,case):
    # These fixed identities and attestations exist only in a new temporary fixture DB.
    db.add_all([User(id='fixture-author'),User(id='fixture-reviewer'),User(id='fixture-reader')]);db.flush()
    db.add_all([Workspace(id='selected',name='Synthetic selected',owner_id='fixture-reader'),
                Workspace(id='other',name='Synthetic other',owner_id='fixture-author')]);db.flush()
    db.add(Membership(workspace_id='selected',user_id='fixture-reader',role='owner'));db.flush()
    for fixture in case.sources:
        s=Source(id=fixture.id,title=fixture.title,text=fixture.text,publisher='Fictional engineering corpus',
            kind=fixture.kind,framework=fixture.framework,version_label=fixture.version,created_by='fixture-author',reviewed=True,
            policy={'basis':'original','commercial_use':True,'content_sha256':digest(fixture.text),'content_reference_ids':[],
                    **{op:True for op in rights.OPERATIONS}})
        db.add(s);db.flush();rights.record_approval(s,'fixture-reviewer');db.commit()
        if fixture.admission!='technical_missing':
            editorial.record(db,s,EditorialDecision(expected_policy_version=s.policy_version,
                expected_review_revision=editorial.revision(s),content_sha256=digest(s.text),decision='approved',
                review_scope=NOTICE,review_note=NOTICE,evidence_ref='ev_synthetic_engineering',evidence_sha256=digest(NOTICE),
                expires_at=now()+3600,confirm_actual_review_performed=True),'fixture-reviewer')
            applicability.record(db,s,ApplicabilityDecision(expected_policy_version=s.policy_version,
                expected_review_revision=editorial.revision(s),decision='approved',issued_at=fixture.public_date,
                publicly_available_at=fixture.public_date,effective_from=fixture.effective_from,effective_to=fixture.effective_to,
                confirm_open_ended=fixture.effective_to is None,frameworks=[case.framework] if s.framework=='AUDIT' else [s.framework],
                entity_types=['public','private','nonprofit'],audit_regimes=fixture.audit_regimes,
                review_scope=NOTICE,review_note=NOTICE,evidence_ref='ev_synthetic_engineering',evidence_sha256=digest(NOTICE),
                expires_at=now()+3600,confirm_actual_applicability_review=True),'fixture-reviewer')
        if fixture.admission=='technical_missing':
            s.policy={**s.policy,'requires_technical_review':True};rights.record_approval(s,'fixture-reviewer')
        if fixture.admission=='reference_only':
            s.policy={**s.policy,'model_input':False,'embed':False};rights.record_approval(s,'fixture-reviewer')
        if fixture.admission=='revoked':s.enabled=False
        db.commit()
    for f in case.documents:
        db.add(Document(id=f.id,workspace_id=f.workspace,uploaded_by='fixture-author',name='Synthetic private document',
            mime='text/plain',size=len(f.text.encode()),checksum=digest(f.text),object_key='synthetic-not-stored',
            chunks=[{'locator':'Synthetic paragraph 1','text':f.text}],authorization_basis='own_original',scan_status='synthetic'))
    db.commit()
    for f in case.relationships:
        edge=authority.propose(db,RelationshipProposal(source=endpoint(db.get(Source,f.source_id)),
            target=endpoint(db.get(Source,f.target_id)),relation=f.relation,scope=f.scope,
            evidence_ref='ev_synthetic_engineering',evidence_sha256=digest(NOTICE)),'fixture-author')
        authority.decide(db,edge.id,RelationshipDecision(expected_revision=edge.revision,expected_sequence=0,decision='approved',
            review_note=NOTICE,evidence_ref='ev_synthetic_engineering',evidence_sha256=digest(NOTICE),
            expires_at=now()+3600,confirm_actual_review_performed=True),'fixture-reviewer')
    context={k:getattr(case,k).isoformat() if hasattr(getattr(case,k),'isoformat') else getattr(case,k) for k in
             ('framework','entity_type','period_start','period_end','knowledge_date','audit_regime')}
    run=Run(workspace_id='selected',user_id='fixture-reader',workflow='deep_research',question=case.question,
        context=context,document_ids=[f.id for f in case.documents])
    db.add(run);db.commit();return run


def resource(row):
    return 'source:'+row['source_id'] if row['source_id'] else 'document:'+row['document_id']


def evaluate_case(db,case):
    run=prepare(db,case)
    indexed=[]
    if db.bind.dialect.name=='postgresql':
        for fixture in case.sources:
            source=db.get(Source,fixture.id)
            if source_search.index_allowed(source):
                entry=source_search.rebuild(db,source,source_search.revision(source),'fixture-reviewer')
                indexed.append({'source_id':source.id,'index_revision':entry.revision,'index_version':entry.index_version})
        db.commit()
    context=rights.runtime_context(db,run)
    started=time.perf_counter()
    pool=retrieval.search(db,run,case.question,case.evidence_limit,rights_context=context)
    doc_first=[next((r for r in pool if r['document_id']==did),None) for did in run.document_ids]
    doc_first=[r for r in doc_first if r]
    rows,plans=authority_evidence.select_evidence(db,run,doc_first+[r for r in pool if r not in doc_first],case.evidence_limit,context=context)
    stored=[]
    for row in rows:
        e=Evidence(run_id=run.id,**row);db.add(e);db.flush();stored.append({'id':e.id,**row})
    authority_evidence.persist(db,run,plans,stored)
    relationships=authority_evidence.packets(db,run,context=context)
    duration=(time.perf_counter()-started)*1000
    body=[r for r in stored if r.get('text') and r['access']!='reference_only']
    found={resource(r) for r in body}
    expected={'source:'+x for x in case.expected_source_ids}|{'document:'+x for x in case.expected_document_ids}
    forbidden={'source:'+x for x in case.forbidden_source_ids}|{'document:'+x for x in case.forbidden_document_ids}
    valid=[]
    for row in body:
        e=db.get(Evidence,row['id']);valid.append(rights.evidence_allowed(db,e,context=context))
    recall=len(found&expected)/len(expected) if expected else None
    precision=len(found&expected)/len(found) if found else None
    failures=[]
    if found&forbidden:failures.append('forbidden_body_retrieved')
    if not all(valid):failures.append('invalid_evidence_binding')
    if case.minimum_recall is not None and recall<case.minimum_recall:failures.append('fixture_recall_regression')
    return {'case_id':case.id,'case_sha256':digest(canonical(case.model_dump(mode='json'))),
        'execution_status':'completed','kind':case.kind,'professional_review_status':case.professional_review_status,
        'source_records':len(case.sources),'document_records':len(case.documents),'authorized_indexes':indexed,
        'source_versions':[{'source_id':s.id,'version':s.version,'text_sha256':digest(s.text)} for s in case.sources],
        'observed_source_revisions':[{'source_id':s.id,'revision':citation_lookup.revision(db.get(Source,s.id))} for s in case.sources],
        'expected_relevant_units':sorted(expected),'retrieved_body_units':sorted(found),
        'missed_units':sorted(expected-found),'extra_units':sorted(found-expected),'forbidden_units_retrieved':sorted(found&forbidden),
        'reference_only_units':sorted({resource(r) for r in stored if r['access']=='reference_only'}),
        'precision':precision,'recall':recall,'binding_checks':len(valid),'binding_checks_passed':sum(valid),
        'observed_relationships':relationships,'relationship_count':len(relationships),'evidence_count':len(stored),'retrieval_ms':round(duration,3),
        'evidence':[{'resource':resource(r),'locator':r['locator'],'text_sha256':digest(r['text']) if r['text'] else None,
                     'access':r['access'],'extraction_context':r['extraction_context']} for r in stored],
        'failures':failures,'claim_support_accuracy':None,'numerical_correctness':None,'model_abstention_accuracy':None,
        'live_model_calls':0,'live_model_cost_usd':None}


@contextmanager
def isolated_sqlite():
    with tempfile.TemporaryDirectory(prefix='osa-engineering-eval-') as root:
        @contextmanager
        def case_database(index):
            database=Database('sqlite:///'+str(Path(root)/f'{index}.db'))
            try:
                database.create_all()
                yield database
            finally:database.engine.dispose()
        yield case_database,sqlite3.sqlite_version


def evaluate(corpus, *, postgres_url=None):
    from .postgres import isolated_postgres
    results=[]
    manager=isolated_postgres(postgres_url) if postgres_url else isolated_sqlite()
    with manager as (factory,database_version):
        for index,case in enumerate(corpus.cases):
            with factory(index) as database:
                try:
                    with database.Session() as db:results.append(evaluate_case(db,case))
                except Exception as error:
                    # Preserve a failed observation without logging fixture bodies or raw exception text.
                    results.append({'case_id':case.id,'case_sha256':digest(canonical(case.model_dump(mode='json'))),
                        'execution_status':'error','error_type':type(error).__name__,'failures':['execution_error'],
                        'professional_review_status':'not_adjudicated','precision':None,'recall':None,
                        'binding_checks':0,'binding_checks_passed':0,'forbidden_units_retrieved':[],
                        'missed_units':[],'retrieval_ms':None,'claim_support_accuracy':None,
                        'numerical_correctness':None,'model_abstention_accuracy':None,'live_model_calls':0,'live_model_cost_usd':None})
    return {'version':VERSION,'corpus_version':corpus.version,'corpus_sha256':digest(canonical(corpus.model_dump(mode='json'))),
        'mode':'local_postgres_indexed_engineering_fixtures' if postgres_url else 'offline_sqlite_actual_retrieval_engineering_fixtures','split':corpus.split,'case_count':len(results),
        'python_version':sys.version.split()[0],'database_version':database_version,'database_engine':'postgresql' if postgres_url else 'sqlite',
        'code_sha256':{str(p.relative_to(Path(__file__).parents[2])):digest(p.read_bytes())
                       for p in sorted(Path(__file__).parents[1].rglob('*.py'))},
        'professional_adjudications':0,'model_calls':0,'workflow_executions':0,'source_search_version':source_search.VERSION,
        'relationship_version':authority_evidence.VERSION,'precision_unit':'unique source/document with retained body; reference-only excluded',
        'latency_scope':'retrieval, relationship expansion, evidence persistence and validation; excludes fixture setup, authorized index builds and model work',
        'limitations':['Fictional development fixtures, not accounting truth or a held-out benchmark.',
            ('Small PostgreSQL indexed corpus; not a scale or production performance claim.' if postgres_url else 'SQLite development fallback only; no PostgreSQL ranking measured.'),
            'No embedding, live model, latency SLO, cost or professional claim support measured.',
            'A valid citation binding does not prove entailment. No numerical or model-abstention score is inferred.',
            'Maximum evidence bounds may intentionally miss relevant material; per-case omissions remain visible.'],
        'passed':not any(r['failures'] for r in results),'cases':results}


def write_report(corpus_path,output, *, postgres_url=None):
    result=evaluate(load(corpus_path),postgres_url=postgres_url)
    Path(output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result


def reviewer_packets(corpus, report):
    """Draft inspection inputs, not approval imports. No real identities/attestations synthesized."""
    if report['corpus_sha256'] != digest(canonical(corpus.model_dump(mode='json'))):
        raise ValueError('Report and corpus versions differ')
    observations={row['case_id']:row for row in report['cases']}
    return {'version':VERSION,'status':'draft_not_professionally_adjudicated',
        'corpus_sha256':report['corpus_sha256'],'professional_review_records':[],
        'packets':[{'case':case.model_dump(mode='json'),'observed':observations[case.id],
                    'reviewer_questions':['Are the permitted source versions and exact citations sufficient?',
                        'Which claims are supported, contradicted, or unresolved, and why?',
                        'Are exceptions, alternatives, missing facts and historical applicability complete?',
                        'What actual qualifications, independence and restricted evidence support any future adjudication?'],
                    'release_threshold_approved':False} for case in corpus.cases]}


def compare_reports(baseline, current, *, cross_engine=False):
    """Same-corpus development regression comparison; latency is descriptive, never an SLO."""
    if cross_engine:
        if {baseline.get('database_engine'),current.get('database_engine')}!={'sqlite','postgresql'}:
            raise ValueError('Cross-engine comparison requires SQLite and PostgreSQL observations')
        if baseline.get('code_sha256')!=current.get('code_sha256'):
            raise ValueError('Cross-engine comparison requires the same application code')
    for key in ('version','corpus_sha256','split','precision_unit')+(() if cross_engine else ('mode',)):

        if baseline.get(key)!=current.get(key):raise ValueError('Reports are not comparable: '+key)
    def by_case(report):
        cases=report['cases'];indexed={r['case_id']:r for r in cases}
        if len(indexed)!=len(cases) or report['case_count']!=len(cases):raise ValueError('Report case membership is inconsistent')
        return indexed
    before,after=by_case(baseline),by_case(current)
    if set(before)!=set(after):raise ValueError('Report cases changed')
    changes=[]
    for cid in sorted(before):
        a,b=before[cid],after[cid]
        if a['case_sha256']!=b['case_sha256']:raise ValueError('Case version changed')
        regressions=[]
        deltas={}
        for metric in ('precision','recall'):
            old,new=a[metric],b[metric]
            deltas[metric]=new-old if old is not None and new is not None else None
            if old is not None and (new is None or new<old):regressions.append(metric+'_decreased_or_unmeasured')
        if set(b['forbidden_units_retrieved'])-set(a['forbidden_units_retrieved']):regressions.append('new_forbidden_body')
        if b['binding_checks']-b['binding_checks_passed']>a['binding_checks']-a['binding_checks_passed']:regressions.append('new_invalid_binding')
        if set(b['failures'])-set(a['failures']):regressions.append('new_case_failure')
        changes.append({'case_id':cid,'metric_deltas':deltas,'retrieval_ms_delta':round(b['retrieval_ms']-a['retrieval_ms'],3) if a['retrieval_ms'] is not None and b['retrieval_ms'] is not None else None,
            'new_missed_units':sorted(set(b['missed_units'])-set(a['missed_units'])),'regressions':regressions})
    return {'version':VERSION,'corpus_sha256':current['corpus_sha256'],'kind':'cross_engine_observation_not_release_approval' if cross_engine else 'development_regression_not_release_approval',
        'baseline_engine':baseline.get('database_engine'),'current_engine':current.get('database_engine'),
        'baseline_sha256':digest(canonical(baseline)),'current_sha256':digest(canonical(current)),
        'professional_adjudications':0,'passed':current['passed'] and not any(c['regressions'] for c in changes),'cases':changes}
