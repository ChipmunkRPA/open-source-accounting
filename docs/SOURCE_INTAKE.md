# Source intake — issue #8

This slice adds a metadata registry for all 32 source families and explicit acquisition,
parsing and staging steps. Family discovery returns the versioned recipes in
`content/source_families.json`; it does not crawl sites. Follow each family issue and
`content/SOURCE_RETRIEVAL_PLAYBOOK.md` when preparing a work manifest. Registration is
not permission, acquisition is not review, and staging is not indexing.

## Operator sequence

1. Register metadata through `POST /api/v1/admin/intake/works`: a `source` using the
   SourceCreate contract and an `IntakeManifest`. The OpenAPI schema is authoritative
   for input shape. Body text is rejected. Select a family, publisher work ID, edition,
   language/jurisdiction, authority, declared coverage unit, parser and access mode.
   Include exact official acquisition URL and each permitted redirect URL, original
   notices, limits, distinct dates (unknown is null), date notes, effective conditions
   and superseded work references. The family/work/edition tuple cannot be reused.
2. Preview metadata, rights revision and operations without network access. A real
   independent rights approver must examine the underlying operation-specific evidence
   and approve that exact source policy/manifest revision using the existing rights API.
   Merely setting a public-candidate mode or an official URL does not allow acquisition.
3. With `SOURCE_FETCH_ENABLED=true`, an approved operator contact in `SEC_USER_AGENT`,
   and explicit `acquire` plus `store_raw` rights, request acquisition with a durable
   idempotency key. Reuse that key to resume after inspecting status. The API requires
   a freshly MFA-authenticated administrator; production cannot use demo headers.
4. Parse a successful artifact explicitly. This additionally requires `extract` and
   `store_text` and verifies the raw hash. XML, structural HTML, PDF and text parsers
   produce immutable normalized passage records with exact locators and text hashes.
5. Stage a parsed version explicitly. Deterministic passage IDs make retries idempotent.
   Passage Sources start unreviewed, require technical and applicability reviews, and
   inherit the parent rights dependency. Disabling/revising/expiring the parent denies
   dependent body use. No model call, index insertion or professional approval occurs.
6. Complete the separate independent review and index workflows in #22–#24 before
   admitting this material to Agent evidence. This slice deliberately has no command
   that can convert a download into professional approval.

CLI (run from `backend`, using the installed virtual environment):

```sh
.venv/bin/python -m app.ingest discover
.venv/bin/python -m app.ingest register --file /private/operator/work-manifest.json
.venv/bin/python -m app.ingest inventory
.venv/bin/python -m app.ingest preview WORK_UUID
.venv/bin/python -m app.ingest acquire WORK_UUID --request-key OPERATOR_REQUEST_ID
.venv/bin/python -m app.ingest parse ARTIFACT_UUID
.venv/bin/python -m app.ingest stage EXTRACTION_UUID
.venv/bin/python -m app.ingest coverage
```

Supply `OSA_API_URL` and a current token in `OSA_INTAKE_TOKEN` through approved secure
channels. Do not put tokens in command arguments, issues or files committed to Git.
The inventory is bounded to 100 records and reports `next_offset`; the API accepts
`?offset=`. HTTPS is required except explicit localhost development. CLI requests do
not follow redirects or use environment proxies. The old SEC CLI acquisition route
and legacy `fetch_sec` service reject network calls and point to this registry.

## Persistence, limits and status

Migration `0002_intake` adds work editions, raw artifacts, normalized extractions,
leased acquisition attempts and a shared request-budget row. Deploy migrations before
workers. All replicas must use the same PostgreSQL database; SQLite budgets coordinate
only one development machine. Cloud workers reject SQLite budgets. Four reservations
per second are shared across families and redirects, below SEC's configured hard cap.

Requests use exact allowlisted HTTPS URLs, checked public IPs pinned to TLS connections
with original-host certificate verification, no credentials/cookies/proxy rotation,
and at most four requests including redirects. Bodies have a manifest byte ceiling
(up to 16 MB), a 120-second network deadline plus bounded socket calls, allowed MIME
checks, and no transparent decompression. HTTP 401/403/429 and detected login/CAPTCHA
pages disable that source route and require operator review; retries cannot bypass the
block with a new idempotency key. No automatic fallback/backoff retry is attempted.
Parser subprocesses have a 25-second wall deadline, 15 CPU seconds and a 512 MiB
address-space bound on Linux; existing PDF/page and parser limits still apply. The
subprocess is a resource boundary, not a complete OS/network sandbox. Production
controlled egress and parser isolation remain security/deployment work.

A 180-second attempt lease survives process crashes. PostgreSQL source-row locks
serialize lease decisions and commit-time rights checks. Raw objects are create-only
(private GCS generation precondition or local atomic hard link); duplicates retain
one work/hash artifact. Normalized JSON is separate from raw bytes. Failed parsing
retains the authorized raw artifact without staging body text. A storage success
followed by DB failure can leave an unreferenced private object; lifecycle reconciliation
and rights-driven deletion of all derived data remain #7/#34 work.

Receipts retain requested/final URL, GET/status, selected ETag/Last-Modified/content
headers, actual retrieval time, raw hash, manifest/policy digest, actor, acquisition
attempt and source dates/notices. Null dates remain unknown. Cookies and arbitrary
upstream headers are not recorded. A redirect destination must already be bound into
the approved manifest. Redistribution is not inferred from artifact possession.
Coverage counts work editions, raw artifacts, parser versions and parsed passages
separately; overlapping units never become a percentage-complete claim.

## Scope still open

- Live smoke downloads require an identified operator contact and real rights review
  of each exact manifest. None were performed for this slice. Tests use original
  synthetic bytes and synthetic attestations; no publisher license is represented.
- Manual imports require exact reviewed delivery evidence, as described below. Private
  records remain reference-only here; private documents use the workspace upload pipeline.
- Family API/bulk discovery adapters, applicability/entity-adoption review, review/index
  commands, deletion and reconciliation remain. Shared counsel decisions, output limits
  and model/export scope controls are documented separately; they do not approve intake.
- Route/audience scope is supplied by server intake. Other scoped grants fail closed
  until the relevant trusted context is implemented. An ingestion-only grant cannot
  automatically authorize public reading or model access.
- Registration does not audit the legality or accuracy of operator declarations.
  Source approvals and technical/accounting judgments still require real people.
- GCS, live identity, model endpoints and production network behavior have not been
  exercised by these local tests. See `progress.md` for exact validation receipts.

## Authorized manual delivery (#8)

`POST /api/v1/admin/intake/works/{id}/import` accepts unencoded raw bytes with the exact reviewed Content-Type and an Idempotency-Key. The CLI equivalent is `python -m app.ingest import WORK_ID --file /private/path/original.xml --mime application/xml --request-key DELIVERY_KEY`. Keep source files and delivery/license evidence outside public Git; authentication uses the existing secret environment channel.

Before import, register an `authorized_manual` manifest containing `manual_delivery`: lowercase `raw_sha256`, exact `byte_count`, `mime`, `method` (`publisher_delivery` or `author_original`), opaque private `evidence_ref` beginning `ev_`, delivery-evidence `evidence_sha256`, and timezone-aware `received_at`. An author-original delivery requires the original-work policy basis. Evidence describes how the exact edition was lawfully delivered; it is not a license grant. The independent rights approver must actually examine that evidence and separately authorize acquire/store_raw for this manifest revision. Upload access, subscription credentials and an uploader's claim do not establish permission. Mirrors, caches, user-account downloads and private workspace documents are not supported acquisition methods here. PRIVATE_UPLOADS cannot enter this global pipeline.

Permissions are checked before body reception and under a source-row lock before registration. Body reception has a 120-second deadline and the exact declared size limit (maximum 16 MB, also subject to the server upload cap). Hash, byte count, MIME and current revision must match. Shared access-page screening rejects login/CAPTCHA/error bodies; this heuristic is not proof of document completeness or authenticity. Parsing remains a separate bounded operation. New manual records without delivery evidence are rejected; old records remain readable but cannot import until a new reviewed edition is registered. Existing HTTP manifest hashes remain unchanged.

Receipts record actual `imported_at`, claimed `manual_delivery.received_at`, delivery evidence hashes, source dates/notices, actor, rights revision and manifest hash. HTTP status, resolved URL and retrieved_at are null: importing does not invent an HTTP observation. One work/hash yields one artifact, with separate attempt records for distinct keys. Retries after a storage/transaction crash reuse immutable bytes. A failed transaction can still leave an unreferenced private object; physical retention/deletion reconciliation remains required. Revocation/expiry blocks retries, and expiry after storage prevents registration. No import grants technical, applicability, model-input or indexing approval.

All current manual-import tests are synthetic original fixtures. No publisher delivery, real license review or full-source acquisition is claimed by this implementation.

## Offline discovery from an acquired index (#8)

`POST /api/v1/admin/intake/artifacts/{id}/discover` (CLI `discover-index ARTIFACT_ID`) derives a durable, unreviewed candidate snapshot from an already acquired, authorized HTML artifact. `GET /api/v1/admin/intake/discoveries/{id}` (CLI `discovery DISCOVERY_ID`) reads that snapshot with current store_text/display_full permission. Mutations require fresh admin authentication; all reads require admin access. Discovery requires store_raw/extract/store_text and never contacts a candidate URL.

Adapter `html-index-1` accepts exact hosts found in that family's versioned retrieval recipe; it does not assume subdomains, mirrors or redirects are interchangeable. It uses the acquired resolved URL (or the declared URL for manual delivery), rejects active/non-HTTPS/credential-bearing routes and HTML base redirects, and excludes links outside the declared family hosts. It preserves each eligible anchor's ordinal, original href, fragment and label. Repeated URLs become one candidate with multiple occurrences. Hidden/form links are excluded. Malformed, oversized or unsupported indexes fail rather than silently produce partial coverage. Subprocess limits match the intake parser's CPU/memory/wall-time protections.

Each immutable snapshot retains the raw hash, full family recipe and its hash, manifest hash, source dates/notices, adapter version and normalized JSON hash. Migration `0009_discovery` adds a table without creating sources, rights or approvals. Concurrent discovery of the same artifact/adapter/recipe creates one snapshot; a changed recipe creates a new version. Coverage reports count discovery snapshots separately from acquired works and parsed evidence.

These are **links in one exact stored index**, not a claim of a complete family inventory. The adapter does not infer work IDs, editions, publication/effective dates or authority from labels. Candidate registration, operation rights, acquisition, parsing, professional review and indexing remain distinct actions. Candidate text is untrusted data. Empty snapshots mean zero eligible links in the observed artifact, not that a publisher has zero publications. API/bulk, JavaScript-rendered indexes, family-specific selectors and edition normalization still require dedicated adapters and official-source validation. No live index acquisition or publisher permission was established by synthetic tests.

The dedicated Crossref JSON works-page adapter is documented in [CROSSREF_INTAKE.md](CROSSREF_INTAKE.md). It uses the same immutable acquisition/discovery records, with additional metadata-only screening before raw storage and shared provider concurrency control. Generic JSON and metadata-to-evidence staging remain unsupported.

## Multipart edition receipts

Use the [multipart inventory API](MULTIPART_EDITIONS.md) to declare required/optional component slots, exact work-manifest/hash bindings and a separate combined representation. Immutable revisions expose missing parts and unexpected deliveries; receipt completeness is explicitly separate from byte integrity, operation rights and human review. No automatic acquisition, parsing, indexing or source admission follows registration.
