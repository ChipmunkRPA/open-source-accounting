# ASU tracking validation — 2026-09-27

Scope: #5/#2/#9/#8/#24/#37. New free reference UI/API, versioned starter metadata, persistent identifier matches and daily authorized-corpus refresh. Main-only operator workflow; no new branch/PR.

Observed local results:

| Command / activity | Actual result |
|---|---|
| `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_asu_tracking.py` | 27 passed; synthetic date, metadata/URL, isolation/revocation, deletion, idempotence, crash rollback, pagination, SQLite concurrency and >2,000-source sweep cases |
| `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/asu-final-backend.xml` | 984 passed, 29 optional PostgreSQL skips, 0 failures, 63.39 seconds |
| `OSA_POSTGRES_TEST_URL=<disposable local socket DB> OSA_DISPOSABLE_TEST_DATABASE=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py` | 29 passed, 0 failures, 21.00 seconds; synthetic data only |
| `OSA_MIGRATION_TEST_DATABASE_URL=<empty disposable local socket DB> backend/.venv/bin/python scripts/check_migrations.py` | Upgrade, parity, downgrade, re-upgrade/parity passed; 43 application tables; existing ledger preserved |
| `cd frontend && npm run typecheck && npm run test:auth && npm run build` | Typecheck passed; 16 identity tests passed; production assets built |
| `backend/.venv/bin/ruff check --select F` on changed Python modules/tests | Final pass |
| `backend/.venv/bin/python scripts/export_contracts.py` | Actual API schema regenerated with three ASU routes |
| `check_content.py`, `check_queue.py`, `content_progress.py --check`, `sec_core_progress.py --check`, `release_preflight.py --check`, `git diff --check` | Passed |
| `python -m app.worker --once` against isolated local demo DB | Completed a real internal sweep of 7 source rows, 0 eligible filing passages, 0 detected mentions; no network/model calls |
| Actual in-app browser | Search 2025-08; Home BancShares early-adoption reference; adopted filter empty state; early-adopted filter restores result; member has no refresh control; admin keyboard refresh completes and timestamp changes; narrow/default and 1280px desktop layouts inspected |

Initial full backend pass was 982/28 skips before adding two robustness cases and the PostgreSQL contract. The final full pass above includes them. One upstream Starlette/httpx deprecation warning remains. An initial lint run found one unused import, corrected. The first disposable PostgreSQL connection used the OS username and failed (role absent); rerun with the existing test role succeeded. A browser pointer action did not activate the search and its subsequent wait timed out; keyboard submission and subsequent rendered/API results were verified. No application test failures were observed. The screenshot `tracking-desktop.png` records the original-data module, not professional evidence.

Content increment: 16 reference ASUs / 12 ASU-filing links / 2 filings / 2 companies / 9 ASUs with examples / 7 with no starter example. **0 full originals acquired, 0 real artifacts parsed, 0 new rights/technical/applicability approvals, 0 Agent admissions, 0 adjudicated evaluations.** The catalog is selected, not verified complete. Synthetic test fixtures do not increase those counts.

Versions: `asu-reference-2026-09-27.1`, `asu-mentions-1`, migration `0015_asu_tracking`. Existing intake parsers and requested `gemini-3.8-flash` unchanged. No live inference, paid resource, production deployment, charge, SMS, notification, license purchase or filing submission occurred.

Open gates: authorized live EDGAR discovery/acquisition for a defined company cohort; FASB index completeness and continuing metadata reconciliation; full artifact hashes/notices/exact dates; independent parser/accounting/applicability review; adjudicated adoption classification. Periodicity depends on the worker being run. The new worker refreshes authorized retained passages, not the external web. GCP project/region/spend and release approvals remain outstanding. See `docs/ASU_TRACKING.md` for the exact operating path.
