# Retrieval evaluation

Issues #25/#36 under #5. `retrieval-evaluation-2` executes the production lexical retrieval, source permission/applicability filters, spreadsheet companion/authority selection, evidence persistence and runtime evidence validation in freshly created temporary SQLite databases or isolated schemas in an explicitly confirmed empty local PostgreSQL test database. It cannot accept a production database URL. No model, network acquisition or external service is called. Temporary synthetic review identities and attestations are isolated from operator data and **never count as professional reviews**.

## Corpus and units

`evaluation/retrieval-engineering-1.json` is original CC0 fictional material: 16 development-regression cases, not a held-out accounting benchmark. Every case binds facts, framework/entity/reporting period/known-as-of date/audit regime, source text and version, relevant/forbidden source or document IDs, expected fictional claims and citation-source bindings, alternatives, missing facts, abstention conditions, optional numerical-check specifications and an explicit evidence cap. Source/admission fixtures, exact relationship endpoints and all observed body/citation hashes are recorded. A strict schema rejects invented adjudication status, duplicate IDs, unknown/conflicting expected resources and invalid relationship/claim citations.

The cases exercise definitions, exceptions, conflicting rule versus company practice, a historical transition, public-availability cutoff, wrong framework/audit regime, reference-only material, disabled rights, missing technical review, another workspace's document, an explicitly selected private document, untrusted injection text as retrieved data, and no supporting source. The injection case **does not measure model resistance**; no model executes it. Foreign-document selection probes retrieval's defense in depth, not an authorized cross-workspace API workflow.

Precision and recall use **unique source/document records whose bodies were selected**, excluding reference-only hits. They do not measure paragraph relevance, entailment, whole-document completeness or accounting correctness. Duplicated lexical/coordinate packets for one source do not inflate these denominators. Empty relevant/retrieved denominators are null, not perfect scores. Exact saved hashes/locators and current evidence checks are reported separately. Relationships retain both exact endpoint contexts; citation existence does not prove claim support.

Each case has only zero to two public source records, plus at most one private document. These cases are not a scale or production-performance benchmark. The existing independent 10,001-source PostgreSQL test remains a synthetic index-mechanics check, not a professionally adjudicated corpus.

## Run and compare

From the repository root:

```sh
PYTHONPATH=backend backend/.venv/bin/python scripts/evaluate_retrieval.py \
  --output /tmp/retrieval-evaluation.json \
  --review-packets /tmp/retrieval-review-packets.json

PYTHONPATH=backend backend/.venv/bin/python scripts/evaluate_retrieval.py \
  --output /tmp/retrieval-replay.json \
  --baseline /tmp/retrieval-evaluation.json \
  --diff-output /tmp/retrieval-diff.json
```

The report records corpus/case hashes, source versions/body hashes, observed source revisions, saved evidence/relationship bindings, all application Python code hashes, Python/SQLite versions and per-case latency. Latency includes retrieval, relationship expansion, persistence and validation; fixture setup, authorized index builds and model work are excluded. Generated review IDs/revisions differ across isolated runs. Compare case hashes and metrics, not random review IDs. Comparisons require identical corpus version/hash/mode/split, case membership and case hashes. They preserve metric deltas, newly missed units and regressions; latency differences are informational, not an approved SLO.

The command returns nonzero for forbidden body retrieval, invalid evidence, a declared fictional recall regression, an execution error, or a regression against a supplied baseline. Failed cases stay in the report with a safe error category. No raw exception text or private fixture text is emitted as a failure message. The development gate is not a production release threshold. Source-support accuracy, numerical correctness, model abstention accuracy and live cost remain **null**, and workflow executions/model calls/professional adjudications remain **zero**.

The initial observed run retained a deliberate capacity gap: `bounded-definition-gap` returned one of two relevant source records (recall 0.5). The other ten nonempty relevant cases returned all annotated source/document records. `lexical-false-positive` also selected a permitted but irrelevant astronomy record (precision 0.5); this is reported even though it is not a rights violation. No forbidden body was retrieved. This is a result on 16 authored fictional cases, not an estimate of real-world precision or safety. The exact report is `reports/retrieval/engineering-evaluation-20260928.json`; observations include limitations and per-case denominators.

CI executes this harness on Python 3.11 and 3.13 and uploads both reports and draft review packets alongside test XML, including failed-run artifacts. It does not promote educational questions, fixtures or mock output to professionally approved evidence.

## Actual adjudication remains pending

Reviewer packets preserve each complete fictional case, observed retrieval and specific review questions. They carry `draft_not_professionally_adjudicated`, no professional reviewer records and no approved release threshold. They are inspection inputs, not an approval-import mechanism. Reports are unsigned local observations; hashes bind their contents, not reviewer qualifications or authenticity.

The 58 educational questions remain separate. No proprietary exam bank, real standards text, customer document or professional outcome is included here. Preparing permitted real cases across the five core topics and every enabled workflow, obtaining qualified independent source/claim adjudications, establishing secure held-out sets excluded from prompt authoring/training, and approving risk-based release thresholds remain open. Large-corpus PostgreSQL/semantic ranking, real provider canaries under explicit budgets, entailment/conflict decisions, numerical scoring and actual cost measurements need their own evidence. No paid resources, source licenses, model substitutions or real professional approvals are authorized by this harness.


## PostgreSQL mode and engine comparison

`--postgres` requires `OSA_DISPOSABLE_TEST_DATABASE=true` and `OSA_EVALUATION_POSTGRES_URL`. The URL must use `postgresql+psycopg`, a loopback connection or local Unix socket, and a database named `osa_eval_<test name>`. Only host/port query overrides are accepted. The operator must create this disposable database beforehand. Do not point this at any application database; the runner rejects pre-existing user schemas, public tables/views/functions/types and concurrent evaluation ownership before creating fixtures.

An advisory lock protects evaluation ownership. Each case gets a generated schema and connection search path; all 48 model tables and the real PostgreSQL full-text indexes are created there. Text indexing calls the production `source_search.rebuild` only when current operation/review gates permit it. Reference-only, disabled and technically unreviewed bodies remain unindexed. Case schemas are removed on success or failure; unrelated objects are not deliberately cleared to make the database eligible. No URL, password or socket path is written into the report.

Example, after securely configuring an empty local test database:

```sh
PYTHONPATH=backend backend/.venv/bin/python scripts/evaluate_retrieval.py   --output /tmp/sqlite-v2.json

OSA_DISPOSABLE_TEST_DATABASE=true PYTHONPATH=backend   backend/.venv/bin/python scripts/evaluate_retrieval.py --postgres   --output /tmp/postgres-v2.json --baseline /tmp/sqlite-v2.json   --diff-output /tmp/engine-diff.json --cross-engine
```

A normal baseline comparison still rejects different modes. `--cross-engine` explicitly permits a SQLite/PostgreSQL pair only with identical evaluator/corpus versions and application code hashes. It reports per-case precision/recall and latency deltas without approving deployment or an SLO. Version-1 observations remain historical; regenerate both sides with version 2 instead of treating old and new schemas as identical.

The initial PostgreSQL 17.11 local run built **20 permitted source-index instances** across 16 isolated cases, with **17 valid body-binding checks** and zero forbidden bodies. Defined precision/recall matched SQLite; empty-denominator metrics stayed null. Both engines retained the 0.5 recall capacity gap and 0.5 precision lexical false positive. Recorded artifacts: `reports/retrieval/engineering-sqlite-v2-20260928.json`, `engineering-postgres-v2-20260928.json` and `engineering-engine-diff-20260928.json` in the same directory. Index creation is excluded from retrieval latency, and these tiny fixtures do not show that PostgreSQL always chooses a GIN plan or establish real accounting relevance.

Fresh-schema execution exposed a SQLAlchemy import-order error in generic `func.to_tsvector` model-index declarations. Both indexes now construct the PostgreSQL-specific `to_tsvector` explicitly; migration round-trip/parity verifies this does not introduce an unintended schema change. CI creates a separate empty `osa_eval_ci` database, tests isolation/refusal/cleanup, executes the PostgreSQL corpus, and retains the explicit engine comparison alongside both reports.

## Exact passage reuse

The subsequent selection fix reuses a lexical passage as an exact relationship endpoint only when source identity, title/category/access, policy version, literal text and absolute character interval agree. Ordinary paragraph locators are reconstructed against the current source, so repeated text at different positions is not interchangeable. Intake passages additionally require an exact current provenance packet. Both endpoints still pass independent rights, technical and applicability checks; replacement occurs only when the complete pair fits the evidence and metadata budgets. Later lexical copies do not reappear. Existing coordinate endpoints and spreadsheet companion bindings are not rewritten; SEC Core packets retain their existing selection behavior.

The immutable `retrieval-engineering-1` corpus now measures **1.0 recall** in `bounded-definition-gap` on both SQLite and PostgreSQL, within the unchanged two-record cap. The lexical false-positive case remains **0.5 precision**. Historical reports remain intact; the new `engineering-{sqlite,postgres}-reuse-20260928.json`, `engineering-reuse-before-after-20260928.json` and `engineering-reuse-engine-diff-20260928.json` preserve the observations and comparisons. This changes selection, not the persisted relationship snapshot contract or professional-review status. Claim entailment, live model evaluation and real corpus coverage remain unverified.
