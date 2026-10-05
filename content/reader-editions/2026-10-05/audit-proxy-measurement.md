# Equal audit scores, different evidence: inspect the measure before the conclusion

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

> **Editorial draft — not professionally reviewed.** Version 2.0.0, 2026-09-29. Organizations, score components and numbers below are fictional and original. This is an educational measurement exercise, not an audit procedure, regulatory threshold or assessment of any real audit function.

## Sources and verification

Liu G, Wang J, Sun Y, Guo J, Zhao Y (2024), *Internal audit quality and accounting information comparability: Evidence from China*, PLOS ONE 19(10): e0310959, [doi:10.1371/journal.pone.0310959](https://doi.org/10.1371/journal.pone.0310959) [plos-audit-comparability-2024], provides an empirical research context. The publisher identifies CC BY 4.0. The article studies a particular Chinese listed-company sample; it is not a US auditing standard, a universal causal result or an approved measure for this application.

Editorial checking on October 4, 2026 inspected the official publisher HTML's publication/copyright metadata, Abstract, section 3.1, section 3.2.2 and the limitations in section 6. The article's license link resolves to CC BY 4.0. Its China-specific data context and stated endogeneity/generalization limitations do not establish a universal causal intervention. The study's substantive results were not replicated.

Earlier reference records describe selected PDF/XML comparisons; they are not newly repeated here. The current HTML check does not validate every formula, image or table. A complete correction/retraction-history search and underlying-data replication remain outstanding. No source formula, table or diagram is reproduced below.

The rubric below is invented for this lesson. It does not reproduce or validate the paper's model. No real accounting or auditing requirement has been verified by this exercise.

## Case: compensation hides a missing safeguard

A fictional analyst proposes a dashboard score:

`Score = escalation-route indicator + covered-risk fraction + timely-closure fraction`

The indicator is 1 when the supplied fictional record says an independent escalation route exists and 0 otherwise. The two fractions are counts with the denominators below. All three components receive equal numerical weight. “Independent” and “timely” are stipulated labels here, not verified professional conclusions. Both teams report the same period; the risk universe and closure populations still need reconciliation before a real comparison.

| Input | Cedar | Birch |
|---|---:|---:|
| Escalation-route indicator | 1 | 0 |
| Covered risks | 10 | 20 |
| Risks in stated universe | 20 | 20 |
| Issues closed within stated deadline | 10 | 20 |
| Issues eligible for closure assessment | 20 | 20 |

Cedar scores `1 + 10/20 + 10/20 = 2.00`. Birch scores `0 + 20/20 + 20/20 = 2.00`. Equal totals conceal different profiles. Under this arithmetic, perfect coverage and closure compensate for a missing escalation route. That substitution is a property of the invented formula, not evidence that the safeguards are interchangeable.

A reviewer should retain the component vector: Cedar `(1, 0.50, 0.50)` and Birch `(0, 1.00, 1.00)`. If a decision requires a minimum safeguard, represent it as a separately justified condition, not as a new weight chosen to produce a desired ranking. This lesson sets no such real-world threshold. Changing a definition or weight requires a new documented version and a reconciliation to earlier results.

## A favorable percentage can deteriorate when the population changes

Now suppose Birch's follow-up register omitted five eligible unresolved issues. With evidence that those five belong in the same period and deadline population, preserve the reported series and produce a corrected series:

- Reported closure: `20/20 = 100.00%`.
- Corrected closure: `20/25 = 80.00%`.
- Change: **20.00 percentage points lower**; **20.00% relative decline** from the reported rate.
- Revised invented composite: `0 + 20/20 + 20/25 = 1.80`.

This is a denominator correction, not a deterioration proven to have occurred during the period. Do not silently rewrite the original dashboard. Keep the original report, issue IDs, inclusion dates, correction rationale and an approval trail. Conversely, do not add five records merely because a reviewer dislikes a favorable result: population membership needs evidence.

## Exceptions and counterexamples

**Missing is not zero.** If escalation evidence is unavailable, use “unknown”; neither a 0 nor a 1 is established. If there are no issues eligible for closure assessment, closure is undefined, not 100% and not zero. A composite requiring that component is unavailable unless a separately justified missing-data rule exists.

**Counts do not measure risk severity.** Ten low-impact risks and ten high-impact risks are equal only as counts. A coverage rate does not by itself establish appropriate coverage. Retain risk descriptions, selection criteria, severity judgments and exclusions; do not invent dollar weights to manufacture comparability.

**Same rate, different evidence.** Nine timely closures out of ten and ninety out of one hundred both equal 90.00%. They do not necessarily provide the same precision or represent comparable populations. Confidence intervals require a justified sampling model; an operational register or judgmental selection is not automatically a random binomial sample.

**Closed does not mean remediated.** An issue can be marked closed administratively while a control still fails. Completion, verified remediation and sustained operation are different claims requiring different evidence. Likewise, a documented escalation route is not proof that staff can use it effectively.

**Association does not identify the intervention.** An observed relationship between a score and reporting outcomes does not show that changing one component will cause those outcomes. Consider selection, measurement error, omitted conditions, reverse causality and population differences. Do not turn an empirical paper into an automatic recommendation for a different entity or jurisdiction.

## Weight sensitivity: the ranking changes with the question

Keep the initial fictional vectors, Cedar (1, 0.50, 0.50) and Birch (0, 1.00, 1.00). Change only the escalation weight to w, leaving the other two weights equal to one. The scores become **Cedar = w + 1** and **Birch = 2**.

- At w = 0.5, Cedar scores 1.5 and Birch 2.0.
- At w = 1.0, both score 2.0.
- At w = 2.0, Cedar scores 3.0 and Birch 2.0.

The ranking reverses even though the underlying evidence is unchanged. This sensitivity is not an argument that a particular weight is correct. It shows that the ranking embeds a value judgment about substitution among different characteristics. Document the intended decision and the rationale for any weight before viewing results; do not choose w after seeing which team wins.

If the result is presented as a percentage of the maximum, update the denominator too. With w = 0.5 the maximum is 2.5, so Cedar is **60%** and Birch **80%**. With w = 2.0 the maximum is 4.0, so Cedar is **75%** and Birch **50%**. Reusing a maximum of three after changing the weight would introduce another error. Even correctly normalized numbers are scores, not probabilities of audit success.

## Missing-data sensitivity is not evidence about the missing fact

Suppose Cedar's escalation-route evidence is unavailable while its two fractions remain 0.50. Under the original unit weights, the score would range from **1.0 to 2.0** if the missing indicator could be either zero or one. This is a conditional bound, not a confidence interval. The evidence does not justify choosing the midpoint 1.5 or reporting a 50% probability of either state.

Use the unavailable component visibly, explain what record could resolve it, and identify whether the intended decision can tolerate the uncertainty. If a safeguard is mandatory under separately established criteria, a composite cannot waive that condition. This exercise establishes no such professional requirement; it explains why an aggregate score is not a substitute for the relevant decision rule.

## A trend can improve because difficult cases disappeared

Consider a separate fictional closure register. In Year A, the team closes 18 of 20 routine issues on time and 2 of 10 complex issues: **20/30 = 66.67%** overall. In Year B, it closes 9 of 10 routine issues and 1 of 5 complex issues: **10/15 = 66.67%** overall. Each type's closure rate remains unchanged, while the number of timely closures falls from 20 to 10. Equal percentages alone would hide the reduced workload.

In another Year B scenario, all ten complex issues are excluded and the twenty routine issues remain, with 18 timely closures. The displayed rate becomes **18/20 = 90%**, despite no improvement in the routine rate and no evidence about the omitted complex issues. Keep the universe, classification and exclusions visible. A changed population can create a changed headline without a changed operating capability.

These cases are original mathematical exercises. They do not estimate the PLOS study's coefficients, validate its proxy, or recommend an audit quality score for an actual organization. Before using empirical research in a memo, distinguish the research question, measured construct, population, method, uncertainty and the decision being proposed in the new setting.

## Free lesson and private workflow boundary

This original educational article remains free under CC BY 4.0. Premium can license private software workflow execution where available and authorized; it does not convert a public document into proprietary standards, grant source-processing rights, or supply professional approval. No real procedure, source grant, posting, model execution or review signature is created by these examples.

## Reusable measurement workpaper

| Field | Evidence to preserve |
|---|---|
| Decision and construct | What the decision needs to know; why each proposed proxy measures it |
| Definition/version | Numerator, denominator, units, cut-off, aggregation and missing-data rules |
| Population | Included records, exclusions, duplicates, period/cohort and reconciliation to source registers |
| Component evidence | Exact supporting record, owner, date, status and limitations for each component |
| Computation | Original inputs, formula, unrounded results and rounding presentation |
| Sensitivity | How rankings change under supported definition, weight and population alternatives |
| Interpretation | Facts versus assumptions, association versus causation, counterexamples and unresolved uncertainty |
| Review | Authorized reviewer, exact revision/hash, scope, findings and expiry; no fabricated sign-off |

## Study checks

1. Why can the two initial totals match while one supplied record lacks an escalation route? Explain the compensation built into the formula; do not conclude equivalence.
2. Recompute Birch after the five eligible unresolved issues are identified. Explain why the result is a restatement of the population, not necessarily a new operational decline.
3. Decide what to show when the closure denominator is zero. Keep the measure unavailable and disclose the reason; do not select a convenient number.
4. Explain why a published paper, a complete original file and a successful parser are insufficient for an entity-specific audit conclusion.

All examples, rubric, arithmetic and study expectations above are original educational content. Source attribution identifies research context, not endorsement. This draft remains excluded from automatic authoritative evidence admission until appropriate source, technical and applicability review.
