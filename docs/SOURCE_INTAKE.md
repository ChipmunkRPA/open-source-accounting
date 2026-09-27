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
- `authorized_manual` is reserved metadata, with acquisition disabled. Private records
  remain reference-only here; private documents use the workspace upload pipeline.
- Family API/bulk discovery adapters, manual import, persisted legal decisions,
  applicability/entity-adoption review, review/index commands, cumulative quotation
  limits, trusted model/export scope propagation, deletion and reconciliation remain.
- Route/audience scope is supplied by server intake. Other scoped grants fail closed
  until the relevant trusted context is implemented. An ingestion-only grant cannot
  automatically authorize public reading or model access.
- Registration does not audit the legality or accuracy of operator declarations.
  Source approvals and technical/accounting judgments still require real people.
- GCS, live identity, model endpoints and production network behavior have not been
  exercised by these local tests. See `progress.md` for exact validation receipts.
