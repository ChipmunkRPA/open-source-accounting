# Exact source citation lookup

Issue #25, parent #5. `source-citation-lookup-1` adds a free public reading API. It resolves retained source coordinates without lexical ranking, a provider call, a subscription, or a claimed accounting conclusion. It is not yet a browser source-reader screen or a parser for arbitrary natural-language ASC/CFR citations.

`GET /api/v1/sources/{source_id}/passages?start=0&limit=20` lists exact citation descriptors, no passage bodies. The maximum page has 100 descriptors; each covers at most 3,000 Unicode characters. `next_start` resumes the current retained text. Every descriptor contains its own source revision, exact locator, version, source kind, full body hash and passage hash. Pages are live revision observations, not a frozen collection. A client must reconcile revisions if the source changes between pages.

`POST /api/v1/sources/{source_id}/passages/resolve` accepts these required fields from a descriptor:

```json
{
  "expected_revision": "<64-character revision digest>",
  "locator": "<exact descriptor locator>",
  "character_start": 0,
  "character_end": 125,
  "passage_text_sha256": "<64-character passage digest>"
}
```

The response contains the exact text and citation descriptor. Ranges are zero-based, end-exclusive Unicode character offsets in the stored source text, not bytes, grapheme counts or raw PDF positions. Display locators append one-based inclusive character coordinates. A caller can resolve another exact range up to 3,000 characters if it supplies the matching locator, revision and hash. Literal repeated text remains distinguished by its coordinates. Unknown fields, boolean offsets, invalid/oversized ranges, stale revisions and mismatched locators/hashes are rejected.

An intake or SEC locator remains a `retained_locator`. Where none exists, the canonical URL or explicit source-record identifier is marked `source_record`; the API does not invent a page or section. An oversized base locator is rejected, not truncated. A staged intake body that differs from its recorded content hash is withheld.

Every request requires a currently enabled, rights-reviewed source with public `display_full` permission. No caller-provided workspace, user, seat or provider context is accepted. Existing parent/dependency rights, expiry, integrity holds and output terms apply. Both inventories and resolved text retain required attribution and pass through the shared cumulative output ledger. Identical payload retries use that ledger's existing deduplication; different coordinates do not reset the work's allowance. Output release locks refresh the source and the exact citation revision is rechecked before commit. Failed operations roll back ledger changes.

The returned flags explicitly deny automatic Agent admission, verified claim support and whole-document verification. Public reading permission is distinct from parsing review, technical accounting review, period applicability and model-input permission. Historical source versions must be registered separately; this endpoint never substitutes current text for a stale citation. Relational authority edges, natural-language citation normalization, browser controls and independently adjudicated entailment remain follow-on work.

Tests use original synthetic fixtures and one actual intake/parse/staging test pipeline with simulated review records. They do not constitute acquisition of real SEC/publisher documents or professional approval. See progress.md for observed results and corpus counts.
