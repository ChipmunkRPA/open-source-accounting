# Goodwill testing: sequence other asset losses before applying the goodwill cap

**Ray Sang’s Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-04**

AI-assisted by Open Source Accounting contributors. Professionally unreviewed: no human review is recorded; this brand does not imply that Ray Sang personally reviewed the article.

## Start with a corrected comparison amount

A goodwill test can be arithmetically accurate yet use the wrong carrying amount. If another asset loss belongs in the reporting unit first, comparing the earlier ledger total with fair value can charge that same shortfall to goodwill as well.

OCC's selected responses put other asset tests first when performed at the same time. The quantitative goodwill loss is the reporting-unit carrying-value excess over fair value, limited to recorded goodwill. This guide applies those two premises only. [OCC, Topic 10B, questions 7 and 8](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=166).

## Define a reporting unit without reconstructing an acquisition

A fictional bank's established transaction-services reporting unit is undergoing a quantitative test. Its identification, goodwill allocation, valuation date and need for testing are stipulated. The guide does not determine reporting-unit boundaries or calculate acquisition goodwill.

Amounts below are in thousands of dollars. Assets and liabilities are already assigned on a basis consistent with the stipulated reporting-unit valuation. There are no tax effects, private-company accounting alternatives, ownership changes or other current-period movements.

Separate analyses under the applicable other-asset models have already established an $80 loss on premises and equipment and a $140 loss on a finite-lived intangible. Their methods and evidence are outside this exercise. Those losses are independent inputs, not numbers reverse-engineered from the reporting-unit fair value. All remaining nongoodwill balances need no further adjustment under the supplied facts.

| Balance | Before those losses | Independently established reduction | After those losses |
|---|---:|---:|---:|
| Cash and equivalents | $520 | $0 | $520 |
| Other financial assets, net | $3,140 | $0 | $3,140 |
| Premises and equipment, net | $900 | $80 | $820 |
| Finite-lived intangible, net | $640 | $140 | $500 |
| Goodwill | $820 | $0 | $820 |
| Total assets | $6,020 | $220 | $5,800 |
| Assigned liabilities | $2,200 | $0 | $2,200 |
| Reporting-unit net carrying amount | $3,820 | $220 | $3,600 |

The first adjustment debits the respective other-asset loss accounts for $80 and $140 and credits their asset or appropriate accumulated-impairment accounts. Goodwill is untouched by these entries. The resulting $3,600 is the comparison amount, including $820 goodwill.

## Apply the goodwill formula once

The independently stipulated reporting-unit fair value is $2,930. The positive excess is $3,600 − $2,930 = $670. Because $670 is below the $820 goodwill balance, the goodwill impairment is $670 and remaining goodwill is $150.

In dollars, the illustrative entry is debit goodwill impairment expense $670,000 and credit goodwill $670,000. It is noncash and is separate from the earlier $220,000 of other-asset losses. No tax entry is illustrated.

After both stages, total assets are $5,130,000. Deducting unchanged liabilities of $2,200,000 leaves $2,930,000. The total current-period loss is $890,000: $220,000 plus $670,000. The complete bridge is $3,820,000 opening net carrying amount − $890,000 total losses = $2,930,000 closing net carrying amount.

That equality with fair value is an outcome of these particular numbers. It is not a rule requiring every reporting unit's books to be written to its fair value.

## Show how the wrong order distorts the answer

Suppose a spreadsheet starts with the unadjusted $3,820 and compares it with $2,930. It finds an $890 excess and applies the $820 goodwill cap, writing off all goodwill. If the independently established $220 other-asset losses are then also recorded, total losses become $1,040 and the final net carrying amount is $2,780.

Compared with the correct bridge, loss is overstated and goodwill understated by $150. The final amount also sits $150 below the stipulated fair value. This is a sequencing error in the invented spreadsheet, not an instruction to skip the independently supported other-asset losses to make the final number fit.

Label the input “after other-asset adjustments, before goodwill adjustment.” An unlabeled “carrying value” cell makes it difficult to detect whether an imported balance is stale or already includes the current goodwill entry.

## Change fair value and observe the cap

Hold the corrected $3,600 net carrying amount and $820 goodwill constant. Each row is an independent alternative at the same measurement date, not a sequence of later-period reversals. All amounts remain in thousands.

| Alternative fair value | Positive carrying-value excess | Goodwill loss | Remaining goodwill | Final net carrying amount |
|---|---:|---:|---:|---:|
| $3,750 | $0 | $0 | $820 | $3,600 |
| $3,190 | $410 | $410 | $410 | $3,190 |
| $2,930 | $670 | $670 | $150 | $2,930 |
| $2,650 | $950 | $820 | $0 | $2,780 |

The last row has a $130 residual difference after goodwill reaches zero. This goodwill formula supplies no further write-down. Charging that $130 to an arbitrary asset would abandon the separately stipulated other-asset results. New evidence might require renewed analysis under another model, but the residual alone does not specify that analysis or its journal entry.

At the opposite end, fair value of $3,750 creates no $150 asset increase. The exercise's impairment formula has a zero floor as well as a goodwill ceiling. An exact $3,600 fair value likewise produces zero goodwill loss.

## Preserve the evidence behind each input

A reviewer needs the unit-boundary documentation, goodwill allocation, dated other-asset conclusions, before-and-after ledger bridge and fair-value workpaper. Reconcile whether liabilities and cash are included consistently on both sides. Record who supplied each assumption and whether it is still unresolved.

These controls help locate mistakes without pretending that spreadsheet agreement validates a valuation. Real recognition, measurement, presentation and disclosure decisions require applicable current literature and qualified review.

## Precise source and retained limits

- [OCC Bank Accounting Advisory Series](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf): August 2026, Topic 10B questions 7 and 8, excluding question 7A; printed pages 162–164, PDF pages 166–168. Bank staff interpretation, not OCC rules; issue-observation cutoff March 31, 2026
- Publisher authority pointers: ASC 350-20-35 and ASC 350-20-35-31 as cited by OCC; [FASB Codification homepage](https://asc.fasb.org/), reference only

Checked October 4, 2026. Publisher-standard bodies, later amendments, tax effects and entity applicability remain unverified or excluded. Professional review and Agent admission remain unperformed.

New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](../../CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, third-party material, prior grants, statutory exceptions and platform agreements are preserved.
