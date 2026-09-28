# Multipart edition inventory — issue #8

An edition can contain required chapters, optional indexes and a separate combined download. An immutable inventory now binds each declared component to an exact intake work manifest and expected raw hash. The authenticated admin API records revisions and reports matching acquisition receipts without treating receipts as content approval.

## Operator sequence

1. Read `GET /api/v1/admin/intake/editions?family_id=…&collection_key=…&edition=…`. This paginated metadata list returns at most 100 summaries, not large manifests. Follow `next_offset` until null. `collection_key` identifies the publication; `edition` identifies the publisher edition. The server's integer `revision` is an internal inventory revision, not a new publisher edition.
2. Register parts through the existing intake-work API as appropriate. Metadata planning does not need acquisition permission. Use returned work IDs and manifest hashes. Work registration still grants no rights.
3. With fresh MFA, `POST /api/v1/admin/intake/editions` supplies the fields below. Use `expected_revision: 0` for the first inventory and the current number for subsequent revisions. An identical retry returns the same latest revision; a competing stale request returns 409. Older revisions remain readable and cannot claim current required-receipt completeness.
4. Acquire/parse/review each part through its separately authorized intake steps. Edition registration does not call those steps or perform network/storage reads. Unknown parts can remain unbound; unknown raw hashes can remain null. Neither counts as a matching receipt.
5. Read `GET /api/v1/admin/intake/editions/{id}`. Resolve missing parts, changed manifests, mismatched receipts, integrity holds or unexpected new deliveries. Record explicit selection changes in a new inventory revision. No update/delete API silently changes a frozen inventory.

Example metadata-only request, with intentionally unbound components:

```json
{
  "family_id": "OMB_TREASURY",
  "collection_key": "compliance-supplement",
  "edition": "2025",
  "expected_revision": 0,
  "coverage_unit": "Declared pilot: Part 1 and Part 2 only; not the full supplement",
  "inventory_note": "Operator must reconcile remaining parts and program files against the publisher index before proposing full edition coverage.",
  "parts": [
    {"key": "part-1", "label": "Background, purpose and applicability", "required": true},
    {"key": "part-2", "label": "Matrix of compliance requirements", "required": true}
  ],
  "combined": {"key": "combined", "label": "Separate combined publication", "required": true}
}
```

This example is not an authoritative full-publication manifest. To bind a part, add its `intake_work_id`, exact `manifest_sha256`, and optionally `expected_raw_sha256`. A hash may be declared before delivery; it is only counted when a matching receipt actually exists. Keys and bound work IDs must be distinct. All components must belong to the declared family. PRIVATE_UPLOADS remains in the workspace pipeline. Component editions are exposed in the report; the inventory author must ensure their relationship to the parent edition is appropriate. The system does not infer historical applicability from a matching year label.

## How the report counts

- `required_parts` and `optional_parts` count declared component slots. The `combined_receipt` is a separate representation and never fills a missing component or adds to either denominator.
- `required_matching_receipts` and `optional_matching_receipts` require the selected raw hash and matching work-manifest provenance in the receipt. An unbound slot, undeclared hash or missing artifact stays incomplete.
- `required_receipts_complete` means all declared required slots have matching receipts in the current inventory revision, with no known integrity hold or unreconciled delivery on those works. It does **not** assert publisher-inventory completeness, current object bytes, available permissions, parser accuracy, professional review or Agent eligibility. Disabled/expired rights do not erase a historical receipt; current rights are reported separately and still govern all operations.
- The server freezes already known raw hashes under acquisition's source-row locks. A subsequently observed hash other than the expected one yields `unreconciled_delivery`. A new revision explicitly reconciles the inventory; no automatic “latest artifact” substitution occurs. A same-URL new delivery cannot silently replace the selected hash.
- Extraction hashes/parser versions and current parser-decision ledger status are separate metadata. Stale, expired or revoked decisions do not become approval. Technical/applicability/index status is explicitly not assessed by this report. No bodies, raw base64, private reviewer notes or source grants are included.

Reads are non-atomic metadata observations across work records, not a live object-storage verification or an admission gate. Use the [integrity reconciliation client](INTEGRITY_RECONCILIATION.md) for actual bytes and the existing independent review workflows for approval. Acquisition under a registered work cannot prove a publisher sent every page; actual completeness needs the independently reviewed inventory plus original-byte and parser checks. This feature does not supply that human judgment.

Bounds: 250 component slots plus one optional combined representation; 100 artifacts per bound work, otherwise an explicit 409 rather than truncating acquisition coverage; at most 10 displayed extractions per selected artifact, with `extractions_truncated` if more exist. List results omit manifests to avoid returning up to 100 large inventories. No fetch/parser limits were raised, no source was acquired, and no route block was bypassed.

Migration `0014_intake_editions` adds one table, preserving prior data. Apply the normal migration before calling these endpoints in an existing installation. Scope still outstanding includes independently reviewed publisher inventories, full acquisition/parsing/professional-review/index reconciliation, and large-corpus performance measurements. Declaring a small pilot does not complete the all-content goal.

## Operator screen

Open **Multipart inventories** from the signed-in source administrator header (`/editions`). The server enforces scoped administration; the navigation link is not authorization. Choose the family, collection, publisher edition, declared scope and limitations. Add required/optional components and, if useful, a separate combined representation. Load more registered works explicitly when the first page is insufficient. Select the exact work and acquired artifact, or declare a known future SHA-256. Unbound components and unknown hashes remain incomplete.

Saving creates an immutable inventory revision. Saved collection identity cannot be edited; start a new inventory for a different collection or publisher edition. Inspect history to see receipt gaps, parser ledger status and current operation permissions. Only the current revision offers **Prepare next revision**; historical reports link to the current revision. A stale save returns a conflict without overwriting another operator's revision. Work lookup failures block saving; draft navigation asks before discarding changes. Rights expiry, source holds and professional reviews continue to be enforced by the existing server workflows.

Browser validation uses disposable synthetic records only; see `reports/intake/EDITIONS_UI.md` and its screenshot. No real publication completeness or review is implied.

## Compare immutable revisions

`GET /api/v1/admin/intake/editions/{id}/comparison` requires scoped administration and compares the selected inventory against its stored immediate predecessor. The screen displays it when inspecting an inventory. Initial inventories compare against an empty declaration, not a nonexistent acquisition record. Both revision IDs and manifest hashes identify the comparison. Missing predecessors, wrong family/collection/publisher edition, skipped/self-linked revisions and altered manifests return an explicit 409.

The response includes added/removed components, per-field before/after values for changed components, ordering, declared required/optional counts, scope/limitation changes and separate combined-representation changes. Frozen known-delivery hashes are included, so acknowledging a newly observed artifact remains visible even when the selected hash stays unchanged. Renaming a key appears as removal plus addition; no unsupported equivalence is inferred. Required components removed or made optional are flagged explicitly. An improved receipt ratio after reducing scope does not mean more content was acquired.

Comparison reads only two immutable inventory records. It does not read source text, storage objects or network endpoints, recompute historical receipt/review states, grant permission or establish publisher completeness. Later deliveries, revocations, reviews and newer inventory revisions do not rewrite the comparison. Use the separate current metadata report and integrity/review workflows for those questions. This is a declaration comparison, not a text redline or professional approval.
