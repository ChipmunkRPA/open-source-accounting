"""Verified entitlement references, not user assertions or publisher credential storage."""
from typing import Annotated, Literal
from pydantic import Field, StrictInt, model_validator
from .schemas import Strict
from .counsel_schemas import Digest, OpaqueRef, Operation

Label = Annotated[str, Field(min_length=1, max_length=120, pattern=r'^[A-Za-z0-9_.:-]+$')]


class ScopeValues(Strict):
    seat_id: Label | None = None
    jurisdiction: Label | None = None
    retention: Label | None = None

    @model_validator(mode='after')
    def at_least_one(self):
        if not any(self.model_dump().values()):
            raise ValueError('At least one verified scope value is required.')
        return self


class ScopeSubmission(Strict):
    expected_policy_version: StrictInt = Field(ge=1)
    expected_rights_revision: Digest
    subject_user_id: str = Field(min_length=1, max_length=128)
    workspace_id: str = Field(min_length=1, max_length=36)
    operations: list[Operation] = Field(min_length=1, max_length=11)
    values: ScopeValues
    provider: Literal['google_cloud', 'mock']
    project: str = Field(max_length=120)
    region: Label
    model_id: Label
    evidence_ref: OpaqueRef
    evidence_sha256: Digest
    effective_at: StrictInt = Field(ge=0)
    expires_at: StrictInt = Field(gt=0)

    @model_validator(mode='after')
    def bounded(self):
        if len(set(self.operations)) != len(self.operations):
            raise ValueError('Operations must be unique.')
        if self.expires_at <= self.effective_at:
            raise ValueError('Expiry must follow the effective time.')
        if self.provider == 'google_cloud' and not self.project.strip():
            raise ValueError('Google Cloud scope requires an explicit project.')
        return self


class ScopeApproval(Strict):
    expected_record_sha256: Digest
    confirm_actual_entitlement_verification: Literal[True]


class ScopeRevocation(Strict):
    expected_record_sha256: Digest
    reason: Literal['seat_removed', 'scope_changed', 'evidence_invalid', 'terms_changed', 'operator_hold']
