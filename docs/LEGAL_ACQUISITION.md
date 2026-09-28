# Official legal-source acquisition packet — #16, parent #5

The [candidate packet](../reports/intake/legal-candidates.json) declares **nine selected units across three families**: six Supreme Court opinion packages decided in 2024 or 2026; one historical 2025 annual CFR XML volume; and two New York public-accountancy statute sections. The [14 original review scenarios](../reports/intake/legal-review-cases.json) are unexecuted and unadjudicated. No preserved original artifact, production parse, runtime rights grant, professional approval or index entry was added. Web PDF text is discovery evidence, not an acquisition receipt. This pilot does not complete any family, court/year universe, procedural history or all-content requirement.

## Routes and observed limits

The House U.S. Code download seed returned HTTP 403 in the preceding session. It was not retried or bypassed. FederalRegister.gov's API documentation redirected to a CAPTCHA/access-request page in this session; no challenge, request or alternative body route was attempted. The earlier Govinfo USCOURTS collection page returned no extractable text; this is not proof that opinions are absent or access is prohibited. Court participation/year coverage and official API enumeration remain to be established. No PACER fees, keys or private credentials were used.

The [Govinfo annual CFR directory](https://www.govinfo.gov/bulkdata/CFR/2025/title-17) exposes volume-level XML candidates. This deliberately selects a historical edition, not current law. The volume-3 directory entry advertises 5.7 MB and a modification time; neither is a verified original-byte receipt or legal effective date. A bounded 500,000-byte read of the directory resolved the exact href; no XML body was downloaded. The existing `ecfr_xml` parser recognizes some SECTION/SECTNO structures, but that does not prove annual-volume completeness, edition provenance, table fidelity or graphics coverage. A dedicated annual-CFR adapter and reviewed rendition comparison remain necessary. Coordinate overlapping securities provisions with #1 instead of counting them twice.

The [CFR XML user guide](https://www.govinfo.gov/bulkdata/CFR/resources/CFR-XML_User-Guide_v1.pdf) is version 1.0 dated December 17, 2009, although its directory modification date is in 2026. Its printed pages 1–4 discuss XML publication status, potential table/graphic differences, reuse and branding. Revalidate its current applicability; do not call it a new 2026 guide or treat it as a runtime approval. Never characterize this application's copies as official government publications.

The accessible [eCFR date guidance](https://www.ecfr.gov/reader-aids/ecfr-developer-resources/understanding-ecfr-dates) distinguishes substantive amendments, any later edits and the date through which a title is current. Preserve `latest_amended_on`, `latest_issue_date`, `up_to_date_as_of`, `meta.date` and `import_in_progress` separately. The interactive documentation shell did not expose endpoint details in the text view; no tested live importer is claimed. [Point-in-time guidance](https://www.ecfr.gov/reader-aids/using-ecfr) describes coverage back to January 2017 and distinguishes eCFR from an official legal edition.

## Selected opinion scope

| Package | Decision date | Official citation | Observed PDF pages | Coordination |
|---|---|---|---:|---|
| Macquarie Infrastructure v. Moab Partners, 22-1165 | 2024-04-12 | 601 U.S. 257 | 12 | #1/#3 disclosure research |
| SEC v. Jarkesy, 22-859 | 2024-06-27 | 603 U.S. 109 | 97 | #3 enforcement |
| Moore v. United States, 22-800 | 2024-06-20 | 602 U.S. 572 | 83 | #20 tax |
| Loper Bright v. Raimondo, 22-451; related 22-1219 | 2024-06-28 | 603 U.S. 369 | 113 | Administrative-law research |
| Murray v. UBS Securities, 22-660 | 2024-02-08 | 601 U.S. 23 | 21 | #3 controls/whistleblower research |
| Sripetch v. SEC, 25-466 | 2026-06-04 | 608 U.S. 555 | 27 | #3 remedies; newer-history candidate |

Exact court-hosted URLs, caption locators and printed package ranges are in the candidate JSON, reached through the official [2023](https://www.supremecourt.gov/opinions/slipopinion/23) and [2025](https://www.supremecourt.gov/opinions/slipopinion/25) term lists. The inspected covers identify preliminary prints/page proofs subject to revision. Court decision dates do not establish when these particular file versions became publicly available. Those publication dates and raw hashes remain null.

The [Court's publication overview](https://www.supremecourt.gov/opinions/USReports.aspx) distinguishes preliminary prints, page proofs and bound U.S. Reports. Preserve physical PDF pages and printed pages independently. A package may contain syllabus, majority, concurrence and dissent; its complete page range is not a majority-only locator. Related dockets do not multiply the artifact count. Disposition, precedential designation and exhaustive later history remain unverified in this metadata packet, and no case holding is adopted as accounting advice. External material linked by the Court needs separate treatment under its [website notice](https://www.supremecourt.gov/policies/web_policies_and_notices.aspx).

## New York pilot

The official Senate pages for [Education Law §7401](https://www.nysenate.gov/legislation/laws/EDN/7401) and [§7404](https://www.nysenate.gov/legislation/laws/EDN/7404) provide a narrow professional-accountancy pilot. The former displays revision label 2014-09-22. The latter displays 2025-11-28 and parallel subdivision 1(2)–(4) clauses labeled until/from November 21, 2026. Preserve the labels as observations, with clause-level applicability still awaiting session-law/regulator reconciliation. Do not equate a page revision label with an enactment or universal effective date; do not decide individual licensing eligibility from this packet.

[Open Legislation](https://legislation.nysenate.gov/) advertises an API-key service. No signup, API key or credential was requested. The selected web pages were publicly readable. This is a state-specific rights proposal, not an application of federal section 105 to all state materials. Referenced private standards, site assets and external commentary are separate works.

## Concrete acquisition and review handoff

Assign an actual rights owner to each exact URL/version and approve only the needed operations, route, internal audience, retention and location. The first proposed operations are `acquire` and `store_raw` for complete originals; `extract` and `store_text` require separate consideration after embedded-material screening. Leave model input, embeddings, full display, quotations, exports, redistribution and training disabled unless individually authorized. Neither this packet nor a government domain is a grant. No permission request was sent.

After approval, use the existing authenticated intake path and preserve requested/final URL, response headers/status/MIME, actual original bytes, SHA-256 and retrieved timestamp. Retain all publication-stage notices. Do not invent older bytes for an overwritten URL. Stage unapproved passages only after independently checking completeness, exact section/page locators, tables and separate opinion voices. Later amended opinions need new immutable versions and reviewed relationships; current copies cannot be used as evidence of what was publicly available earlier.

For each original educational case brief, use the following authoring record after source acquisition:

1. Identify court, docket, jurisdiction, document type, exact hash/stage and research as-of date.
2. Separate allegations, accepted facts, procedural events, party arguments, majority reasoning and other opinions, each with actual locators.
3. State the narrow issue, disposition and limits; connect it to a declared accounting question without importing an unsupported rule.
4. Record later-history sources checked and unresolved gaps; do not claim a proprietary citator-equivalent result.
5. Write an original hypothetical changing one material fact or jurisdiction, then explain which question requires fresh evidence. Mark all provisional analysis as unreviewed.
6. Have a qualified independent reviewer assess the exact revision and scope; separately approve historical applicability and source operations before indexing/admission.

No completed briefs or gold answers are claimed here. Prioritized remaining scope includes securities/SOX statutory versions, auditor-liability decisions, copyright/source-use cases, tax opinions, lower federal courts and additional state jurisdictions. The next engineering task is annual-CFR XML provenance/completeness handling with original offline fixtures, while authorization and review owners remain outstanding.

## Parser follow-up evidence

The guide's printed page 12 identifies `GPOTABLE/BOXHD/CHED` header cells and `ROW/ENT` data cells. Inspected `backend/app/sec_core/parsers.py::ecfr_xml` iterates only TR/ROW table rows and TD/TH/ENT cells; it does not emit BOXHD/CHED headers in the normal table path. A nonempty extraction therefore cannot prove header-complete annual CFR tables. Next work must preserve verified header relationships, detect unsupported spans/graphics rather than silently lose them, and retain distinct annual-volume provenance. Use original synthetic fixtures and the actual source-intake rights/review pipeline; no real-volume parser success is claimed here.
