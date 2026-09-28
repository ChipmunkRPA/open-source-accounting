# Resumable corpus integrity reconciliation

This explicit operator client calls the authenticated intake API. It inventories existing database artifact records, then verifies a bounded number per invocation. It does not acquire publisher content or run unattended. Verification failures can place entire works on integrity hold. Use an approved environment/project/bucket and its read-cost authorization before running against GCS.

Supply a short-lived administrator ID token from the approved secret channel in `OSA_ADMIN_ID_TOKEN`. The server still enforces verified email, MFA, scoped role and recent authentication. Do not paste tokens into command arguments, issues, logs or state files. `report` needs no token or network.

From the backend directory, choose a private state path outside the repository and the actual approved API origin:

```sh
.venv/bin/python -m app.reconcile_integrity plan --base-url https://APPROVED-ORIGIN --state /PRIVATE-DIRECTORY/integrity.json
.venv/bin/python -m app.reconcile_integrity run --base-url https://APPROVED-ORIGIN --state /PRIVATE-DIRECTORY/integrity.json --steps 5
.venv/bin/python -m app.reconcile_integrity report --base-url https://APPROVED-ORIGIN --state /PRIVATE-DIRECTORY/integrity.json
```

Replace both placeholders; do not use these literal examples as a deployment configuration. Optionally add `--family SEC_RULES` (or another registry ID) to **plan** to partition the inventory. Family scope is frozen in the file; do not repeat the option for run/report. Other families are explicitly out of scope in that report. With no family filter, every registered family appears, including zero database counts.

`plan` only collects metadata; it refuses to overwrite an existing state file. Inventory is bounded to 10,000 artifacts per plan, collected using paginated IDs. Collection spans time and is not an atomic database snapshot. Additions or changes after collection require a new plan. A family larger than that limit requires further operator partitioning capability before this client can cover it; it must not be reported complete.

`run` processes 1–25 pending artifacts (default five), sending the inventoried raw hash as a server precondition. Each result is written atomically and fsynced before proceeding. Private mode-600 state and a process lock prevent ordinary disclosure/concurrent overwrites. State and observation checksums detect accidental alteration; they are not signatures or protection against a privileged actor rewriting hashes. Redirects, environment proxies and non-loopback plain HTTP are refused/disabled. Requests use a bounded timeout and no client retry loop.

Transport errors, rate limits, server errors and expired authentication pause with the current item pending. Refresh authentication through the normal secure channel before resuming. If a response was lost after a server commit, resume can repeat that verification/audit observation; it does not automatically release a hold or repeatedly increment an existing one. Denied permissions and stale/missing/over-limit records remain explicit terminal results for that inventory. To retry those after remediation, create a new plan. No terminal error counts as verification success.

Report units are deliberately separate: inventoried artifact records, raw-byte verified/failed, denied, unobserved, and artifacts whose work was held at observation time. Hold counts overlap the other columns. Normalized extraction statuses cover only units returned by observations, not a reconciled extraction inventory. `pending` counts requests not processed, not artifacts approved. New objects, later corruption, later holds, later rights changes, publisher authenticity, corpus completeness, professional review, indexing and evaluations are not inferred from a completed scan. Results remain private; do not commit state or upload it to a public issue. The existing private server audit contains each completed verification observation.

Hold release and re-review remain separate operations described in [editorial review operations](EDITORIAL_REVIEWS.md). No real source or Cloud storage was accessed during development tests of this client.
