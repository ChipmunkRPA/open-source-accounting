# Operation rights implementation and remaining gates

Issue #7 is in progress, not complete. The 11 recognized operations are `acquire`, `store_raw`, `extract`, `store_text`, `embed`, `model_input`, `display_full`, `quote`, `export`, `redistribute`, and `train`. Unknown actions, truthy non-booleans, expired/not-yet-effective grants, unreviewed revisions and missing scope context deny access. A reference-only record never authorizes body operations. HTTP approval now requires the exact rights revision, policy version and an explicit reviewer attestation, in addition to the existing fresh MFA, scoped role and separation-of-duties checks.

The revision binds work title/publisher/URL/version, body hash, grants, scope, evidence reference and attribution. Editorial/applicability annotations remain separate. Each new approval increments the policy version so old saved evidence cannot revive. Existing records without a bound rights approval fail closed and must be re-reviewed; no data migration invents approval. Synthetic local seed accounts are marked as demo fixtures and are prohibited in production.

`license_evidence_ref` is an opaque reference to a restricted evidence system, not the legal advice or agreement itself. Its presence does not verify a license. Authorized reviewers must validate the evidence. Scoped grants require exact route/workspace/seat/audience/provider/region/retention/jurisdiction context; Agent retrieval/model/output paths now supply server-derived workspace, route, audience, provider and region context. Seat, retention and jurisdiction scopes are now resolved from independently verified per-user/workspace records; they deny when those records are missing or stale. See [verified scopes](VERIFIED_SCOPES.md). See [runtime checks](RUNTIME_RIGHTS.md).

## Pending implementation

- Complete family adapters, live authorized smoke, manual import and review/index integration in #8. The metadata-only pre-acquisition registry and rights-gated raw/parsed storage are implemented; legacy acquisition entry points are disabled. See [intake scope](../SOURCE_INTAKE.md).
- Obtain actual publisher-seat, jurisdiction and provider-retention evidence for verified scope records; verify provider behavior and implement public/service context and retention deletion (#25/#26/#29/#34). Runtime records and per-model-call checks are implemented; no client field may self-assert an entitlement.
- Persist retention-aware deletion across derived indexes/caches/articles. Revision-bound counsel proposals, independent decisions, separate rights activation and revocation are implemented; actual counsel identities/evidence remain unavailable. See [counsel records](COUNSEL_RECORDS.md). Conservative work-group output accounting now applies across registered-source output paths; disguised copies/manual uploads still need cross-corpus provenance controls. See [output rights](OUTPUT_RIGHTS.md).
- Verify actual attribution obligations and work grouping before enabling restricted-source grants. Server notices now render in source/evidence/results/memo views and all four export formats; this is not proof of a license.
- Obtain real operation-specific permissions and independent review. Nine request packets are drafts only. No fair-use approval or publisher license was fabricated.

## Policy-page observations, 2026-09-27

Seven official policy pages were read using web retrieval. These are discovery notes, not saved original HTTP artifacts, legal advice, acquisition permissions or source-corpus additions. No publisher standard or commercial explanatory body was downloaded. Exact HTTP-body hashes and response headers are unavailable in this discovery pass and are not invented.

- The [Copyright Office fair-use explanation](https://www.copyright.gov/fair-use/more-info.html), factors and concluding paragraph, describes a case-specific inquiry without a guaranteed word-count formula.
- [IFRS intellectual property](https://www.ifrs.org/legal/intellectual-property/), Licensing, points ongoing product/service use to a license agreement and licensee questionnaire.
- [AICPA terms](https://www.aicpa-cima.com/resources/article/terms-of-service), ownership/personal-use paragraphs, do not establish permission for this public commercial AI service.
- [IFAC intellectual property](https://www.ifac.org/ifac-intellectual-property), use rules and request route, requires written permission beyond individual reference and identifies OPRI. Actual edition ownership remains to be checked.
- [IIA licensing](https://www.theiia.org/en/about-us/licensing/), licensing scope FAQ, excludes public AI inclusion under the described license. Specific compatible authorization remains required.
- [DART terms](https://dart.deloitte.com/USDART/obj/vsid/441069), section 2.9, restrict AI/ML and automated collection; separate compatible authorization is unresolved.
- [PCAOB terms](https://pcaobus.org/privacypolicy), Authorized Use and Intellectual Property Rights (displayed update September 9, 2021), separate restrictions on automated collection from conditional Public Materials reuse.

FAF/COSO/ISACA and other product-specific terms/contact routes still need verification. The all-family matrix preserves all 32 recipes without granting any text operation.
