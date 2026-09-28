# Retrieval evaluation

Issues #25/#36 under #5. `retrieval-evaluation-1` executes the production lexical retrieval, source permission/applicability filters, spreadsheet companion/authority selection, evidence persistence and runtime evidence validation in freshly created temporary SQLite databases. It cannot accept a production database URL. No model, network acquisition or external service is called. Temporary synthetic review identities and attestations are isolated from operator data and **never count as professional reviews**.

## Corpus and units

`evaluation/retrieval-engineering-1.json` is original CC0 fictional material: 16 development-regression cases, not a held-out accounting benchmark. Every case binds facts, framework/entity/reporting period/known-as-of date/audit regime, source text and version, relevant/forbidden source or document IDs, expected fictional claims and citation-source bindings, alternatives, missing facts, abstention conditions, optional numerical-check specifications and an explicit evidence cap. Source/admission fixtures, exact relationship endpoints and all observed body/citation hashes are recorded. A strict schema rejects invented adjudication status, duplicate IDs, unknown/conflicting expected resources and invalid relationship/claim citations.

The cases exercise definitions, exceptions, conflicting rule versus company practice, a historical transition, public-availability cutoff, wrong framework/audit regime, reference-only material, disabled rights, missing technical review, another workspace's document, an explicitly selected private document, untrusted injection text as retrieved data, and no supporting source. The injection case **does not measure model resistance**; no model executes it. Foreign-document selection probes retrieval's defense in depth, not an authorized cross-workspace API workflow.

Precision and recall use **unique source/document records whose bodies were selected**, excluding reference-only hits. They do not measure paragraph relevance, entailment, whole-document completeness or accounting correctness. Duplicated lexical/coordinate packets for one source do not inflate these denominators. Empty relevant/retrieved denominators are null, not perfect scores. Exact saved hashes/locators and current evidence checks are reported separately. Relationships retain both exact endpoint contexts; citation existence does not prove claim support.

Each case has only zero to two public source records, plus at most one private document. These cases are not a scale or PostgreSQL-ranking benchmark. The existing independent 10,001-source PostgreSQL test remains a synthetic index-mechanics check, not a professionally adjudicated corpus.

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

The report records corpus/case hashes, source versions/body hashes, observed source revisions, saved evidence/relationship bindings, all application Python code hashes, Python/SQLite versions and per-case latency. Latency includes retrieval, relationship expansion, persistence and validation; fixture setup and model work are excluded. Generated review IDs/revisions differ across isolated runs. Compare case hashes and metrics, not random review IDs. Comparisons require identical corpus version/hash/mode/split, case membership and case hashes. They preserve metric deltas, newly missed units and regressions; latency differences are informational, not an approved SLO.

The command returns nonzero for forbidden body retrieval, invalid evidence, a declared fictional recall regression, an execution error, or a regression against a supplied baseline. Failed cases stay in the report with a safe error category. No raw exception text or private fixture text is emitted as a failure message. The development gate is not a production release threshold. Source-support accuracy, numerical correctness, model abstention accuracy and live cost remain **null**, and workflow executions/model calls/professional adjudications remain **zero**.

The initial observed run retained a deliberate capacity gap: `bounded-definition-gap` returned one of two relevant source records (recall 0.5). The other ten nonempty relevant cases returned all annotated source/document records. `lexical-false-positive` also selected a permitted but irrelevant astronomy record (precision 0.5); this is reported even though it is not a rights violation. No forbidden body was retrieved. This is a result on 16 authored fictional cases, not an estimate of real-world precision or safety. The exact report is `reports/retrieval/engineering-evaluation-20260928.json`; observations include limitations and per-case denominators.

CI executes this harness on Python 3.11 and 3.13 and uploads both reports and draft review packets alongside test XML, including failed-run artifacts. It does not promote educational questions, fixtures or mock output to professionally approved evidence.

## Actual adjudication remains pending

Reviewer packets preserve each complete fictional case, observed retrieval and specific review questions. They carry `draft_not_professionally_adjudicated`, no professional reviewer records and no approved release threshold. They are inspection inputs, not an approval-import mechanism. Reports are unsigned local observations; hashes bind their contents, not reviewer qualifications or authenticity.

The 58 educational questions remain separate. No proprietary exam bank, real standards text, customer document or professional outcome is included here. Preparing permitted real cases across the five core topics and every enabled workflow, obtaining qualified independent source/claim adjudications, establishing secure held-out sets excluded from prompt authoring/training, and approving risk-based release thresholds remain open. PostgreSQL/semantic ranking, real provider canaries under explicit budgets, entailment/conflict decisions, numerical scoring and actual cost measurements need their own evidence. No paid resources, source licenses, model substitutions or real professional approvals are authorized by this harness.
