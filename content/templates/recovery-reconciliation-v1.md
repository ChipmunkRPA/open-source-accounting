# Recovery evidence workpaper: reconcile files, transactions and service readiness

> **AI-assisted editorial draft — not professionally reviewed.** Version 1.0.0, 2026-09-29. All entities, times, amounts, targets and events below are fictional and original. This is an educational workpaper, not evidence of a recovery performed for any real organization or a prescribed audit procedure.

## Sources and verification

National Institute of Standards and Technology, *The NIST Cybersecurity Framework (CSF) 2.0*, NIST CSWP 29, published February 26, 2024, [official publication](https://doi.org/10.6028/NIST.CSWP.29), physical PDF page 25 / printed page 20, includes backup and logging topics PR.DS-11 and PR.PS-04. [nist-csf-2-0] These provide context; NIST does not establish the fictional targets, financial reconciliation or procedures in this workpaper. Applicable accounting, auditing, contractual and legal criteria must be established separately.

The retained original was retrieved September 29, 2026, SHA-256 `3c31f46fee98cac0c4323453e5109291a213b4de7fef8c058af9bf67f717433c`. The existing source record documents an AI-assisted selected-page locator check, not independent professional approval or complete publication review. This exercise adds no new source acquisition or current-edition verification. Financial-reporting conclusions and entity-specific applicability remain primary-authority gaps.

## Fictional recovery timeline and explicit targets

Harbor Ledger's assumed policy measures recovery time from incident declaration until independently authorized service release, and data-loss exposure from the latest consistent restored transaction point to the incident cutoff. All timestamps below are UTC on the same fictional day, with no clock skew. The assumed targets are at most 120 minutes for recovery time and at most 15 minutes for potential data loss. They are stipulated for arithmetic only; they are not recommended defaults.

| Event | UTC time |
|---|---|
| Latest consistent restored transaction | 13:45 |
| Incident declared and transaction cutoff | 14:00 |
| Files copied into recovery environment | 14:32 |
| Database recovery completed | 14:48 |
| Reconciliation completed | 15:20 |
| Authorized service release | 15:35 |

Measured recovery time is **95 minutes**, leaving **25 minutes** against the assumed 120-minute target. Potential data-loss exposure is **15 minutes**, exactly the assumed limit. File copying alone took 32 minutes; using that as the end of recovery would omit database recovery, reconciliation and release authorization. A copied file's modification time is not proof of a consistent transaction point.

The 15-minute interval does not prove that any transaction was lost. Examine logs, queue acknowledgments, external confirmations and the restored database. Conversely, an apparently empty queue does not prove zero loss when acknowledgments or logs are unavailable. Record unknown outcomes explicitly.

## Reconcile the exposure interval before proposing corrections

Assume an independently reconciled posting log establishes the following four events after 13:45 and through 14:00. Amounts are fictional dollars. These are signed changes in an illustrative balance, not complete journal entries.

| Event ID | Signed change | Restored state |
|---|---:|---|
| E101 | 1200 | Present once |
| E102 | -200 | Missing |
| E103 | 500 | Missing |
| E104 | -100 | Present once |

The authoritative comparison population totals `1200 - 200 + 500 - 100 = 1400`. Restored events total `1200 - 100 = 1100`. The missing signed difference is **300**. Two of four events are absent, but that 50% count does not measure financial materiality or authorize a correction. Validate the comparison log's completeness and exact cutoff before treating it as the population.

For this example, restoring the missing events once would reconcile the illustrative balance. In a real system, establish each event's business state and idempotency key before replay. A payment may already have reached an external bank even if the local database row is missing. Blindly resending it can duplicate the economic event. Reconcile the external state, propose a bounded recovery action and obtain the actual required authorization. This workpaper does not authorize posting entries or transmitting payments.

A zero net difference is insufficient: missing +500 and -500 events offset financially while both remain absent. Compare event identities, counts, signs, currency, entity, dates and relevant dimensions, as well as totals. Do not combine currencies or unrelated entities into a reassuring net number.

## Evidence and decision template

| Field | Evidence to retain | Unresolved condition |
|---|---|---|
| Incident scope | Systems, entity, UTC cutoff, declaration and affected interfaces | Unknown cutoff or inconsistent clocks |
| Recovery criteria | Actual approved targets, start/end definitions and decision owner | Unapproved targets or changed definitions |
| Backup identity | Immutable object/version IDs, hashes, creation evidence, encryption/key availability | Manifest created only after the suspected corruption |
| Consistency | Database recovery point and matching object/index versions | Files individually match but database references another revision |
| Transaction comparison | Source population, exact event IDs, counts, signed amounts and external state | Incomplete logs, duplicates or unmatched acknowledgments |
| Authorization | Proposed replay, expected result, idempotency test and revision-bound approval | Approval is missing, stale or for another plan |
| Service verification | Identity/MFA, permissions, read/write behavior, queues and evidence exports | A healthy process responds while workflows remain broken |
| Review and release | Actual reviewer, exact workpaper revision, findings, unresolved exceptions and release record | A copied signature or automatic success flag |

## Exceptions and reporting limits

Hash equality proves equality to the selected baseline bytes; it does not prove that the baseline was complete, authentic or uncorrupted. A manifest first created after an incident is an observation, not independent proof of the pre-incident state. Preserve the original baseline and investigate differences rather than editing expected hashes to obtain a match.

A same-host temporary restore does not test loss of that host, unavailable keys, a region outage or remote retention. A successful database restore does not by itself verify source artifacts, derived indexes, access restrictions or deletion obligations. Preserve the scope of each test and list untested dependencies.

If a source's use permission expired, a recovered copy does not renew it. Keep retention, restore access, public display, model use and export permissions separate. Recovery should also reconcile deletion records so an old backup does not silently reactivate removed personal or licensed material.

Report measured times, confirmed missing/duplicate events, unreconciled amounts and unavailable evidence separately. Do not convert an unresolved exception into a successful recovery merely because the assumed time targets were met. This draft needs actual independent technical review before use as approved evidence.

Original educational text © Open Accounting contributors, licensed under CC BY 4.0. Source attribution does not imply NIST endorsement or transfer rights in separately referenced material.
