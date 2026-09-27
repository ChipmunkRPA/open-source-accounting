# SEC durable applicability reconciliation (#23)

The SEC route now accepts ApplicabilityDecision and appends to the existing private applicability ledger. General and SEC routes share locking, expiry, technical/parser binding, scope and evidence checks. Legacy SEC date flags grant no model access. SEC evidence requires explicit period end and reviewed framework/entity scope; period start and saved exports are checked too. No migration, approval backfill or actual content review.

Initial targeted SEC/general run: 27 passed before adding five new SEC cases. Initial full regression found one synthetic saved-evidence fixture missing required source_kind; corrected. Final regression: **758 passed / 21 optional PostgreSQL skipped**; receipt sec-applicability-backend.xml. One upstream Starlette/httpx warning remains.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_sec_core_integration.py backend/tests/test_applicability.py -q --junitxml=reports/intake/sec-applicability-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/sec-applicability-backend.xml
backend/.venv/bin/python -m ruff check backend/app backend/tests/test_sec_core_integration.py --select F
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

No new local PostgreSQL, migration, browser or live-provider test in this slice; schema unchanged. Existing applicability UI is exposed for SEC without a separate form. CI is checked independently after push.

New synthetic cases cover legacy-flag denial, expiry/revocation and saved-export withholding with preserved history, period-start mismatch, entity mismatch and absent period end. Existing SEC tests now require explicit ledger review before evidence admission. Fixtures do not count as human review. Actual SEC coverage remains 28 selected excerpts from seven sources, zero full HTTP original documents and zero real approvals. All-family scope remains unchanged. No paid resources or deployment.

Client migration: old SEC payload fields content_sha256/public_available_at/confirm_source_history_checked are replaced by the shared exact revision, public date, scope, evidence/expiry and attestation contract. Old payloads cannot create approvals. Historical flags are not silently converted to reviewed facts. The existing migration 0012_applicability is required. See docs/EDITORIAL_REVIEWS.md.
