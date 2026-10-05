# Servicing assets: keep the measurement election separate from cash collected

**Ray Sang’s Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-05**

AI-assisted by Open Source Accounting contributors. Professionally unreviewed; no human review is recorded, and the brand does not imply personal review by Ray Sang. This original bank-accounting exercise is not an official standard, an ASC replacement or advice to change an accounting election.

## Start after recognition, with the election already documented

A servicing arrangement may generate current fee cash while the recorded servicing asset declines. Those are different parts of the closing workpaper. A cash collection total cannot establish the asset's carrying value, and a valuation movement cannot establish how much cash was collected.

The OCC's August 2026 Bank Accounting Advisory Series, Topic 9A, question 2, describes class-level subsequent measurement using either amortization with impairment assessment or fair value with changes in earnings. It also describes the irreversibility of a fair-value election and a constrained change from amortization to fair value. [OCC, printed pages 134–135 / PDF pages 138–139](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=138).

This guide takes recognition and class elections as supplied facts. It does not decide whether a loan transfer was a sale, whether servicing rights should first be recognized, or whether a particular grouping qualifies as a class. Keeping those questions outside the arithmetic prevents a successful rollforward from being mistaken for evidence of initial recognition.

## Synthetic register with two different measurement paths

Assume a fictional bank has two established classes, Orchard and Harbor. Orchard uses the amortization method, and Harbor uses the fair-value method. There are no additions, disposals, transfers, currency effects or policy changes in the period. All servicing fees are earned and collected in the period; all operating costs are incurred and paid in the period. No accrual or tax difference is omitted from the stipulated exercise.

Orchard begins with an unamortized balance of $180,000 and a valuation allowance of $10,000, giving a $170,000 net asset. Its independently supported amortization charge is $18,000. The resulting balance before allowance is $162,000. A separately completed impairment assessment determines that the required closing allowance is $14,000 and closing net asset is $148,000. The exercise stipulates one impairment stratum and no direct write-off or recovery restriction; it does not teach how to select strata or compute amortization.

Harbor begins at a $240,000 fair value and ends at a supported $218,000 fair value. Under its stipulated election, the $22,000 decline is the measurement charge. No additional amortization is applied to Harbor.

| Closing control | Orchard: amortization | Harbor: fair value | Total |
|---|---:|---:|---:|
| Opening net asset | $170,000 | $240,000 | $410,000 |
| Amortization charge | ($18,000) | $0 | ($18,000) |
| Additional impairment allowance | ($4,000) | $0 | ($4,000) |
| Fair-value loss | $0 | ($22,000) | ($22,000) |
| Closing net asset | $148,000 | $218,000 | $366,000 |

The $44,000 decline is fully explained: $18,000 amortization + $4,000 allowance increase + $22,000 fair-value loss. Using the entire $14,000 closing allowance as a new charge would count the $10,000 opening allowance again.

## Keep the gross balance and allowance visible

For Orchard, the illustrative entries debit amortization expense $18,000 and credit the servicing asset $18,000, then debit impairment expense $4,000 and credit the valuation allowance $4,000. Closing gross balance $162,000 less closing allowance $14,000 equals $148,000.

For Harbor, debit fair-value loss $22,000 and credit the servicing asset $22,000. These three entries have total debits and credits of $44,000. They contain no cash account because the example supplies noncash subsequent-measurement changes.

A single line labeled “asset adjustment” could produce the correct ending total while losing important information. The next period needs Orchard's $162,000 pre-allowance balance and $14,000 allowance separately. Harbor needs its $218,000 fair-value balance and the continuing election record. A shared $366,000 total is insufficient for that purpose.

## Reconcile fee cash to the exercise's income

Orchard collects $62,000 of earned servicing fees and pays $25,000 of operating costs, yielding $37,000 of operating cash margin. Harbor collects $85,000 and pays $36,000, yielding $49,000. The combined cash margin is therefore $86,000.

Subtracting Orchard's $22,000 total noncash charges gives $15,000 of its simplified period income. Subtracting Harbor's $22,000 fair-value charge gives $27,000. Combined simplified income is $42,000, and adding back $44,000 of noncash charges reconciles it to the $86,000 cash margin.

This is a deliberately closed exercise, not a complete statement-of-cash-flows classification. Actual settlements, advances, servicing liabilities, unpaid fees, taxes, and sale transactions could require additional lines. The example cannot establish those lines by subtraction from an unexplained residual.

## Parallel sensitivity: the two paths need not move alike

Keep Orchard's supplied $18,000 amortization but assume a fresh independent impairment assessment requires only a $7,000 closing allowance. The existing $10,000 allowance then falls by $3,000; the exercise produces a $3,000 release and a $155,000 closing net asset. Orchard's total net charge becomes $15,000 and simplified income becomes $22,000.

Separately assume Harbor's supported closing fair value is $248,000. Its $8,000 increase produces a gain, a $248,000 closing asset and $57,000 simplified income. Combined assets become $403,000 and simplified income becomes $79,000. The $7,000 net asset decline reconciles the $86,000 cash margin to that income.

These are parallel alternative facts, not instructions to reverse a particular historical write-off or switch methods to obtain a preferred result. Valuation evidence and the existing election determine the path; the desired earnings number does not.

## Evidence and source limits

Source ID: **osa-occ-servicing-subsequent-measurement**. The official August 2026 OCC staff guidance was examined October 5, 2026 and its metadata was saved to GitHub before drafting. The source's loan-sale example, interest-only strip, figures and initial-recognition analysis are not reproduced.

The numeric registers are invented. Actual ASC text, later amendments, election eligibility, class/stratum construction, valuation and the pattern of estimated servicing income require separate evidence and review. Primary-text gaps remain; professional review is unperformed and default Agent eligibility is false. An official agency's interpretation is not a professionally approved conclusion for this bank.

New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](../../CONTENT-TERMS.md), only to the extent rights exist and are controlled. Source works, facts, prior grants and statutory/platform exceptions remain separate.
