# SEC Core 0.7.0 — standalone source addon

Prepared September 27, 2026. **This branch publishes native SEC Core code and source data, not the previously incomplete full application.** The complete downloadable v0.7 build additionally integrates the existing FastAPI service, TypeScript screen, MFA-protected review endpoint and Agent retrieval. Those integrations depend on the full application baseline.

## What is available here

- `backend/app/sec_core/`: validation, read-only search, conservative XML/HTML/PDF parsing, explicit HTTP acquisition and a staging adapter.
- `content/sec_core/catalog.json`: **34 acquisition targets** across S-X, S-K, Regulation G, SABs, FRM, CFIs and official forms. Targets overlap and vary in size; this is not a completeness percentage.
- `content/sec_core/excerpts.json`: **28 selected official-source excerpts from seven sources, 3,514 words**. Text was transcribed from official-source web retrieval; it is not original HTTP bytes or a complete mirror.
- `backend/tests/test_sec_core_unit.py`: **41 offline tests**, run locally. The complete integrated application passed **248 Python tests**, including four new app-integration tests and the previous 203 tests.
- `content/sec_core/work_queue.json`: ordered development backlog, not scheduled execution.

The seven excerpted sources are S-K Item 10(e), non-GAAP CFIs, SAB 99, SAB 108, the FRM introduction/revisions, selected FRM Topic 1 text, and Form 8-K General Instructions B.1–B.2. Original Form 8-K PDF page 3 was visually inspected during transcription. Source as-of, individual revision and acquisition timestamps are separate fields. Neither a website wrapper date nor an ingestion date is treated as a rule effective date.

**Zero complete source documents; zero original HTTP artifacts; zero independently reviewed or Agent-approved passages.** S-X, Regulation G and most forms/manual sections remain inventoried only. The original 63-item editorial content pack is unchanged and is not included by merely publishing this addon. No proprietary standards corpus is included.

## Run without the full application

Python 3.11+ with SQLite FTS5 is sufficient for validation and preview:

```bash
PYTHONPATH=backend python -m app.sec_core validate
PYTHONPATH=backend python -m app.sec_core inventory
PYTHONPATH=backend python -m app.sec_core preview 'equal prominence' --family cfi

python -m pip install 'pytest>=8.3,<10'
PYTHONPATH=backend python -m pytest backend/tests/test_sec_core_unit.py -q
```

Python treats `app` as a namespace package on this addon branch. No Gemini or cloud credentials are needed. Search is a read-only preview, not Agent admission or an accounting conclusion. Its small in-memory index is rebuilt on demand; it is not the production scalable retrieval system.

## Acquire a complete source explicitly

Direct network intake was blocked by DNS/network restrictions in the development environment. The acquisition path was tested with synthetic responses, **not a successful live SEC download**.

```bash
export SEC_USER_AGENT='YourApplication your-real-contact@your-domain.example'
PYTHONPATH=backend python -m app.sec_core acquire ecfr-part-210 \
  --as-of YYYY-MM-DD \
  --output ./data/sec-core \
  --rate-budget ./data/sec-budget.sqlite \
  --acknowledge-access-policy
```

Replace the edition date and contact example with actual values. The operator must review source access terms and choose a valid eCFR edition. The command never automatically substitutes today's date. Successful intake stores raw and normalized hashes, source URLs, parser version and pending reviews. It does not approve the source.

The gateway allows only specified government HTTPS hosts, validates redirects/DNS, identifies the application, and enforces byte/time limits. It stops on 401/403/429 and access-control pages. It does not bypass blocks through proxies, captcha solving or mirrors. Production still requires controlled egress and deployment tests.

The default rate budget reserves four requests per second. SEC guidance sets an aggregate ceiling of ten requests per second per user across machines. All ingestion processes and future Practice/Audit pipelines must share the operator's total budget. SQLite coordinates only one machine; Cloud Run refuses that configuration. A shared PostgreSQL budget requires a separately provisioned table and row:

```sql
CREATE TABLE sec_request_budget (name TEXT PRIMARY KEY, next_at DOUBLE PRECISION NOT NULL);
INSERT INTO sec_request_budget (name, next_at) VALUES ('shared', 0);
```

Use the same PostgreSQL URL for every worker and secure the credentials. The implementation serializes reservations with `FOR UPDATE` using database time. Production concurrency/jitter tests remain outstanding. No cloud resource or database table was created during this build.

## Parse and review carefully

CFR XML preserves section identifiers, structural blocks, source notes and linearized table rows. Local `source block N` labels are not invented legal subsections. HTML parsing requires a bounded main/article container; historical layouts may fail until a reviewed selector is added. CFI question suffixes are preserved. PDF extraction needs `pypdf`, uses physical-page locators and has no OCR or table-fidelity guarantee.

In the complete application, `stage --author EXISTING_SOURCE_ADMIN_ID` stages selected excerpts without approving them. `stage-snapshot --file SNAPSHOT.json --raw-directory RAW_DIRECTORY --author EXISTING_SOURCE_ADMIN_ID` verifies raw hashes, reparses the bytes and stages the result idempotently. These commands depend on the full app's models, database and configuration and cannot run from this addon alone.

Independent rights and technical reviews remain mandatory, tied to exact content hashes. Historical research requires separately reviewed applicability/public-availability metadata. The integrated app provides a recent-MFA-protected applicability-review endpoint. No actual professional review was performed; test reviewers are fixtures.

Reviewed staff text may be primary evidence of a staff position without becoming a Commission rule. The FRM remains non-authoritative. Paid Agent access never grants rights to otherwise restricted sources.

## Build queue

1. [SEC Core #1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1): active; full acquisition, independent review, scalable indexing and current/historical coverage remain open.
2. [SEC Practice #2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2): queued after Core. Define a pilot issuer/period universe; collect filings, complete UPLOAD/CORRESP threads, disclosure examples and XBRL/notes evidence. Company practice is not SEC approval.
3. [SEC Audit & Enforcement #3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3): queued after Core and the first Practice milestone. Add independence/OCA guidance, disclosure letters, AAER underlying complaints/orders/judgments and procedural history. Separate allegations, settlements and findings.

These are GitHub development issues, **not background tasks, scheduled crawlers or promised future delivery**. The generated SEC progress report tracks inventory, selected text and review separately. Code publication is not website deployment.

## Validation and remaining work

The full local application passed 248 Python tests, TypeScript typecheck/demo build and 16 mocked MFA-controller tests. The 41 standalone SEC tests are included here. No live Gemini, Identity Platform, PostgreSQL shared throttling or Google Cloud deployment was tested. The existing full-app Agent search still has a 2,000-source scan bound that must be replaced before a large corpus launch. Complete-source acquisition, expert accounting review, source-history checks and adjudicated benchmarks remain release gates.

## Source and rights references

Checked September 27, 2026. Catalog links do not prove complete acquisition or permission for embedded third-party material.

- SEC access guidance: https://www.sec.gov/about/developer-resources
- SEC reuse policy: https://www.sec.gov/about/webmaster-frequently-asked-questions
- eCFR API: https://www.ecfr.gov/developers/documentation/api/v1
- FRM authority/revisions: https://www.sec.gov/about/divisions-offices/division-corporation-finance/financial-reporting-manual
- Non-GAAP CFIs: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures
- The exact official URL and locator for each excerpt are in `excerpts.json`.

New code is MIT-licensed. Identified government-source excerpts are not newly relicensed as CC BY/MIT original editorial work. No ownership of underlying government text or rights to agency marks are claimed. Screen embedded third-party material before reuse. No regulator or standard-setter endorsement is represented.
