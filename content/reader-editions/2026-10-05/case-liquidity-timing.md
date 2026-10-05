# Worked case: a later financing receipt cannot pay an earlier obligation

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Educational draft · v1.1.0 · 2026-10-04 · Editorial checks only; no human professional review.**

## Stipulated facts

All facts are invented and amounts are USD. Opening unrestricted cash is 800000. Six successive monthly payment groups each total 150000. A proposed 500000 financing receipt is uncommitted and, for the optimistic branch, arrives at the end of month six after that month's payments. No other cash flows, borrowing rights or deferrals are assumed.

The table calculates a planned cumulative funding position. A negative number is a funding shortfall under the assumptions, not a claim that actual cash can be spent below zero without a facility.

## Reproduce both branches

| Stage | Signed flow | Funding position before assumed financing |
|---|---:|---:|
| Opening | +800000 | 800000 |
| Month one payments | -150000 | 650000 |
| Month two payments | -150000 | 500000 |
| Month three payments | -150000 | 350000 |
| Month four payments | -150000 | 200000 |
| Month five payments | -150000 | 50000 |
| Month six payments | -150000 | -100000 |

Add signed flows to the opening position. Total planned payments are 6 × 150000 = 900000. Thus 800000 − 900000 = −100000. Under the stipulated sequence, the first identified gap occurs during the sixth payment group. The packet does not give daily dates or individual payments, so it cannot locate the exact day or payment where usable cash runs out.

| Branch at the end of month six | Position before financing | Assumed receipt | Closing modeled position |
|---|---:|---:|---:|
| Receipt does not occur | -100000 | 0 | -100000 |
| Receipt occurs after payments | -100000 | +500000 | 400000 |

The second branch's positive final amount does not cure the earlier 100000 shortfall. To fund all scheduled payments before the late receipt, the model would need at least 100000 of additional usable resources or an equivalent supported change to payment timing, excluding any fees, minimum liquidity requirements or other omitted flows. This is a model dependency, not a financing recommendation.

## Counterexample: same end point, different ordering

Move the assumed 500000 receipt to immediately before the sixth payment group while leaving all other stipulated flows unchanged. The position is then 50000 + 500000 = 550000 before that group and 550000 − 150000 = 400000 after it.

Both receipt branches end at 400000, but only the earlier-receipt branch has no negative funding position in this coarse monthly sequence. Daily obligations or other facts could still reveal a gap. The financing remains uncommitted in both branches, so neither is evidence that funds are actually available.

## Research and output boundaries

Obtain actual payment dates, cash restrictions, facilities, conditions, financing commitments and evidence for proposed deferrals. Identify the accounting framework, financial-statement/issuance dates and applicable assessment horizon. Current ASC 205-40 and audit requirements were not verified for this case. [fasb-asc; pcaob-as2415]

The useful output is the reproducible schedule, the first identified modeled gap, missing timing facts and alternative assumptions. It is not a prediction of survival, a completed going-concern assessment, a legal insolvency conclusion or a professional opinion.

## Sources and verification

- [FASB Codification](https://asc.fasb.org/): research reference; current primary text not accessed
- [PCAOB AS 2415](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2415): link only; exact current applicability unverified
Fresh automated retrieval of the PCAOB standard was not performed after the [PCAOB Terms of Use](https://pcaobus.org/privacypolicy), Authorized Use section, was inspected on October 4, 2026 and an automated-gathering restriction identified. Its current text, amendment status and engagement applicability remain unverified. No third-party standard body is reproduced. [pcaob-terms]

Original educational content by Open Accounting contributors. Licensed under **CC BY 4.0**. The original explanation and fictional examples remain freely readable; third-party publications retain their own rights. No human professional approval, source-operation grant, Agent admission or final accounting/audit conclusion is created.
