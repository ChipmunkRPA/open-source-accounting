# Operator and reviewer decisions — never fabricate these

| Decision | Why needed | Related issues | Codex can do now |
|---|---|---|---|
| Full baseline access | GitHub main may lack app; remote Codex cannot assume ChatGPT sandbox access | #6 | Verify supplied ZIP; prepare clean reconciliation PR |
| GCP project, region, DNS, billing and spend limits | Resources and paid API/SMS usage require authority | #26–#28, #38, #40 | IaC plan, mock/contract tests, explicit cost estimate |
| Live Google credentials and approved model endpoint | Requested model is not proven in the operator's project | #26 | Configurable adapter, current docs check, disabled live smoke script |
| Identity Platform, authorized domains and test-phone consent | Real TOTP/SMS and recovery need configured project and user control | #27–#29 | Build and test controller/contracts; prepare staging checklist |
| Content permissions/licenses or counsel-reviewed bounded use | Public AI, retrieval, export and Git redistribution are distinct uses | #7, #9–#21 | Metadata/reference layers; license request packet; synthetic adapter tests |
| Independent accountant/auditor/specialist review | AI-generated draft is not approved evidence | #22–#23, #36 | Review packets, finding workflow and exact-hash approval mechanism |
| Usage allowance, concurrency/grace, actual billing terms | $89.99/year approved; 30 monthly tasks not approved | #30, #38 | Test configurable proposed policies without activation |
| Tax/refund/auto-renewal/privacy terms | Depend on actual operator, jurisdictions and business choices | #30, #39–#40 | Draft implementation questions and configuration hooks, not legal approval |
| Private data retention, recovery and incident support | Cannot promise zero retention or staffed support from code | #27–#29, #38 | Document actual data flow; implement deletion and escalation receipts |
| Notification provider/consent/schedule | MFA SMS consent is not alert/marketing consent | #37 | Opt-in UI and mocked delivery; keep schedules disabled |
| Launch scope and production approval | A scoped beta differs from a comprehensive research service | #40 | Evidence-linked readiness report, rollback plan and residual-risk register |

A blocker record needs: issue, owner (unassigned until a real owner accepts), exact decision or missing input, affected operations, evidence, safe fallback, independent work available, and next command. Never put credentials or confidential legal advice in public issue bodies. Do not request secrets in chat; use approved environment/secret mechanisms.
