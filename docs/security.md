# Security and content-rights implementation notes

Implemented boundaries: explicit production configuration validation; Firebase server token verification
adapter; private workspace checks before read/write/retrieval; operation-specific source rights;
unknown-source denial; separate admin and rights-approver actions; server-side paid gates; timestamped
webhook HMAC verification; bounded model inputs; non-executable text rendering; file size/format limits;
subprocess document parsing; optional ClamAV INSTREAM; private local/GCS storage adapters; sanitized
provider errors; restricted SEC utility with allowlisted hosts and no redirects; memo/source rechecks.

This list is not a security audit or certification. High-priority remaining review:

1. Real-origin authentication, identity lifecycle, password reset/MFA, CSRF/CORS/CSP deployment, Firebase
   account enumeration behavior and revoked-token scenarios; confirm social-auth choices.
2. Production PostgreSQL multi-worker contention, queue recovery, pool capacity and exactly how model
   call duplication is billed after crashes. New requests are not globally rate-limited by edge infrastructure.
3. Scanner networking/update health, parser/container sandbox hardening, hostile archives, large PDFs,
   path/resource isolation, and operating-system differences.
4. Private GCS IAM/retention/backups and user/account deletion; support operator break-glass access with
   accountable logs. No claim that 'not used for training' means zero provider retention.
5. Gemini live schema/tool safety, unsupported-citation and prompt-injection adversarial benchmark;
   model verification is not independent assurance.
6. Stripe API-version-specific reconciliation, refunds/disputes, taxes/receipts, event delivery retries,
   unknown event shapes, interrupted renewals, old invoices and reconciliation after downtime.
7. Source legal review and licensing. Approval metadata is an operator decision, not a legal safe harbor.
   Short-copy limits/anti-reconstruction across many chats are not a complete production defense here.
8. Human-led accessibility audit and full desktop/mobile E2E. The browser harness virtualizes history
   and storage and cannot prove deployed-origin security or WCAG conformance.

Default deployment never includes real proprietary standards or confidential user documents. A seed
reference identifies authority but does not claim that its text was inspected. Commercial Agent pricing
must be part of the actual permissions review. Do not use a publisher mirror/upload/search cache to
circumvent a restriction. No runtime decision automatically classifies a use as legally fair use.
