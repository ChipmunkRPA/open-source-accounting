"""Human technical-review attestations. No model may manufacture these decisions."""
from typing import Literal
from pydantic import Field
from .schemas import Strict


class ReferenceBinding(Strict):
    reference_id: str = Field(min_length=1, max_length=128)
    source_id: str = Field(min_length=1, max_length=128)
    review_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    policy_version: int = Field(ge=1)
    locator: str = Field(min_length=1, max_length=2000)


class EditorialDecision(Strict):
    expected_policy_version: int = Field(ge=1)
    expected_review_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    content_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['approved', 'changes_requested', 'rejected', 'revoked']
    review_scope: str = Field(min_length=10, max_length=2000)
    review_note: str = Field(min_length=20, max_length=4000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expires_at: int = Field(ge=1)
    checked_reference_ids: list[str] = Field(default_factory=list, max_length=100)
    reference_bindings: list[ReferenceBinding] = Field(default_factory=list, max_length=200)
    confirm_actual_review_performed: Literal[True]


class ParserDecision(Strict):
    expected_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_sequence: int = Field(ge=0)
    decision: Literal['approved', 'changes_requested', 'rejected', 'revoked']
    review_scope: str = Field(min_length=10, max_length=2000)
    review_note: str = Field(min_length=20, max_length=4000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expires_at: int = Field(ge=1)
    checked_passage_indices: list[int] = Field(default_factory=list, max_length=10000)
    confirm_raw_and_citations_checked: Literal[True]


class RevisionComparison(Strict):
    before_source_id: str = Field(min_length=1, max_length=128)
    after_source_id: str = Field(min_length=1, max_length=128)
    before_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    after_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    before_policy_version: int = Field(ge=1)
    after_policy_version: int = Field(ge=1)
