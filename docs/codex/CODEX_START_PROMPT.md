# Codex execution prompt — Open Source Accounting

Take over `ChipmunkRPA/open-source-accounting` and work through the live master issue #5 and its dependency-ordered queue. This is an implementation/content-building handoff, not a request for another high-level design. Read the supplied handoff directory before editing: `AGENTS.md`, `BASELINE_AUDIT.md`, `tasks/ISSUE_INDEX.md`, `tasks/queue.json`, `content/SOURCE_RETRIEVAL_PLAYBOOK.md`, `content/EXISTING_CONTENT_RETRIEVAL_MAP.md`, `content/topic_coverage.json`, and `tasks/OPERATOR_DECISIONS.md`. Re-read the current GitHub issue bodies and repository instructions; preserve newer maintainer changes.

## Begin with issue #6

The complete app is inside `baseline/open_source_accounting_v0_7_sec_core.zip`, SHA-256 `3d4f78aa6bfab4323af14ce58cf1b8f77cba2967d984bdbdf378fd9a1ff5529f`. Run `python scripts/verify_handoff.py` from this handoff directory first. Do not assume the repository has the whole app: at handoff, main contained bootstrap files, and draft PR #4 contained only the SEC addon. Inspect live main/branches/PRs, extract the verified ZIP outside the checkout, compare it with existing work, and prepare a normal source integration PR. No force-push, history replacement, or blind execution of old encoded materialization workflows. Reconcile README.md/readme.md for case-insensitive filesystems. Install dependencies cleanly, build the real production assets, run migrations/tests, and record actual failures rather than reusing historical success counts.

## Preserve these decisions

- General AI chat and the public learning/source-reading library are free. Hosted Agent work costs **US$89.99/year**. Do not add a monthly plan, silent overages or an unlimited promise. The proposed 30-task/month allowance and grace policy need maintainer approval.
- Use Google Cloud. The requested generation model is **Gemini 3.8 Flash (`gemini-3.8-flash`)**; verify actual Cloud endpoint, SDK/settings, location, pricing and availability. Do not silently replace the model, provider or region. The mock provider is for explicit local tests only.
- Every real signed-in user, including Free, requires verified email and Google Authenticator-compatible **TOTP OR SMS MFA**. Public educational pages stay anonymous. Enforce verified identity/MFA and recent authentication on the server; do not weaken this to make tests pass.
- Keep source permissions, user entitlements, subscriptions, technical review and date applicability separate. A paid account, uploaded document, temporary cache, public web page or agent workflow does not itself license proprietary text.

## Build all content families, not just SEC

Use the source-family recipes and issues for FASB/GASB, PCAOB/AICPA, IFRS/IASB/ISSB, IAASB/IESBA/IPSASB, GAO/FASAB/OMB/Treasury, federal/state law and courts, COSO/IIA/ISACA/NIST, accounting-firm/commercial publications, open textbooks/papers, industry regulators, local frameworks and our own material. The three SEC issues remain part of this wider plan. Audit and map every existing original item; broaden topic depth with real authority, exceptions, original cases, templates and evaluation questions.

For each source, discover the current official documents and check the actual acquisition route and operation rights. Use permitted APIs/feeds/downloads with identifiable bounded requests; preserve original artifacts, hashes, exact locators, versions, issued/available/effective dates and notices. Do not bypass paywalls, blocked sites, publisher AI restrictions or access terms through mirrors, search caches or user credentials. FASB/AICPA/IFRS and other restricted texts remain reference-only until a specific authorized basis exists; PCAOB acquisition restrictions are separate from public-material reuse. Prepare license/legal-review requests but do not purchase or submit agreements yourself. Original analysis is welcome; disguised copying is not.

## Execute the queue

Choose the highest-priority unblocked task and complete a bounded, tested slice in an issue-linked branch/PR. Use parallel work only for independent tasks with clear ownership and no shared-file conflicts. Continue useful unblocked code, metadata, original draft or test work when one family requires a license, credential or human review. Record the exact blocker and next step; do not stop the whole project or fabricate approval.

Finish shared ingestion/parsing/retrieval/review infrastructure, the five core Agent workflows and the queued accounting/auditing/disclosure/monitoring extensions, MFA, billing, workspaces/memos/exports, UI/accessibility, security/privacy, Cloud infrastructure, evaluations, operations and documentation. Implement task-specific behavior, not just additional prompt labels. Keep experimental/unsupported capabilities visibly gated.

Every PR updates `progress.md` with precise coverage units and actual inventoried/acquired/parsed/rights-cleared/professionally-reviewed/applicability-reviewed/indexed/evaluated status; actual test commands and results; source/model versions; failures; operator blockers; and the next resumable action. Link the issue and resulting commit. Unit tests, a second LLM pass, an educational Q&A set and a generated reviewer name are not professional approval. Existing drafts/excerpts remain unreviewed until an actual qualified reviewer approves the exact revision.

Do not deploy production, create paid resources, activate live billing, send real SMS/notifications, purchase licenses, submit filings or post journal entries without explicit operator approval. Credentials must use the approved environment/secrets mechanism, never public GitHub issues. At the end of each session, summarize files/commits/tests, unresolved gates and the next queue task. Do not imply unattended continuation after the session ends.
