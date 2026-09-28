"""Relational records. UTC timestamps are integer epoch seconds on both SQLite and PostgreSQL."""
import time
import uuid
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, Float, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def uid():
    return str(uuid.uuid4())


def now():
    return int(time.time())


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), default='')
    name: Mapped[str] = mapped_column(String(120), default='Member')
    role: Mapped[str] = mapped_column(String(30), default='member')
    stripe_customer_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Membership(Base):
    __tablename__ = 'memberships'
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default='editor')


class Subscription(Base):
    __tablename__ = 'subscriptions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    provider_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(40), default='free')
    term_start: Mapped[int] = mapped_column(Integer, default=0)
    paid_until: Mapped[int] = mapped_column(Integer, default=0)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    renewal_failed: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_reconciled: Mapped[int] = mapped_column(Integer, default=0)
    last_invoice_id: Mapped[str | None] = mapped_column(String(128))


class UsageWindow(Base):
    __tablename__ = 'usage_windows'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    start_at: Mapped[int] = mapped_column(Integer, primary_key=True)
    end_at: Mapped[int] = mapped_column(Integer)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[int] = mapped_column(Integer, default=0)


class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(160), default='New chat')
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    chat_id: Mapped[str] = mapped_column(ForeignKey('chats.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(12))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    sequence: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('chat_id', 'sequence'),)


class Idempotency(Base):
    __tablename__ = 'idempotency'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    scope: Mapped[str] = mapped_column(String(160), primary_key=True)
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String(128), default='')
    response: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(250))
    publisher: Mapped[str] = mapped_column(String(160))
    canonical_url: Mapped[str] = mapped_column(String(1500), default='')
    kind: Mapped[str] = mapped_column(String(40), default='original_commentary')
    framework: Mapped[str] = mapped_column(String(20), default='US_GAAP')
    version_label: Mapped[str] = mapped_column(String(80), default='1')
    effective_from: Mapped[str | None] = mapped_column(String(10))
    effective_to: Mapped[str | None] = mapped_column(String(10))
    text: Mapped[str | None] = mapped_column(Text)
    policy: Mapped[dict] = mapped_column(JSON, default=dict)
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(200))
    mime: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(250))
    chunks: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default='ready')
    authorization_basis: Mapped[str] = mapped_column(String(200))
    scan_status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Run(Base):
    __tablename__ = 'runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    workflow: Mapped[str] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    facts: Mapped[list] = mapped_column(JSON, default=list)
    document_ids: Mapped[list] = mapped_column(JSON, default=list)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    plan: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(40), default='draft', index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    execution_id: Mapped[str | None] = mapped_column(String(36))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey('runs.id'))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_start: Mapped[int | None] = mapped_column(Integer)
    usage_status: Mapped[str] = mapped_column(String(20), default='none')
    error_code: Mapped[str | None] = mapped_column(String(80))
    model_id: Mapped[str] = mapped_column(String(80), default='gemini-3.8-flash')
    token_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    updated_at: Mapped[int] = mapped_column(Integer, default=now)


class Evidence(Base):
    __tablename__ = 'evidence'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id', ondelete='CASCADE'), index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey('sources.id'))
    document_id: Mapped[str | None] = mapped_column(ForeignKey('documents.id'))
    title: Mapped[str] = mapped_column(String(250))
    locator: Mapped[str] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text)
    access: Mapped[str] = mapped_column(String(40))
    policy_version: Mapped[int | None] = mapped_column(Integer)
    extraction_context: Mapped[dict] = mapped_column(JSON, default=dict)
    source_kind: Mapped[str] = mapped_column(String(40))


class RunEvent(Base):
    __tablename__ = 'run_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(60))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id'), unique=True)
    state: Mapped[str] = mapped_column(String(20), default='queued', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[int] = mapped_column(Integer, default=now)
    lease_until: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class ModelBudget(Base):
    """One explicit spending authorization. No reset, renewal or automatic refill."""
    __tablename__ = 'model_budgets'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    terms: Mapped[dict] = mapped_column(JSON)
    terms_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    authorization_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    authorized_by: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    expires_at: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    limit_nanos: Mapped[int] = mapped_column(BigInteger)
    per_call_nanos: Mapped[int] = mapped_column(BigInteger)
    held_nanos: Mapped[int] = mapped_column(BigInteger, default=0)
    committed_nanos: Mapped[int] = mapped_column(BigInteger, default=0)
    revoked_at: Mapped[int | None] = mapped_column(Integer)


class ModelAttempt(Base):
    """Non-content inference receipts survive application rollback and parent deletion."""
    __tablename__ = 'model_attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    operation_key: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey('workspaces.id', ondelete='SET NULL'))
    run_id: Mapped[str | None] = mapped_column(ForeignKey('runs.id', ondelete='SET NULL'), index=True)
    chat_id: Mapped[str | None] = mapped_column(ForeignKey('chats.id', ondelete='SET NULL'))
    run_revision: Mapped[int | None] = mapped_column(Integer)
    execution_id: Mapped[str | None] = mapped_column(String(36))
    phase: Mapped[str] = mapped_column(String(30))
    provider: Mapped[str] = mapped_column(String(30))
    project: Mapped[str] = mapped_column(String(30))
    location: Mapped[str] = mapped_column(String(20))
    model_id: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(80))
    thinking: Mapped[str] = mapped_column(String(10))
    output_limit: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    finished_at: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(20), default='pending')
    error_code: Mapped[str | None] = mapped_column(String(80))
    http_status: Mapped[int | None] = mapped_column(Integer)
    usage: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    cost_state: Mapped[str] = mapped_column(String(20), default='unknown')
    cost_estimate: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    budget_id: Mapped[str | None] = mapped_column(ForeignKey('model_budgets.id'), index=True)
    reserved_nanos: Mapped[int | None] = mapped_column(BigInteger)
    budget_state: Mapped[str | None] = mapped_column(String(20))


class Memo(Base):
    __tablename__ = 'memos'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey('runs.id'))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    updated_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('run_id'),)


class MemoRevision(Base):
    __tablename__ = 'memo_revisions'
    memo_id: Mapped[str] = mapped_column(ForeignKey('memos.id', ondelete='CASCADE'), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Review(Base):
    __tablename__ = 'reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    memo_id: Mapped[str] = mapped_column(ForeignKey('memos.id'), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    kind: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Watch(Base):
    __tablename__ = 'watches'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'))
    topic: Mapped[str] = mapped_column(String(200))
    cadence_days: Mapped[int] = mapped_column(Integer, default=7)
    next_at: Mapped[int] = mapped_column(Integer, default=now)
    last_source_at: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_at: Mapped[int] = mapped_column(Integer, default=now)


class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    watch_id: Mapped[str | None] = mapped_column(ForeignKey('watches.id'))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class BillingEvent(Base):
    __tablename__ = 'billing_events'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[str] = mapped_column(String(128), default='')
    status: Mapped[str] = mapped_column(String(20), default='received')
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Audit(Base):
    __tablename__ = 'audit_log'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Feedback(Base):
    __tablename__ = 'feedback'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    run_id: Mapped[str | None] = mapped_column(ForeignKey('runs.id'))
    category: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


Index('jobs_due', Job.state, Job.available_at, Job.lease_until)


class IntakeWork(Base):
    """Immutable work/edition/route definition; authorization lives on the metadata-only Source."""
    __tablename__ = 'intake_works'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), unique=True)
    family_id: Mapped[str] = mapped_column(String(80), index=True)
    work_id: Mapped[str] = mapped_column(String(160))
    edition: Mapped[str] = mapped_column(String(80))
    manifest: Mapped[dict] = mapped_column(JSON)
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('family_id', 'work_id', 'edition'),)


class SourceArtifact(Base):
    __tablename__ = 'source_artifacts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    work_id: Mapped[str] = mapped_column(ForeignKey('intake_works.id'), index=True)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(250))
    byte_count: Mapped[int] = mapped_column(Integer)
    mime: Mapped[str] = mapped_column(String(100))
    receipt: Mapped[dict] = mapped_column(JSON)
    acquired_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('work_id', 'raw_sha256'),)


class SourceExtraction(Base):
    __tablename__ = 'source_extractions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    artifact_id: Mapped[str] = mapped_column(ForeignKey('source_artifacts.id'), index=True)
    parser_version: Mapped[str] = mapped_column(String(100))
    normalized_sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(250))
    passage_count: Mapped[int] = mapped_column(Integer)
    parsed_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('artifact_id', 'parser_version'),)


class ApplicabilityReview(Base):
    __tablename__ = 'applicability_reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    payload: Mapped[dict] = mapped_column(JSON)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class ParserReview(Base):
    __tablename__ = 'parser_reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    extraction_id: Mapped[str] = mapped_column(ForeignKey('source_extractions.id'), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    payload: Mapped[dict] = mapped_column(JSON)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('extraction_id', 'sequence'),)


class EditorialReview(Base):
    __tablename__ = 'editorial_reviews'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    decision: Mapped[str] = mapped_column(String(30))
    review_revision: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class SourceDiscovery(Base):
    __tablename__ = 'source_discoveries'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    artifact_id: Mapped[str] = mapped_column(ForeignKey('source_artifacts.id'), index=True)
    adapter_version: Mapped[str] = mapped_column(String(100))
    recipe_sha256: Mapped[str] = mapped_column(String(64))
    normalized_sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(250))
    candidate_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('artifact_id', 'adapter_version', 'recipe_sha256'),)


class IntakeAttempt(Base):
    __tablename__ = 'intake_attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    work_id: Mapped[str] = mapped_column(ForeignKey('intake_works.id'), index=True)
    request_key: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(20), default='fetching')
    lease_owner: Mapped[str] = mapped_column(String(36))
    lease_until: Mapped[int] = mapped_column(Integer)
    artifact_id: Mapped[str | None] = mapped_column(ForeignKey('source_artifacts.id'))
    error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('work_id', 'request_key'),)


class SourceRequestBudget(Base):
    __tablename__ = 'sec_request_budget'
    name: Mapped[str] = mapped_column(Text, primary_key=True)
    next_at: Mapped[float] = mapped_column(Float, default=0.0)


class OutputBudget(Base):
    __tablename__ = 'source_output_budgets'
    group_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    limits_sha256: Mapped[str] = mapped_column(String(64))
    terms_revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    released_chars: Mapped[int] = mapped_column(BigInteger, default=0)


class OutputRelease(Base):
    __tablename__ = 'source_output_releases'
    group_id: Mapped[str] = mapped_column(ForeignKey('source_output_budgets.group_id'), primary_key=True)
    payload_sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    character_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class CounselRecord(Base):
    """Immutable proposal plus review lifecycle; legal analysis stays in a restricted vault."""
    __tablename__ = 'source_counsel_records'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    proposal: Mapped[dict] = mapped_column(JSON)
    record_sha256: Mapped[str] = mapped_column(String(64))
    submitted_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    submitted_at: Mapped[int] = mapped_column(Integer, default=now)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    reviewed_at: Mapped[int | None] = mapped_column(Integer)
    activated_policy_version: Mapped[int | None] = mapped_column(Integer)
    revoked_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    revoked_at: Mapped[int | None] = mapped_column(Integer)
    revocation_reason: Mapped[str | None] = mapped_column(String(30))


class SourceScopeGrant(Base):
    __tablename__ = 'source_scope_grants'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    subject_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'))
    proposal: Mapped[dict] = mapped_column(JSON)
    record_sha256: Mapped[str] = mapped_column(String(64))
    submitted_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    submitted_at: Mapped[int] = mapped_column(Integer, default=now)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    approved_at: Mapped[int | None] = mapped_column(Integer)
    revoked_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    revoked_at: Mapped[int | None] = mapped_column(Integer)
    revocation_reason: Mapped[str | None] = mapped_column(String(30))
    __table_args__ = (Index('uq_source_scope_active', 'source_id', 'subject_user_id', 'workspace_id',
        unique=True, postgresql_where=(status == 'approved'), sqlite_where=(status == 'approved')),)


class OutputAmendment(Base):
    __tablename__ = 'source_output_amendments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    group_id: Mapped[str] = mapped_column(ForeignKey('source_output_budgets.group_id'), index=True)
    proposal: Mapped[dict] = mapped_column(JSON)
    record_sha256: Mapped[str] = mapped_column(String(64))
    submitted_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    submitted_at: Mapped[int] = mapped_column(Integer, default=now)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    reviewed_at: Mapped[int | None] = mapped_column(Integer)
    released_chars_at_apply: Mapped[int | None] = mapped_column(BigInteger)
    applied_terms_revision: Mapped[int | None] = mapped_column(Integer)


class CorrectionCase(Base):
    __tablename__ = 'correction_cases'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='open')
    version: Mapped[int] = mapped_column(Integer, default=1)
    policy_version: Mapped[int] = mapped_column(Integer)
    review_revision: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class CorrectionEvent(Base):
    __tablename__ = 'correction_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey('correction_cases.id'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    action: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text)
    source_policy_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('case_id', 'version'),)


class IntakeEdition(Base):
    """Immutable declared multipart inventories; never acquisition or professional approval."""
    __tablename__ = 'intake_editions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    family_id: Mapped[str] = mapped_column(String(80))
    collection_key: Mapped[str] = mapped_column(String(160))
    edition: Mapped[str] = mapped_column(String(80))
    revision: Mapped[int] = mapped_column(Integer)
    request_sha256: Mapped[str] = mapped_column(String(64))
    manifest: Mapped[dict] = mapped_column(JSON)
    manifest_sha256: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    __table_args__ = (UniqueConstraint('family_id', 'collection_key', 'edition', 'revision'),)


class ASUMention(Base):
    """Derived identifiers only; never retains filing text after source deletion."""
    __tablename__ = 'asu_mentions'
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE'), primary_key=True)
    asu_id: Mapped[str] = mapped_column(String(7), primary_key=True)
    source_revision: Mapped[str] = mapped_column(String(64))
    detected_at: Mapped[int] = mapped_column(Integer)


class ASURefresh(Base):
    __tablename__ = 'asu_refresh'
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    cursor: Mapped[str] = mapped_column(String(36), default='')
    upper_id: Mapped[str] = mapped_column(String(36), default='')
    state: Mapped[str] = mapped_column(String(20), default='idle')
    started_at: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[int | None] = mapped_column(Integer)
    next_due: Mapped[int] = mapped_column(Integer, default=0)
    scanned: Mapped[int] = mapped_column(Integer, default=0)
    eligible: Mapped[int] = mapped_column(Integer, default=0)
    matches: Mapped[int] = mapped_column(Integer, default=0)
