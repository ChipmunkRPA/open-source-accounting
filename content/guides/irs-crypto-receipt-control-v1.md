# Cryptocurrency hard forks: distinguish a ledger event from receipt and control

**Ray Sang’s Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-04**

AI-assisted by Open Source Accounting contributors. Professionally unreviewed; no human review is recorded, and the brand does not imply personal review by Ray Sang. This is a bounded reading of a retained 2019 IRS ruling, not current-law advice, a filing instruction or a financial-reporting standard.

## The question the retained ruling actually answers

A network can change without its users receiving a new asset. Revenue Ruling 2019-24 separates a hard fork that delivers no new cryptocurrency to the taxpayer from a hard fork followed by an airdrop that the taxpayer can control. Its two holdings address those specific fact patterns. They are not a rule that every digital-asset announcement produces income, or that every receipt called an airdrop has identical treatment. [Retained ruling, PDF pages 1 and 5](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-19-24.pdf#page=1).

For the second pattern, the ruling ties ordinary income to receipt of the new asset and measures it using fair market value at receipt. It also links the new asset’s basis to the amount included in income. Those conclusions belong to the federal tax analysis in the ruling; they do not choose a GAAP measurement model. [PDF pages 4–5](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-19-24.pdf#page=4).

## Build three separate timelines

The useful workpaper has three clocks: when the network changed, when the new units appeared on a ledger, and when the particular taxpayer obtained the ability to dispose of them. Combining these into one date conceals the key factual question.

The ruling explains that a ledger record ordinarily accompanies receipt, but it is not conclusive. It describes an exchange-managed wallet that does not support the new asset: the customer may lack control despite an airdrop being recorded. It also warns that constructive receipt can precede the ledger record. Therefore, neither “the blockchain says December” nor “the exchange posted in January” is a complete analysis. [PDF pages 2–3](https://github.com/ChipmunkRPA/open-source-accounting/blob/38daa93e71a5287a6b372ac70af7f82122f53f73/content/irs-source-pilot/2026-10-04/originals/rr-19-24.pdf#page=2).

Record each time with its time zone and supporting evidence. An exchange email, an account credit and an enabled withdrawal function may describe different events. If the evidence conflicts, preserve the conflict rather than automatically accepting the latest timestamp. A customer’s choice not to sell is also different from an inability to dispose of the units.

## Synthetic case: a year-end custody delay

All facts and figures below are invented. Assume a cash-method, calendar-year taxpayer and facts within the ruling’s hard-fork/airdrop setting. Assume no earlier actual or constructive receipt, no special exception, and a supported fair-market-value observation at the eventual receipt time. These are exercise assumptions, not conclusions supplied by an account statement.

- On December 30 of Year 1, a network forks and 18 new units appear at an exchange-managed address associated with the taxpayer
- At that time, the exchange does not support the asset; the taxpayer cannot transfer, sell, exchange or otherwise dispose of those units
- On January 4 of Year 2, the exchange enables disposal. The stipulated fair market value at that moment is $7.50 per unit
- A dashboard had displayed an indicative $9.00 per unit on December 30

Under the retained ruling’s reasoning and these assumptions, the relevant receipt event is January 4. The calculation is 18 × $7.50 = $135 of ordinary income and $135 of initial basis for the new lot. The December display would have produced 18 × $9.00 = $162, overstating this exercise’s receipt-date amount by $27 and placing it in the wrong year.

This does not establish that a delayed account entry always moves income into a later year. Change the facts so the taxpayer could dispose of the units on December 30, but did not notice the balance until January. The delay in awareness no longer demonstrates the absence of control. Reopen the receipt date and valuation rather than carrying forward the January result.

## Reconcile quantities, income and basis without counting the asset twice

The new-lot register should connect the 18 received units to the $135 receipt value and identify the supporting price evidence. The legacy holdings remain a separate lot; this example makes no conclusion about their basis or subsequent value.

Suppose a later internal transfer moves six of the 18 units between accounts owned by the same taxpayer. The exercise’s quantity control shows 12 units in one account and six in the other, still 18 in total. That movement is not evidence of a second hard-fork receipt. The historical $135 lot basis can be tracked as $90 and $45 solely for this identical-unit, no-fee bookkeeping illustration. No later sale, gain, loss or fee treatment is analyzed here.

An import routine that labels both the exchange credit and the destination-wallet credit “income” would record 24 units of purported receipts. The excess six units come from counting a transfer twice. Compare transaction identifiers and account ownership before summing receipts. This is an original reconciliation control, not an IRS-prescribed workpaper.

## A compact evidence worksheet

For each disputed event, retain: legacy asset; new asset; number of new units; taxpayer’s account or address; network event time; ledger time; earliest supported disposal time; possible earlier constructive-receipt evidence; valuation time and source; income amount; resulting lot basis; and unresolved facts. Do not put private keys, seed phrases or account credentials in this worksheet.

The control conclusion and the valuation conclusion require different evidence. A credible price does not establish receipt, and a confirmed receipt does not make an unsupported price reliable. If the disposal date is unknown, the defensible result is an unresolved timing issue, not a zero entered merely to make the schedule balance.

## Questions that change the conclusion

1. No new units were received following the fork. What amount does this ruling attribute to the fork alone? Under its first holding, no gross income arises from that event
2. Eighteen units were received, but the receipt-date value is missing. Can the $135 example fill the gap? No; the quantity is known, but the monetary conclusion remains unsupported
3. The transaction is staking compensation rather than an airdrop following a fork. Does the second holding decide it? No; that transaction requires different research

## Exact source and remaining limits

Source ID **irs:rev-rul:2019-24**; U.S. Internal Revenue Service, Revenue Ruling 2019-24, retained five-page advance PDF. The existing catalog identifies IRB publication on October 28, 2019; final IRB-text reconciliation remains pending. This work used the already-committed PDF and complete text, without a new IRS retrieval. Document year 2019 is not a determination of the taxpayer’s applicable tax year.

The retained ruling is primary administrative material, but later treatment, separately cited Code/regulation text, taxpayer-specific applicability and current law have not been comprehensively checked. Primary-text gaps remain for that wider analysis. Professional review and Agent admission are unperformed; default Agent eligibility remains false.

All prose and synthetic calculations here are original commentary. The linked IRS document remains separate government source text, with no IRS endorsement implied. New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](../../CONTENT-TERMS.md), only to the extent rights exist and are controlled; facts, government text, prior grants, statutory exceptions and platform agreements are preserved.
