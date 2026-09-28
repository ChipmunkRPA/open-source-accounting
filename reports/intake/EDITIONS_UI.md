# Multipart inventory UI validation — #8 / #23

Scope: source administrator `/editions` screen; no backend/schema/provider changes. Parent #5. Work directly on main per operator direction.

Observed local commands (2026-09-27):

- `npm --prefix frontend run typecheck` — passed.
- `npm --prefix frontend run test:auth` — 16 passed, zero failures.
- `npm --prefix frontend run build` — passed; local Identity Platform bundle produced.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_intake_editions.py -q --junitxml=reports/intake/editions-ui-targeted.xml` — 23 passed, zero failures; one upstream Starlette/httpx deprecation warning.

Browser: disposable local SQLite/demo identity, mock provider, loopback port 8782. Member denied scoped administration. Administrator created inventory revision 1 with one acquired synthetic component and one missing required appendix; report showed 1/2 required receipts. Saved revision 2 explicitly making the appendix optional, report showed 1/1 required and 0/1 optional with no complete-publication/approval claim. Inspected revision 1: historical warning, preserved 1/2 count, disabled Prepare next revision, and link to current revision. Existing extraction remained pending. Screenshot `editions-ui.png` contains synthetic data only. The prior temporary tab was automatically closed at turn end; reopened the same running demo and verified persisted revisions before saving the screenshot.

These are synthetic browser/API checks, not independent accounting review, live identity, source acquisition or GCP validation. No production database, source body, provider or paid resource was accessed. No new genuine acquisition, parsing, rights, technical/applicability approval, indexing or adjudicated evaluation coverage.

Limits: declared inventories are not independently verified publisher inventories. Real full-edition artifacts, byte/table reconciliation, professional approvals and corpus-scale measurements remain outstanding. Published directly on main as [ea15f1a](https://github.com/ChipmunkRPA/open-source-accounting/commit/ea15f1ac7934953af7b44bdb266b0206b0c3f3ba). [CI 36366824628](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36366824628) passed on Python 3.11 and 3.13: each observed **856 backend passes / 28 optional skips**, then **28 PostgreSQL passes**, **16 identity tests / zero failures**, frontend production build, **41-table** migration round trip/schema parity, contracts/content/queue/publication checks and Docker build. Local preflight and diff checks passed before publication. Disposable demo server and browser tab closed. CI retains the existing checkout Node 20 deprecation and upcoming runner-image notices.
