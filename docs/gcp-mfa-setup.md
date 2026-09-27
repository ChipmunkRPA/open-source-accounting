# Google Cloud deployment and mandatory MFA

## Architecture and scope

Use Firebase Authentication **with Identity Platform** for application users. Email/password is the initial provider implemented in the UI. Google Authenticator-compatible TOTP and SMS are alternative second factors. Reading the public library does not require an account. Real signed-in users, including free-chat users, must complete MFA before access to any private workspace API.

This is distinct from administrators' Google Cloud console authentication. Enforce organization-level administrator MFA separately. Workload identities and service accounts do not receive SMS or TOTP; use least-privilege IAM and short-lived workload credentials.

No cloud resources have been deployed by this release. The examples create billable resources only when an operator explicitly applies them.

## Project preparation

1. Select a dedicated GCP project and enable the services in `infra/main.tf`. Upgrade/enable Identity Platform. Review costs and quotas first.
2. Enable email/password and a strong password policy. Enable email-enumeration protection and customize verified-email/password-reset templates and support contacts. Do not use phone-only sign-in as a substitute for MFA.
3. Register the exact production and staging hostnames. Avoid wildcard domains. Separate production and staging projects are preferred.
4. Review SMS destinations. The provided helper requires an explicit country/region allowlist; `US` is only an example. Configure provider-level quotas, spending alerts and abuse controls. The browser's resend cooldown is a convenience, not a security boundary.
5. Preview TOTP/SMS configuration:

```bash
python scripts/configure_identity_platform.py \
  --project YOUR_PROJECT_ID \
  --domain app.example.com \
  --sms-region US
```

After inspecting the preview and authenticating an administrator through ADC, explicitly apply:

```bash
python scripts/configure_identity_platform.py \
  --project YOUR_PROJECT_ID \
  --domain app.example.com \
  --sms-region US \
  --apply --acknowledge-project-wide-change
```

The helper reads the current configuration, preserves existing authorized domains and unrelated MFA providers, patches only MFA/authorized-domains/SMS-region/email-provider fields, and checks the result. It does not create a project, turn on billing, upgrade the project, or configure tenants. Tenant-specific MFA policies need separate configuration and validation; the application supports a configured tenant ID and rejects other-tenant tokens.

The helper uses project MFA `ENABLED` to allow the enrollment handshake; the backend makes MFA mandatory for private application access. Existing `MANDATORY` state is preserved. TOTP uses one adjacent interval in the proposed starter configuration; review usability and risk before changing it.

## Production environment

```dotenv
APP_ENV=production
AUTH_MODE=firebase
MFA_REQUIRED=true
FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
FIREBASE_API_KEY=YOUR_PUBLIC_CLIENT_IDENTIFIER
FIREBASE_AUTH_DOMAIN=YOUR_PROJECT_ID.firebaseapp.com
FIREBASE_TENANT_ID=
AUTH_SESSION_MAX_AGE_SECONDS=43200
AUTH_RECENT_SECONDS=300
MODEL_PROVIDER=google_cloud
MODEL_ID=gemini-3.8-flash
MODEL_LOCATION=us
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
DEMO_BILLING_ENABLED=false
AUTO_SEED=false
AUTO_CREATE_SCHEMA=false
```

Also supply the existing production PostgreSQL, GCS, HTTPS, scanner and origin settings. Secrets belong in Secret Manager, not this file or Git. Firebase client API identifiers are public configuration, not administrator secrets; restrict their permitted API usage appropriately. The app will reject a Firebase emulator environment in real-auth mode.

Build the browser SDK locally into the deployment image:

```bash
cd frontend
npm install
npm run typecheck
npm run test:auth
npm run build
```

The SDK is bundled from pinned `firebase`, `qrcode`, and `esbuild` dependencies. Commit an audited lockfile after a successful clean install. No remote QR generator receives the TOTP secret. The separate `build:demo` skips this bundle and must not be used for production. Production startup fails when the identity bundle is absent.

Cloud Run receives workload credentials through its service account. Firebase Admin verifies token signatures/audience/expiry and checks revocation. The Terraform starter adds only `firebaseauth.users.get` for that identity read; the runtime does not receive user-update or Identity Platform configuration-admin privileges.

## Required user journeys

**New user:** sign up → verify email → choose TOTP or SMS → enroll and verify code → sign out → sign in with password → verify second factor → server checks reserved token claims → provision workspace.

**Existing user without MFA:** first factor succeeds only far enough to display enrollment. `/auth/status` provides a limited status response but does not provision a workspace or return private data.

**Returning user:** password → choose existing factor → verify code → server permits private requests. Failed, missing, unsupported or stale claims are denied.

**Backup factor:** Security → reauthenticate using the existing factor → enroll another method → sign in again. The UI does not offer removal of the final factor.

**Sensitive change:** sign in within five minutes before billing-portal/checkout actions, membership changes, source permission changes, technical approval or document deletion. A token refresh does not reset `auth_time`. Sensitive writes are never automatically replayed after reauthentication.

**Session expiry:** original authentication older than twelve hours requires a fresh sign-in. Tokens and refresh state remain in browser memory; reload may require sign-in again. No JWT, OTP, seed, QR payload or password is stored in local/session storage or application telemetry.

## Recovery and administration

Do not build an email-only bypass. A user with another enrolled factor should use it. Otherwise verify ownership through a documented operator recovery process, independently approve the reset, use a time-limited administrator identity, revoke refresh tokens, reset only the necessary factor, notify the user through established channels, and require new enrollment before application access. Record actor, approval, timestamp and action, not TOTP secrets or codes.

There is no self-service recovery-code system or automated factor-reset endpoint in v0.6. Define support contacts, identity evidence, escalation, and recovery retention before public launch. Never disclose whether a private account exists through public support/API responses.

## Staging checklist

Test both factor types on the actual deployed origin, including QR scanning, manual key, email verification, reCAPTCHA, SMS retries, expired codes, wrong codes, backup selection, lost-device handling, cancellation during a request, revoked sessions, disabled accounts, missing/forged reserved claims, tenant mismatch, production rejection of demo headers, and source/billing permissions after MFA.

Check CSP with the real SDK and reCAPTCHA version. Only the listed Google reCAPTCHA origins are permitted; do not fix failures with wildcard scripts, `unsafe-eval`, or an authentication bypass. Test screenshots/telemetry do not capture real enrollment secrets. Ensure the production API does not expose schema-management or development billing routes. The existing `/dev/subscription` route fails closed outside local/test configuration.

## Official implementation references

- Firebase TOTP MFA: https://firebase.google.com/docs/auth/web/totp-mfa
- Firebase SMS MFA: https://firebase.google.com/docs/auth/web/multi-factor
- Reserved token claims and original authentication time: https://firebase.google.com/docs/reference/admin/node/firebase-admin.auth.decodedidtoken
- SDK releases (12.19.0 selected): https://firebase.google.com/support/release-notes/js
- SMS region policies: https://docs.cloud.google.com/identity-platform/docs/admin/sms-regions
- Project configuration API: https://docs.cloud.google.com/identity-platform/docs/reference/rest/v2/Config

Documentation reviewed September 27, 2026. Live configuration and SDK behavior still require project-specific verification.
