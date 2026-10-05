# Replacement retirement checks: reconcile prior withholding before treating cash as new income

**Ray Sang’s Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-04**

AI-assisted by Open Source Accounting contributors. Professionally unreviewed; no human review is recorded, and this label does not imply that Ray Sang personally reviewed the article. This guide explains a retained 2025 IRS ruling’s limited facts; it is not current filing advice or a plan-administration opinion.

## A replacement payment has a history

Revenue Ruling 2025-15 considers a qualified retirement-plan distribution whose first check is not cashed, is canceled, and is followed by another check. The plan administrator had withheld the required federal income tax, remitted that same amount, and mailed the first check. The ruling separately analyzes adjustment or refund of the first withholding, withholding on the replacement, and reporting of each distribution. [Retained ruling, PDF pages 1–2](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf#page=1).

The important comparison is between the accrued benefit at the second issuance and the amount of the first check, which was already net of withholding. Comparing the second benefit with the original gross distribution can hide a new increment. Comparing two net check amounts can also hide withholding on that increment. Preserve all three quantities instead of using a generic “original amount” field.

## Separate three decisions

First, cancellation of an uncashed check does not itself make correct withholding an overpayment. Under the stated facts, the amount withheld was correct and equaled the amount remitted. The ruling therefore allows neither the described adjustment nor the described refund. This does not decide cases of actual overwithholding or erroneous remittance. [PDF pages 3–5](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf#page=3).

Second, when the accrued benefit at replacement is no greater than the first check, the ruling requires no new federal withholding for that replacement. When it is greater, the excess is a separate designated distribution subject to the applicable withholding rules. The ruling’s footnote 6 identifies circumstances in which withholding is not required, so this is not a universal positive-rate formula. [PDF pages 5–6](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf#page=5).

Third, reporting is a distinct question. The initial gross distribution and initial withholding remain reportable in the ruling’s 2024 example. At replacement, the relevant new reportable amount is the excess, subject to the $10 reporting rule described in the source; the whole replacement check is not automatically a second gross distribution. [PDF pages 6–8, including footnotes 7–8](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf#page=6).

## Synthetic workpaper: reconstruct the first distribution

Assume a fictional plan and participant satisfying the ruling’s relevant facts: a qualified plan without the specified Roth, employer-securities or health-benefit complications; a U.S. calendar-year participant with no section 3405 withholding election and no investment in the contract; no relevant exception to income inclusion; no later service-based benefit accrual; and the same issuer and recipient for both checks.

In 2024 the fictional gross designated distribution is $1,450. Stipulate that $290 was the correctly determined federal withholding and was fully remitted; this guide does not derive a rate or withholding election. The first check therefore equals $1,160. It is canceled after remaining uncashed for six months.

The workpaper must retain $1,450 gross, $290 withheld/remitted and $1,160 payable by check. Their identity is $1,450 = $290 + $1,160. Replacing the canceled check does not reverse the historical $290 tax remittance under the ruling’s stated facts. Nor should the original gross reporting amount be reduced to the net check merely because that is the participant-facing payment instrument.

## Three replacement outcomes

Consider each branch independently, not as successive payments:

| Branch | Accrued benefit at replacement | First check | Excess for separate-distribution analysis |
|---|---:|---:|---:|
| A: no increment | $1,160 | $1,160 | $0 |
| B: earnings increment | $1,435 | $1,160 | $275 |
| C: lower remaining benefit | $1,145 | $1,160 | No positive excess |

Branch A produces a $1,160 replacement check with no new withholding or reporting under the ruling’s matched facts. Branch C likewise has no new withholding or reporting under that comparison; the $15 reduction still needs an operational explanation, but the ruling does not turn it into a tax refund or decide the participant’s entitlement dispute.

For Branch B, separately stipulate that applying the relevant withholding rules to the $275 increment produces $55 of withholding. The replacement check is then $1,435 − $55 = $1,380. Reporting of the new distribution uses $275 for gross and taxable amounts under the exercise’s no-basis assumptions, and $55 for withholding. It does not report either $1,435 or $1,380 as the entire new distribution.

An economic cross-check is $1,450 original gross + $275 new increment = $1,725. That equals $1,380 finally delivered by the replacement check + $290 earlier remittance + $55 new remittance. The canceled $1,160 first check must not be counted again as cash received.

## Thresholds require separate fields

If the increment were $9, the isolated increment would be below the source’s $10 reporting boundary. That does not establish the year’s reporting result unless other distributions and the statutory aggregation condition are considered. It also does not decide whether withholding applies. A reporting threshold and a withholding exception answer different questions.

The useful worksheet therefore has distinct fields for the increment, applicable withholding rule and exceptions, annual reporting aggregation, and reporting year. A single “below threshold” checkbox loses the distinction. Amounts and rates in this article are synthetic; the applicable instructions and law must be verified for an actual reporting year.

## Facts that stop this shortcut

The source expressly leaves out a replacement paid by a different person, payment to a different recipient, PBGC Missing Participants Program questions, title I ERISA issues, and whether mailing to an address known to be wrong is appropriate. It also limits its conclusions to the pivotal facts stated. [PDF pages 7–8, footnote 9](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf#page=7).

Ask whether prior withholding was actually correct, whether remittance equals the recorded withholding, whether additional benefits accrued from service, and whether the issuer and recipient are unchanged. A “no” or unknown answer calls for additional research, not automatic application of the table. Preserve the original check, cancellation, benefit ledger, remittance support and replacement calculation as separate records.

## Exact source and remaining limits

Source ID **irs:rev-rul:2025-15**; U.S. Internal Revenue Service, Revenue Ruling 2025-15, retained eight-page advance PDF. The existing catalog identifies IRB publication on August 4, 2025; final IRB-text reconciliation remains pending. Its initial-distribution example and cited Form 1099-R instructions concern 2024. Its publication year is not a blanket tax-year scope or a currentness certification.

This work examined only the already-committed ruling and extracted text, with no new IRS retrieval. The cited underlying Code, regulations, annual form instructions and subsequent treatment were not independently acquired or comprehensively updated here. Wider primary-text and applicability gaps remain; professional review and Agent admission are unperformed, and default Agent eligibility stays false.

The explanation and fictional workpaper are original commentary, separate from the linked IRS government text. No IRS endorsement is implied. New first-party text is designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](../../CONTENT-TERMS.md), only where rights exist and are controlled; facts, government text, prior grants and statutory/platform exceptions remain unaffected.
