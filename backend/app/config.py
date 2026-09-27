"""Explicit environment configuration; insecure demo modes cannot run in production."""
from pathlib import Path
from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .providers.gemini_contract import MODEL_ID, endpoint

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(str(ROOT / '.env'), '.env'), extra='ignore')
    app_env: Literal['local', 'test', 'production'] = 'local'
    database_url: str = 'sqlite:///./data/accounting.db'
    data_dir: str = './data'
    content_dir: str = str(ROOT / 'content')
    auth_mode: Literal['dev', 'firebase'] = 'dev'
    model_provider: Literal['mock', 'google_cloud'] = 'mock'
    model_id: Literal['gemini-3.8-flash'] = MODEL_ID
    model_location: str = 'us'
    google_cloud_project: str = ''
    model_budget_id: str = ''  # Explicit operator authorization; empty denies live app inference.
    firebase_project_id: str = ''
    firebase_auth_domain: str = ''
    firebase_tenant_id: str = ''
    mfa_required: bool = True
    auth_session_max_age_seconds: int = 43200
    auth_recent_seconds: int = 300
    firebase_api_key: str = ''  # Public client identifier, not an admin credential.
    storage_provider: Literal['local', 'gcs'] = 'local'
    gcs_bucket: str = ''
    app_origin: str = 'http://localhost:8000'
    allowed_origins: str = 'http://localhost:8000,http://127.0.0.1:8000'
    demo_billing_enabled: bool = True
    billing_enabled: bool = False
    billing_terms_approved: bool = False
    stripe_secret_key: str = ''
    stripe_webhook_secret: str = ''
    stripe_price_id: str = ''
    stripe_api_version: str = ''  # Set to the version used by your Stripe webhook endpoint.
    annual_price_cents: int = 8999
    agent_tasks_per_month: int = 30  # PROPOSED operating limit; approve before launch.
    agent_concurrency: int = 2
    renewal_grace_days: int = 0  # No automatic grant of free credit without operator decision.
    chat_messages_per_hour: int = 30  # Abuse/cost control, never a payment requirement.
    max_upload_mb: int = 10
    max_documents_per_workspace: int = 50
    max_document_characters: int = 300000
    upload_scanning_required: bool = False
    clamav_host: str = ''
    clamav_port: int = 3310
    source_fetch_enabled: bool = False
    sec_user_agent: str = ''
    enable_experimental_agents: bool = False
    auto_seed: bool = True
    auto_create_schema: bool = True
    worker_lease_seconds: int = 600
    worker_poll_seconds: float = 2.0
    max_job_attempts: int = 3
    worker_token: str = ''

    @model_validator(mode='after')
    def safe_configuration(self):
        import os
        if (os.environ.get('K_SERVICE') or os.environ.get('CLOUD_RUN_JOB')) and self.app_env != 'production':
            raise ValueError('Cloud Run workloads must use APP_ENV=production; demo mode is local only.')
        if self.annual_price_cents != 8999:
            raise ValueError('The approved annual price is USD 89.99 (8999 cents).')
        if self.agent_tasks_per_month < 1 or self.agent_concurrency < 1:
            raise ValueError('Usage limits must be positive.')
        if not 0 <= self.renewal_grace_days <= 30:
            raise ValueError('Invalid fixed renewal grace.')
        if self.model_location not in {'us', 'eu', 'global'}:
            raise ValueError('Choose an explicitly supported model multi-region; no silent fallback.')
        if self.model_provider == 'google_cloud' and not self.google_cloud_project:
            raise ValueError('GOOGLE_CLOUD_PROJECT is required for live inference.')
        if self.model_provider == 'google_cloud':
            endpoint(self.google_cloud_project, self.model_location, self.model_id)
        if self.auth_mode == 'firebase':
            if not self.firebase_project_id or not self.mfa_required:
                raise ValueError('Firebase mode requires a project and mandatory MFA.')
            import os, re
            if os.environ.get('FIREBASE_AUTH_EMULATOR_HOST'):
                raise ValueError('Firebase emulator is forbidden in real authentication mode.')
            if not self.firebase_auth_domain:
                self.firebase_auth_domain = self.firebase_project_id + '.firebaseapp.com'
            if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', self.firebase_auth_domain):
                raise ValueError('FIREBASE_AUTH_DOMAIN must be a hostname.')
        if not 60 <= self.auth_recent_seconds <= 900:
            raise ValueError('Recent sign-in window must be 60–900 seconds.')
        if not self.auth_recent_seconds <= self.auth_session_max_age_seconds <= 86400:
            raise ValueError('Session age must be between the recent window and 24 hours.')
        if self.app_env == 'production':
            if self.auth_mode != 'firebase' or self.demo_billing_enabled or self.model_provider == 'mock':
                raise ValueError('Production forbids dev authentication, mock inference, and demo billing.')
            if self.database_url.startswith('sqlite') or self.storage_provider != 'gcs':
                raise ValueError('Production requires PostgreSQL and private GCS storage.')
            if self.auto_create_schema or self.auto_seed:
                raise ValueError('Production uses migrations and separately reviewed seed/import data.')
            if not self.app_origin.startswith('https://') or not self.gcs_bucket or not self.firebase_api_key:
                raise ValueError('Production requires HTTPS and a GCS bucket.')
            if not self.upload_scanning_required or not self.clamav_host:
                raise ValueError('Production uploads require the configured malware scanner.')
        if self.billing_enabled and (not self.billing_terms_approved or not all([
            self.stripe_secret_key, self.stripe_webhook_secret, self.stripe_price_id,
            self.stripe_api_version,
        ])):
            raise ValueError('Billing requires approved terms and complete Stripe configuration.')
        return self
