# Recovery evidence workpaper: reconcile files, transactions and service readiness

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

> **Editorial draft — not professionally reviewed.** Version 2.0.0, 2026-10-04. All entities, times, amounts, targets and events below are fictional and original. This is an educational workpaper, not evidence of a recovery performed for any real organization or a prescribed audit procedure.

## Sources and verification

National Institute of Standards and Technology, *The NIST Cybersecurity Framework (CSF) 2.0*, NIST CSWP 29, published February 26, 2024, [official publication](https://doi.org/10.6028/NIST.CSWP.29), physical PDF page 25 / printed page 20, includes backup and logging topics PR.DS-11 and PR.PS-04. [nist-csf-2-0] These provide context; NIST does not establish the fictional targets, financial reconciliation or procedures in this workpaper. Applicable accounting, auditing, contractual and legal criteria must be established separately.

The earlier reference record describes a retained original and selected-page locator check. Editorial review on October 4, 2026 re-read the official PDF's abstract, physical page 25 / printed page 20 (backup and logging), and physical page 28 / printed page 23 (RC.RP-03, RC.RP-05 and RC.RP-06). The recovery topics distinguish restoration-asset integrity, restored-service integrity and completion criteria. This is limited context, not a complete current-edition review, prescribed financial reconciliation, exact match to an earlier snapshot, or approval for any real recovery.

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

## Replay counterexample: a balanced plan can produce an unbalanced execution

Continue only the supplied four-event example. The restored signed total is 1,100. The intended missing events are E102 = −200 and E103 = +500. A correct once-only replay would give **1,100 − 200 + 500 = 1,400**. If E103 is mistakenly replayed twice, the result becomes **1,100 − 200 + 500 + 500 = 1,900**, exceeding the stipulated comparison by **500**.

A plan that lists the right missing events does not prove its execution was once-only. Retain the actual replay receipt for each stable event key and compare the post-replay population with the complete expected population. Reconcile both success and timeout results: a client timeout can occur after a server commits a change. Do not treat the absence of a client success message as proof that nothing happened.

This example does not authorize any replay or external payment. If an event corresponds to a real transfer, confirm its external economic state through authorized records and route consequential actions through the required approval or handoff. Restoring a local database row and resending a bank instruction are different operations.

## A dependency case: the database returns before the service can be released

In a separate fictional variation, keep the 14:00 incident start and database completion at 14:48, but suppose required supporting attachments cannot be verified until 16:09. Assume the approved release criteria require those attachments and the authorized release occurs at 16:09. The measured recovery time is **129 minutes**, which exceeds the stipulated 120-minute target by **9 minutes**. Reporting 48 minutes because the database was ready would use the wrong end event.

Conversely, if a limited read-only service is separately authorized at 15:00, state exactly which capability became available then and which remained unavailable. Do not call partial restoration full recovery. Preserve each release decision, dependencies, restrictions and user impact; a subsequent full recovery does not change the earlier partial status.

### Consistency requires relationships, not only matching file hashes

Suppose a restored invoice row points to attachment version V3, but only V2 is present. Both files may individually match their recorded hashes, yet the relationship is wrong. Validate the manifest linking the database revision, attachment version and any derived search index. A correct hash of V2 does not establish that V2 is the version required by the restored row.

A derived index may be rebuildable from authorized sources, but that does not mean a rebuild is already approved or complete. A restored credential, entitlement or source license also needs current validity; recovered bytes cannot recreate expired permissions. Reconcile retention and deletion records so recovery does not quietly re-enable material that should remain unavailable.

### Record the uncertainty that clocks cannot resolve

If the incident start is estimated within a ten-minute range, display that uncertainty instead of a falsely exact recovery time. If source systems use different timezones or unsynchronized clocks, preserve original timestamps and normalization assumptions. If the latest consistent restored point is unknown, leave potential data-loss exposure unknown. An attractive time metric cannot compensate for unverified transaction completeness or release authority.

## Free lesson and private workflow boundary

This original educational article remains free under CC BY 4.0. Premium can license private software workflow execution where available and authorized; it does not convert a public document into proprietary standards, grant source-processing rights, or supply professional approval. No real procedure, source grant, posting, model execution or review signature is created by these examples.

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
