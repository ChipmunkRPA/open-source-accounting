# DOCX extraction validation — 2026-09-27

Original synthetic packages only. No actual source acquisition, accepted legal revisions, reviewer approval, cloud/model call or deployment.

Observed commands:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_docx_parser.py backend/tests/test_documents_agents.py backend/tests/test_pdf_parser.py --junitxml=/tmp/osa-docx-targeted.xml`: **66 passed**, 8.46 seconds after merge diagnostics and package-part checks.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/osa-docx-backend.xml`: **955 passed / 28 optional PostgreSQL skips / zero failures**, 59.27 seconds, before final two edge cases.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_docx_parser.py --junitxml=/tmp/osa-docx-final.xml`: final **24 DOCX cases passed**, 1.73 seconds, including tracked table-grid changes and duplicate relationship identities.
- `backend/.venv/bin/ruff check --select F backend/app/docx_parser.py backend/app/services/documents.py backend/app/parse_worker.py backend/app/agents/workflows.py backend/tests/test_docx_parser.py`: final passed.
- Actual API/model schema export and unchanged-schema diff, content and queue checks passed: 63 items / 26 references / 58 questions / 3 arithmetic checks; 38-task DAG / 32 family recipes / 63 baseline hashes / 47 topics / 16 workflows.

Initial failure: merged-cell fixture correctly blocked but reported generic inconsistent grid instead of the specific merge reason. Moved merge detection before grid-count validation; rerun passed. Initial lint reported one unused test import, removed. One upstream Starlette/httpx warning remains. No frontend/schema migration changed; local frontend/PostgreSQL/migration checks were not rerun in this slice.

Fixtures cover interleaved paragraphs/tables, numeric/empty cells, header declarations and exact paths/hashes, chunk ranges, tracked revisions/comments/hidden text/fields/graphics/content controls, merged cells, supplemental stories, hyperlinks without fetching, unresolved numbering metadata, malformed/unsafe/ambiguous archives and relationships, no-row upload failure, and new-versus-legacy workflow limits. Temporary JUnit files are local test receipts, not source/review evidence. Known unsupported scope: `docs/DOCX_EXTRACTION.md`.

Published on main as [bd3a0fd](https://github.com/ChipmunkRPA/open-source-accounting/commit/bd3a0fd7d18cb167286848f8ca4735b1abbe6a83). [CI 36370426002](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36370426002) passed the final combined code on Python 3.11 and 3.13: each **957 backend passes / 28 optional skips**, followed by **28 PostgreSQL passes**, **16 identity tests / zero failures**, frontend production build, **41-table** migration round trip/schema parity, contracts/content/queue/publication checks and Docker build. Generated-progress, publication preflight and diff checks passed before publication.
