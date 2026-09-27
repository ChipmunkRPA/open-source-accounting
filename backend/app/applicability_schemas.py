"""Independent applicability attestations; dates are never inferred from import time."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict


class ApplicabilityDecision(Strict):
    expected_policy_version: int = Field(ge=1)
    expected_review_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['approved','changes_requested','rejected','revoked']
    issued_at: date | None = None
    publicly_available_at: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    confirm_open_ended: bool = False
    frameworks: list[Literal['US_GAAP','IFRS']] = Field(default_factory=list,max_length=3)
    entity_types: list[Literal['public','private','nonprofit']] = Field(default_factory=list,max_length=3)
    audit_regimes: list[Literal['PCAOB','AICPA','GAGAS','NONE']] = Field(default_factory=list,max_length=4)
    conditions: list[str] = Field(default_factory=list,max_length=30)
    review_scope: str = Field(min_length=10,max_length=2000)
    review_note: str = Field(min_length=20,max_length=4000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expires_at: int = Field(ge=1)
    confirm_actual_applicability_review: Literal[True]

    @model_validator(mode='after')
    def dates_and_scope(self):
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError('Effective interval is reversed.')
        if any(len(c.strip())<5 or len(c)>1000 for c in self.conditions):
            raise ValueError('Conditions must describe the unresolved applicability rule.')
        if (len(set(self.frameworks))!=len(self.frameworks) or len(set(self.entity_types))!=len(self.entity_types)
                or len(set(self.audit_regimes))!=len(self.audit_regimes)):
            raise ValueError('Scope entries must be distinct.')
        if self.decision=='approved':
            if not all([self.issued_at,self.publicly_available_at,self.effective_from,self.frameworks,self.entity_types]):
                raise ValueError('Approval requires issued, public and effective dates and explicit framework/entity scope.')
            if self.effective_to is None and not self.confirm_open_ended:
                raise ValueError('Confirm an explicitly open-ended interval.')
            if self.issued_at>date.today() or self.publicly_available_at>date.today():
                raise ValueError('Actual issuance and public availability cannot be future claims.')
        return self
