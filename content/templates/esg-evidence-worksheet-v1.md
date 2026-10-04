# ESG claim and evidence worksheet

> **AI-assisted editorial draft — not professionally reviewed.** Original educational material. No standard text or real emissions factors are reproduced. No compliance, materiality, assurance or accounting conclusion is established.

## Claim register

| Field | Entry |
|---|---|
| Claim ID, owner and exact proposed wording | |
| Environmental/social/governance subject | |
| Entity, facilities/population and period | |
| Audience, jurisdiction and reporting purpose | |
| Framework, exact edition and adoption instrument | Unverified until evidenced |
| Issued / publicly available / effective dates | Separate fields; unknown stays unknown |
| Transition, exceptions and applicability decision | |
| Included/excluded units and reasons | |
| Prior-period definition and comparability | |

## Input-to-output trace (one row per input)

Record input ID; entity/site/person-population identifier; start/end dates; original artifact location and SHA-256; exact page/table/cell locator; retrieved date; confidentiality/workspace; original value and unit; normalized value and unit; transformation formula; factor identifier/version/units/geography/year/gas coverage; factor artifact hash/locator; source-operation permission; missing/estimated status; duplicate key and disposition; reviewer and unresolved questions. For personal data, use appropriately scoped identifiers and authorized storage, not this public example as a destination.

Store issued, available, effective and retrieved dates independently for each external source. A retrieval timestamp cannot fill the other three fields. Preserve originals and derive a new version rather than overwriting input evidence. A policy link or source citation is not a stored artifact.

## Calculation and reconciliation

| Check | Result / evidence / unresolved difference |
|---|---|
| Original-to-normalized units, including scale and sign | |
| Population count and quantity reconciliation | |
| Duplicates, missing units and estimates | |
| Calculation formula and reproducible output | |
| Denominator definition and zero-denominator handling | |
| Prior/current period bridge: activity, boundary, method/factor changes | |
| Sensitivity assumptions, limitations and excluded items | |
| Proposed financial-reporting implications in separate issue file | |

## Filled fictional record: review the denominator and the sentence

Assume one location, one month and 100 employees at month end. Seventy-two employees are asserted to have completed a named training module. There are no duplicate people under the exercise assumptions; actual completion evidence remains to be inspected. Twenty of the employees are half-time, so a separate FTE measure is 90. The example does not prescribe a GRI disclosure or any legal training requirement.

| Field | Fictional entry |
|---|---|
| Claim | “72% of the 100 employees in this defined month-end population completed module M” |
| Numerator | 72 distinct people with asserted completion; corroboration unresolved |
| Denominator | 100 employees at month end, not 90 FTE |
| Calculation | 72 ÷ 100 × 100 = 72% |
| Missing evidence | Completion records, scope changes and actual criterion for the intended disclosure |
| Forbidden promotion | Do not change “asserted completion” into “independently verified effective training” |

If the requested metric instead concerns everyone employed at any time during the month, month-end headcount may be incomplete. If ten people left before month end and five of them completed the module, the separately supplied period-wide population would be **110**, with **77** asserted completions, yielding **70%**. Retain both populations; do not replace the denominator while forgetting the relevant leavers in the numerator.

## Claims can share data but need different decisions

A count of people attending a course can support an attendance statement under its assumptions. It does not by itself support competence, safety improvement, legal compliance, or a causal claim about productivity. Add a separate claim row for each proposed conclusion, with the criteria and evidence it requires. Avoid one generic “reviewed” status that appears to approve every downstream use.

Record a calculation revision separately from a reporting-policy decision. A corrected duplicate can change a number without changing the policy. A revised boundary can change the comparison even when every source number is accurate. A new framework edition may affect what must be considered without establishing which original records are complete.

## Original exception checklist

- Population mismatch: numerator and denominator refer to different dates, entities or people
- Missing inputs: a blank or unavailable site/record has been treated as zero
- Duplicate or overlap: different file names describe the same activity or overlapping time
- Method change: a new rate, conversion, estimate or boundary is hidden inside the trend
- Unsupported wording: “verified,” “complete,” “compliant,” “effective” or “on track” exceeds the evidence
- Revision mismatch: the reviewed file differs from the file behind the published figure

For each exception retain the affected claim, original evidence, proposed correction, actual decision and unresolved impact. A small net movement can hide several important corrections. The worksheet should help a reviewer find those differences, not compress them into an unexplained confidence score.

## A completed arithmetic check is not a release approval

The preparer may accurately reproduce 72% while the underlying attendance assertions remain uncorroborated. Label the calculation as passed under supplied inputs and retain the evidence gap. If a reviewer later inspects records, record which people, revisions and completion criteria were covered. Do not backdate that work or infer review of the entire population from an unspecified sample.

## Review and output gate

Record each decision separately: permission for acquisition, storage, parsing, embeddings, model input, display/quotation and export; workspace/seat access; fresh Agent entitlement; technical review; historical applicability; and final disclosure/assurance decision by an authorized person. A paid subscription grants none of the other approvals. Every review must identify reviewer, date, scope, exact revision/hash, evidence, exceptions and expiry where relevant. Blank review fields remain unapproved.

Use draft wording: “Under the stated fictional assumptions, the calculation is X; boundary, method and authoritative reporting conclusions remain unresolved.” Replace it only when real evidence and applicable review justify a stronger claim. Keep rejected alternatives, reviewer questions and proposed corrections. No automatic submission, external notification, financial posting or assurance opinion is authorized by completing this worksheet.


## Sources and verification

The [GHG Protocol directory](https://ghgprotocol.org/standards) [ghg-standards-directory] and [GRI directory](https://www.globalreporting.org/how-to-use-the-gri-standards/gri-standards-english-language/) [gri-standards-directory] were observed on October 4, 2026 as discovery routes. Rights checks then identified restrictions; no standards bodies or factor datasets were acquired.

[GHG Protocol terms](https://ghgprotocol.org/terms-use), February 2023, section 1 and section 3, restrict extraction and public/commercial reuse. [GRI terms](https://www.globalreporting.org/media/mgspa4n4/gri-global-website-term-of-use-mpgc-05222025_25-august.pdf), August 28, 2025, physical page 4, sections 3–4, restrict automated access, derivatives and software/tool use without the specified authorization. GRI's [copyright policy](https://www.globalreporting.org/copyright/) also describes permission requirements. Acquisition stopped at those rights findings; no workaround, publisher permission or software certification is claimed.

The substantive material here is original reasoning and fictional arithmetic, not a paraphrase of a complete protected standard. Applicable editions, legal adoption, reporting criteria, real factors and source-operation rights remain unresolved. AI editorial checking of this article does not resolve those gaps or constitute professional assurance.

## Standard education and Premium execution

This original article remains free Standard educational content under CC BY 4.0. Premium licenses private software workflow execution only where the feature is available and the required permissions exist. It does not sell ownership of government text, supply publisher rights, establish a correct accounting treatment, or create professional approval. No real filing, posting, model call or private workflow was executed for this lesson.


---
Original content: Open Accounting contributors · CC BY 4.0 · Version 1.0.0 · 2026-10-04. Third-party materials retain their own rights.
