# Content retrieval playbook — all source families

This handbook covers every content family agreed for Open Source Accounting, plus separately gated specialist extensions. It is not limited to SEC. The machine-readable counterpart is `source_families.json`; live issue checklists remain the execution source of truth.

## Non-negotiable distinction

**A URL is inventory, a saved original artifact is acquisition, parsed text is extraction, and approved evidence requires actual rights, technical and applicability review.** Do not count a page link or a model-generated summary as a retrieved authoritative document. Do not claim exhaustive coverage without a declared universe. Model output, deterministic calculations and original explanatory articles are separate artifacts.

The free chat plus paid public Agent service is a commercial-use consideration. An agent, a temporary cache or limited quotation does not automatically establish fair use. Rights counsel may review a particular bounded use; Codex cannot grant itself approval. Specific licenses may permit processing without public redistribution. Source content must never be automatically included under the software's MIT license or the original-content CC license.

## Repeatable acquisition protocol

1. **Inventory:** declare source/work IDs, publisher, editions, frameworks, languages, jurisdictions, date range and unit of coverage. Record discovery roots separately from final document URLs. Identify duplicates and overlapping units.
2. **Authorize route and operation:** check actual publisher policies and rights holder for this edition. Record fetch/store/parse/embed/model/display/quote/export/Git redistribution/train permissions separately. Unknown means not enabled. Draft requests for human submission; do not buy or agree to licenses.
3. **Acquire:** documented APIs/bulk feeds first, otherwise permitted manual or explicit downloads. Identify the application/contact, share rate limits across workers, constrain destinations, redirects, bytes, file types and requests. A 403, CAPTCHA, paywall or incompatible terms is a blocker, not an invitation to use a mirror.
4. **Receipt:** retain requested/final URL, method/status, headers when available, acquisition time, raw hash, rights policy/version, operator/run, source title and original artifact location. A web transcription can remain a marked excerpt but is not a full HTTP snapshot.
5. **Parse:** preserve exact rule/standard/question/section, tables, definitions, footnotes and source structure. Distinguish printed pages from physical pages and normalized block labels from legal identifiers. Compare extraction to original renderings; use OCR only when necessary and reviewed.
6. **Version:** retain issued/publicly available/effective/retrieved dates independently, plus entity/adoption conditions and amendment/supersession relationships. No silent replacement of an imported version.
7. **Review:** separate acquisition/rights review, parsing/locator verification, professional content review and applicability assessment. Approval is tied to hashes and real authorized reviewers. Unreviewed public drafts must not auto-enter Agent evidence.
8. **Index and release:** filter rights, workspace, user/seat, framework and dates before model access; preserve those checks at answer and export. A reference-only source stays reference-only. Check cumulative disclosure/reconstruction across queries and exports.
9. **Evaluate and maintain:** test citations, contradiction, unsupported cases and source changes; report true scope and review counts. Maintenance schedules need explicit operator/provider authorization and costs.

## Minimum source record

```json
{
  "family_id": "FASB",
  "work_id": "operator-defined-stable-id",
  "version_id": "edition-or-content-hash",
  "canonical_url": "verified official source URL",
  "authority_class": "standard_or_rule_or_staff_or_practice_or_commentary",
  "framework": "explicit framework",
  "jurisdiction": "explicit jurisdiction",
  "language": "en",
  "issued_at": null,
  "publicly_available_at": null,
  "effective_conditions": [],
  "retrieved_at": null,
  "raw_sha256": null,
  "parser_version": null,
  "source_body_status": "reference_only",
  "policy_id": "review-required",
  "rights_review": "pending",
  "technical_review": "pending",
  "agent_eligible": false
}
```

Unknown dates remain null with a reason. Examples above are schema concepts, not an authorization or a claim that text exists.

## Approved source acquisition versus unrestricted crawling

PCAOB illustrates why acquisition and reuse are separate: conditional Public Materials reuse does not make automated website extraction authorized. FASB/AICPA/IFRS and commercial research access is not blanket AI permission. IIA software permissions do not generally open public-AI use; request AI-specific authorization. OpenStax/OER must be inspected per book and edition. A DOI record does not license an abstract/full text. A company filing is not federal-authored merely because EDGAR publishes it. Government publications can contain separately protected components.

## Families and executable next steps


### SEC_RULES — Regulation S-X, S-K and Regulation G

Issues: [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1). Default: **public_work_candidate**.

**Coverage unit:** part + dated section inventory; do not double count sections and whole parts.

**Official/discovery seeds**
- `https://www.ecfr.gov/developers/documentation/api/v1`
- `https://www.ecfr.gov/current/title-17/chapter-II/part-210`
- `https://www.ecfr.gov/current/title-17/chapter-II/part-229`
- `https://www.ecfr.gov/current/title-17/chapter-II/part-244`

**Retrieval procedure**
1. Resolve a documented as-of date and use the eCFR versioner full XML endpoint for Title 17 parts 210/229/244; inspect current API docs before using the existing template.
2. Persist original XML and HTTP receipt; enumerate actual sections and nested provisions, definitions, exceptions, tables and appendices.
3. Link amended regulations and Federal Register records; distinguish current-effective from historical-known-at-date research.

**Required locators:** CFR title/part/section/subparagraph; as-of version; table/footnote.

**Boundary:** Official reuse and third-party incorporations still require screening; regulations are not a source license for private standards.

**First deliverable:** Acquire and parse one complete declared part with exact locator and version tests, then expand.

### SEC_SAB — Staff Accounting Bulletins and codification

Issues: [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1). Default: **public_work_candidate**.

**Coverage unit:** bulletin and codified topic/version, linked not double counted.

**Official/discovery seeds**
- `https://www.sec.gov/rules-regulations/staff-guidance/selected-staff-accounting-bulletins/sec-staff-accounting-bulletin-codification-staff-accounting-bulletins`
- `https://www.sec.gov/rules-regulations/staff-guidance/staff-accounting-bulletins`

**Retrieval procedure**
1. Discover every bulletin/topic from the official index; resolve current original publication and codified destination.
2. Download through the shared identifiable SEC gateway; retain facts/question/interpretive response/notes together.
3. Record issuance, amendment/rescission and applicability; replace the selected SAB99/108/14 references with reviewed actual source units.

**Required locators:** SAB number; Topic/subtopic; question/response; issued/rescinded relationship.

**Boundary:** Staff interpretation is not a Commission rule; do not silently treat rescinded text as current.

**First deliverable:** Inventory all codified topics and retrieve scoped complete documents; test a rescission relationship.

### SEC_FRM — Financial Reporting Manual

Issues: [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1). Default: **public_work_candidate**.

**Coverage unit:** dated FRM section with explicit topic coverage.

**Official/discovery seeds**
- `https://www.sec.gov/about/divisions-offices/division-corporation-finance/financial-reporting-manual`

**Retrieval procedure**
1. Follow current FRM topic and update links from the official landing page; build complete topic/section enumeration.
2. Acquire original HTML/downloads, retaining section labels, tables, exceptions, links and revision notes.
3. Separate revisions, aliases and former section identifiers; maintain non-authoritative staff label in retrieval/UI/export.

**Required locators:** topic/section; revision date; table/note.

**Boundary:** A landing page link is not the manual; current HTML does not alone establish historical availability.

**First deliverable:** Replace introduction/Topic1-only excerpt seed with a declared reviewed section collection.

### SEC_CFI — Corporation Finance Interpretations / historical C&DIs

Issues: [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1). Default: **public_work_candidate**.

**Coverage unit:** interpretation collection + numbered Q&A version.

**Official/discovery seeds**
- `https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations`

**Retrieval procedure**
1. Enumerate relevant S-X/S-K/non-GAAP/form/reporting interpretation categories through current official navigation.
2. Acquire each Q&A with question, complete answer, notes and last-change date; preserve historical C&DI aliases.
3. Map renumbered/withdrawn questions rather than assuming permanent numbering.

**Required locators:** collection; question number; revision date.

**Boundary:** Current names/identifiers must be rechecked; staff interpretations are distinct from underlying rules.

**First deliverable:** Acquire full selected non-GAAP collection and exact Q&A citations, then cover other categories.

### SEC_FORMS — Official filing forms and instructions

Issues: [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1). Default: **public_work_candidate**.

**Coverage unit:** form edition and instruction/item.

**Official/discovery seeds**
- `https://www.sec.gov/submit-filings/forms-index`

**Retrieval procedure**
1. Resolve the actual official form download from the form index, not guessed PDF filenames.
2. Prioritize 10-K/10-Q/8-K/S-1/S-3/S-4/20-F/6-K/F-1 and relevant amendment instructions.
3. Retain edition/date, instructions, items, appendices and page labels; compare tables to rendered PDFs before review.

**Required locators:** form; general instruction/item; printed and physical page; edition.

**Boundary:** A blank form does not count as issuer practice or full text of an incorporated private standard.

**First deliverable:** Acquire a complete form and general-instruction/item parser fixture; enumerate remaining editions.

### SEC_FILINGS — EDGAR issuer filings and disclosure examples

Issues: [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2). Default: **public_filing_screening_required**.

**Coverage unit:** CIK/accession/document + declared issuers/forms/periods.

**Official/discovery seeds**
- `https://www.sec.gov/about/developer-resources`
- `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`

**Retrieval procedure**
1. Declare a pilot issuer/form/period universe and resolve CIKs. Use documented submissions/older index files to enumerate accessions.
2. Resolve each official primary document and relevant exhibits from archive metadata; acquire actual HTML/PDF with amendment links.
3. Extract policy/footnote/MD&A/ICFR/earnings-release examples with context, tables and public availability.

**Required locators:** CIK/accession; form/document; item/note/table/footnote; report period.

**Boundary:** Issuer-authored filings are not federal-authored works merely by submission; screen embedded third-party material and label practice, not authority.

**First deliverable:** A source-screened pilot in revenue/non-GAAP/acquisition/ICFR with actual disclosure evidence.

### SEC_CORRESPONDENCE — SEC comment letters and issuer responses

Issues: [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2). Default: **public_filing_screening_required**.

**Coverage unit:** numbered comment and linked correspondence thread.

**Official/discovery seeds**
- `https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence`

**Retrieval procedure**
1. Discover UPLOAD and CORRESP accessions plus responses included in other filings using official EDGAR metadata.
2. Link original filing, numbered comment, issuer response, follow-up and revised disclosure; store uncertainty/missing links explicitly.
3. Preserve letter, filing, public-release and ingestion dates independently; curate a defined issue/company pilot.

**Required locators:** accession; comment number; thread/event; page/paragraph.

**Boundary:** Thread closure is not SEC approval; correspondence availability is not instantaneous.

**First deliverable:** Complete and intentionally incomplete thread fixtures with cited gap indicators.

### SEC_XBRL — XBRL Company Facts and financial-statement/notes datasets

Issues: [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2). Default: **public_dataset_candidate**.

**Coverage unit:** accession/concept/context/unit/period and dataset vintage.

**Official/discovery seeds**
- `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- `https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets`
- `https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets`

**Retrieval procedure**
1. Use documented Company Facts endpoints and official bulk dataset download links; record dataset release/vintage.
2. Preserve entity, contexts/dimensions, currency/units, scale/sign/decimals, period, taxonomy, custom tags and amendments.
3. Reconcile selected extracted records to original filing narratives/tables; do not assume Company Facts includes every custom/dimensional disclosure.

**Required locators:** CIK/accession; concept/context/unit; period; note/table.

**Boundary:** Structured facts are not a complete narrative corpus; keep original filings and dataset limitations.

**First deliverable:** A reproducible pilot with fact-to-filing reconciliation and notes context.

### SEC_AUDIT_ENFORCEMENT — OCA, disclosures guidance, AAER and reporting releases

Issues: [#3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3). Default: **public_work_candidate**.

**Coverage unit:** guidance Q&A/release and case document/event.

**Official/discovery seeds**
- `https://www.sec.gov/about/divisions-offices/office-chief-accountant`
- `https://www.sec.gov/rules-regulations/staff-guidance/office-chief-accountant-staff-letters`
- `https://www.sec.gov/rules-regulations/staff-guidance/disclosure-guidance`
- `https://www.sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases`
- `https://www.ecfr.gov/current/title-17/chapter-II/part-211`

**Retrieval procedure**
1. Navigate OCA independence/current staff publications and link underlying rules; enumerate a defined guidance period.
2. Follow AAER and release records to original complaints/orders/judgments and later dispositions; index document-level procedural state.
3. Acquire original allowed artifacts, parse exact locators, and require case-history and technical review.

**Required locators:** release/docket; Q&A/paragraph/page; event/date; disposition.

**Boundary:** AAER list is not exhaustive; distinguish allegations, settlements, adjudicated findings and speeches/staff positions.

**First deliverable:** Source-screened independence pilot and a small complete enforcement-history collection.

### FASB — FASB ASC, ASUs, Concepts and implementation material

Issues: [#9](https://github.com/ChipmunkRPA/open-source-accounting/issues/9). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** ASC reference/version and ASU/amendment record.

**Official/discovery seeds**
- `https://asc.fasb.org/`
- `https://www.fasb.org/`
- `https://www.accountingfoundation.org/`

**Retrieval procedure**
1. Navigate official current pages for references, ASUs, concepts, agendas and taxonomies; detailed dynamic pages need verification.
2. Build independently maintained IDs/links/adoption metadata; draft FAF service-license request covering public paid AI use.
3. After specific clearance only, use approved feed/manual import with paragraph/exception/table/version preservation; keep licensed raw text outside public Git.
4. Build original explanations and examples from legitimately examined evidence while blocked; never reconstruct ASC through publisher mirrors.

**Required locators:** Topic/Subtopic/Section/Paragraph; ASU number; effective entity/transition.

**Boundary:** Free reading does not license processing; ASU announcements/project summaries do not verify every current ASC criterion.

**First deliverable:** Reference map for five core topics plus explicit rights request and disabled licensed adapter.

### GASB — GASB standards and implementation Q&As

Issues: [#10](https://github.com/ChipmunkRPA/open-source-accounting/issues/10). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** statement/codification/Q&A edition.

**Official/discovery seeds**
- `https://www.gasb.org/`
- `https://www.accountingfoundation.org/`

**Retrieval procedure**
1. Use official navigation to inventory statements, codification, implementation guides and transitions.
2. Obtain actual FAF/GASB permissions for intended text operations; use metadata and original teaching material before clearance.
3. Upon clearance preserve required/application material, paragraph IDs and entity-period applicability; government annual reports are a separately reviewed practice corpus.

**Required locators:** statement/paragraph; implementation Q&A; edition/effective date.

**Boundary:** State/local accounting subject does not make GASB a federal government work.

**First deliverable:** Governmental-accounting reference directory and scoped licensed-import fixtures.

### PCAOB — PCAOB auditing, quality, ethics, inspections and enforcement

Issues: [#11](https://github.com/ChipmunkRPA/open-source-accounting/issues/11). Default: **authorized_route_required**.

**Coverage unit:** standard/paragraph/version or public inspection/case document.

**Official/discovery seeds**
- `https://pcaobus.org/oversight/standards`
- `https://pcaobus.org/oversight/inspections`
- `https://pcaobus.org/oversight/enforcement`
- `https://pcaobus.org/privacypolicy`

**Retrieval procedure**
1. Inventory actual current/archived AS, attestation, ethics/independence and quality standards via official indexes.
2. Use documented manual downloads or explicitly authorized feeds; do not enable a website crawler contrary to extraction terms.
3. Review Public Materials conditions, AI transmission and normalization/display obligations; preserve original notices and excluded third-party components.
4. Parse standard IDs, SEC approval/effective periods, public inspection findings and case dispositions.

**Required locators:** AS/QC/paragraph; edition/approval/effective date; report period; case/release.

**Boundary:** Conditional publication reuse is separate from automated acquisition and model-training permission; do not seek nonpublic inspection material.

**First deliverable:** Approved-route standard import and exact-version fixtures with reference-only fallback.

### AICPA — AU-C, AT-C, AR-C, ethics, quality and guides

Issues: [#12](https://github.com/ChipmunkRPA/open-source-accounting/issues/12). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** codified section/paragraph and guide edition.

**Official/discovery seeds**
- `https://www.aicpa-cima.com/`
- `https://www.aicpa-cima.com/resources/article/terms-of-service`

**Retrieval procedure**
1. Navigate official standards/ASB resources for SAS/AU-C, SSAE/AT-C, SSARS/AR-C, ethics, quality management and guides.
2. Draft use-specific permission request; membership/personal access is not public-service AI authorization.
3. On clearance import approved feed/files with required/application/example distinctions, engagement regime, dates and exact locators.

**Required locators:** AU-C/AT-C/AR-C/paragraph; edition; engagement type.

**Boundary:** Do not scrape member products or reuse credentials; user SOC reports are private inputs.

**First deliverable:** Complete scoped reference inventory and original nonissuer decision aids, licensed fixture adapter only.

### IFRS — IASB/ISSB, IFRIC/SIC, SMEs and adoption

Issues: [#13](https://github.com/ChipmunkRPA/open-source-accounting/issues/13). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** standard/paragraph/language/edition/adoption.

**Official/discovery seeds**
- `https://www.ifrs.org/issued-standards/`
- `https://www.ifrs.org/legal/intellectual-property/`
- `https://www.ifrs.org/products-and-services/ifrs-accounting-licensing/`

**Retrieval procedure**
1. Discover official issued standards, agenda decisions, examples/basis, SMEs, ISSB and taxonomy publications.
2. Prepare the licensing questionnaire/request with the actual free/paid service and AI processing scope; do not submit without authorization.
3. After clearance import appropriate editions, languages, effective/adoption rules, exceptions and locators; taxonomy license separate.
4. Author comparison matrices from independently verified criteria rather than copied third-party tables.

**Required locators:** IAS/IFRS/IFRIC/SIC/paragraph; required vs issued edition; jurisdiction/language.

**Boundary:** ISSB, SMEs and local endorsed IFRS are distinct scopes; mere download availability is not a public AI license.

**First deliverable:** Core reference map plus declared comparison scope and rights/adoption blockers.

### IAASB — IAASB assurance and quality standards

Issues: [#14](https://github.com/ChipmunkRPA/open-source-accounting/issues/14). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** standard/paragraph/edition/language.

**Official/discovery seeds**
- `https://www.iaasb.org/`
- `https://www.ifac.org/ifac-intellectual-property`

**Retrieval procedure**
1. From the official root discover the current handbook and ISA/ISQM/ISAE/ISRE/ISRS and relevant sustainability assurance; verify title, language and edition. Generic publication pages may resolve to unrelated translations.
2. Verify the actual rights owner for the edition; prepare an explicit public paid AI/RAG permission request rather than assuming IFAC grants everything.
3. Only approved feeds/files may enter text processing; preserve paragraph/application distinctions, notices, local adoption and language versions.

**Required locators:** standard/paragraph; edition/language; effective/local adoption.

**Boundary:** Free handbook access is not a blanket open license; do not mix frameworks.

**First deliverable:** Board-specific reference registry, license packet and synthetic parser/connector tests.

### IESBA — IESBA ethics and independence

Issues: [#14](https://github.com/ChipmunkRPA/open-source-accounting/issues/14). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** standard/paragraph/edition/language.

**Official/discovery seeds**
- `https://www.ethicsboard.org/`
- `https://www.ifac.org/ifac-intellectual-property`

**Retrieval procedure**
1. From the official root discover the current handbook and Code/requirements/application and independence provisions; verify title, language and edition. Generic publication pages may resolve to unrelated translations.
2. Verify the actual rights owner for the edition; prepare an explicit public paid AI/RAG permission request rather than assuming IFAC grants everything.
3. Only approved feeds/files may enter text processing; preserve paragraph/application distinctions, notices, local adoption and language versions.

**Required locators:** standard/paragraph; edition/language; effective/local adoption.

**Boundary:** Free handbook access is not a blanket open license; do not mix frameworks.

**First deliverable:** Board-specific reference registry, license packet and synthetic parser/connector tests.

### IPSASB — IPSASB public-sector standards

Issues: [#14](https://github.com/ChipmunkRPA/open-source-accounting/issues/14). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** standard/paragraph/edition/language.

**Official/discovery seeds**
- `https://www.ipsasb.org/`
- `https://www.ifac.org/ifac-intellectual-property`

**Retrieval procedure**
1. From the official root discover the current handbook and IPSAS and current related public-sector implementation material; verify title, language and edition. Generic publication pages may resolve to unrelated translations.
2. Verify the actual rights owner for the edition; prepare an explicit public paid AI/RAG permission request rather than assuming IFAC grants everything.
3. Only approved feeds/files may enter text processing; preserve paragraph/application distinctions, notices, local adoption and language versions.

**Required locators:** standard/paragraph; edition/language; effective/local adoption.

**Boundary:** Free handbook access is not a blanket open license; do not mix frameworks.

**First deliverable:** Board-specific reference registry, license packet and synthetic parser/connector tests.

### GAO — GAO Yellow Book, Green Book and related guidance

Issues: [#15](https://github.com/ChipmunkRPA/open-source-accounting/issues/15). Default: **public_work_candidate**.

**Coverage unit:** publication edition/chapter/paragraph and erratum.

**Official/discovery seeds**
- `https://www.gao.gov/yellowbook`
- `https://www.gao.gov/greenbook`
- `https://www.gao.gov/copyright`

**Retrieval procedure**
1. Follow current landing pages to official original editions, historical copies, errata and implementation guidance.
2. Check government authorship/reuse terms and third-party inclusions; download via permitted route retaining original bytes/notices.
3. Parse chapter/paragraph/table/page; distinguish engagement-type effective triggers and compare rendered tables.

**Required locators:** book/edition; chapter/paragraph; physical/printed page.

**Boundary:** Guidance/FAQs are not automatically equal to standards; keep Yellow versus Green purposes and versions clear.

**First deliverable:** Full source-cleared editions with exact citation and visual extraction checks.

### FASAB — Federal Accounting Standards Advisory Board

Issues: [#15](https://github.com/ChipmunkRPA/open-source-accounting/issues/15). Default: **public_work_candidate**.

**Coverage unit:** SFFAS/SFFAC/interpretation/technical publication version.

**Official/discovery seeds**
- `https://fasab.gov/accounting-standards/`

**Retrieval procedure**
1. Enumerate official Handbook, standards/concepts, interpretations, technical bulletins/releases and amendments.
2. Verify each original publication notice/rights and download routes; preserve hierarchy and effective-date scope.
3. Parse actual paragraph/section locators and create original federal accounting examples with specialist review.

**Required locators:** publication number; paragraph; edition/effective date.

**Boundary:** Federal FASAB framework is not GASB; verify work-specific rights and reused content.

**First deliverable:** Handbook inventory and a complete scoped source import with exact locators.

### OMB_TREASURY — OMB circulars, grants and Treasury reporting guidance

Issues: [#15](https://github.com/ChipmunkRPA/open-source-accounting/issues/15). Default: **public_work_candidate**.

**Coverage unit:** circular/supplement/manual edition, fiscal year and program.

**Official/discovery seeds**
- `https://www.whitehouse.gov/omb/`
- `https://www.ecfr.gov/current/title-2/subtitle-A/chapter-II/part-200`
- `https://tfm.fiscal.treasury.gov/`

**Retrieval procedure**
1. Resolve current official navigation to relevant A-123/A-136 circulars, annual Compliance Supplements and Treasury manuals.
2. Acquire regulations and circulars as distinct authority classes; preserve fiscal-year/program/appendix context and revisions.
3. Parse compliance matrices/schedules and reconcile tables; maintain old annual versions separately.

**Required locators:** circular/chapter/appendix; program; fiscal year; table/paragraph.

**Boundary:** Do not collapse annual supplements or represent agency examples as universal GAAP.

**First deliverable:** Documented pilot annual edition and version-aware compliance-table fixtures.

### FEDERAL_LAW — Federal statutes and regulations

Issues: [#16](https://github.com/ChipmunkRPA/open-source-accounting/issues/16). Default: **public_work_candidate**.

**Coverage unit:** title/section or dated regulation/release.

**Official/discovery seeds**
- `https://uscode.house.gov/download/download.shtml`
- `https://www.govinfo.gov/bulkdata/`
- `https://www.ecfr.gov/developers/documentation/api/v1`
- `https://www.federalregister.gov/developers/documentation/api/v1`

**Retrieval procedure**
1. Use official bulk/API docs for securities/SOX/accounting-related law and relevant regulations.
2. Preserve statutory version, regulation effective dates, proposed/final distinction and amendments.
3. Screen privately incorporated material and keep exact section/subparagraph locators.

**Required locators:** USC/CFR title/section; paragraph; edition/effective date.

**Boundary:** Official publication does not erase every embedded private copyright; proposals are not operative rules.

**First deliverable:** Scoped authoritative-law corpus with amendments and applicability tests.

### COURTS — Official court opinions and procedural history

Issues: [#16](https://github.com/ChipmunkRPA/open-source-accounting/issues/16). Default: **official_opinion_candidate**.

**Coverage unit:** court/docket/opinion version and procedural event.

**Official/discovery seeds**
- `https://www.govinfo.gov/app/collection/USCOURTS`
- `https://www.supremecourt.gov/opinions/opinions.aspx`

**Retrieval procedure**
1. Discover official opinions from court/govinfo sources for declared subject/jurisdiction/year scope.
2. Preserve docket, court, date, precedential designation where stated, pages and actual disposition; retrieve amended and later official records when available.
3. Write original case briefs with facts/arguments/holding/reasoning clearly separated from procedural records.

**Required locators:** court/docket; decision date; page/paragraph; opinion version.

**Boundary:** No Westlaw/Lexis headnotes or proprietary citator data; no fee-incurring PACER retrieval without approval; do not claim exhaustive later history.

**First deliverable:** Pilot with actual opinions and disclosed later-history gaps, expert reviewed.

### STATE_LOCAL_LAW — State/local statutes, opinions and public reports

Issues: [#16](https://github.com/ChipmunkRPA/open-source-accounting/issues/16), [#10](https://github.com/ChipmunkRPA/open-source-accounting/issues/10). Default: **per_jurisdiction_review**.

**Coverage unit:** jurisdiction/document/version.

**Official/discovery seeds**
- `https://www.usa.gov/state-governments`

**Retrieval procedure**
1. Choose an explicit state/local pilot, identify its authentic legislature/court/regulator source and permissions.
2. Verify official government-edict versus other-agency/contractor content status; do not apply federal section105 universally.
3. Acquire only through permitted routes and retain jurisdiction/version/exact citations.

**Required locators:** jurisdiction; statute/case/report; paragraph/page; date.

**Boundary:** Government-adjacent content or issuer reports need separate rights assessment.

**First deliverable:** Metadata map and reviewed source-specific route for one pilot.

### COSO — COSO IC/ERM and thought papers

Issues: [#17](https://github.com/ChipmunkRPA/open-source-accounting/issues/17). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** framework/publication/edition/principle.

**Official/discovery seeds**
- `https://www.coso.org/guidance-on-ic`
- `https://www.coso.org/`

**Retrieval procedure**
1. Discover core frameworks and free downloads with exact applicable licensing terms.
2. Request software/public AI/paid-service permission; distinguish distributing an intact free download from embedding its contents in software.
3. Until cleared, create independent risk-control explanations and link references; no copied diagrams/framework prose.

**Required locators:** framework/edition; principle/section; page.

**Boundary:** Free downloads are not automatic software-use permission.

**First deliverable:** Reference map and licensing packet plus original control examples.

### IIA_ISACA — IIA internal audit and ISACA/COBIT

Issues: [#17](https://github.com/ChipmunkRPA/open-source-accounting/issues/17). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** framework/standard/requirement/edition.

**Official/discovery seeds**
- `https://www.theiia.org/en/standards`
- `https://www.theiia.org/en/about-us/licensing/`
- `https://www.theiia.org/en/copyright-notice/`
- `https://www.isaca.org/`

**Retrieval procedure**
1. Inventory current and historical IIA standards/topical requirements and relevant COBIT/ISACA publications separately.
2. Review exact software and AI clauses. IIA published licensing materials require specific AI authorization and do not generally authorize public AI use.
3. Build metadata and independent internal-audit/ITGC examples; licensed ingestion only after explicit compatible permission.

**Required locators:** standard/requirement; framework/edition; section/page.

**Boundary:** A generic software license does not establish AI authorization; do not infer performed audit work from documents.

**First deliverable:** Permission-specific reference layers and original control-design cases.

### NIST — NIST government IT/security/control guidance

Issues: [#17](https://github.com/ChipmunkRPA/open-source-accounting/issues/17). Default: **public_work_candidate**.

**Coverage unit:** publication/control identifier/version.

**Official/discovery seeds**
- `https://csrc.nist.gov/publications`

**Retrieval procedure**
1. Discover official CSF, SP and AI risk guidance relevant to finance systems; check publication notices and external components.
2. Acquire permitted official formats, preserving version, control IDs, withdrawn/superseded status and tables.
3. Map guidance to original ITGC examples without calling NIST a GAAP/COSO requirement.

**Required locators:** publication/version; control/section; page.

**Boundary:** Government guidance scope and private incorporated material must be distinguished.

**First deliverable:** One reviewed publication-to-control map with precise citations.

### PUBLISHERS — Big Four, other firms, textbooks and proprietary research

Issues: [#18](https://github.com/ChipmunkRPA/open-source-accounting/issues/18). Default: **reference_only_until_scope_cleared**.

**Coverage unit:** publisher/product/article/edition.

**Official/discovery seeds**
- `https://dart.deloitte.com/USDART/obj/vsid/441069`
- `https://viewpoint.pwc.com/`
- `https://www.ey.com/`
- `https://kpmg.com/`

**Retrieval procedure**
1. Discover official metadata and source terms only through allowed routes; check embedded FAF/AICPA/COSO rights.
2. Prepare permission packets. Do not fetch restricted body text into AI, scrape user accounts, or use search/mirror/upload as a bypass.
3. Write genuine original teaching material, not mass paraphrases; licensed body adapters stay disabled until exact operation rights are established.

**Required locators:** publisher/product; title/edition; section/page.

**Boundary:** No DART AI use absent appropriate separate permission; learning ideas is distinct from copying protected expression.

**First deliverable:** Reference directory, blocked-source tests and per-product permission requests.

### OPEN_LITERATURE — Open textbooks, academic articles and OER

Issues: [#19](https://github.com/ChipmunkRPA/open-source-accounting/issues/19). Default: **license_by_work_version**.

**Coverage unit:** book/chapter or DOI/manuscript version.

**Official/discovery seeds**
- `https://openstax.org/subjects/business`
- `https://www.crossref.org/documentation/retrieve-metadata/rest-api/`
- `https://creativecommons.org/share-your-work/cclicenses/`

**Retrieval procedure**
1. Discover works through official publishers, DOI metadata and institutional repositories; inspect actual full-text version and license.
2. Check CC0/BY/SA/NC/ND obligations and third-party figures per edition; NC is not automatically compatible with the paid Agent.
3. Acquire allowed text preserving chapter/page/attribution/modification notices, manuscript-vs-record version, corrections and retractions.

**Required locators:** DOI/version; chapter/page; license/attribution.

**Boundary:** DOI/abstract/search availability is not permission; empirical research/textbooks are not authoritative standards.

**First deliverable:** A license-verified scoped collection, attribution/export tests and retraction handling.

### REGULATORS — Banking, tax, plan, utility and industry reporting

Issues: [#20](https://github.com/ChipmunkRPA/open-source-accounting/issues/20). Default: **per_publication_review**.

**Coverage unit:** regulator/report/schedule/jurisdiction/period.

**Official/discovery seeds**
- `https://www.ffiec.gov/`
- `https://www.fdic.gov/`
- `https://www.occ.treas.gov/`
- `https://www.federalreserve.gov/`
- `https://www.irs.gov/irb`
- `https://www.irs.gov/forms-instructions`
- `https://www.dol.gov/agencies/ebsa`
- `https://www.ferc.gov/`
- `https://content.naic.org/`

**Retrieval procedure**
1. Select specific regulator/industry pilots and resolve current official reporting instructions/APIs/downloads.
2. Check work authorship/private rights; NAIC material is not federal public domain. Separate tax law/instructions from GAAP.
3. Acquire permitted versions and structured reports with schedules, units, periods and historical amendments.

**Required locators:** regulator/report/schedule; tax or fiscal year; paragraph/page.

**Boundary:** Specialist/jurisdiction scope and source rights must be explicit; no filing or tax-rate assumptions.

**First deliverable:** One report-instruction pilot per approved industry, reviewed before production routing.

### LOCAL_FRAMEWORKS — National standards, legal adoption and translations

Issues: [#21](https://github.com/ChipmunkRPA/open-source-accounting/issues/21). Default: **per_jurisdiction_review**.

**Coverage unit:** standard/language/local adoption/version.

**Official/discovery seeds**
- `https://www.frc.org.uk/`
- `https://www.aasb.gov.au/`
- `https://www.auasb.gov.au/`
- `https://www.frascanada.ca/`
- `https://eur-lex.europa.eu/`
- `https://www.ifrs.org/use-around-the-world/`

**Retrieval procedure**
1. Choose one jurisdiction at a time and navigate official standard-setter/regulator/legislative sources.
2. Record local modifications, endorsement law, required date and language; inspect translation and narrative reuse rights.
3. Acquire only under compatible rights; use specialist-reviewed original comparisons while text is blocked.

**Required locators:** local standard/paragraph; jurisdiction/adoption date; language/version.

**Boundary:** IFRS as issued is not always local-endorsed IFRS; machine translation is not authoritative local text.

**First deliverable:** Explicit opt-in pilot with reference/rights/adoption matrix.

### ORIGINAL — Our guides, cases, templates, questions and playbooks

Issues: [#22](https://github.com/ChipmunkRPA/open-source-accounting/issues/22), [#23](https://github.com/ChipmunkRPA/open-source-accounting/issues/23). Default: **original_content_review_required**.

**Coverage unit:** immutable content item/version and independently adjudicated question.

**Official/discovery seeds**
- `repo:content/manifest.json`
- `repo:content/references/sources.json`
- `repo:content/qa/questions.json`

**Retrieval procedure**
1. Read each actual file, verify manifest hash and referenced sources, and record retain/revise/supersede disposition.
2. Author original source-supported scope/decision/case/template material; never copy exam banks or replace a publisher passage with synonyms.
3. Generate new immutable versions and content progress; require actual independent review for Agent admission.

**Required locators:** item ID/version/hash; section; source references.

**Boundary:** Public draft availability does not establish technical correctness or primary-text verification; contributors grant only rights held.

**First deliverable:** Complete all63 item retrieval/review mapping, then deepen core topics.

### PRIVATE_UPLOADS — User contracts, memos, workpapers and private reports

Issues: [#24](https://github.com/ChipmunkRPA/open-source-accounting/issues/24), [#29](https://github.com/ChipmunkRPA/open-source-accounting/issues/29), [#31](https://github.com/ChipmunkRPA/open-source-accounting/issues/31), [#34](https://github.com/ChipmunkRPA/open-source-accounting/issues/34). Default: **workspace_private_authorization_required**.

**Coverage unit:** workspace/document/version/page/clause/cell.

**Official/discovery seeds**
- `repo:backend/app/services/documents.py`
- `repo:backend/app/api/workspaces.py`

**Retrieval procedure**
1. Accept only authorized files through authenticated MFA workspace; validate formats and quarantine before parsing.
2. Check publisher-specific restrictions even for user-provided files, and constrain model/provider retention.
3. Keep private source and derivatives isolated; citations resolve only within authorized workspace; delete derivatives on deletion.

**Required locators:** workspace/document/hash; page/clause/sheet/cell; revision.

**Boundary:** No public Git, cross-workspace retrieval, shared cache, training or public content ingestion; upload checkbox is not a blanket license.

**First deliverable:** Secure private parsing-to-evidence flow with permission and deletion tests.
