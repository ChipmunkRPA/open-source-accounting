"""Reference metadata, not FASB text, rights grants or professional approval."""
import calendar
import re
from datetime import date
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, model_validator
from .schemas import Strict
from .intake_schemas import https_url

Status = Literal['mentioned', 'not_yet_adopted', 'adopted', 'early_adopted']


def sec_identity(url):
    https_url(url)
    p = urlsplit(url)
    match = re.fullmatch(r'/Archives/edgar/data/([0-9]{1,10})/([0-9]{18})/([A-Za-z0-9_.-]+)', p.path)
    if p.hostname != 'www.sec.gov' or p.query or not match:
        raise ValueError('An exact official SEC filing document URL is required.')
    return match.group(1), match.group(2)


class ASU(Strict):
    id: str = Field(pattern=r'^20[0-9]{2}-[0-9]{2}$')
    subject: str = Field(min_length=3, max_length=200)
    topic: str = Field(min_length=1, max_length=80)
    issued: str
    date_precision: Literal['day', 'month', 'year']
    official_url: str = Field(max_length=1500)
    checked_on: date

    def interval(self):
        if self.date_precision == 'day':
            start = end = date.fromisoformat(self.issued)
        elif self.date_precision == 'month':
            start = date.fromisoformat(self.issued+'-01')
            end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
        else:
            start, end = date(int(self.issued), 1, 1), date(int(self.issued), 12, 31)
        return start, end

    @model_validator(mode='after')
    def valid(self):
        patterns = {'day': r'\d{4}-\d{2}-\d{2}', 'month': r'\d{4}-\d{2}', 'year': r'\d{4}'}
        if not re.fullmatch(patterns[self.date_precision], self.issued):
            raise ValueError('Issuance precision must match its date.')
        start, _ = self.interval()
        if start.year != int(self.id[:4]) or start > self.checked_on:
            raise ValueError('ASU year and observed issuance must agree.')
        https_url(self.official_url)
        if urlsplit(self.official_url).hostname not in {'fasb.org', 'www.fasb.org', 'storage.fasb.org', 'xbrl.fasb.org'}:
            raise ValueError('Use an official FASB reference.')
        return self


class FilingReference(Strict):
    asu_id: str
    company: str = Field(min_length=1, max_length=200)
    cik: str = Field(pattern=r'^[0-9]{1,10}$')
    accession: str = Field(pattern=r'^[0-9]{10}-[0-9]{2}-[0-9]{6}$')
    form: Literal['10-K', '10-Q', '20-F', '40-F', '8-K', '10-K/A', '10-Q/A']
    filed_on: date | None
    period_end: date | None
    url: str = Field(max_length=1500)
    locator: str = Field(min_length=1, max_length=300)
    status: Status
    observation: str = Field(min_length=1, max_length=500)
    checked_on: date

    @model_validator(mode='after')
    def valid(self):
        cik, accession = sec_identity(self.url)
        if int(cik) != int(self.cik) or accession != self.accession.replace('-', ''):
            raise ValueError('SEC URL identity conflicts with filing metadata.')
        if self.filed_on and self.filed_on > self.checked_on:
            raise ValueError('Cannot check a future filing.')
        return self


class Catalog(Strict):
    version: str
    checked_on: date
    asus: list[ASU] = Field(max_length=1000)
    filings: list[FilingReference] = Field(max_length=10000)

    @model_validator(mode='after')
    def valid(self):
        ids = {a.id for a in self.asus}
        keys = {(f.asu_id, f.url) for f in self.filings}
        if len(ids) != len(self.asus) or len(keys) != len(self.filings):
            raise ValueError('Duplicate ASU or filing reference.')
        if any(f.asu_id not in ids for f in self.filings):
            raise ValueError('Filing references an unregistered ASU.')
        if any(x.checked_on > self.checked_on for x in [*self.asus, *self.filings]):
            raise ValueError('Catalog check date precedes a reference check.')
        return self
