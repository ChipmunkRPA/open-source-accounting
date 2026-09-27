# Progress update contract

Merge this structure into the existing `progress.md`; do not discard history or manufacture new test results. Machine-readable counts should be generated from manifests and actual review records.

## Snapshot
Date; app/content/schema versions; git commit/branch; environment; referenced task issues.

## Current task
Issue/ID; precise scope; changes; observed outcome; remaining blocker; next resumable action.

## Source/content coverage
| Family/topic | Declared universe/unit | Inventoried | Original artifacts acquired | Parsed/locator checked | Rights cleared | Human technically reviewed | Applicability reviewed | Indexed | Evaluated | Stale/blocked |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|

Use null/unknown with a reason instead of inventing a universe. Report overlapping whole-document and passage counts separately. An excerpt is not a complete document; metadata/links are not acquisition; draft publication is not Agent approval. Do not write an aggregate 'GAAP 80% complete' metric.

## Product capability
| Workflow/module | Implemented scope | Mock/fixture checks | Live checks | Human review | Production enabled | Limitations |
|---|---|---|---|---|---|---|

## Validation log
Exact command; timestamp; tested commit/config; exit code; observed pass/failure counts; output artifact/hash; whether mock/offline/live/manual. Historical counts retain their original dates and scope.

## Blockers and decisions
Owner, required action, affected task/operation, safe fallback, unblocked work, next resume instruction.

## Completion evidence
PR, actual commit, current CI state, artifacts, source/model versions, review records. Close issues only for fulfilled acceptance criteria. Move genuine unmet conditions to explicit issues, not a footnote hidden under 'done'.
