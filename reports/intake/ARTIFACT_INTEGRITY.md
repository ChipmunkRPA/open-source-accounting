# Stored artifact integrity (#8/#23)

Observed **809 backend passed / 24 optional PostgreSQL skipped**, including **11 new integrity tests**. TypeScript typecheck, production Identity Platform build, lint F, API contract and content/hash/queue/generated-progress checks passed. No test failures; one upstream Starlette/httpx warning. No new schema/migration or local PostgreSQL assertion. CI results recorded after observation.

```sh
backend/.venv/bin/python -m pytest backend/tests/test_artifact_integrity.py -q --junitxml=reports/intake/artifact-integrity-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/artifact-integrity-backend.xml
backend/.venv/bin/python -m ruff check backend/app/services/artifact_integrity.py backend/app/services/storage.py backend/app/api/intake.py backend/app/services/intake.py --select F
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
```

Tests cover private access/no approval, raw missing/corrupt/oversized states, parse retry denial, normalized missing/invalid passages, denied rights before reads, unrelated object-key rejection, redacted provider errors, separate raw/text permissions, mocked GCS bounded raw range/no retries/missing mapping, and local nonregular/path escape rejection. GCS contract checked against https://docs.cloud.google.com/python/docs/reference/storage/latest/google.cloud.storage.blob.Blob; no live bucket accessed.

Browser: disposable local SQLite/mock fixture, registered/acquired/parsed using the synthetic gateway only. Admin inspected the artifact and explicitly verified 113 raw bytes plus one normalized passage; expected/observed hashes matched. Screenshot artifact-integrity-ui.png. Tab/server stopped. No actual publisher source acquired, no rights/professional approval, no paid resources, deployment, live inference/billing/SMS or notifications.

Observations are point-in-time, stored in private audit records, not an atomic corpus inventory, authenticity attestation, professional decision or immutable external audit archive. No text is returned. No automatic repair, quarantine or downstream invalidation added. Corpus-wide verified coverage, remediation and live GCS remain outstanding.
