# SEC submissions adapter validation

Scope #2/#8/#24 under #5; `sec-submissions-1`. Sources and operating limits: [pilot](../../docs/ASU_FILING_PILOT.md). Two reference-only feed proposals, zero actual acquisitions/discovered rows/filing bodies or professional approvals. Existing ASU references remain separate. No live endpoint call, model, cloud, charge or notification was performed.

Observed commands on September 27, 2026:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_sec_submissions.py backend/tests/test_crossref_discovery.py`: **73 passed** before the last three submissions-only robustness cases.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/submissions-backend.xml`: **1019 passed / 29 optional PostgreSQL skips / zero failures**, 52.45 seconds, before those last three additions.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_sec_submissions.py`: final **38 passed**, including overflow/row budget, empty snapshot/history interval and a real API reference-registration denial with a synthetic transport that received zero calls.
- `backend/.venv/bin/ruff check --select F` on changed Python modules/tests: passed.
- `backend/.venv/bin/python scripts/export_contracts.py`: regenerated actual parser enum/API schema.
- `check_content.py`, `check_queue.py`, `content_progress.py --check`, `sec_core_progress.py --write` and `--check`, `release_preflight.py --check`, `git diff --check`: passed.

Tests use original synthetic metadata, transport receipts and explicit synthetic rights fixtures. They verify deterministic exact record hashes/locators, separate dates, different submitter/registrant CIKs, unsafe/unknown/uneven values, no guessed amendment predecessor, missing primary documents, immutable/idempotent discovery, and the ban on staging metadata as filing-body evidence. No independent professional review is implied. One upstream Starlette/httpx deprecation warning remains; no application test failure was observed. No frontend/migration code was changed or local build/migration rerun claimed.

Next real gate: actual operation authorization/contact configuration, followed by retained root and linked-history snapshots, accession reconciliation and exact filing-body acquisition. Other content-family work and secure parsers remain active independently. External scheduling is not activated.

## Publication receipt

Published directly on main as [ae48a73](https://github.com/ChipmunkRPA/open-source-accounting/commit/ae48a73b0736cda6505e6359c30f840f0702db18). [CI 36375135885](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36375135885) passed on Python 3.11 and 3.13: each **1022 backend passes / 29 optional PostgreSQL skips**, then **29 PostgreSQL passes**, **16 identity tests / zero failures**, frontend production build, **43-table** migration round trip/schema parity, contracts/content/queue/publication checks and Docker build. These are actual final combined results, including the three final robustness tests.
