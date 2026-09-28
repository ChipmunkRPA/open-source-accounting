"""Evaluation integrity and actual isolated retrieval; never accounting adjudication."""
from copy import deepcopy
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.evaluation.schema import Corpus
from app.evaluation.retrieval import load,evaluate,reviewer_packets

CORPUS=Path(__file__).resolve().parents[2]/'evaluation/retrieval-engineering-1.json'


@pytest.fixture(scope='module')
def measured():
    corpus=load(CORPUS)
    return corpus,evaluate(corpus)


def test_actual_fixture_metrics_preserve_gap_and_unmeasured_dimensions(measured):
    corpus,report=measured
    assert report['passed'] and report['case_count']==16 and report['professional_adjudications']==0
    rows={r['case_id']:r for r in report['cases']}
    assert rows['bounded-definition-gap']['recall']==0.5
    assert rows['bounded-definition-gap']['missed_units']==['source:definition']
    assert rows['definition-link']['recall']==1 and rows['definition-link']['relationship_count']==1
    assert rows['lexical-false-positive']['precision']==0.5 and rows['lexical-false-positive']['extra_units']==['source:irrelevant']
    assert rows['reference-only']['reference_only_units']==['source:reference']
    assert rows['tenant-isolation']['retrieved_body_units']==[]
    assert rows['selected-private-document']['retrieved_body_units']==['document:selected-doc']
    for row in report['cases']:
        assert not row['forbidden_units_retrieved']
        assert row['binding_checks']==row['binding_checks_passed']
        assert row['claim_support_accuracy'] is None and row['numerical_correctness'] is None
        assert row['model_abstention_accuracy'] is None and row['live_model_cost_usd'] is None
    assert report['code_sha256'] and report['model_calls']==0
    packets=reviewer_packets(corpus,report)
    assert packets['professional_review_records']==[] and len(packets['packets'])==16
    assert all(not p['release_threshold_approved'] for p in packets['packets'])


@pytest.mark.parametrize('change',['professional','unknown_expected','duplicate','conflicting','unknown_endpoint','claim_citation','date','extra'])
def test_corpus_rejects_invalid_or_invented_approval(change):
    raw=load(CORPUS).model_dump(mode='json');case=raw['cases'][0]
    if change=='professional':case['professional_review_status']='approved'
    elif change=='unknown_expected':case['expected_source_ids'].append('missing')
    elif change=='duplicate':raw['cases'].append(deepcopy(case))
    elif change=='conflicting':case['forbidden_source_ids']=['root']
    elif change=='unknown_endpoint':case['relationships'][0]['target_id']='missing'
    elif change=='claim_citation':case['expected_claims'][0]['citation_source_ids']=['missing']
    elif change=='date':case['period_start']='2026-01-01'
    else:case['operator_database_url']='postgresql://operator'
    with pytest.raises(ValidationError):Corpus.model_validate(raw)


def test_report_corpus_mismatch_cannot_create_review_packet(measured):
    corpus,report=measured
    with pytest.raises(ValueError):reviewer_packets(corpus,{**report,'corpus_sha256':'0'*64})


def test_regression_is_retained_not_silently_dropped():
    raw=load(CORPUS).model_dump(mode='json')
    raw['cases']=[raw['cases'][1]]
    raw['cases'][0]['minimum_recall']=1
    report=evaluate(Corpus.model_validate(raw))
    assert not report['passed']
    assert report['cases'][0]['failures']==['fixture_recall_regression']
    assert report['cases'][0]['recall']==0.5


def test_comparison_preserves_version_and_detects_lost_recall(measured):
    from app.evaluation.retrieval import compare_reports
    _,report=measured
    identical=compare_reports(report,deepcopy(report));assert identical['passed']
    changed=deepcopy(report);changed['cases'][0]['recall']=0.5
    delta=compare_reports(report,changed)
    assert not delta['passed']
    assert any('recall_decreased_or_unmeasured' in r['regressions'] for r in delta['cases'])
    with pytest.raises(ValueError):compare_reports(report,{**report,'corpus_sha256':'0'*64})
    changed=deepcopy(report);changed['cases'].pop()
    with pytest.raises(ValueError):compare_reports(report,changed)


def test_failed_case_is_preserved_and_runner_makes_no_network_or_provider_calls(monkeypatch):
    import socket
    from app.services import retrieval
    def forbidden(*a,**kw):raise AssertionError('Network/provider call forbidden in offline evaluation')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    monkeypatch.setattr('app.providers.gemini.get_model',forbidden)
    corpus=load(CORPUS)
    assert evaluate(corpus)['passed']
    monkeypatch.setattr(retrieval,'search',lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('Synthetic private fixture contents')))
    report=evaluate(corpus)
    assert not report['passed'] and len(report['cases'])==16
    assert all(r['execution_status']=='error' and r['failures']==['execution_error'] for r in report['cases'])
    assert 'Synthetic private fixture contents' not in str(report)
