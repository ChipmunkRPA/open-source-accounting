"""Explicit directed relationships between retained passages, never inferred approval."""
from typing import Literal
from pydantic import Field,model_validator
from .schemas import Strict


class Endpoint(Strict):
    source_id: str = Field(min_length=1,max_length=36)
    revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    locator: str = Field(min_length=1,max_length=16000)
    character_start: int = Field(strict=True,ge=0)
    character_end: int = Field(strict=True,ge=1)
    passage_text_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class RelationshipProposal(Strict):
    source: Endpoint
    target: Endpoint
    relation: Literal['cites','amends','supersedes','defines','illustrates','compares']
    scope: str = Field(min_length=20,max_length=2000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def distinct(self):
        if self.source.source_id==self.target.source_id:
            raise ValueError('Choose two distinct source records; intra-record relationships are not supported.')
        return self


class RelationshipDecision(Strict):
    expected_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_sequence: int = Field(strict=True,ge=0)
    decision: Literal['approved','rejected','revoked']
    review_note: str = Field(min_length=20,max_length=4000)
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    expires_at: int = Field(strict=True,ge=1)
    confirm_actual_review_performed: Literal[True]
