"""Human claim assessments; no source permission or release approval is implied."""
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict


class PassageAssessment(Strict):
    evidence_id: str = Field(min_length=1, max_length=36)
    relationship: Literal['supports', 'contradicts', 'context_only', 'unresolved']
    rationale: str = Field(min_length=20, max_length=2000)


class ClaimDecision(Strict):
    expected_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_sequence: int = Field(strict=True, ge=0)
    decision: Literal['supported', 'contradicted', 'unresolved', 'revoked']
    passages: list[PassageAssessment] = Field(default_factory=list, max_length=12)
    review_note: str = Field(min_length=20, max_length=4000)
    competence_scope: str = Field(min_length=20, max_length=2000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expires_at: int = Field(strict=True, ge=1)
    confirm_actual_review_performed: Literal[True]
    confirm_competence_and_independence: Literal[True]

    @model_validator(mode='after')
    def consistent(self):
        ids = [p.evidence_id for p in self.passages]
        if len(ids) != len(set(ids)):
            raise ValueError('Assess each cited passage once.')
        kinds = {p.relationship for p in self.passages}
        if self.decision == 'supported' and ('supports' not in kinds or 'contradicts' in kinds or 'unresolved' in kinds):
            raise ValueError('Supported claims need supporting evidence and no unresolved or contradictory bindings.')
        if self.decision == 'contradicted' and 'contradicts' not in kinds:
            raise ValueError('Contradicted claims need an explicitly contradictory passage.')
        if self.decision == 'revoked' and self.passages:
            raise ValueError('Revocation contains no passage assessments.')
        return self
