"""Original engineering corpus only. Never interprets fixture attestations as real reviews."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from ..schemas import Strict


class FixtureSource(Strict):
    id: str = Field(pattern=r'^[a-z0-9_-]{1,36}$')
    title: str = Field(min_length=1,max_length=250)
    text: str = Field(min_length=1,max_length=3000)
    version: str = Field(min_length=1,max_length=80)
    kind: Literal['standard','rule','staff_guidance','original_commentary','company_practice'] = 'original_commentary'
    framework: Literal['US_GAAP','IFRS','AUDIT'] = 'US_GAAP'
    public_date: date = date(2020,1,1)
    effective_from: date = date(2021,1,1)
    effective_to: date | None = None
    audit_regimes: list[Literal['PCAOB','AICPA','GAGAS','NONE']] = Field(default_factory=list,max_length=4)
    admission: Literal['eligible','reference_only','revoked','technical_missing'] = 'eligible'


class FixtureDocument(Strict):
    id: str = Field(pattern=r'^[a-z0-9_-]{1,36}$')
    text: str = Field(min_length=1,max_length=3000)
    workspace: Literal['selected','other'] = 'selected'


class FixtureRelationship(Strict):
    source_id: str
    target_id: str
    relation: Literal['cites','amends','supersedes','defines','illustrates','compares']
    scope: str = Field(min_length=20,max_length=2000)


class NumericalCheck(Strict):
    label: str = Field(min_length=1,max_length=200)
    expected_decimal: str = Field(pattern=r'^-?[0-9]+(?:\.[0-9]+)?$')
    tolerance_decimal: str = Field(pattern=r'^[0-9]+(?:\.[0-9]+)?$')
    units: str = Field(min_length=1,max_length=80)


class ExpectedClaim(Strict):
    id: str = Field(pattern=r'^[a-z0-9_-]{1,80}$')
    statement: str = Field(min_length=10,max_length=2000)
    citation_source_ids: list[str] = Field(min_length=1,max_length=20)
    status: Literal['fictional_expectation_not_professional_adjudication']


class Case(Strict):
    id: str = Field(pattern=r'^[a-z0-9_-]{1,80}$')
    kind: Literal['engineering_fixture']
    professional_review_status: Literal['not_adjudicated']
    question: str = Field(min_length=10,max_length=3000)
    scenario: str = Field(min_length=10,max_length=2000)
    facts: list[str] = Field(min_length=1,max_length=30)
    framework: Literal['US_GAAP','IFRS'] = 'US_GAAP'
    entity_type: Literal['public','private','nonprofit'] = 'public'
    period_start: date = date(2025,1,1)
    period_end: date = date(2025,12,31)
    knowledge_date: date = date(2025,12,31)
    audit_regime: Literal['PCAOB','AICPA','GAGAS','NONE'] = 'NONE'
    sources: list[FixtureSource] = Field(default_factory=list,max_length=100)
    documents: list[FixtureDocument] = Field(default_factory=list,max_length=20)
    relationships: list[FixtureRelationship] = Field(default_factory=list,max_length=20)
    expected_source_ids: list[str] = Field(default_factory=list,max_length=100)
    expected_document_ids: list[str] = Field(default_factory=list,max_length=20)
    forbidden_source_ids: list[str] = Field(default_factory=list,max_length=100)
    forbidden_document_ids: list[str] = Field(default_factory=list,max_length=20)
    expected_claims: list[ExpectedClaim] = Field(default_factory=list,max_length=30)
    acceptable_alternatives: list[str] = Field(default_factory=list,max_length=30)
    missing_facts: list[str] = Field(default_factory=list,max_length=30)
    abstention_conditions: list[str] = Field(min_length=1,max_length=30)
    numerical_checks: list[NumericalCheck] = Field(default_factory=list,max_length=20)
    evidence_limit: int = Field(strict=True,ge=1,le=24)
    minimum_recall: float | None = Field(default=None,ge=0,le=1)

    @model_validator(mode='after')
    def bindings(self):
        if self.period_start>self.period_end:raise ValueError('Reversed reporting period')
        for rows,expected,forbidden in ((self.sources,self.expected_source_ids,self.forbidden_source_ids),
                                         (self.documents,self.expected_document_ids,self.forbidden_document_ids)):
            ids=[r.id for r in rows]
            if len(ids)!=len(set(ids)):raise ValueError('Duplicate fixture ID')
            if len(expected)!=len(set(expected)) or len(forbidden)!=len(set(forbidden)):raise ValueError('Duplicate expected/forbidden binding')
            if not set(expected+forbidden)<=set(ids) or set(expected)&set(forbidden):raise ValueError('Unknown or conflicting relevance binding')
        source_ids={s.id for s in self.sources}
        if len({c.id for c in self.expected_claims})!=len(self.expected_claims):raise ValueError('Duplicate expected claim ID')
        for claim in self.expected_claims:
            if not set(claim.citation_source_ids)<=source_ids:raise ValueError('Unknown expected claim citation')
        for edge in self.relationships:
            if edge.source_id not in source_ids or edge.target_id not in source_ids or edge.source_id==edge.target_id:
                raise ValueError('Invalid relationship endpoints')
        if self.minimum_recall is not None and not (self.expected_source_ids or self.expected_document_ids):
            raise ValueError('Recall threshold needs a nonempty relevant set')
        return self


class Corpus(Strict):
    version: str = Field(pattern=r'^retrieval-engineering-[0-9]+$')
    license: Literal['CC0-1.0']
    provenance: Literal['original fictional engineering fixtures; no accounting authority']
    split: Literal['development_regression_not_holdout']
    cases: list[Case] = Field(min_length=1,max_length=100)

    @model_validator(mode='after')
    def unique_cases(self):
        if len({c.id for c in self.cases})!=len(self.cases):raise ValueError('Duplicate case ID')
        return self
