# Reviewer packets (#23)

Observed backend: **693 passed / 19 optional PostgreSQL cases skipped**, including **14 new packet/reference cases**. Initial targeted packet run had 13 passes; the additional private-SEC-note exclusion case passed in the full suite. Prior content/editorial/SEC targeted regression: 60 passed. No test failures. One upstream Starlette/httpx warning remains. New JUnit evidence: review-packets-backend.xml; initial targeted evidence: review-packets-targeted.xml.

Commands actually run from repository root:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_content_library.py backend/tests/test_editorial_ledger.py backend/tests/test_sec_core_integration.py -q
backend/.venv/bin/python -m pytest backend/tests/test_review_packets.py -q --junitxml=reports/intake/review-packets-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/review-packets-backend.xml
backend/.venv/bin/python -m ruff check backend/app/content.py backend/app/services/editorial.py backend/app/api/library.py backend/tests/test_review_packets.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
# From frontend:
npm run typecheck
npm run test:auth
npm run build
```

Frontend typecheck, 16 mocked auth tests and production Identity Platform bundle passed. No schema migration changed; no new local PostgreSQL or migration result is claimed. CI separately covers clean installs, PostgreSQL and Docker.

Browser: an isolated synthetic SQLite/mock application at 127.0.0.1:8779 showed the new Download review packet button. The click/download-event wait timed out after 30 seconds, resetting the tool session. Reattached to the existing tab: page remained healthy and console had no error/warning entries. No downloaded file path was returned. Therefore actual browser download completion is **unverified**, even though API export/rights/hash/limit tests pass. Cause is not established; recheck in a deployed supported browser. Temporary server and tab stopped afterward. Initial reads guessed two nonexistent file paths and one zsh glob; corrected with repository evidence, no modifications from those failed reads.

All decisions/data are synthetic. No actual full source acquisition, parsing, professional review, model inference, cloud provisioning or external transmission occurred. Reference metadata snapshots are not linked-publication revision verification. Public drafts remain unapproved; packet generation does not alter their gates.
