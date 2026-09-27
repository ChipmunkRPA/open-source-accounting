"""Mandatory Identity Platform MFA: the server trusts only SDK-verified reserved claims."""
from dataclasses import dataclass
import math
import time
from fastapi import Depends, Request, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from .models import User, Workspace, Membership
from .errors import fail

@dataclass(frozen=True)
class Identity:
    uid: str
    email: str
    name: str
    email_verified: bool
    factor: str | None
    factor_id: str | None
    auth_time: int
    mode: str = 'firebase'

    @property
    def mfa_verified(self):
        return self.factor in {'totp', 'phone'} and bool(self.factor_id)

def session(request: Request):
    with request.app.state.db.Session() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise

def settings(request: Request):
    return request.app.state.settings

def verify_firebase_token(token: str, project: str, tenant: str = '') -> dict:
    """Small external boundary. Never log credentials or the SDK exception body."""
    import firebase_admin
    from firebase_admin import auth, tenant_mgt
    name = 'osa-' + project
    try:
        app = firebase_admin.get_app(name)
    except ValueError:
        try:
            app = firebase_admin.initialize_app(options={'projectId': project}, name=name)
        except ValueError:
            app = firebase_admin.get_app(name)  # Another request initialized it.
    if tenant:
        return tenant_mgt.auth_for_tenant(tenant, app=app).verify_id_token(token, check_revoked=True)
    return auth.verify_id_token(token, app=app, check_revoked=True)

def identity_from_claims(claims: dict, config, *, clock=None) -> Identity:
    """Policy validation AFTER signature, expiration and revocation verification."""
    clock = time.time() if clock is None else clock
    uid = claims['uid'] if 'uid' in claims else claims.get('sub')
    if (claims.get('aud') != config.firebase_project_id
            or claims.get('iss') != 'https://securetoken.google.com/' + config.firebase_project_id
            or not isinstance(uid, str) or not 1 <= len(uid) <= 128 or claims.get('sub') != uid):
        fail('UNAUTHENTICATED', 'This session is invalid for this application.', 401)
    meta = claims.get('firebase')
    if not isinstance(meta, dict) or (meta.get('tenant') or '') != config.firebase_tenant_id:
        fail('UNAUTHENTICATED', 'This session is invalid for this application.', 401)
    if meta.get('sign_in_provider') not in {'password', 'google.com', 'microsoft.com', 'apple.com', 'facebook.com', 'github.com'}:
        fail('UNSUPPORTED_FIRST_FACTOR', 'Use a supported verified-email sign-in first.', 403)
    stamp = claims.get('auth_time')
    if (isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or not math.isfinite(stamp)
            or stamp <= 0 or stamp > clock + 60):
        fail('UNAUTHENTICATED', 'Invalid sign-in timestamp.', 401)
    if clock - stamp > config.auth_session_max_age_seconds:
        fail('REAUTH_REQUIRED', 'Sign in again with your password and second factor.', 401)
    factor, factor_id = meta.get('sign_in_second_factor'), meta.get('second_factor_identifier')
    return Identity(uid, str(claims.get('email') or ''), str(claims.get('name') or 'Member'),
                    claims.get('email_verified') is True,
                    factor if isinstance(factor, str) else None,
                    factor_id if isinstance(factor_id, str) and factor_id else None, int(stamp))

def verified_identity(request: Request) -> Identity:
    config = request.app.state.settings
    if config.auth_mode == 'dev':
        principal = request.headers.get('x-dev-user', 'demo')
        if principal not in {'demo', 'reviewer', 'admin', 'approver', 'editor'}:
            fail('UNAUTHENTICATED', 'Unknown local demo identity.', 401)
        identity = Identity(principal, '', 'Local demo', True, None, None, int(time.time()), 'dev')
    else:
        bearer = request.headers.get('authorization', '')
        if not bearer.startswith('Bearer ') or not bearer[7:] or len(bearer) > 20000:
            fail('UNAUTHENTICATED', 'Sign in to continue. General chat is free.', 401)
        try:
            identity = identity_from_claims(verify_firebase_token(bearer[7:], config.firebase_project_id, config.firebase_tenant_id), config)
        except HTTPException:
            raise
        except Exception:
            fail('UNAUTHENTICATED', 'Your session is invalid, revoked, or expired.', 401)
    request.state.identity = identity
    return identity

def current_user(request: Request, identity: Identity = Depends(verified_identity), db: Session = Depends(session)) -> User:
    if identity.mode != 'dev':
        if not identity.email_verified:
            fail('VERIFY_EMAIL', 'Verify your email before setting up a second factor.', 403)
        if not identity.mfa_verified:
            fail('MFA_REQUIRED', 'Verify with an authenticator app or text message to continue.', 403)
    user = db.get(User, identity.uid)
    if not user:
        if identity.mode == 'dev':
            fail('SETUP_REQUIRED', 'Run the local seed command first.', 503)
        user = User(id=identity.uid, email=identity.email, name=identity.name)
        db.add(user)
        db.flush()
        workspace = Workspace(owner_id=user.id, name='My workspace')
        db.add(workspace)
        db.flush()
        db.add(Membership(workspace_id=workspace.id, user_id=user.id, role='owner'))
        db.commit()
    return user

def fresh_user(request: Request, user: User = Depends(current_user)) -> User:
    identity = request.state.identity
    if identity.mode != 'dev' and time.time() - identity.auth_time > request.app.state.settings.auth_recent_seconds:
        fail('RECENT_AUTH_REQUIRED', 'Sign in again and verify your second factor for this change.', 403)
    return user

def workspace_access(db: Session, user: User, workspace_id: str, action: str = 'read'):
    member = db.get(Membership, (workspace_id, user.id))
    if not member:
        fail('NOT_FOUND', 'Workspace not found.', 404)
    if action == 'edit' and member.role not in {'owner', 'editor'}:
        fail('FORBIDDEN', 'Workspace editing permission is required.', 403)
    if action == 'owner' and member.role != 'owner':
        fail('FORBIDDEN', 'Workspace owner permission is required.', 403)
    if action == 'review' and member.role not in {'owner', 'editor', 'reviewer'}:
        fail('FORBIDDEN', 'Workspace review permission is required.', 403)
    return member


def require_admin(user: User, approve: bool = False):
    allowed = {'rights_approver'} if approve else {'admin', 'rights_approver'}
    if user.role not in allowed:
        fail('FORBIDDEN', 'This action requires a scoped administrator.', 403)


def lock_user(db: Session, user_id: str):
    # All quota-admission writers serialize on the same user row in PostgreSQL.
    if db.bind.dialect.name == 'sqlite':
        db.execute(update(User).where(User.id == user_id).values(name=User.name))
    return db.scalar(select(User).where(User.id == user_id).with_for_update())
