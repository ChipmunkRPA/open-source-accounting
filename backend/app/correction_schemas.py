from typing import Literal
from pydantic import Field, field_validator
from .schemas import Strict


class CorrectionCreate(Strict):
    source_id: str = Field(min_length=1, max_length=36)
    kind: Literal['correction', 'takedown']
    expected_policy_version: int = Field(ge=1)
    expected_review_revision: str = Field(pattern=r'^[a-f0-9]{64}$')
    note: str = Field(min_length=10, max_length=4000)

    @field_validator('note')
    @classmethod
    def meaningful(cls, value):
        if len(value.strip()) < 10: raise ValueError('Provide a substantive administrative note.')
        return value.strip()


class CorrectionAction(Strict):
    expected_version: int = Field(ge=1)
    action: Literal['triage', 'resolve', 'dismiss', 'reopen', 'disable']
    note: str = Field(min_length=10, max_length=4000)
    _meaningful = field_validator('note')(CorrectionCreate.meaningful.__func__)
