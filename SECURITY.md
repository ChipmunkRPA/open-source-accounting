# Security status and reporting

This is a development starter, not an audited production service. Local demo
authentication and demo billing are intentionally insecure outside localhost.
Production configuration rejects those modes; configuration checks are not a
substitute for a deployment security review.

Do not place vulnerabilities involving credentials, private documents, or account
access in a public issue. Once the repository exists, maintainers should enable
GitHub private vulnerability reporting and advertise the enabled reporting route.
No private reporting endpoint or monitored email address is claimed in this draft.
For public issues, describe non-sensitive symptoms without customer data.

Before public hosting: validate authentication/authorization, CSRF/CORS and HTTP
policies, queue permissions, source acquisition, file parsing/malware scanning,
provider retention, billing webhooks, rate limits, backups, deletion, and recovery.
Restrict technical-review and rights-approval roles separately. Never mark content
professionally reviewed simply to bypass an Agent source gate.

The publication preflight uses bounded heuristic secret patterns. It is not a
complete secret scanner, dependency audit, or proof of absence of sensitive data.
Review the exact release manifest and staged diff before publishing.

## v0.6 Identity Platform MFA

All Firebase-authenticated private APIs require verified email and SDK-verified reserved second-factor sign-in claims. First-factor-only users may call only the limited enrollment-status route and public endpoints. Production cannot disable this policy or use emulator/dev identities. High-risk changes additionally require recent authentication. See `docs/gcp-mfa-setup.md` for required live tests and recovery controls. The current release has not received an independent security audit; do not send real secrets in public issues.
