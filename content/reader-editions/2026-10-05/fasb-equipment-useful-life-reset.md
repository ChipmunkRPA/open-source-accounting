# Equipment retirement plans: rebuild depreciation from the remaining service period

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Ray Sang Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-05**

By Open Source Accounting contributors. No human professional review is recorded; the brand does not imply that Ray Sang personally reviewed this article. Educational draft only; Agent use is denied.

## Begin with the service plan, then rebuild the schedule

A plan to stop using equipment changes the period over which its remaining depreciable amount must be allocated. It does not supply every accounting conclusion needed for the asset. In the selected bank-context response, OCC staff retain equipment in held-for-use accounting while use continues and revise its depreciation horizon to reach residual value when use ends.

This original exercise isolates that remaining-service calculation. The equipment stays in use until each stated endpoint. An independently supplied assessment concludes that no separate impairment adjustment is required. That premise is necessary: a spreadsheet that balances cannot establish recoverability or replace the assessment.

## Three machines, three remaining service periods

Fictional Alder Field Bank approves a supported equipment-replacement schedule on July 1, 2026. New information changes the estimated service periods on that date; there is no prior-period error. June depreciation is already recorded. All amounts below are dollars, and residual estimates remain unchanged.

Straight-line depreciation and whole-month charging are stipulated. July is the first revised month, and the stated final service month receives a full charge. The supplied old remaining lives were 36 months for the sorter, 42 for the embosser and 36 for the counter. Each old schedule charged $1,000 monthly.

| Asset | Historical cost | Accumulated depreciation, June 30 | July 1 carrying amount | Residual | Last service day | Revised months |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Envelope sorter | 108,000 | 66,000 | 42,000 | 6,000 | June 30, 2027 | 12 |
| Card embosser | 84,000 | 39,000 | 45,000 | 3,000 | March 31, 2028 | 21 |
| Coin counter | 60,000 | 24,000 | 36,000 | 0 | December 31, 2027 | 18 |
| Total | 252,000 | 129,000 | 123,000 | 9,000 | Different dates | — |

The new monthly charges are ($42,000 less $6,000) divided by 12 = $3,000; ($45,000 less $3,000) divided by 21 = $2,000; and $36,000 divided by 18 = $2,000. The combined charge initially becomes $7,000 monthly. Historical cost is not divided by the new remaining months: doing so would allocate amounts already depreciated a second time.

## Allocate the remaining balance, without rewriting the past

This depreciation-only forecast starts July 1. A zero after an asset's final service period means no further charge in this exercise. Residual amounts are retained solely for the reconciliation; later retirement, disposal and derecognition accounting are outside the table.

| Asset | July–December 2026 | January–June 2027 | July–December 2027 | January–March 2028 | Future depreciation total | Endpoint residual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Envelope sorter | 18,000 | 18,000 | 0 | 0 | 36,000 | 6,000 |
| Card embosser | 12,000 | 12,000 | 12,000 | 6,000 | 42,000 | 3,000 |
| Coin counter | 12,000 | 12,000 | 12,000 | 0 | 36,000 | 0 |
| Total | 42,000 | 42,000 | 24,000 | 6,000 | 114,000 | 9,000 |

Each row proves that opening carrying amount equals future depreciation plus residual. Across all assets, $123,000 = $114,000 + $9,000. Previously recorded accumulated depreciation of $129,000 is preserved. Adding the forecast $114,000 produces $243,000 accumulated depreciation at the individual service endpoints, leaving $9,000 against the $252,000 original cost.

The aggregate journals below retain the asset-level amounts in the schedule; they do not authorize posting.

1. July–December 2026: debit depreciation expense $42,000; credit accumulated depreciation $42,000
2. January–June 2027: debit depreciation expense $42,000; credit accumulated depreciation $42,000
3. July–December 2027: debit depreciation expense $24,000; credit accumulated depreciation $24,000
4. January–March 2028: debit depreciation expense $6,000; credit accumulated depreciation $6,000

## Reconcile the first close and diagnose an error

At December 31, 2026, the individual carrying amounts are $24,000, $33,000 and $24,000, totaling $81,000. The ledger bridge independently gives $252,000 cost less ($129,000 opening accumulated depreciation plus $42,000 current charges) = $81,000. There is no cash movement from these depreciation entries.

Leaving the old schedules running would produce only $18,000 for the six months and $105,000 closing net equipment. Under the supplied revised facts, expense would be understated and net equipment overstated by $24,000. A cash reconciliation would not detect this error.

The opposite mistake is an immediate July reduction of all three assets to their combined $9,000 residual merely because replacement is planned. That would recognize $114,000 instead of the correct six-month $42,000, overstating this period's expense and understating December net equipment by $72,000. This comparison depends on the supplied no-separate-impairment conclusion and continuing use; it is not a general prohibition on recognizing asset losses.

## Sensitivity: move one endpoint after another close

Independently vary the forecast: on January 1, 2027, new supported information moves the coin counter's final service day to June 30, 2027. Its December carrying amount remains $24,000. With zero residual and six months remaining, its new monthly charge is $4,000, rather than $2,000.

January–June depreciation becomes sorter $18,000 plus embosser $12,000 plus counter $24,000 = $54,000. Debit depreciation expense and credit accumulated depreciation $54,000 for that period. The combined carrying amount at June 30, before any subsequent retirement accounting, becomes $6,000 + $21,000 + $0 = $27,000, compared with $39,000 in the original forecast. The $12,000 difference changes timing; it does not revise the $42,000 already recorded in the previous six months. The counter still absorbs exactly $36,000 from July 2026 through its revised endpoint.

## Evidence checklist and source limits

For each asset, retain its identifier, June ledger balance, approved service endpoint, residual support, revision date, depreciation convention and separate impairment conclusion. Reconcile each monthly charge to the asset register and investigate service continuing beyond the forecast date rather than automatically extending the table. Unknown residuals or stop-use dates require new evidence.

This exercise excludes outsourcing contract terms, sale, held-for-sale classification, leases, software, impairment measurement, tax and the source's scenarios.

- [OCC Bank Accounting Advisory Series, question](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=113) and [response](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=114): August 2026 edition, Topic 5C, Miscellaneous Other Assets, question 4; printed pages 109–110 / PDF pages 113–114, one-based
- ASC 360-10 is a reference-only pointer cited by OCC; current FASB primary text was not verified

The 244-page edition reports issues observed through March 31, 2026. Checked October 5, 2026. These dates do not establish issuance, adoption or effective dates. OCC staff interpretations address national banks and federal savings associations; they are not OCC rules or FASB-authored standards. Primary-text, amendment and current-applicability gaps remain. No source body or human approval is included.

New first-party copyrightable text is designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, titles, third-party material and prior MIT/CC BY grants are excluded; statutory exceptions and applicable platform agreements prevail. These terms apply prospectively to this new text only.
