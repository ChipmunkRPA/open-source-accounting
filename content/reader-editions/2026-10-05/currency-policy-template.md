# Template: currency and exchange-rate policy evidence

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Editorial draft · v1.0.0 · 2026-10-04 · No professional review recorded.**

Link currency conclusions and rate selections to facts before configuring finance systems.

## Purpose

Link currency conclusions and rate selections to facts before configuring finance systems. This is a working template, not a complete mandatory disclosure or audit checklist.

## Workpaper fields

| Field | Entry |
|---|---|
| Entity / consolidation path | [Complete or explicitly mark unknown] |
| Books / functional / reporting currencies | [Complete or explicitly mark unknown] |
| Transaction type and amount | [Complete or explicitly mark unknown] |
| Rate quotation direction / source / date | [Complete or explicitly mark unknown] |
| Proposed measurement basis | [Complete or explicitly mark unknown] |
| Historical or average rate rationale | [Complete or explicitly mark unknown] |
| Settlement / remeasurement / translation bridge | [Complete or explicitly mark unknown] |
| Authority gap | [Complete or explicitly mark unknown] |
| Approver / effective configuration date | [Complete or explicitly mark unknown] |

## Completion procedure

Assign a stable item ID and retain source-document versions. Record assumptions separately from confirmed facts. Link evidence at a passage, clause, or transaction level. Mark current authoritative text unavailable when appropriate. Numerical checks should show formulas and inputs; review should not consist only of checking whether an entry balances.

## Filled fictional rate-policy record

Assume one EUR 25,000 invoice is to be converted to USD under a supplied teaching convention. Rate record R1 says USD 1.08/EUR at the invoice date. Record R2 says USD 1.12/EUR at month end. Neither is assumed to be the required accounting rate; they represent different dated inputs needing a policy decision.

| Field | Fictional entry |
|---|---|
| Original amount | EUR 25,000 |
| R1 result | 25,000 × 1.08 = USD 27,000 |
| R2 result | 25,000 × 1.12 = USD 28,000 |
| Difference | USD 1,000 |
| Actual policy criterion | Unverified; do not choose the rate merely because it matches a target |
| Configuration state | Proposed mapping only; no system change performed |

If the ERP uses R2 while a separately approved policy requires R1 for the specified balance, the workpaper should describe a policy/configuration mismatch and its numerical effect under that assumption. It should not silently alter the policy to validate the existing system. Conversely, a preparer's preference for R1 is not evidence that the ERP is wrong.

## Four identities belong in the rate register

Record the currency pair and direction; economic date/time and timezone; provider/quote type; and exact source revision. Add the intended balance or transaction class and approved use. A “USD rate” can be meaningless without the base currency. A closing date can still leave uncertainty about market, time of day and quote type. Two vendors can publish different valid observations for different purposes.

Do not average reciprocal quotes as if they were rates in the same direction. Convert to a common, explicitly justified direction first and retain precision. A triangulated rate introduces another source/time dependency; document both legs rather than hiding them behind a single calculated number. The template does not establish whether triangulation or any particular quote is permitted by the applicable framework.

## Change-control checklist for finance configuration

Before a proposed rate-policy change, identify affected entities, transaction classes, periods and stored balances. Preserve the prior mapping, the proposed mapping, supported rationale and authorized reviewer. Test representative fictional inputs in an authorized test environment before any real system change. Keep the observed test result distinct from approval to deploy the change.

A useful proposed test set includes correct direction, reversed direction, missing rate, stale date, duplicate provider observation and a late-arriving correction. Define expected refusal or review behavior before execution. A missing rate should not silently default to one; a rate of one would assert equal currency units. This is an original control design, not a claim that the application already enforces it or an accounting standard prescribes these test cases.

## Review a rate change without rewriting history

Suppose an official data provider later corrects its historical quote. Retain the original observed quote, the corrected quote, the provider's notice and dates, and the analysis of affected workpapers. Do not replace old evidence as though the correction had been known at the original review. Any accounting error or subsequent-event conclusion needs its own applicable criteria.

Report the exact workpaper revision reviewed and any untested currencies or transaction types. A successful test for a USD/EUR payable does not cover every consolidation, hedging or high-inflation scenario. Keep unsupported conclusions unresolved rather than broadening a narrow result.

## Reviewer questions

- Are rate units explicit?
- Does a system default differ from the approved policy?
- Were late-period concentrated transactions evaluated?
- Can the proposed entry be traced to a specific exchange difference?

## Release checklist

Record the preparer, reviewer, exact revision, review date, unresolved exceptions, and intended reporting period. Clear a human-review badge when a material fact or conclusion changes. A draft can be useful while unresolved, but it must not be exported as professionally approved. Do not place client secrets in public contributions.

## Sources and verification

The [FASB homepage](https://fasb.org/) [fasb-asc] is a human research starting point only. Current project source review identified FAF/FASB/GASB restrictions on AI use, automated collection and non-homepage linking. No restricted standard body, alternate copy or current accounting paragraph was acquired for this revision. Exact applicable Codification text, effective dates, elections and transition remain unverified.

Editorial checking on October 4, 2026 covers the original explanations and calculations under explicit assumptions. It is not a human CPA/auditor attestation or a claim that an unavailable source has been reviewed. The publication does not create source-operation rights or automatic Agent admission.

## Standard education and Premium execution

This original article remains free Standard educational content under CC BY 4.0. Premium licenses private software workflow execution only where available and authorized. It does not grant publisher rights, settle accounting conclusions, or supply professional review. The examples do not perform a private workflow, model run, configuration change, filing or journal posting. Feature availability and execution permissions require separate verification.

Original educational content by Open Source Accounting contributors. Licensed under **CC BY 4.0**. No third-party standard text is relicensed. Do not use this draft as an audit opinion, certification, or final accounting conclusion.
