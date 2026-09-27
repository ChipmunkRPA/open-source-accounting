# Crossref metadata intake (#8, #19)

Adapter `crossref-works-1` supports a single explicitly scoped Crossref works-list JSON page. It produces bibliographic candidates, never authoritative accounting evidence or full-text permission. It does not fetch abstracts, article bodies, license pages, DOI redirects or next pages.

## Verified official contracts

Checked 2026-09-27:

- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) describes deposited scholarly metadata and warns that some abstracts can be copyrighted. The dedicated route selects bibliographic fields and refuses unexpected fields before raw storage.
- [Official metadata format](https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md) describes partial publication dates, contributor records, version-specific licenses and resource links, and update/relation records. The adapter preserves those distinctions, with record hashes and JSON-pointer locators. A year-only date remains year-only; registration/indexing dates never become publication or accounting-effective dates.
- [Accessing full texts](https://www.crossref.org/documentation/retrieve-metadata/text-and-data-mining/) distinguishes resource URLs, versions and intended uses. Links do not guarantee access; an accepted-manuscript license cannot silently authorize a version-of-record download. The output retains claims without granting any source operation.
- [Access and authentication](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) currently lists public rate/concurrency limits of 5/1 and polite limits of 10/3, and describes rate/pool response headers. This implementation conservatively allows one in-flight Crossref request across workers plus the existing shared 4-request/second intake rate. PostgreSQL advisory locks coordinate deployed workers; local SQLite uses an OS file lock. It retains the rate/pool headers in receipts. No premium subscription or API key is used. 403/429 still stop the route for operator review; no automatic retries or cursor traversal are introduced. Operators must reassess returned limits and official policy before live runs.

These public documentation checks are not an actual API smoke test, a license review or proof that every publisher's records match the supported shape.

## Prepare a metadata manifest

Use family `OPEN_LITERATURE`, parser `crossref_metadata`, and only MIME `application/json`. Requested URL must use `https://api.crossref.org/works` or `/v1/works`, with no redirects. The query must specify a topic (`query` or `query.bibliographic`), `filter=from-pub-date:YYYY-MM-DD,until-pub-date:YYYY-MM-DD`, `rows` from 1 through 100, and `select` containing exactly these fields:

```text
DOI,title,type,publisher,container-title,author,license,link,update-to,update-policy,relation,issued,published-print,published-online,created,deposited,indexed
```

Optional `cursor` identifies an explicitly reviewed subsequent page; optional `mailto` identifies the real operator. Do not invent a contact. The existing `SEC_USER_AGENT` setting must also identify the operator before any real network request, despite its legacy name. Every requested URL, including pagination, is part of the immutable reviewed manifest. No downloaded full text or user credentials are accepted through this adapter.

Register metadata through the existing CLI/API, obtain real independent operation review, then acquire/import and run `discover-index ARTIFACT_ID`, followed by `discovery DISCOVERY_ID`. Acquire/store_raw/**extract** permissions are required because the bounded subprocess screens JSON before storage. Discovery additionally needs store_text; candidate viewing needs store_text/display_full. Runtime switches stay disabled until configured for an approved operation. Manual delivery uses the same byte-bound manifest and screening. No real permission was added by this implementation.

## Evidence and limitations

Accepted records retain DOI/title/authors/venue, partial dates, license version/start claims, full-text-link version/intended-use metadata and correction/retraction/version relations. The raw artifact, per-record hash, JSON-pointer locator, exact query, API message version, adapter version and family recipe remain traceable. Unknown editions and accounting-effective dates remain null. An update notice's `update-to` field points to the updated work; it is not automatically a retraction flag for the notice itself. Missing update fields do not prove that a work is unretracted.

Each DOI occurs once per page; duplicates or malformed records fail the page for review. Upstream total-results and next-cursor are retained but never counted as acquired works. Unselected fields, duplicate JSON keys, unsupported shapes, non-finite numbers, oversized bodies and invalid dates fail before storage. An HTTP 200 JSON error envelope is not an acquired artifact. Metadata cannot use the ordinary parse/stage route to become evidence; each candidate requires its own separately reviewed acquisition and evidence lifecycle.

Live corpus acquisition, work-specific license inspection, independent technical/applicability review, cross-page inventory/version reconciliation and human-adjudicated evaluations remain open. All implementation fixtures are synthetic; no actual article or publisher index was acquired.
