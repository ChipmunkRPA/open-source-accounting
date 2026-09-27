"""Private-review references only. Never accept legal advice or publisher bodies here."""
from typing import Annotated, Literal
from pydantic import Field, StrictInt, model_validator
from .schemas import Strict

OpaqueRef = Annotated[str, Field(pattern=r'^ev_[A-Za-z0-9_-]{8,120}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Operation = Literal['acquire', 'store_raw', 'extract', 'store_text', 'embed', 'model_input',
                    'display_full', 'quote', 'export', 'redistribute', 'train']


class CounselAssessments(Strict):
    purpose: OpaqueRef
    nature: OpaqueRef
    amount_and_substantiality: OpaqueRef
    output_and_reconstruction: OpaqueRef
    market_effect: OpaqueRef
    access_route_and_terms: OpaqueRef
    jurisdiction: OpaqueRef


class CounselSubmission(Strict):
    expected_policy_version: StrictInt = Field(ge=1)
    expected_rights_revision: Digest
    operations: list[Operation] = Field(min_length=1, max_length=11)
    evidence_ref: OpaqueRef
    evidence_sha256: Digest
    assessments: CounselAssessments
    effective_at: StrictInt = Field(ge=0)
    expires_at: StrictInt = Field(gt=0)

    @model_validator(mode='after')
    def bounded_decision(self):
        if len(set(self.operations)) != len(self.operations):
            raise ValueError('Operations must be unique.')
        if self.expires_at <= self.effective_at:
            raise ValueError('An explicit review expiry must follow its effective time.')
        return self


class CounselReview(Strict):
    expected_record_sha256: Digest
    decision: Literal['approved', 'rejected']
    confirm_actual_independent_counsel_review: Literal[True]


class CounselRevocation(Strict):
    expected_record_sha256: Digest
    reason: Literal['withdrawn', 'scope_changed', 'evidence_invalid', 'terms_changed', 'operator_hold']
