# Google Cloud Gemini contract — #26 / parent #5

Observed **2026-09-27**, public documentation only. No ADC discovery, inference,
project inspection or paid resource operation was performed. This is not proof of
access in an operator's project or a completed staging acceptance test.

## Public contract and routing

Google's [3.8 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash)
(“Model specifications”, “Basic request”, “Mandatory API rules”) lists
`gemini-3.8-flash` as GA. It documents REST v1 `generateContent`, and a Python
`google-genai` example with `enterprise=True`. LOW/MEDIUM/HIGH thinking are
supported; MINIMAL is not. We retain REST with ADC rather than changing SDKs.
Installed/locked transport: `google-auth 2.58.1`, `requests 2.34.2`. No
`google-genai` package or live SDK execution was verified. No model substitution
is allowed. Server validation of structured JSON remains mandatory.

The [Cloud endpoints page](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations)
(“Multi-region endpoints” host table and REST example; global endpoint note)
documents these routes:

| Configured location | Host |
|---|---|
| `us` | `aiplatform.us.rep.googleapis.com` |
| `eu` | `aiplatform.eu.rep.googleapis.com` |
| `global` | `aiplatform.googleapis.com` |

All use `/v1/projects/{project}/locations/{location}/publishers/google/models/gemini-3.8-flash:generateContent`.
The prior `{us,eu}-aiplatform.googleapis.com` construction was incorrect for these
multi-regions. Location is never rewritten. `us` in examples remains a proposed
configuration, not operator approval. Network/private-connectivity and data
residency acceptance still require the chosen deployment's review.

Project IDs follow the [Resource Manager projectId format](https://docs.cloud.google.com/resource-manager/reference/rest/v3/projects).
Path/query/fragment input, arbitrary hosts, other models and unverified locations
are rejected before transmission. HTTP redirects and automatic auth replay are
disabled. ADC uses the Cloud Platform scope; credentials remain backend-only.

## Implemented limits and response handling

The application allows text turns only, at most 20, ending with a user turn.
The complete serialized request (including system prompt and schema) is capped
at 180,000 bytes. Application output caps cannot exceed 8,000 tokens. HTTP uses
10-second connect / 90-second read timeouts and a 4 MiB decompressed response
limit. These are request controls, **not a guaranteed wall-clock or dollar cap**.
No built-in search/URL/computer/code tools, provider file stores, cached-content
references, tuning, sampling overrides or candidate-count override are sent.

Only one complete STOP candidate is released. Unexpected tool/non-text parts and
grounding metadata are rejected. Hidden thought text is not displayed. Invalid
usage never becomes a fabricated zero, and a new call clears previous usage and
model-version metadata. Valid usage remains available on the adapter even when
output/schema checks fail. Nothing logs raw requests, provider errors or bodies.

The [REST response reference](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/v1/GenerateContentResponse)
(“Candidate.finishReason”, “UsageMetadata”) defines completion and separate prompt,
candidate, thinking and tool-result counters. Total consistency and nonnegative
integer counters are checked; cache counts cannot exceed input counts. Actual
model-version metadata is retained separately from numeric usage.

401/403/404/429/503 and timeout failures produce safe categories. This slice does
not retry inference: an ambiguous timeout can already have incurred charges.
Bounded backoff, durable per-attempt accounting, a total execution deadline and
in-flight cancellation remain #26 work. Existing worker lease recovery is not
provider request idempotency; cancellation checkpoints cannot recall a request.

## Dated cost estimate, not a spend approval

Google's [pricing table](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing)
(“Gemini 3”, Standard rows for 3.8 Flash, observed 2026-09-27) gives these USD rates
per million tokens. Output includes reasoning.

| Rate period | Global input / output | US or EU input / output |
|---|---|---|
| Through 2026-12-31 | 0.75 / 3.75 | 0.825 / 4.125 |
| Starting 2027-01-01 | 1.50 / 7.50 | 1.65 / 8.25 |

`gemini_costs.estimate_usd` applies that dated snapshot using Decimal arithmetic.
It assumes Standard text requests with **no cached-input discount**. It excludes
priority/batch, tools, cache storage, other services, taxes and negotiated terms.
Dates before observation and unknown models/locations are rejected. Future
estimates use the published schedule, not a guarantee against later repricing.
Recheck before approving staging or production spend.

The formula is `(prompt tokens × input rate + (candidate + thinking tokens) ×
output rate) / 1,000,000`. A synthetic US request with 1,000,000 input and
1,000,000 combined output/thinking tokens estimates $4.95 under introductory
rates and $9.90 under the published later rates. These are calculations, not
measured application costs. No task allowance or subscription price is changed.

Actual live cost per successful Agent task remains **unmeasured**. It must include
every billable attempt (also schema failures, cancelled/failed tasks and retries)
in a cohort, divided by completed tasks, plus allocated non-model costs. The
[attempt ledger](MODEL_ATTEMPTS.md) now preserves known and unknown costs and
reports dated estimates for complete tracked cohorts. Legacy run usage alone is
not a complete cost ledger. Spend reservations and invoice reconciliation remain
unimplemented; synthetic estimates are not real bills or authorization to spend.

## Retention is a separate gate

Google's [retention documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention)
(“Training restriction”, “Customer data retention”, “In-memory data caching”)
distinguishes no training without permission from storage controls. It describes
conditional abuse logging, additional Advanced AI terms, optional request/response
logging, and default project-isolated in-memory caching with a 24-hour TTL.
Grounding and stateful APIs have different retention behavior. This application
does not enable those optional tools/APIs, but that does not establish the
project's actual cache or abuse-logging state. Verify account-specific terms,
exceptions, project logging/cache settings, region and each source-operation
authorization before transmitting protected text. No zero-retention assertion
or license grant is created by this document.

## Remaining acceptance and resumable work

Owner remains unassigned until an actual operator accepts. Required input:
approved GCP project, location, spend ceiling, secure workload identity, API/IAM
and model access, retention evidence, and staging authorization. Keep secrets
out of issues/chat. An eventual smoke must use synthetic/public authorized input
and record endpoint, resolved model version, request configuration, usage, dated
estimate and observed billing; exercise chat, planning, application-authorized
tool roundtrip, evidence synthesis and error behavior. No smoke was run here.

The [durable attempt ledger](MODEL_ATTEMPTS.md) now captures application calls,
including known usage from rejected outputs, and exposes explicitly incomplete
cost estimates. Budget reservations, bounded retry/cancellation/spend controls
remain under #26. Independently continue family
discovery and authorized import/review/index integration under #8. All 32 content
families remain required; this technical-document check adds no accounting
source acquisition, professional review or Agent evidence.

These are linked browser observations, not an immutable HTTP acquisition packet:
raw response bytes/headers/hashes and original issued/effective dates were not
captured. Revalidation must consult the official sources again. No source text
from these pages is entered in the accounting corpus.
