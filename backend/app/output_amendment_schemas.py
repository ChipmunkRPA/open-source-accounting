"""Reviewable term transitions; no counter-reset or work-regrouping operation."""
from typing import Literal
from pydantic import Field, StrictInt
from .schemas import Strict, OutputControl
from .counsel_schemas import Digest, OpaqueRef


class OutputAmendmentSubmission(Strict):
    expected_limits_sha256: Digest
    expected_terms_revision: StrictInt = Field(ge=1)
    expected_sources_sha256: Digest
    new_control: OutputControl
    evidence_ref: OpaqueRef
    evidence_sha256: Digest
    review_expires_at: StrictInt = Field(gt=0)


class OutputAmendmentReview(Strict):
    expected_record_sha256: Digest
    expected_released_chars: StrictInt = Field(ge=0)
    decision: Literal['apply', 'reject']
    confirm_actual_terms_review: Literal[True]
    confirm_counters_preserved: Literal[True]
