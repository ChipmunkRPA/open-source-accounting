# SEC recent comments

Free public route `/sec-comments`, API `/api/v1/sec-comments`; parent #5, source #2, ingestion #8/#24 and retrieval #25. Search company, CIK, accession, reviewed filing or topic; filter staff letters (`UPLOAD`) versus company responses (`CORRESP`), topic and recent two calendar years by letter date or all retained dates. Results include topic counts within the selected records, draft analysis, follow-up questions, official links, explicit chain links when known and immutable artifact provenance when retained.

The [SEC correspondence guide](https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence) identifies those form types and explains delayed release following completed reviews or registration effectiveness. [SEC's detailed guide](https://www.sec.gov/answers/how-to-search-for-edgar-correspondence) distinguishes filing dates from release dates and notes that some responses occur in other filings. Rulemaking comments are a separate collection. Never infer absence, resolution, misconduct, staff acceptance or a complete chain from a date filter or isolated letter.

## Actual coverage

`sec-comments-reference-2026-09-28.1` contains two verified references across two companies, one staff letter and one company response, with original concise editorial analyses:

- [Lionsgate July 21, 2026 staff letter](https://www.sec.gov/Archives/edgar/data/2052959/000000000026007220/filename1.pdf), page 1 comment 1: segment/non-GAAP disclosures. [Official index](https://www.sec.gov/Archives/edgar/data/2052959/000000000026007220/0000000000-26-007220-index.html) establishes filing date and form.
- [Driven Brands January 5, 2026 response](https://www.sec.gov/Archives/edgar/data/1804745/000180474526000002/filename1.htm), comments 1–2 and associated responses: materiality, recurring errors and controls. The header establishes CORRESP and the letter date. Filing and public-release dates remain unverified. The index could not be read in this session; no date was inferred from the accession or response text.

These are selected reference records, **not downloaded whole originals**. Current increment: 2 references / 2 original draft analyses / 0 retained full artifacts / 0 actual pipeline parses / 0 independent parser, accounting or applicability reviews / 0 Agent admissions / 0 adjudicated evaluations. Neither reference is represented as a complete correspondence chain. Staff concerns reproduced in the company response are explicitly attributed as such. Independent reviews remain pending.

## Retained archive and analysis

Register exact SEC document URLs using the existing source intake endpoint and an optional `sec_correspondence` manifest object (schema in OpenAPI). Metadata binds company/CIK/accession/form, letter/filing/publicly-available/checked dates, reviewed filing, locator and explicit related accession IDs to the immutable manifest. Only SEC_FILINGS document-body parsers accept it. Older manifests omit the new null field, preserving existing hashes. Prepared reference-only proposals are in `content/sec_comment_pilot`; these proposals grant no operations.

After actual operation-specific authorization, acquire original bytes through the bounded official gateway, parse and stage with the existing raw/normalized hashes, notices and review workflow. Current authorized public-candidate passages appear on each archive request. Reads recheck parent rights/revision, source text hash and intake bindings; revoked, changed, private or missing bindings are excluded. A public URL alone is not reuse authorization. Stored original downloads and review packets remain subject to existing access controls; the public page links to the official original and shows provenance, not a raw-storage bypass.

`sec-comment-topics-1` performs deterministic lexical topic analysis of eligible retained text. It emits exact passage locators and zero-based character match ranges, text hash and analysis version. It does not use Gemini, execute source instructions, summarize management positions, determine whether a concern is resolved or grant professional approval. Editorial starter analyses remain separate from automatic matches. Topic counts measure selected records, not SEC-wide trends or comment severity.

At most 20,000 eligible-candidate source rows are examined per request; truncation is explicit. Each record displays at most 100 findings/provenance records, and each topic finding at most 20 match offsets with total match count; partial analysis is explicit. Public result pages contain at most 100 records. A persistent, evaluated large-corpus index remains follow-on work.

## Updating

Use the existing SEC submissions discovery adapter to identify UPLOAD/CORRESP candidates, follow older-history descriptors and exact filing indexes, then reconcile explicit document relationships. An accession prefix need not equal the registrant CIK. Retain letter, filing and first-publicly-observed dates separately; the first observation is not proof of the initial release date. A company/date match alone does not establish a response relationship. Preserve amendments and corrections as new versions.

This change does not activate external acquisition, a scheduler, notifications, paid resources or model inference. The selected reference catalog is updated by a reviewed normal main commit; authorized retained records refresh on page/API reads. Pending: approved external discovery/acquisition cohort and contact settings, actual operation authorizations, complete correspondence chains, independent analysis review and evaluation. No claim of exhaustive or continuously crawling EDGAR coverage is made.
