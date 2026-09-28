# Spreadsheet parser validation — 2026-09-28

Scope: private XLSX/CSV upload and Agent extraction limitations, #24/#29/#31 under #5. Version `spreadsheet-cells-1`. No actual content acquisition, professional review, index admission or model call.

Observed local checks:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_spreadsheet_parser.py backend/tests/test_docx_parser.py`: **58 passed** before final package-type/phonetic/default-style hardening.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_spreadsheet_parser.py`: final **37 passed** with the additional package, scalar/footer and default-style hardening cases.
- `cd frontend && npm run typecheck && npm run test:auth && npm run build`: passed typecheck, **16 identity tests**, production build.
- `backend/.venv/bin/ruff check --select F` on changed Python modules/tests: passed.
- `backend/.venv/bin/python scripts/export_contracts.py`: passed, no public API schema change.
- Content/queue checks passed. Generated progress/publication/diff checks run before publication.

Fixtures are original synthetic ZIP/XML and CSV data. Tests cover formula/cache distinctions, hidden/merged context, exact sparse cell locations, leading zeros/signs, physical CSV lines, workbook dates/declarations/footers, unsafe archives/XML/links/embeddings, unsupported visuals/tables, package-type checks, default styles, limits, upload/storage and Agent guardrails. Unsupported upload stores no document; CSV/XLSX use the existing private deletion/access pipeline. No browser journey or local PostgreSQL/migration rerun is claimed for this slice. One upstream Starlette/httpx warning remains. No application test failures observed.

The full local regression before final hardening observed **1056 passed / 29 optional PostgreSQL skips / zero failures** in 60.62 seconds (`PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/spreadsheet-backend.xml`). Final CI below verifies the combined code and additional tests. Source-family coverage is unchanged; these tests do not supply real financial workpapers or licensed data. See `docs/SPREADSHEET_EXTRACTION.md` for supported structures, original-byte retention and remaining source-intake/format-review work.

## Publication receipt

Published directly on main as [5624adb](https://github.com/ChipmunkRPA/open-source-accounting/commit/5624adb90b7b996524c5bacffeac24b33dc8781e). [CI 36376001645](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36376001645) passed on Python 3.11 and 3.13: each **1059 backend passes / 29 optional PostgreSQL skips**, then **29 PostgreSQL passes**, **16 identity tests / zero failures**, frontend production build, **43-table** migration round trip/schema parity, contracts/content/queue/publication checks and Docker build. This verifies the final combined implementation and all 37 spreadsheet cases.
