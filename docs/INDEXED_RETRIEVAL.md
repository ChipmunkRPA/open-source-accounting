# Authorized PostgreSQL lexical retrieval

Issue #25, parent #5. `postgres-simple-lexical-1` replaces the first-2,000-source scan on PostgreSQL with GIN full-text candidate lookup. SQLite streams sources for development compatibility; it is not an indexed production benchmark. Private workspace uploads remain on their separate authorized document path.

The PostgreSQL `simple` configuration is explicit in both expression indexes and queries, following the [PostgreSQL index documentation](https://www.postgresql.org/docs/18/textsearch-tables.html). Public source titles and explicitly indexed source bodies have separate indexes. Source-body indexing is never a migration backfill, license grant, professional review or permission to call a model. No provider is invoked by lexical indexing. pgvector, a separately verified embedding endpoint, semantic recall/reranking evaluation and the authority graph remain outstanding.

## Build and remove an exact source index

An administrator with a fresh authenticated session may:

1. `GET /api/v1/admin/sources/{source_id}/search-index` to read the expected revision and separate stored/current/allowed states.
2. `POST` the same route with `{"expected_revision":"<exact revision>"}` to create or replace one index entry. Repeating the same current revision is idempotent. Stale revisions fail before writing.
3. `DELETE` the same route to remove derived text and its index entries while retaining the source and audit history. Disabling that source through the source API also removes its own index entry. Source deletion cascades to index entries.

The conservative indexing gate requires current `embed` and `store_text` rights in the fixed `source_index` / `internal_ingestion` context, including existing parent, parser, technical, applicability and dependency checks. Direct or intake-parent scoped grants are excluded from the global index; workspace/seat/provider-specific indexes are not implemented. Source bodies must be nonempty and at most 100,000 characters; larger works must first be staged as appropriate source units, never silently truncated. The index version and exact rights/editorial/body/policy revision are stored. The entry contains a derived copy of the title/body and must be treated as source content in retention and backup policies.

Expiry, changed approvals/body/provenance, parent revocation and operation denial prevent use of an old body index. Such entries do not silently refresh. Direct disabling removes the entry immediately; expiry or ancestor changes can leave inaccessible derived bytes pending explicit removal. Operators can use the resumable cleanup sweep below to remove affected live entries and must separately apply the approved backup-retention process. This release does not claim automatic physical purge of every transitive dependency or backup. The original immutable source corpus remains separate.

## Runtime behavior and bounds

Candidate IDs are the union of matching title and body indexes, streamed in deterministic source-ID order. There is no arbitrary first-2,000-source exclusion. Indexed bodies must still match their current exact revision and indexing authorization. Missing/stale/unpermitted body entries supply only independently available title-reference candidates; they never fall back to unindexed body reads as evidence. Model, storage, quotation, technical/parser, framework, entity, reporting-period, historical applicability, dependency and final output gates continue to apply. Required review cannot be replaced by a high lexical score.

Queries use literal ASCII alphanumeric/hyphen tokens and OR lexical matching, then the existing paragraph ranker. At most 64 distinct terms of 256 characters each are accepted; oversized queries produce an explicit error rather than silent term loss. There is no stemming, semantic entailment, multilingual completeness or authority ordering claim. Matching sources are streamed in batches of 100, and retained source ranking candidates are periodically trimmed to the requested top results. A broad query can still visit many matches; latency/admission limits and evaluated semantic ranking remain work under #25/#36. Selected private document behavior and workflow evidence limits remain separate.

## Observed verification

The real local PostgreSQL scale fixture contains **10,001 original synthetic sources and index entries** with a single planted body hit after the old cutoff. PostgreSQL's natural `EXPLAIN ANALYZE` plan used `ix_source_search_body_fts`, with no forced planner setting: **0.673 ms** index-query execution and **0.005907 seconds** application retrieval in one observation; planted-hit recall **1/1**. The fixture also checks revocation, changed bodies, explicit rebuild/removal and cascade deletion. This is not professional accounting accuracy, real-source coverage, general recall/precision or a production latency guarantee. See progress.md for final combined regressions and CI evidence.

## Resumable cleanup of stale derived entries

`source-index-cleanup-1` provides explicit administrator maintenance without creating a schedule:

1. Start with `POST /api/v1/admin/search-index/sweeps`, supplying an `Idempotency-Key` of 16–200 characters. A repeated key for the same actor returns the same sweep; it never resets progress. The stored cleanup version remains attached to that sweep. A version mismatch blocks advancement and requires a new key/new sweep; old observations are not relabeled.
2. Read `GET /api/v1/admin/search-index/sweeps/{id}` for the persisted sequence/cursor and separate initial-stored, scanned, retained, removed and vanished counts.
3. Advance with `POST /api/v1/admin/search-index/sweeps/{id}/advance` and `{"expected_sequence":0}` (then the returned sequence). Each atomic batch checks at most 100 entries. A stale retry gets a revision conflict; reload status before continuing. Writes require a fresh authenticated administrator session.
4. Read paginated `GET /api/v1/admin/search-index/sweeps/{id}/receipts?after=0` for bounded per-entry observations and receipt hashes. Receipts preserve source ID, exact index revision/version, indexed-text hash and outcome, never the source body. They are restricted administrative records.

The sweep fixes an upper source ID but does not freeze corpus membership or approvals. Entries added behind the cursor require another sweep. Initial-stored is a separate point-in-time count, not a denominator that guarantees a complete inventory. Retained means current at that entry's check, not an approval or lasting assertion. Vanished means the selected entry disappeared before its check; entries removed before candidate selection are not invented as observed removals. Completion means the observed ID-range traversal ended, not that future content or rights changes are cleared.

Cleanup takes the same source-before-index row locks used by rebuilding, then re-reads the entry. PostgreSQL sweep locks and SQLite writer serialization prevent conflicting advances; expected sequences reject stale retries. Index-row deletion, counters, cursor and receipt share a transaction, so a crash rolls them all back. Required rights/review checks include ancestors and publication dependencies; stale revisions, expiry, revocation, new scoped restrictions and obsolete index versions remove the derived entry. Original sources, immutable acquisitions, review records and user artifacts are not deleted or reapproved by this operation.

Deletion removes live derived rows and their GIN entries. It does **not** attest to forensic disk erasure, MVCC/vacuum completion, removal from replicas/backups or completion of the operator's retention policy. No automatic cadence, background job or notification has been activated. New index builds remain explicit and separately authorized.


## Administrator interface

Open **Search indexes** from the administrator account links, or **Search index** beside a source in Source administration. `/search-index/{source_id}` loads one exact source; `/search-index?sweep={id}` opens a saved sweep. The screen requires the server-reported administrator/rights-approver role, and all API actions independently retain their server-side role and fresh-session checks.

The screen exposes exact-revision build/refresh, explicit derived-index removal, stored-versus-current state, and permission/review gating. A changed input invalidates its loaded state; requests disable conflicting controls, stale responses are discarded after navigation/selection changes, and a revision conflict requires reloading. No control approves source rights or accounting review.

Cleanup can be started with a retry-stable request key, advanced one batch at a time, and reopened after reload. Saved sweeps use 20-item chronological keyset pages; receipt pages are read separately and expand bounded hash-only observations on demand. Errors leave reload controls available rather than silently repeating a mutation. `GET /admin/search-index/inventory` reports stored entries, with `current_entries: null` and `approval_granted: false`; it does not label stale stored bytes as approved indexed coverage.

Local browser QA used an isolated SQLite database, mock mode and synthetic sources. It verified build/removal, one retained and one revoked entry in a cleanup batch, receipt disclosure, saved-sweep reload, missing-source handling, stale-revision rejection, disabled actions and non-admin denial. A 390×844 viewport check verified readable controls and scrollable tables. [Synthetic mobile screenshot](../reports/retrieval/index-cleanup-mobile.png). This is not a deployed-origin, live MFA, real rights-review or production-index coverage result.
