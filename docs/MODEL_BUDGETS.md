# Model spending reservations — #26 / parent #5

Live application inference now requires `MODEL_BUDGET_ID` naming an active,
unexpired operator authorization for the exact provider/project/location/model
and verified price catalog. Empty configuration denies live chat and Agent
dispatch. Mock mode needs no funding. This does not authorize any actual spend,
change the $89.99 annual price, create a monthly allowance or charge a user for
overages. Free chat remains free; exhausted hosting funds do not require payment
from a Free user.

## Operator authorization

An operations administrator with recent verified sign-in can submit
`POST /api/v1/admin/model-budgets`. The typed request binds exact routing, total
USD limit, per-call reservation, expiry, current catalog version, an opaque private
approval-evidence reference/hash, and explicit Boolean attestation of actual
operator spending authorization. An API flag is not independent proof of consent:
the real operator must approve these exact terms first. Codex must not create a
real authorization merely because the API exists. Tests use synthetic attestations.

Authorization terms and digest are immutable. An identical resubmission returns
the existing record, including its revoked state, without adding funds. There is
no reset, edit, refill, auto-renewal or reactivation endpoint. A different envelope
requires a new explicit approval and explicit runtime selection; total possible
spend across envelopes is additive, not a single account-wide cap. Old unknown
liabilities remain attached to their original envelopes. Unbudgeted legacy unknown
liabilities in the same routing scope block admission pending reconciliation.

`GET /api/v1/admin/model-budgets/{id}` shows limit, held, committed and available
amounts. `POST .../{id}/revoke` requires the expected terms digest and recent admin
authentication. Revocation prevents subsequent admissions and is checked again
immediately before dispatch. Already transmitted requests cannot be recalled.
Rights approvers and ordinary members cannot authorize or inspect these budgets.
Source permissions, verified-email/MFA, subscription and workspace gates remain
independent and run as before.

## Conservative reserve basis

The [official model guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash)
(model specifications, observed again 2026-09-27) lists a 1,048,576-token context
and 65,536-token output limit. The reserve floor deliberately includes the entire
context and **two** output ceilings as a conservative allowance for output and
thinking, priced at the higher published post-intro rate in the
[dated catalog](GEMINI_CONTRACT.md). This doubled ceiling is our conservative
calculation, not an additional Google model specification.

The resulting minimum is USD 2.555904 for global and USD 2.8114944 for US/EU.
Operator-entered amounts support six decimals and must round upward sufficiently
to cover that floor. There is no default live dollar authorization. The maximum
API envelope is USD 1,000,000, always subject to explicit approval. Expiry cannot
exceed 30 days or the catalog's 2026-10-27 UTC review deadline. Reverification and
a new version are required beyond that date.

This conservative envelope is intentionally much larger than a typical small
request's estimate. It is an application admission control, **not a guarantee of
the Google invoice**. Changed provider limits/prices, unrelated resources,
requests outside this application, taxes and account arrangements are not capped
by it. Cloud budget alerts likewise are not represented as enforcement here.

## Atomic reservation and settlement

Before a live call, the same transaction that inserts its durable attempt receipt
conditionally increments held funds only when `held + committed + per_call <=
limit`. Integer nanodollars avoid floating-point undercounting. A conflicting
operation key or failed insertion rolls the reservation back. PostgreSQL and
SQLite both use the conditional update; no read-then-unlocked decrement exists.

Known pre-dispatch/non-200 failure releases the exact reservation atomically with
receipt settlement. An unknown outcome keeps it held indefinitely, including
after expiry/revocation/process death. A known estimate moves the **full reserved
amount** to committed funds, even if the estimate is much smaller. Committed here
means encumbered authorization, not measured expense. Estimates do not refill
funds. Duplicate settlements cannot credit or debit twice.

If an observed estimate exceeds its reserve, the larger estimate is committed,
the budget is disabled, the receipt is marked overrun and the answer is withheld.
This records the failure honestly; it cannot undo a provider charge already
incurred. No automatic retry is added. Every newly authorized retry must obtain
another reservation.

## Migration, limits and next work

`0008_budgets` adds one budget table and nullable receipt references/reservation
fields. It creates no authorization and does not erase or fund legacy usage.
Migration tests preserve a prior unknown model receipt and prior output ledger.
Production downgrade would remove this financial-control evidence and must use
an approved recovery procedure; tests run only on disposable local databases.

Still required: invoice-backed reconciliation with immutable evidence and
independent review before reducing held/committed funds; accounting for old
unbudgeted liabilities; bounded retries/deadlines/cancellation; efficient verified
per-request reservations; actual authorized staging, resolved model/version,
privacy/retention evidence and measured costs. No real budget has been created,
provider called, resource provisioned or production deployment performed by this
implementation. Continue all-family ingestion/review work independently while
operator and reviewer gates remain unresolved.
