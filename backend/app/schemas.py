"""Shared validated HTTP and model contracts; unknown fields never grant capabilities."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class WorkspaceCreate(Strict):
    name: str = Field(min_length=1, max_length=120)


class MemberAdd(Strict):
    email: str = Field(min_length=3, max_length=320)
    role: Literal['editor', 'reviewer', 'viewer'] = 'reviewer'


class ChatCreate(Strict):
    title: str = Field(default='New chat', max_length=160)


class ChatSend(Strict):
    message: str = Field(min_length=1, max_length=8000)


class Context(Strict):
    framework: Literal['US_GAAP', 'IFRS', 'BOTH', 'UNKNOWN'] = 'US_GAAP'
    entity_type: Literal['public', 'private', 'nonprofit', 'unknown'] = 'unknown'
    audit_regime: Literal['PCAOB', 'AICPA', 'GAGAS', 'NONE', 'UNKNOWN'] = 'UNKNOWN'
    period_start: date | None = None
    period_end: date | None = None
    knowledge_date: date | None = None
    early_adoption: str = Field(default='Not specified', max_length=1000)
    industry: str = Field(default='', max_length=100)

    @model_validator(mode='after')
    def dates(self):
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError('Reporting period start must not follow its end.')
        return self


class Fact(Strict):
    text: str = Field(min_length=1, max_length=2000)
    status: Literal['confirmed', 'assumption', 'unknown'] = 'unknown'


class RunCreate(Strict):
    workspace_id: str
    workflow: str = 'deep_research'
    question: str = Field(min_length=10, max_length=8000)
    context: Context = Field(default_factory=Context)
    facts: list[Fact] = Field(default_factory=list, max_length=50)
    document_ids: list[str] = Field(default_factory=list, max_length=10)
    inputs: dict = Field(default_factory=dict)

    @field_validator('document_ids')
    @classmethod
    def unique_documents(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('Each selected document must be unique.')
        return value

    @field_validator('inputs')
    @classmethod
    def input_size(cls, value):
        import json
        if len(json.dumps(value)) > 50000:
            raise ValueError('Task inputs exceed the 50,000-character limit.')
        return value


class RunUpdate(Strict):
    expected_revision: int = Field(ge=1)
    facts: list[Fact] = Field(max_length=50)
    context: Context


class RunStart(Strict):
    expected_revision: int = Field(ge=1)
    confirm_scope: Literal[True]


class FollowUp(Strict):
    question: str = Field(min_length=10, max_length=8000)


class Plan(Strict):
    issues: list[str] = Field(max_length=12)
    missing_questions: list[str] = Field(max_length=12)
    proposed_queries: list[str] = Field(max_length=5)
    scope: str = Field(max_length=2000)


class Claim(Strict):
    id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=2500)
    basis: Literal['source', 'inference', 'user_fact', 'calculation']
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)


class Section(Strict):
    heading: str = Field(max_length=150)
    body: str = Field(max_length=12000)
    claim_ids: list[str] = Field(default_factory=list, max_length=30)


class ResultTable(Strict):
    title: str = Field(max_length=180)
    columns: list[str] = Field(min_length=1, max_length=12)
    rows: list[list[str]] = Field(max_length=100)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode='after')
    def consistent_rows(self):
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError('All table rows must match the column count.')
        if any(len(cell) > 3000 for row in self.rows for cell in row):
            raise ValueError('Table cell too long.')
        return self


class Analysis(Strict):
    title: str = Field(max_length=200)
    summary: str = Field(max_length=4000)
    sections: list[Section] = Field(min_length=1, max_length=20)
    claims: list[Claim] = Field(default_factory=list, max_length=60)
    tables: list[ResultTable] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(min_length=1, max_length=30)
    open_questions: list[str] = Field(default_factory=list, max_length=30)


class Finding(Strict):
    claim_id: str = Field(max_length=80)
    severity: Literal['warning', 'block']
    reason: str = Field(max_length=1500)


class Verification(Strict):
    findings: list[Finding] = Field(default_factory=list, max_length=60)
    limitations: list[str] = Field(default_factory=list, max_length=12)


class MemoCreate(Strict):
    workspace_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default='', max_length=200000)


class MemoUpdate(Strict):
    expected_revision: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=200000)


class ReviewCreate(Strict):
    expected_revision: int = Field(ge=1)
    note: str = Field(default='', max_length=3000)


class OutputControl(Strict):
    mode: Literal['bounded', 'unrestricted']
    group_id: str = Field(min_length=1, max_length=120, pattern=r'^[A-Za-z0-9_.:-]+$')
    max_chars_per_response: StrictInt | None = Field(default=None, ge=0, le=2_000_000_000)
    max_chars_total: StrictInt | None = Field(default=None, ge=0, le=2_000_000_000)

    @model_validator(mode='after')
    def validate_limits(self):
        if self.mode == 'bounded':
            if self.max_chars_per_response is None or self.max_chars_total is None:
                raise ValueError('Bounded output requires reviewed per-response and cumulative limits.')
            if self.max_chars_per_response > self.max_chars_total:
                raise ValueError('Response limit cannot exceed cumulative limit.')
        elif self.max_chars_per_response is not None or self.max_chars_total is not None:
            raise ValueError('Unrestricted output cannot specify limits.')
        return self


class SourcePolicy(Strict):
    basis: Literal['original', 'government_work', 'license', 'reviewed_use', 'reference_only']
    commercial_use: StrictBool = False
    acquire: StrictBool = False
    store_raw: StrictBool = False
    extract: StrictBool = False
    model_input: StrictBool = False
    store_text: StrictBool = False
    display_full: StrictBool = False
    quote: StrictBool = False
    export: StrictBool = False
    embed: StrictBool = False
    redistribute: StrictBool = False
    train: StrictBool = False
    effective_at: StrictInt | None = Field(default=None, ge=0)
    expires_at: StrictInt | None = Field(default=None, ge=0)
    license_evidence_ref: str | None = Field(default=None, max_length=250)
    attribution: str = Field(default='', max_length=2000)
    output_control: OutputControl | None = None
    scope: dict[Literal['route', 'workspace_id', 'seat_id', 'audience', 'provider', 'region', 'retention', 'jurisdiction'], list[str]] = Field(default_factory=dict)
    review_note: str = Field(min_length=10, max_length=3000)

    @model_validator(mode='after')
    def validate_rights(self):
        from .services.rights import OPERATIONS
        if self.effective_at is not None and self.expires_at is not None and self.effective_at >= self.expires_at:
            raise ValueError('Rights expiry must follow the effective date.')
        if any(not values or any(not value.strip() for value in values) for values in self.scope.values()):
            raise ValueError('Scope restrictions require explicit nonempty values.')
        if self.basis == 'reference_only' and any(getattr(self, op) for op in OPERATIONS):
            raise ValueError('Reference-only metadata cannot grant body operations.')
        if self.basis in {'license', 'reviewed_use'} and any(getattr(self, op) for op in OPERATIONS) and not self.license_evidence_ref:
            raise ValueError('Operation grants require a restricted license/review evidence reference.')
        return self


class RightsApproval(Strict):
    expected_policy_version: int = Field(ge=1)
    expected_rights_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirm_actual_rights_review: Literal[True]


class SourceCreate(Strict):
    title: str = Field(min_length=1, max_length=250)
    publisher: str = Field(min_length=1, max_length=160)
    canonical_url: str = Field(default='', max_length=1500)
    kind: Literal['standard', 'rule', 'staff_guidance', 'company_example', 'original_commentary', 'reference']
    framework: Literal['US_GAAP', 'IFRS', 'BOTH', 'AUDIT'] = 'US_GAAP'
    version_label: str = Field(default='1', max_length=80)
    effective_from: date | None = None
    effective_to: date | None = None
    text: str | None = Field(default=None, max_length=200000)
    policy: SourcePolicy

    @model_validator(mode='after')
    def validate_source(self):
        from urllib.parse import urlparse
        if self.canonical_url and (urlparse(self.canonical_url).scheme != 'https' or
                                   not urlparse(self.canonical_url).hostname):
            raise ValueError('Source links must use HTTPS.')
        if self.text and not self.policy.store_text:
            raise ValueError('This policy does not permit storage of the submitted source text.')
        if self.policy.basis == 'reference_only' and self.text:
            raise ValueError('Reference-only sources cannot contain source text.')
        if self.text and self.policy.basis in {'license', 'reviewed_use'}:
            raise ValueError('Submit restricted works as metadata only until a separately authorized intake is available.')
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError('Invalid effective-date range.')
        return self


class WatchCreate(Strict):
    workspace_id: str
    topic: str = Field(min_length=3, max_length=200)
    cadence_days: Literal[1, 7, 30] = 7
    consent: Literal[True]


class Preferences(Strict):
    reduced_motion: bool = False
    compact: bool = False
    default_framework: Literal['US_GAAP', 'IFRS', 'UNKNOWN'] = 'US_GAAP'


class FeedbackCreate(Strict):
    run_id: str | None = None
    category: Literal['accuracy', 'citation', 'privacy', 'copyright', 'interface', 'other']
    message: str = Field(min_length=10, max_length=5000)
