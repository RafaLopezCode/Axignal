# Coverage register

Campaign: `AXIGNAL-PR-2026-10-06-01`; final revalidated snapshot `016235736db002038f8063f3abd311ba5dca110c`. Agent reviews began from parent `a2a6f956ce7e77a9201357cbfc50987afb863099`; only Docker Compose canary secret group and its contract test changed afterward, and the Orchestrator revalidated that slice (9 passing tests).

## Agent and domain coverage

| Package | Primary owner / model | Scope actually reviewed | Disposition |
|---|---|---|---|
| A/B | `identity_tenancy` / gpt-6-luna, high | Commercial identity/sessions; tenant memberships; Xeed scope/cardinality; Customer Zero boundary; synthetic 1/2/100 | Audited; IDT-01..04 |
| C/D/E | `brain_evidence` / gpt-6-luna, high | Perception/source contracts, EB-04 vertical, canonical admission/epistemics, market-map integration, DRI, Jev authorization | Audited; BRAIN-01..04 |
| F/G | reused `admin_ops` / gpt-6-luna, high | Memory/research/Prime/live runtime, costs/budget/leases, AXENT, generative UI and subscriber Human First connection | Audited; MEMORY-01..03, UX-01..02 |
| H/J | `billing_acquisition` / gpt-6-luna, high | Pricing/CTA, checkout and webhook authority, entitlements/reconciliation, public Landing, first-party acquisition | Audited; COMM-01..09 |
| I | `admin_ops` / gpt-6-luna, high | AO-00..31 dispositions, Customer Zero dogfood, internal operations maturity | Audited; ADMIN-01..03 |
| K/L | `security_reliability` / gpt-6-luna, high | Admin/subscriber security boundary, production evidence, backup/recovery, privacy/applicability limits, QA | Audited; SEC-01, OPS-01..02 |

Cross-review: Orchestrator independently checked IDT-01, COMM-01, BRAIN-01, the current Human First app boundary and test failures. Each package report was reconciled to the same HEAD. CDE, H/J, I and K/L did not execute identical full suites; their focused results remain separate.

## Critical-flow case catalogue

This campaign freezes the following bounded catalogue before stating any coverage ratio. A case can be verified at a particular layer without implying runtime/E2E readiness. `Contract/code` means the repository rule or fixture; `external/runtime` means the deployed service or real subscriber journey.

| Case | Required behavior | Cases audited / evidence | Result by layer |
|---|---|---|---|
| C01 | Public visitor can start authenticated subscriber sign-up/login | Auth contracts and route | Contract shows explicitly unavailable; no subscriber runtime |
| C02 | Identity can establish/revoke Principal and session | Identity spec/routes | Missing by declared scope; provider/session/revocation not implemented |
| C03 | Principal obtains only authorized Tenant membership | Xeed reader and focused tests | Contract tested; durable production membership backing absent |
| C04 | Subscriber adds one Organization with truthful unresolved/ambiguous state | Customer Zero contract only | Internal path present; commercial path absent |
| C05 | Subscriber adds 2 Organizations with independent outcomes | Synthetic harness; commercial flow not present | Product E2E unverified |
| C06 | Subscriber adds 100 Organizations under quota/idempotency/budget | EB-08 synthetic SQLite test | Synthetic storage/recovery verified; acquisition/observation scale unverified |
| C07 | Two tenants may share public Organization without private-focus leakage | Tenant authority contracts/focused tests | Contract coverage; deployed two-subscriber runtime unverified |
| C08 | Price CTA completes hosted checkout and ties payer to consumption scope | Landing CTA, routes, billing code/AO-10 | CTA gates to unavailable access; checkout creation absent in repository |
| C09 | Verified payment grants correct capacity and renewal/cancel/replay are safe | AO-10 fixture tests | Deterministic provider-event contracts tested; sandbox/live/reconciliation unknown |
| C10 | Brain composes registered-Xeed observation into grounded output | EB-04 composition and tests | Narrow synthetic vertical composed; commercial/runtime wiring unverified |
| C11 | Official web claim remains DECLARED, not OBSERVED | MASTER, EB-04 canonical materializer and assertion | Contractual epistemic mismatch verified in code and test |
| C12 | Market posture routes distinct B2B/B2C/B2G research | Market map/planner contracts | Individual planner rules tested; EB-04 composition absent |
| C13 | Low public presence yields bounded gap and contextual follow-up | Pilot validation, AXENT, fixture tests | Partial deterministic logic; measurement contract and company-specific diagnosis unverified |
| C14 | Observation/Learning Memory, Prime, leases and budget survive/re-evaluate work | 148 focused Python Memory/Prime/scheduler/batch/runtime/budget/canary + EB-04 tests (agent report) | Component contracts and controlled tests pass; no live canary output, and actual total cost cap is not proven |
| C15 | Human sees output, uncertainty and exact evidence in a persistent journey | README/app routes and 51 frontend tests | Typed-plan fixture and internal JSON AXENT differ; real EB-04 output is not connected to app |
| C16 | AXENT acts only within authorized evidence and preserves context | AXENT local/server contracts, 51 frontend tests | Local/internal scoped paths tested; no live provider/research tools |
| C17 | Admin Customer Zero observes AXIGNAL internally and persists re-observation | AO-24A / FR-30 documents and focused tests | Internally recorded E2E; visual acceptance pending; not commercial onboarding |
| C18 | Service can restore production Admin/runtime and roll back with measured RPO/RTO | Runbook/AO-29 | Rollback instructions exist; external backup restore drill not evidenced |
| C19 | Current production release matches an exact verified SHA/digest/config/health | Historical deployment docs only | Current deployed SHA/digest/health UNKNOWN |
| C20 | Consent/legal-controller disclosure and production capture are appropriately gated | Public Landing + local gate contracts | Public page says prelaunch/legal data to confirm before capture/accounts/contracts; live flags unknown |
| C21 | Own-site SEO metadata and deployed indexing are correct | Static source inspection | Static metadata present; deployed crawl/index results unknown |
| C22 | Jev evaluation is authorized, reproducible and measured | MCA / EB-05 reassessment | Jev call blocked by terms/corpus authority; no quality/cost/latency result |
| C23 | Privacy, retention, incident handling and Admin hardening have accepted evidence | AO-29 / SEC-01 | Required internal work not started; applicability/acceptance unknown |
| C24 | Release gates, browser QA and human acceptance support the actual candidate | Focused tests and historical artifacts | Full deterministic gates and fresh visual/release-candidate verification not run in this campaign |

## Denominators and exclusions

Catalogue denominator is 24 bounded cases. This is not an exhaustive feature/spec catalog; no percentage is reported because each case contains multiple evidence layers and the full candidate/environment is not available. In the table, â€œcontract testedâ€ does not count as external/runtime coverage. Customer Zero internal results are not substituted for C01â€“C09. Browser screenshot evidence was not freshly captured in this campaign, and test suites listed by agents are not treated as end-to-end commercial journey passes.

## Domain coverage summary

| Domain | Primary auditor | Main audited flows | External/live cases run | Gaps |
|---|---|---|---|---|
| A/B Identity, account, tenancy, Xeed | identity_tenancy | auth boundary; membership check; internal attention; synthetic 1/2/100 | 0 | provider/session, persistent subscriber provisioning and actual scale |
| C/D/E Brain, source, evidence | brain_evidence + Orchestrator | EB-04 composition, evidence admission, market planner, presence, Jev | 0 | epistemic correction, broader market integration, measured DRI, live authorized research |
| F/G Memory and Human First | admin_ops follow-up + Orchestrator | memory/runtime and AI SDK/presentation binding | 0 | see MEMORY/UX findings in report; no live data or provider |
| H/J Billing/Landing | billing_acquisition | public CTA, AO-10 event contracts, pricing/SEO copy | 0 | checkout sandbox, paid subscriber/tenant binding, live state |
| I Admin | admin_ops | AO roadmap, Customer Zero, Admin authority and readiness | 1 documented prior production dogfood record; no new probe | AO-24A visual acceptance; AO-28..31 closure |
| K/L Security/reliability | security_reliability | Compose/RBAC contracts, runbook and AO-29 | 0 | deployed state, backup restore, incident/retention evidence |
