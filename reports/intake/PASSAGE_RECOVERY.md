# Fresh passage recovery revisions (#8/#23)

Observed full backend **830 passed / 25 optional PostgreSQL skipped**, before final retry-identity and ordinary-stage stale guards. Final combined source-intake/recovery run **37 passed**, including **10 new recovery cases**; recovery-only run **10 passed**. PostgreSQL contracts **26 passed**, including two concurrent recovery requests creating one new revision and retaining the prior binding. TypeScript/build, lint F and API contract passed. No schema or new migration assertion; reused migrated disposable 40-table PostgreSQL database. Implementation [89c7fa2](https://github.com/ChipmunkRPA/open-source-accounting/commit/89c7fa270475168bf169c5732f2eec0c04914f37) passed [CI 36364288334](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36364288334): Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker. Content/hash/queue/generated-progress/publication checks passed.

```sh
backend/.venv/bin/python -m pytest backend/tests/test_passage_recovery.py -q --junitxml=reports/intake/passage-recovery-targeted.xml
backend/.venv/bin/python -m pytest backend/tests/test_source_intake.py backend/tests/test_passage_recovery.py -q --junitxml=reports/intake/passage-recovery-final.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/passage-recovery-backend.xml
# Explicit disposable PostgreSQL URL and flag supplied through environment:
backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/passage-recovery-postgres.xml
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

No failures; one upstream Starlette/httpx warning. Tests cover role/stale-hash/hold/current-binding rejection, raw/normalized/predecessor integrity, rollback after a later passage fails, idempotent recovery identity, tampered retry metadata, no copied approvals and old-source preservation. Rights approval alone still does not admit new model evidence. Browser: synthetic recovered work required acknowledgement, then produced one new source/predecessor pair with explicit no-approval/no-evidence-restoration message. Screenshot passage-recovery-ui.png. Temporary servers/tab stopped.

No real content repaired/acquired, no professional approval, paid resource, production, live inference/billing/SMS/notification. Recovery preserves publisher editions and source history; independent reviews/current permissions still required. No automatic reattachment of memos, indexes or prior evidence. Large extraction performance and live Cloud recovery remain unverified.
