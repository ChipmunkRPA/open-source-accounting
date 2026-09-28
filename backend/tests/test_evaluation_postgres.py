"""Actual local PostgreSQL, dedicated EMPTY test DB only. No operator corpus."""
import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine,text
from app.evaluation.postgres import isolated_postgres,validated_url,require_empty
from app.evaluation.retrieval import load,evaluate


@pytest.fixture
def evaluation_url():
    value=os.environ.get('OSA_EVALUATION_POSTGRES_URL')
    if not value:pytest.skip('Dedicated empty local PostgreSQL evaluation DB not supplied')
    validated_url(value)
    return value


def test_actual_indexed_retrieval_and_cleanup(evaluation_url):
    corpus=load(Path(__file__).resolve().parents[2]/'evaluation/retrieval-engineering-1.json')
    report=evaluate(corpus,postgres_url=evaluation_url)
    assert report['passed'],[(c['case_id'],c['failures']) for c in report['cases']]
    assert report['database_engine']=='postgresql' and report['case_count']==16
    rows={c['case_id']:c for c in report['cases']}
    assert rows['definition-link']['relationship_count']==1
    assert rows['bounded-definition-gap']['recall']==0.5
    assert rows['lexical-false-positive']['precision']==0.5
    for cid in ('reference-only','revoked-rights','missing-technical-review'):
        assert rows[cid]['authorized_indexes']==[]
    assert sum(len(c['authorized_indexes']) for c in report['cases'])==20
    assert not any(c['forbidden_units_retrieved'] for c in report['cases'])
    engine=create_engine(evaluation_url)
    try:
        with engine.connect() as connection:require_empty(connection)
    finally:engine.dispose()


def test_preexisting_objects_are_refused_and_preserved(evaluation_url):
    engine=create_engine(evaluation_url)
    try:
        with engine.begin() as connection:
            require_empty(connection)
            connection.execute(text('CREATE TABLE public.synthetic_preserve (value integer)'))
            connection.execute(text('INSERT INTO public.synthetic_preserve VALUES (42)'))
        with pytest.raises(ValueError,match='not empty'):
            with isolated_postgres(evaluation_url):pass
        with engine.begin() as connection:
            assert connection.execute(text('SELECT value FROM public.synthetic_preserve')).scalar()==42
            connection.execute(text('DROP TABLE public.synthetic_preserve'))
    finally:engine.dispose()


def test_concurrent_evaluation_ownership_is_rejected(evaluation_url):
    with isolated_postgres(evaluation_url):
        with pytest.raises(ValueError,match='Another evaluation'):
            with isolated_postgres(evaluation_url):pass


def test_case_failure_cleans_only_its_generated_schema(evaluation_url):
    with pytest.raises(RuntimeError,match='synthetic failure'):
        with isolated_postgres(evaluation_url) as (factory,_):
            with factory(0):raise RuntimeError('synthetic failure')
    with isolated_postgres(evaluation_url):pass
