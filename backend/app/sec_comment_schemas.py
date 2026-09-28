"""Public correspondence metadata, never a grant or a conclusion of misconduct."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict


class Correspondence(Strict):
    company: str = Field(min_length=1,max_length=200)
    cik: str = Field(pattern=r'^[0-9]{1,10}$')
    accession: str = Field(pattern=r'^[0-9]{10}-[0-9]{2}-[0-9]{6}$')
    form: Literal['UPLOAD','CORRESP']
    url: str = Field(max_length=1500)
    letter_date: date
    filed_on: date | None = None
    publicly_available_on: date | None = None
    checked_on: date
    reviewed_filing: str = Field(min_length=1,max_length=300)
    related_accessions: list[str] = Field(default_factory=list,max_length=30)
    locator: str = Field(min_length=1,max_length=300)

    @model_validator(mode='after')
    def identity(self):
        import re
        from .asu_schemas import sec_identity
        cik, accession = sec_identity(self.url)
        if int(cik)!=int(self.cik) or accession!=self.accession.replace('-',''):
            raise ValueError('Correspondence URL and identity disagree.')
        if any(d and d>self.checked_on for d in (self.letter_date,self.filed_on,self.publicly_available_on)):
            raise ValueError('Observed dates cannot follow verification.')
        if self.publicly_available_on and self.publicly_available_on<self.letter_date:
            raise ValueError('Public availability precedes the letter.')
        if len(set(self.related_accessions))!=len(self.related_accessions) or any(not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',a) or a==self.accession for a in self.related_accessions):
            raise ValueError('Related accession links must be explicit, unique and distinct.')
        return self


class Reference(Correspondence):
    topics: list[str] = Field(max_length=20)
    staff_concern: str = Field(max_length=1500)
    company_response: str = Field(max_length=1500)
    analysis: str = Field(max_length=1500)
    follow_up: str = Field(max_length=1500)


class Catalog(Strict):
    version: str
    checked_on: date
    records: list[Reference] = Field(max_length=10000)

    @model_validator(mode='after')
    def distinct(self):
        if len({r.accession for r in self.records})!=len(self.records) or any(r.checked_on>self.checked_on for r in self.records):
            raise ValueError('Duplicate or future reference.')
        return self
