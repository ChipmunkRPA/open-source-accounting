"""Metadata-only contracts. Registering an official URL never authorizes a download."""
from datetime import date, datetime, timezone
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


class ManualDelivery(Strict):
    """Claims requiring independent review, never an authorization by themselves."""
    raw_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    byte_count: int = Field(ge=1, le=16_000_000)
    mime: Literal['application/xml', 'text/xml', 'text/html', 'application/pdf', 'text/plain', 'application/json']
    method: Literal['publisher_delivery', 'author_original']
    evidence_ref: str = Field(pattern=r'^ev_[A-Za-z0-9_-]{1,120}$')
    evidence_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    received_at: datetime

    @model_validator(mode='after')
    def actual_time(self):
        if self.received_at.tzinfo is None or self.received_at > datetime.now(timezone.utc):
            raise ValueError('Delivery time must be timezone-aware and not in the future.')
        return self


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
    parser: Literal['ecfr_xml', 'structural_html', 'pdf', 'text', 'crossref_metadata']
    parser_family: str = Field(default='generic', max_length=80)
    cfr_title: str = Field(default='17', pattern=r'^\d{1,3}$')
    allowed_mime: list[Literal['application/xml', 'text/xml', 'text/html', 'application/pdf', 'text/plain', 'application/json']] = Field(min_length=1, max_length=6)
    max_bytes: int = Field(default=2_000_000, ge=1, le=16_000_000)
    issued_at: date | None = None
    publicly_available_at: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    date_notes: str = Field(min_length=5, max_length=2000)
    effective_conditions: list[str] = Field(default_factory=list, max_length=30)
    supersedes: list[str] = Field(default_factory=list, max_length=30)
    notices: list[str] = Field(min_length=1, max_length=30)
    manual_delivery: ManualDelivery | None = None

    def canonical_metadata(self):
        data = self.model_dump(mode='json')
        # Preserve hashes of previously registered manifests and their rights reviews.
        if self.manual_delivery is None:
            data.pop('manual_delivery')
        return data

    @model_validator(mode='after')
    def validate_route(self):
        for url in [self.requested_url, *self.redirect_urls]:
            https_url(url)
        if self.parser == 'crossref_metadata':
            from .crossref_discovery import query_contract
            query_contract(self.requested_url)
            if self.family_id != 'OPEN_LITERATURE' or self.redirect_urls or self.allowed_mime != ['application/json']:
                raise ValueError('Crossref metadata requires OPEN_LITERATURE, JSON only and no redirects.')
        elif 'application/json' in self.allowed_mime:
            raise ValueError('JSON intake requires a dedicated reviewed metadata adapter.')
        if self.access_mode in {'reference_only', 'private'} and self.route != 'reference_only':
            raise ValueError('Private uploads use the workspace pipeline; reference-only records cannot fetch.')
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError('Invalid applicability interval.')
        if self.manual_delivery is not None:
            if (self.route != 'authorized_manual' or self.redirect_urls
                    or self.manual_delivery.byte_count > self.max_bytes
                    or self.manual_delivery.mime not in self.allowed_mime):
                raise ValueError('Manual delivery must match the approved route, MIME and byte limit.')
        return self


class IntakeCreate(Strict):
    source: SourceCreate
    manifest: IntakeManifest

    @model_validator(mode='after')
    def metadata_only(self):
        if self.manifest.route == 'authorized_manual' and self.manifest.manual_delivery is None:
            raise ValueError('New manual records require exact delivery evidence before review.')
        if self.manifest.family_id == 'PRIVATE_UPLOADS' and self.manifest.route != 'reference_only':
            raise ValueError('Private uploads require the workspace pipeline.')
        if (self.manifest.manual_delivery and self.manifest.manual_delivery.method == 'author_original'
                and self.source.policy.basis != 'original'):
            raise ValueError('Author-original delivery requires the original-work basis.')
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


class IntegrityHoldRelease(Strict):
    expected_policy_version: int = Field(ge=1)
    note: str = Field(min_length=10, max_length=2000)
    confirm_reverification_and_stale_evidence: Literal[True]
