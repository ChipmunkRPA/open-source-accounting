from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .providers.gemini_costs import CATALOG_VERSION


class BudgetAuthorization(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    project: str = Field(pattern=r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')
    location: Literal['us', 'eu', 'global']
    model_id: Literal['gemini-3.8-flash']
    provider: Literal['google_cloud']
    catalog_version: Literal['google-cloud-gemini-3.8-flash-standard-2026-09-27'] = CATALOG_VERSION
    limit_usd: str = Field(pattern=r'^[0-9]{1,7}(\.[0-9]{1,6})?$')
    per_call_usd: str = Field(pattern=r'^[0-9]{1,7}(\.[0-9]{1,6})?$')
    expires_at: int
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{8,100}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirm_operator_spend_authorization: Literal[True]

    @field_validator('confirm_operator_spend_authorization', mode='before')
    @classmethod
    def actual_boolean(cls, value):
        if value is not True:
            raise ValueError('Explicit operator attestation is required.')
        return value


class BudgetRevocation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_terms_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class BudgetView(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    terms: BudgetAuthorization
    terms_sha256: str
    active: bool
    expires_at: int
    limit_usd: str
    per_call_usd: str
    held_usd: str
    committed_usd: str
    available_usd: str
