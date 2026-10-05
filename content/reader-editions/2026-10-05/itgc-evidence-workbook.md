# IT control evidence: eight worked cases and a review template

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

> **Editorial draft — not professionally reviewed.** Version 2.0.0, 2026-10-04. All entities, amounts, policies and evidence described below are fictional assumptions. Procedures are proposals, not work performed. This workbook is free educational material; it is not an audit opinion or approved Agent evidence.

## Sources and verification

Use these cases to distinguish a control design, its implementation and evidence of its operation. The financial-reporting application is our original inference, not a NIST accounting requirement. Establish the entity, engagement criteria, reporting date, systems and relevant financial assertions before adapting a case. Recognition, measurement, presentation and disclosure conclusions are outside this workbook's scope; obtain the applicable accounting and auditing sources separately.

Source: National Institute of Standards and Technology (2024), *The NIST Cybersecurity Framework (CSF) 2.0*, NIST CSWP 29, [official publication](https://doi.org/10.6028/NIST.CSWP.29). Edition 2.0 was published February 26, 2024. The acquired PDF's physical page 25, printed page 20, contains PR.AA-05, PR.DS-11, PR.PS-01 and PR.PS-04. These identify access, backup, configuration and logging topics respectively. Their relationship to the cases is contextual, not a claim that NIST prescribes our procedures, sample sizes or thresholds. Referenced external standards are not incorporated into this workbook.

The prior reference record identifies a separately retained original and selected-page check. On October 4, 2026, Editorial review re-read the official PDF's abstract, Appendix A physical page 25 / printed page 20, and recovery identifiers on physical page 28 / printed page 23. The source describes high-level outcomes and is not a prescribed procedure checklist. This review does not assert byte identity with the earlier artifact or a full current-standards search. No actual entity obligation, source permission or professional approval follows from the publication date. [nist-csf-2-0]

## 1. Access: a signed review with unresolved privileged accounts

**Assumed facts.** Cedar Ledger Ltd has 80 active ERP identities at September 30, including eight privileged identities. An owner signs a quarterly export. Two privileged service identities have no documented owner; three departed employees remain active. Assume those groups do not overlap. No evidence establishes whether either group used the system after it should have been disabled.

**Calculation.** Five of 80 identities need investigation (6.25%). Two of eight privileged identities lack an owner (25%). These denominators answer different questions. Neither percentage measures error probability, proves unauthorized posting or establishes deficiency severity.

**Proposed evidence and procedure.** Reconcile the export to the authentication directory and ERP role assignments, including service and emergency accounts. Obtain termination timestamps, permission history, owner assignments and subsequent activity logs. Inspect approval independence and what information the reviewer actually saw. Record requested evidence separately from obtained evidence. A signed screenshot alone does not prove population completeness or the precision of the review.

**Exception and counterexample.** A service identity may be necessary for an interface and should not be disabled without evaluating dependencies. The exception still needs a responsible owner, a defined privilege scope and monitoring. Conversely, an identified owner does not make excessive privileges appropriate. Related NIST topic: PR.AA-05, physical 25 / printed 20.

## 2. Changes: emergency approval is not an automatic pass

**Assumed facts.** The deployment log lists 24 production changes. Twenty have approvals before deployment. Four are marked emergency; two of those have a next-day review and two have no review evidence. The fictional policy permits next-day emergency review but does not waive testing or independent authorization. One developer can both modify and deploy a revenue-interface rule.

**Calculation.** Pre-deployment approvals cover 20/24 (83.33%, rounded). The other four must not be silently treated as failures or passes. Only 22/24 (91.67%, rounded) have either timing pattern documented, and that number is not an effectiveness conclusion.

**Proposed evidence and procedure.** Reconcile tickets to immutable deployment identifiers; examine the deployed version, testing, approver role, timestamps and rollback evidence. Review emergency criteria and both unreviewed exceptions. Evaluate whether another control addressed the developer's conflicting access with sufficient scope and precision; do not assume that a generic manager sign-off compensates.

**Edge case.** A ticket approved before deployment can refer to a different commit. Matching ticket dates without matching code versions misses that failure. Related topic: PR.PS-01, physical 25 / printed 20; NIST does not set the fictional next-day policy.

## 3. Backups: successful creation is not successful restoration

**Assumed facts.** Thirty nightly backups are scheduled; 29 finish successfully. One restore exercise takes 95 minutes against a fictional 60-minute recovery objective. The restored database omits the latest 45 minutes of activity against a fictional 15-minute data-loss objective. The restore used only the database, while attachments reside in another store.

**Calculation.** Backup completion is 29/30 (96.67%, rounded). The exercise exceeds the recovery-time target by 35 minutes and the data-loss target by 30 minutes. A high completion rate does not eliminate either gap.

**Proposed evidence and procedure.** Reconcile the schedule, actual runs and failures; inspect retention, access and encryption records. Obtain exact restore start/end times, source cutoff and restored transaction cutoff. Test a consistent database-and-attachment recovery boundary, with ownership and customer deletion obligations considered. A test is only performed when its actual execution evidence exists.

**Counterexample.** A restore that opens the application but cannot retrieve supporting attachments does not establish full-service recovery. A later successful exercise does not rewrite the result of this one. Related topic: PR.DS-11, physical 25 / printed 20. Target times are assumed business decisions, not NIST-prescribed values.

## 4. Interfaces: equal totals can conceal errors

**Assumed facts.** A billing file contains three records: A = 100, B = 200 and C = 300 dollars. The ledger receives A = 100, B = 200 and duplicate B = 200, plus a separate erroneous D = 100. Both sides total 600 dollars. Record C is missing. Assume no tax, currency or valid timing differences.

**Calculation.** Net dollar difference is zero, but record counts are three versus four; missing C is 300, duplicate B is 200 and unexpected D is 100. Netting the two directions hides the missing record.

**Proposed evidence and procedure.** Compare stable transaction IDs, counts, values and cutoff, retain rejected-record logs, investigate duplicates and trace corrections to both sides. Define how a retry is distinguished from a genuinely new transaction. Correlate logs across systems rather than assuming one green job status proves completeness.

**Edge case.** If the destination intentionally splits one bill across accounts, record-count equality is not the expected control. Use a documented parent-child key and reconcile allocation totals. Related topic: PR.PS-04, physical 25 / printed 20; this reconciliation design is our original financial-system example.

## 5. Spreadsheets: protection is not formula accuracy

**Assumed facts.** A close workbook should calculate a fictional 2% allowance on four balances: 12,000, 18,000, 25,000 and 45,000 dollars. The locked formula excludes the last row. The rate is an exercise assumption, not an accounting policy recommendation.

**Calculation.** The complete balance is 100,000 and the intended result is 2,000. The truncated range totals 55,000 and returns 1,100, a difference of 900. Password protection preserves the error rather than correcting it.

**Proposed evidence and procedure.** Identify the approved workbook hash/version, trace input completeness, inspect formula ranges and independently recalculate. Check hidden rows, manual overrides, links and whether new rows enter the approved formula. Do not execute external links or macros merely to inspect evidence.

**Exception.** A deliberately excluded balance needs a supported scope rationale; it is not necessarily an error. Here the stipulated policy includes all four rows. Related topic: PR.PS-01, physical 25 / printed 20; measurement under actual accounting standards still requires separate analysis.

## 6. AI posting: a proposal is not authorization

**Assumed facts.** A model proposes a 12,500-dollar journal. A reviewer approves draft hash H1. A later edit changes the account or amount, producing H2. The posting service receives H2 and the approval for H1. No valid approval for H2 exists.

**Proposed design and evidence.** Bind approval to the exact version, workspace, authorized reviewer and intended posting operation. Require server-side authorization at execution and a durable idempotency key. Preserve the proposed entry, approval decision, executed version and actual posting receipt as separate records. Model confidence, a second model pass or a subscription is not permission to post.

**Counterexamples.** Retrying the same authorized operation should not duplicate an entry. Reusing its key for different content should be rejected, not treated as a successful retry. Approval of H1 should not silently authorize H2. Related topic: PR.AA-05, physical 25 / printed 20; these are proposed application controls, not a representation that this product posts journals or that the scenarios have been tested in a real entity.

## 7. A point-in-time access report misses a period-wide risk

**Assumed facts.** A quarterly control is intended to review every privileged identity active at any time during the quarter. The period-end export contains eight privileged identities. Separate historical logs identify three more that were active earlier and disabled before quarter end. Assume the groups do not overlap and the historical population is complete. The signed review covers only the eight current identities.

**Calculation.** The intended period-wide population is **8 + 3 = 11 identities**. The evidence covers **8/11 = 72.73%**, rounded, of that supplied identity population. The quarter-end snapshot covers 8/8 current identities but cannot support a claim of 100% coverage of the eleven-identity period population. This measures coverage of identities, not days of exposure, transactions or severity.

**Original analysis.** Match the control objective to the export's time basis. A snapshot can answer who had access at one cutoff; it cannot by itself answer who had access throughout a quarter. If the actual approved control is intentionally point-in-time, evaluate that design as such rather than silently expanding its promised coverage. Obtain dated role history and activity where relevant; a later disablement does not establish that earlier access was appropriate.

**Counterexample.** A service identity may be renamed without representing a new principal. Do not add it twice from aliases. Conversely, reuse of the same display name can conceal different principals. Use immutable identities and supported effective dates; keep unknown identity relationships unresolved.

## 8. A remediation test covers a new configuration, not the whole year

**Assumed facts.** A flawed interface operated from January through August. A revised control was deployed September 1. One test on September 15 uses the new configuration and passes its supplied test conditions. No evidence of the earlier configuration's effectiveness or the full September production population is supplied.

**Proposed evidence.** Bind the new design, deployment, test input, actual output and reviewer decision to exact configuration versions. Keep the earlier exposure period visible. A passed test can support the observed result for that version and scenario; it does not rewrite the earlier eight months or establish operation under every condition. If the configuration changes again after the test, identify the affected assumptions and repeat relevant tests under authorization.

**A stronger teaching test set.** Define one expected-success input, one deliberately invalid input, one duplicate/retry input and one delayed or interrupted input. Record expected behavior before execution and preserve actual results. This is an original way to expose gaps in the proposed design; it is not a NIST-mandated number of tests or an audit sampling plan. A hypothetical test set does not mean the application has been tested.

## Cross-case review checklist

For each conclusion ask whether the population, time interval, system boundary and exact revision match the claim. “All identities reviewed,” “all changes approved,” “all backups usable” and “all postings authorized” are different assertions. One green dashboard tile cannot establish them collectively.

Separate a control's existence from its precision. A review can be real but too broad to detect the particular problem. Identify the information the reviewer used, exceptions they could reasonably see, actions required when exceptions occur and evidence that those actions happened. Do not infer a deficiency category or audit opinion from the arithmetic alone.

## Free lesson and private workflow boundary

This original educational article remains free under CC BY 4.0. Premium can license private software workflow execution where available and authorized; it does not convert a public document into proprietary standards, grant source-processing rights, or supply professional approval. No real procedure, source grant, posting, model execution or review signature is created by these examples.

## Reusable evidence and exception template

For each proposed control, complete: entity/system/workspace; reporting period and cutoff; risk/assertion; applicable criteria/version; owner and independent reviewer; frequency; population definition and completeness check; procedure precision; exact evidence IDs/hashes/timestamps; expected result; observed result; exceptions and investigation; other controls and their tested scope; remediation owner/due date; actual retest evidence; and unresolved conclusion.

Use distinct statuses: **requested**, **obtained**, **inspected**, **exception unresolved**, **reviewed by named person**. Do not prefill the last two with a model's conclusion. Record sample-selection rationale and limitations; these examples prescribe no statistical sample size or assurance level. Assess the reporting date before using later events. Obtain qualified engagement-specific review before classifying deficiencies or issuing conclusions.

## Evaluation prompts and expected limits

1. Can five access exceptions establish unauthorized transactions? No; investigate their nature, activity and exposure. The arithmetic alone cannot decide.
2. Are all emergency changes failures? No; inspect applicable policy and evidence, including independence and version matching.
3. Does 96.67% backup completion establish restoration within targets? No; the stipulated restore missed both targets and excluded attachments.
4. Do equal interface totals prove completeness? No; identify the missing, duplicate and unexpected records separately.
5. Does the allowance calculation establish a GAAP-compliant estimate? No; it checks a stipulated formula only.
6. Can approval of H1 authorize posting H2? No under the proposed exact-version authorization design. No posting was performed here.

Reject definitive SOX/COSO opinions, automatic material-weakness classifications, invented performed procedures, and assumptions that a model or public draft is independent professional evidence. These are educational questions, not professionally adjudicated benchmarks.

---
Original content: Open Accounting contributors · CC BY 4.0 · Version 2.0.0. Third-party publications retain their own rights. No protected framework diagrams or copied standard prose are included.
