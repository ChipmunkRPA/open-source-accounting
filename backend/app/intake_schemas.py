"""Metadata-only contracts. Registering an official URL never authorizes a download."""
from datetime import date
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field, model_validator
from .schemas import Strict, SourceCreate


def https_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.port not in {None, 443} or parts.fragment
                or any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value):
            raise ValueError('Invalid intake URL.')
    except ValueError as exc:
        raise ValueError('Use a credential-free HTTPS URL without fragments or nonstandard ports.') from exc
    return value


class IntakeManifest(Strict):
    family_id: str = Field(min_length=1, max_length=80)
    work_id: str = Field(min_length=1, max_length=160)
    edition: str = Field(min_length=1, max_length=80)
    language: str = Field(min_length=2, max_length=40)
    jurisdiction: str = Field(min_length=1, max_length=120)
    authority_type: str = Field(min_length=1, max_length=80)
    coverage_unit: str = Field(min_length=3, max_length=300)
    access_mode: Literal['public_candidate', 'licensed', 'reference_only', 'private']
    route: Literal['official_http', 'authorized_manual', 'reference_only']
    requested_url: str = Field(min_length=1, max_length=1500)
    redirect_urls: list[str] = Field(default_factory=list, max_length=3)
    parser: Literal['ecfr_xml', 'structural_html', 'pdf', 'text']
    parser_family: str = Field(default='generic', max_length=80)
    cfr_title: str = Field(default='17', pattern=r'^\d{1,3}$')
    allowed_mime: list[Literal['application/xml', 'text/xml', 'text/html', 'application/pdf', 'text/plain']] = Field(min_length=1, max_length=5)
    max_bytes: int = Field(default=2_000_000, ge=1, le=16_000_000)
    issued_at: date | None = None
    publicly_available_at: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    date_notes: str = Field(min_length=5, max_length=2000)
    effective_conditions: list[str] = Field(default_factory=list, max_length=30)
    supersedes: list[str] = Field(default_factory=list, max_length=30)
    notices: list[str] = Field(min_length=1, max_length=30)

    @model_validator(mode='after')
    def validate_route(self):
        for url in [self.requested_url, *self.redirect_urls]:
            https_url(url)
        if self.access_mode in {'reference_only', 'private'} and self.route != 'reference_only':
            raise ValueError('Private uploads use the workspace pipeline; reference-only records cannot fetch.')
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError('Invalid applicability interval.')
        return self


class IntakeCreate(Strict):
    source: SourceCreate
    manifest: IntakeManifest

    @model_validator(mode='after')
    def metadata_only(self):
        if self.source.text:
            raise ValueError('Intake registration is metadata only.')
        if self.source.canonical_url != self.manifest.requested_url or self.source.version_label != self.manifest.edition:
            raise ValueError('Source URL/version must match the immutable intake manifest.')
        for field in ('effective_from', 'effective_to'):
            if getattr(self.source, field) is not None and getattr(self.source, field) != getattr(self.manifest, field):
                raise ValueError('Source dates must agree with the immutable intake manifest.')
        if self.source.policy.basis == 'reference_only' and self.manifest.access_mode != 'reference_only':
            raise ValueError('Reference-only policies require reference-only intake mode.')
        return self
