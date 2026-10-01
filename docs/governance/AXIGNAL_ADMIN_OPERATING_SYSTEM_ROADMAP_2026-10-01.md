# AXIGNAL Admin & Business Operating System Roadmap — 2026-10-01

**Status:** ACTIVE EXECUTION CONTRACT
**Type:** Subordinate implementation roadmap; not product doctrine or architectural authority.
**Authority:** MASTER PRODUCT MODEL → Engineering Constitution → accepted ADRs → product/architecture specs → this roadmap.
**Repository baseline:** `main @ c2ae21025075d85b175c9b87031bc272cf0ce6a9`.
**Inputs:** current Admin V0.1 specification and P0-ADMIN-01 contracts; FR-00→FR-31 closure evidence; documents in `D:\AXIGNAL\Asesor Frontera`; current MASTER pricing/flywheel/marketing doctrine.
**Execution mode:** one active task at a time unless an explicitly external-evidence task is marked PARALLEL.

## 1. Purpose

This roadmap turns AXIGNAL Admin from a pre-implementation observability specification into the internal operating system used to run AXIGNAL as a real business without weakening AXIGNAL's epistemic boundaries.

The target is one coherent privileged AXIGNAL shell for the founder/operator, reusing the subscriber product's visual grammar while exposing authorized internal operations: system governance, customer/account operations, AXIGNAL's own CRM, acquisition and marketing, Search Console and analytics, integrations and APIs, Stripe/billing, finance/accounting, fiscal/VeriFactu operations, provider/source economics, premium advisory workbench, exports and internal agent access.

This roadmap does **not** make CRM, billing, accounting, tax state, private analytics or internal commercial assertions part of AXIGLAND. It creates separate first-party operational domains and governed projections over them.

A task is not DONE because a screen exists. Runtime/product work normally progresses through IMPLEMENTED → PROVED → INTEGRATED → DEPLOYED → VERIFIED E2E. Documentation-only tasks require authority reconciliation, deterministic checks and integration.
## 2. Non-negotiable invariants

```text
ONE_CANONICAL_AXIGLAND
ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH
AXIGNAL_INTERNAL_CRM_STATE != AXIGLAND_ECONOMIC_TRUTH
COMMERCIAL_RELATIONSHIP_WITH_AXIGNAL != OBSERVED_ECONOMIC_RELATIONSHIP
CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE
STRIPE_STATE != AXIGLAND_TRUTH
ACCOUNTING_STATE != AXIGLAND_TRUTH
TAX_STATE != AXIGLAND_TRUTH
GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION
WEB_ANALYTICS_PRIVATE_METRIC != PUBLIC_OBSERVATION
NEWSLETTER_ENGAGEMENT != BUSINESS_TRUTH
COMMERCIAL_OUTCOME != EPISTEMIC_VALIDITY
ADMIN_ACTION != CANONICAL_WRITE
ADMIN_EVENT != FAXT
ADMIN_METRIC_REQUIRES_LINEAGE
UNKNOWN != ZERO
MISSING_COST != FREE
PRIVATE_CUSTOMER_DATA_NEVER_BECOMES_PUBLIC_AXIGLAND_TRUTH
AXENT / MODEL / AGENT OUTPUT != ADMIN_AUTHORITY
SECRETS_NEVER_ENTER_EXPORTS_OR_AGENT_CONTEXT
PUBLIC_SUBSCRIBER_AUTH != ADMIN_AUTH
PRODUCT_MCP != ADMIN_MCP
SPECIFIED != IMPLEMENTED
```
## 3. Business-model constraints

Current commercial hypotheses remain hypotheses until empirical evidence closes them:

- AXIGNAL subscription: `€9.95/month` including the first Xeed.
- Additional Xeed: `€4.95/month` each.
- Xignals are not billable units.
- Free weekly brief/newsletter: acquisition hypothesis, not a free Xeed entitlement.
- Premium human External Intelligence / Frontier Advisor service: separate high-touch offer, currently discussed around `€995/month`, still requiring willingness-to-pay and bundle validation.
- FR-27 remains READY, not DONE, until real buyer/job/WTP evidence exists.

Admin must measure these hypotheses without silently converting them into validated economics.

## 4. Flywheels Admin must make inspectable

### 4.1 Computational/economic flywheel

```text
XEED → OBSERVATION → GOVERNED MEMORY → REUSE
→ LOWER MARGINAL COST / FASTER ANSWERABILITY
→ MORE / BETTER XEEDS → MORE SHARED KNOWLEDGE ↺
```
### 4.2 Commercial flywheel hypothesis

```text
AXIGNAL SELF-DEMO / CONTENT
→ FREE EVIDENCE-BACKED BRIEF
→ RECURRING ATTENTION / TRUST
→ PAID XEED
→ ADDITIONAL XEEDS
→ PREMIUM ADVISORY WHEN NEEDED
→ MORE GOVERNED OBSERVATION / LEARNING
→ BETTER REUSE + LOWER COST + BETTER PRODUCT
→ BETTER DEMO / CONTENT ↺
```

Admin must distinguish measured flywheel behavior from the hypothesis above.

## 5. Execution rules

1. Only one AO task may be IN_PROGRESS unless a task is explicitly external evidence / compliance review.
2. Prefer reuse → repair → extend → consolidate → create.
3. Existing P0-ADMIN-01 observability contracts are reused unless evidence requires amendment.
4. Admin uses owning-domain services; the UI and Admin Projection are never data authority.
5. First-party operational domains may own AXIGNAL business facts but may not write economic truth into AXIGLAND.
6. Subscriber, Admin and future staff/advisor authorizations remain separate.
7. Every privileged command is authenticated, authorized, versioned and audited.
8. No third-party dashboard becomes the system of record merely because Admin displays it.
9. Financial/fiscal functionality must preserve source references and reconciliation state.
10. Compliance-sensitive functions require explicit legal/compliance gates.
11. No model or agent receives unrestricted SQL/database access, secrets or canonical-write authority.
12. Every AO task closes with evidence, not narrative.
## 6. Status model

`NOT_STARTED → READY → IN_PROGRESS → BLOCKED → DONE → DEFERRED → REJECTED`

**CURRENT_TASK = AO-01**

## 7. Closure rule

Every task contains an `AUDIT_CLOSURE` condition. When AO-00→AO-31 are complete, AXIGNAL will request a new, deeper Frontier Advisor audit. The auditor receives the current canonical repository, production evidence, business/flywheel evidence, known UNKNOWN/DEFERRED items and this roadmap without a requested score or verdict.

# PHASE A — RECONCILE ADMIN AUTHORITY

## AO-00 — Admin V0.2 / AXIGNAL Operating System Doctrine

**Status:** DONE
**Priority:** P0
**Goal:** reconcile Admin V0.1 with the newly authorized broader internal operating scope before implementation.

### Closure evidence (2026-10-01)
- MASTER amended with §2.1A, narrowly authorizing first-party internal AXIGNAL business operations while preserving the subscriber/core no-CRM boundary.
- ADR-0055 accepted: `Admin Private Business Operations Are Separate From AXIGLAND`.
- `AXIGNAL_ADMIN_PRODUCT_SPEC.md` advanced to V0.2 `ACCEPTED_GOVERNED_SPECIFICATION`; implementation remains `PRE_IMPLEMENTATION`.
- V0.2 explicitly authorizes AXIGNAL's own internal CRM, acquisition/marketing, private GSC/web analytics, integrations/APIs, Stripe/billing, finance/accounting, fiscal/VeriFactu operations and staff-only Frontier Advisor workbench.
- P0-ADMIN-01 observability architecture/contracts retained and amended narrowly: first-party AXIGNAL CRM/commercial workflow is permitted; subscriber/customer-owned CRM/workflow and private-state-to-AXIGLAND inference remain forbidden.
- Focused AO-00 + roadmap contracts: 8 PASS.
- Full pytest: 705 PASS.
- Ruff format/check: PASS.
- mypy: PASS (139 source files).
- UTF-8 integrity check: PASS on MASTER/Admin/architecture/ADR-0055.

### Work
- Update `AXIGNAL_ADMIN_PRODUCT_SPEC.md` from V0.1 to a living V0.2 specification.
- Preserve Admin as an internal operating surface, not product doctrine or AXIGLAND authority.
- Explicitly authorize AXIGNAL's **own internal CRM** while preserving `AXIGNAL_INTERNAL_CRM_STATE != AXIGLAND_ECONOMIC_TRUTH`.
- Add acquisition/marketing, GSC/web analytics, Stripe/billing, finance/accounting, fiscal/VeriFactu, APIs/integrations, newsletter operations and Frontier Advisor Workbench to Admin scope.
- Define the boundary between first-party business records and observed-world economic records.
- Reconcile existing P0-ADMIN-01 contracts and architecture; amend rather than duplicate.
- Record material architecture decisions as ADRs.
### Acceptance
- No contradiction remains between MASTER's “AXIGNAL is not a CRM” and Admin's internal CRM authorization.
- Subscriber product cannot access privileged Admin domains.
- Admin cannot use private operational data as AXIGLAND truth.
- Existing Admin observability contracts have an explicit retained/amended/superseded disposition.
- Governance and architecture checks green.

### AUDIT_CLOSURE
A future auditor cannot reasonably claim that Admin implementation expanded scope through undocumented doctrine drift.

## AO-01 — Admin Identity, RBAC and Privileged Session Boundary

**Status:** NOT_STARTED
**Depends on:** AO-00
**Priority:** P0

### Work
- Define staff/admin identity separate from subscriber authorization.
- Implement role/scopes for founder/full privileged, business, finance/fiscal, operations, research/intelligence, technical/system, support and agent-safe read paths.
- Require least privilege, auditable privilege changes, session expiry and fail-closed authorization.
- Keep Admin credentials and Product/Subscriber credentials distinct.
- Define step-up/dual-approval requirements for destructive or high-impact actions where justified.

### Acceptance
- Unauthorized subscriber cannot reach Admin read models or routes.
- Role tests prove allowed and denied operations.
- Privilege changes create immutable audit events.
- No secret/token appears client-side, in exports or agent context.

### AUDIT_CLOSURE
Admin privilege is a verified security boundary, not a hidden route convention.
## AO-02 — Unified AXIGNAL Admin Shell

**Status:** NOT_STARTED
**Depends on:** AO-01
**Priority:** P0 UX

### Goal
Admin must feel like privileged AXIGNAL, not a separate enterprise dashboard product.

### Work
- Reuse AXIGNAL's Human-First spatial language, left rail, contextual AXENT surface, temporal drill-down and evidence/explanation grammar where applicable.
- Add explicit Admin mode/state and privileged navigation.
- Create top-level domains: Command Center, Customers/CRM, Acquisition, Revenue, Xeeds, AXIGLAND Quality, AXENT/Brain, Governance, Integrations, Finance/Fiscal, Frontier Advisor and System.
- Make operational state visually distinct from epistemic/economic state.
- Preserve keyboard, responsive and reduced-motion contracts.

### Acceptance
- User can tell immediately whether they are in Subscriber or Admin context.
- No Admin operational card can visually masquerade as FAXT/Xignal/AXIGLAND evidence.
- Browser QA at desktop and mobile widths.
- Admin navigation is keyboard-operable and deep-linkable.

### AUDIT_CLOSURE
A future UX audit cannot reasonably describe Admin as an unrelated dashboard or confuse internal business state with AXIGLAND.
# PHASE B — ADMIN DATA PLANE AND OBSERVABILITY

## AO-03 — Admin Event Envelope and Projection Runtime

**Status:** NOT_STARTED
**Depends on:** AO-00, AO-01
**Priority:** P0

### Work
- Implement the first production Admin event/observation ingestion contracts from P0-ADMIN-01.
- Preserve producer ownership; Admin references owning-domain records rather than copying truth into a shadow authority.
- Implement durable, temporal Admin Projection read models with schema/version/fingerprint.
- Distinguish logs, traces, metrics, operational events and economic observations.
- Add replay/idempotency/correction semantics.

### Acceptance
- Projection rebuild/replay deterministic for supported event classes.
- Same source event cannot double-count a metric.
- Corrections preserve original history.
- Admin projection outage cannot mutate owning domains.

### AUDIT_CLOSURE
`SPECIFIED_NOT_IMPLEMENTED` no longer applies to the Admin Projection substrate.
## AO-04 — Command Center / Executive State

**Status:** NOT_STARTED
**Depends on:** AO-03
**Priority:** P0

### Work
Implement the executive landing view over real read models:
- MRR/ARR and paying accounts.
- Active Xeeds and Xeed economics.
- Customer/product activity.
- Source/provider/system health.
- Evidence/currentness/provenance quality.
- Open incidents/critical alerts.
- Flywheel indicators with explicit methodology.

### Acceptance
- Every material number drills into definition, period, source inputs and lineage.
- UNKNOWN/missing inputs never render as zero.
- Time comparison distinguishes data-method change from business change.

### AUDIT_CLOSURE
Command Center is an inspectable projection rather than a collection of unexplained KPI cards.
## AO-05 — Xeed & AXIGLAND Observatory

**Status:** NOT_STARTED
**Depends on:** AO-03
**Priority:** P0

### Work
- Xeed lifecycle, germination state, first-value timing, currentness, observation coverage and active/inactive state.
- Cost/revenue attribution per Xeed without double-counting shared observations.
- AXIGLAND growth, reuse, currentness, provenance, contradiction and entity-resolution observability.
- Trace Admin metrics back to governed Observation/Learning/canonical references.

### Acceptance
- Admin can diagnose why a Xeed is expensive, stale, blocked or low-value.
- Shared cost and triggered cost remain distinguishable.
- Reuse does not count as new knowledge.

### AUDIT_CLOSURE
Xeed economics and AXIGLAND reuse can be inspected from runtime evidence rather than inferred manually.

## AO-06 — AXENT / Brain / Provider Observatory

**Status:** NOT_STARTED
**Depends on:** AO-03
**Priority:** P0
### Work
- Research objectives, routing, stop reasons, budget exhaustion and no-progress.
- Provider/model usage through provider-neutral contracts.
- Structured evaluator/JEV observations when available.
- Cost, latency, retry/failure, abstention and useful-output attribution.
- Knowledge Frontier and unresolved gaps.

### Acceptance
- Provider cost/performance can be compared on compatible jobs without making the provider authority.
- Failure and abstention remain first-class.
- Commercial outcomes cannot relabel model correctness.

### AUDIT_CLOSURE
Admin can explain where cognitive spend goes and why, without provider lock or opaque scores.

## AO-07 — Governance, Policy Registry, Audit and Alerts

**Status:** NOT_STARTED
**Depends on:** AO-01, AO-03
**Priority:** P0
### Work
- Versioned policy registry for budgets, source acquisition, currentness, retention, provider routing, canonical admission and alerts.
- Immutable privileged-action audit.
- Alert classes for unsupported write attempts, stale coverage, source/provider failure, cost spikes, payment failures, security incidents and governance drift.
- Bounded commands route through owning services; Admin never mutates stores directly.

### Acceptance
- Policy change shows actor, before/after, reason and effective version.
- High-impact command has authorization and result audit.
- `UNSUPPORTED_CANONICAL_WRITE_TARGET` stays zero in normal operation.

### AUDIT_CLOSURE
Governance is executable/inspectable, not merely documented.

# PHASE C — AXIGNAL BUSINESS OPERATIONS

## AO-08 — Internal CRM Domain for AXIGNAL

**Status:** NOT_STARTED
**Depends on:** AO-00, AO-01, AO-03
**Priority:** P0 Business
### Work
Implement a first-party CRM strictly for AXIGNAL's own commercial operations:
- prospect/company/contact records;
- acquisition source and consent basis;
- opportunity/deal lifecycle;
- notes/tasks/follow-up only for AXIGNAL commercial operations;
- linkage to an AXIGNAL account after conversion;
- optional reference to an observed Organization only by explicit ID mapping, never by semantic equivalence.

### Acceptance
- Creating a CRM lead cannot create/modify Organization/FAXT/Relationship/Xignal.
- AXIGLAND observation cannot silently create a CRM commercial relationship.
- CRM exports are internal and privacy-governed.
- Audit distinguishes commercial claim, user-provided data and public observation.

### AUDIT_CLOSURE
Internal CRM exists without turning AXIGNAL product or AXIGLAND into a CRM.

## AO-09 — Account, Subscription and Customer Operations

**Status:** NOT_STARTED
**Depends on:** AO-08
**Priority:** P0 Business
### Work
- Account/users/plan/subscription/Xeed entitlement model.
- Signup, activation, first-Xeed, upgrade/downgrade/cancel/suspend states.
- Customer 360 over first-party service state.
- Support/correction/claim-review references.
- Product-funnel and retention/cohort read models.

### Acceptance
- Subscription/account state is authoritative only for AXIGNAL service operations.
- Entitlement is enforced server-side.
- Account lifecycle and Xeed entitlement are replayable/auditable.

### AUDIT_CLOSURE
AXIGNAL can operate real paying accounts without manual database intervention.

## AO-10 — Stripe Payments and Billing Integration

**Status:** NOT_STARTED
**Depends on:** AO-09, AO-18
**Priority:** P0 Revenue
### Work
- Stripe customer/subscription/product/price mapping behind an adapter.
- Support current commercial hypothesis: first-Xeed base plan + additional-Xeed quantity/entitlement without billing Xignals.
- Webhook verification, idempotency, payment state, failed-payment/dunning, refund/cancel handling.
- Preserve Stripe as payment/billing provider, not AXIGNAL business-truth authority beyond Stripe-owned payment records.

### Acceptance
- Duplicate/out-of-order webhooks do not double-charge or corrupt entitlement.
- Payment success/failure maps deterministically to billing state.
- Xignal count never affects invoice quantity.
- Sandbox E2E before live enablement.

### AUDIT_CLOSURE
Revenue collection and entitlements are integrated and replay-safe rather than manually reconciled.

## AO-11 — Revenue, Cohorts and Unit-Economics Runtime

**Status:** NOT_STARTED
**Depends on:** AO-05, AO-09, AO-10
**Priority:** P0 Business
### Work
- MRR, ARR, ARPA, revenue/Xeed, churn, expansion, contraction and cohort retention.
- `COST_PER_ACTIVE_XEED_MONTH`, contribution/Xeed and variable-cost ratio.
- Triggered, attributed, shared and avoided-recompute economics.
- Compare measured economics with €9.95/€4.95 hypotheses without assuming validation.

### Acceptance
- Every financial metric has lineage and period.
- Cross-currency values are not summed without governed conversion.
- Missing costs remain UNKNOWN.
- Shared cost allocation is versioned and explainable.

### AUDIT_CLOSURE
The next audit can inspect measured unit economics rather than only pricing theory.
# PHASE D — ACQUISITION, MARKETING AND DISTRIBUTION

## AO-12 — Marketing & Acquisition Event Model

**Status:** NOT_STARTED
**Depends on:** AO-03, AO-08
**Priority:** P1 Growth

### Work
- First-party campaign/source/content/landing/request events.
- Consent and lawful-basis references.
- UTM/referrer/campaign attribution with explicit limitations.
- Separate anonymous marketing telemetry, known contact, CRM prospect, customer and subscriber identities.

### Acceptance
- Anonymous visit cannot silently become a named CRM person.
- Attribution model is versioned and does not claim causal certainty.
- Marketing engagement never becomes AXIGLAND truth.

### AUDIT_CLOSURE
Acquisition performance becomes measurable without contaminating product epistemology.

## AO-13 — Google Search Console Integration for AXIGNAL

**Status:** NOT_STARTED
**Depends on:** AO-18
**Priority:** P1 Growth
### Work
- Server-side authorization appropriate to the selected Google integration.
- Import AXIGNAL's own GSC query/page/country/device/search-appearance measurements.
- Retain property, period, dimensions, freshness and API provenance.
- Keep GSC private analytics isolated from public DRI observations.

### Acceptance
- `GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION` enforced in contracts/tests.
- Revoked credentials fail closed.
- Admin can compare marketing performance without writing GSC metrics into AXIGLAND.

### AUDIT_CLOSURE
AXIGNAL's own search performance can be operated from Admin with the private/public observation boundary intact.

## AO-14 — Web/Product Analytics and Attribution

**Status:** NOT_STARTED
**Depends on:** AO-12, AO-18
**Priority:** P1 Growth
### Work
- Landing/product events for page/chapter navigation, CTA, signup, first-Xeed, Today/evidence interaction, return behavior and conversion.
- Privacy-minimized analytics ingestion from selected provider(s) or AXIGNAL-owned events.
- Funnel/cohort read models.
- Bot/internal traffic handling where possible.

### Acceptance
- Analytics definitions are versioned.
- Admin can trace landing → signup → Xeed → paid conversion without treating correlation as causation.
- Sensitive subscriber content is excluded from generic analytics events.

### AUDIT_CLOSURE
Marketing/product decisions no longer depend on disconnected external dashboards.

## AO-15 — Free Weekly Brief Request, Eligibility and Consent

**Status:** NOT_STARTED
**Depends on:** AO-08, AO-12
**Priority:** P1 Growth
### Work
- `BriefRequest` and accepted/declined review flow.
- Subject/company matching and clarification path.
- Objective fit/evidence-coverage criteria.
- Separate request-processing permission from newsletter consent.
- Decline/correction/retention/unsubscribe state.
- No automatic free Xeed creation.

### Acceptance
- Request != subscriber != customer != lead truth in AXIGLAND.
- Accepted request still requires affirmative newsletter consent.
- Ambiguous company identity fails to clarification.

### AUDIT_CLOSURE
The free acquisition hypothesis can be piloted without consent or ontology shortcuts.

## AO-16 — Evidence-Backed Weekly Brief Pipeline

**Status:** NOT_STARTED
**Depends on:** AO-15, AO-05, AO-06, AO-18
**Priority:** P1 Growth
### Work
- Up to three material evidence-backed items; fewer or no-send when appropriate.
- Preserve source, date, observation condition, why-it-may-matter and UNKNOWN.
- Deterministic eligibility/currentness/dedup gates before optional model drafting.
- Human review during pilot.
- Versioned issue snapshot, delivery record and correction history.

### Acceptance
- No filler item to satisfy quota.
- Model cannot invent a development or upgrade inference to observation.
- Sent issue can be reconstructed from evidence and versions.

### AUDIT_CLOSURE
The free brief demonstrates AXIGNAL honestly rather than becoming an AI-content marketing engine.

## AO-17 — Acquisition Funnel and Conversion Observatory

**Status:** NOT_STARTED
**Depends on:** AO-14, AO-15, AO-16, AO-10
**Priority:** P1 Growth
### Work
Measure:
- request/accept/consent/delivery/engagement;
- evidence clicks and recurring readership;
- free → paid Xeed conversion and time-to-conversion;
- additional-Xeed attach;
- premium-advisory inquiry/close;
- unsubscribe/complaint/correction/delivery costs.

### Acceptance
- Conversion is reported as commercial behavior, not product truth.
- Bot opens and ambiguous engagement are separately classified where possible.
- Cohort cost and gross contribution inspectable.

### AUDIT_CLOSURE
The commercial flywheel is measurable rather than a narrative hypothesis.

# PHASE E — INTEGRATIONS AND API OPERATIONS

## AO-18 — Integration Registry, Credentials and Connection Governance

**Status:** NOT_STARTED
**Depends on:** AO-01, AO-07
**Priority:** P0 Infrastructure
### Work
- Central registry of external integrations, scopes, owner, environment, status, credential reference, rotation/expiry, webhook endpoints, quotas and failure state.
- Secrets remain in secret storage, never Admin database/export.
- Connection health and revocation.

### Acceptance
- No plaintext secret in repository, Admin projection, logs or exports.
- Disabled/revoked integrations fail closed.
- Every integration has explicit data/authority boundary.

### AUDIT_CLOSURE
External services are governed capabilities, not scattered credentials and ad-hoc API calls.

## AO-19 — API/Webhook Operations Console

**Status:** NOT_STARTED
**Depends on:** AO-18
**Priority:** P1 Infrastructure
### Work
- Inventory AXIGNAL public/internal APIs and webhooks.
- Health, latency, error rate, quota/rate-limit and schema/version visibility.
- Replay-safe webhook inbox where required.
- Bounded retry/dead-letter operations.
- No arbitrary request console with unrestricted credentials.

### Acceptance
- Operator can diagnose API/webhook failures from Admin.
- Replay cannot duplicate financial/entitlement side effects.
- Sensitive payloads minimized/redacted.

### AUDIT_CLOSURE
Integration failures become operable without SSH/database archaeology.
# PHASE F — FINANCE, ACCOUNTING AND FISCAL CONTROL

## AO-20 — Invoice and Financial Document Domain

**Status:** NOT_STARTED
**Depends on:** AO-10
**Priority:** P0 Finance

### Work
- Internal invoice/payment/refund/credit-note references and immutable lifecycle.
- Link commercial billing events to accounting/fiscal adapters.
- Preserve document IDs, periods, currency, tax basis and source-provider references.
- Do not make Admin's display of an invoice the legal/fiscal system of record unless explicitly authorized later.

### Acceptance
- Stripe payment and invoice/accounting document are distinct records.
- Corrections/credit notes preserve prior history.
- Financial exports reconcile to source documents.

### AUDIT_CLOSURE
AXIGNAL can explain revenue documents end-to-end rather than relying on Stripe UI alone.

## AO-21 — Accounting Adapter and Reconciliation

**Status:** NOT_STARTED
**Depends on:** AO-20, AO-18
**Priority:** P0 Finance
### Work
- Choose/integrate an accounting system/provider or explicitly authorize an AXIGNAL-owned ledger only through a separate architecture decision.
- Chart-of-accounts mapping, income/expense/cost categories and reconciliation references.
- Stripe/payment-processor fees, refunds and settlement reconciliation.
- Import business expenses and infrastructure/provider costs with provenance.
- Period close state and discrepancy queue.

### Acceptance
- Admin can reconcile billed → paid → settled → accounted amounts.
- Unknown/unmatched transactions remain unresolved, never auto-balanced.
- Accounting mutations are audited and separate from AXIGLAND.

### AUDIT_CLOSURE
Financial reporting has a reconciled source trail rather than manually combined dashboards.

## AO-22 — VeriFactu / SIF Compliance Architecture Decision

**Status:** NOT_STARTED
**Depends on:** AO-20, AO-21
**Priority:** P0 Compliance
### Work
- Reconcile current official AEAT VeriFactu/SIF technical and legal requirements at implementation time.
- Default evaluation: integrate a compliant external SIF/VeriFactu provider through an adapter rather than silently making AXIGNAL itself regulated invoicing software.
- Compare provider route vs own-SIF route on control, cost, reliability and compliance burden.
- If own SIF is selected, require a separate ADR/compliance project covering integrity/traceability, required records, hashes, invoice requirements, AEAT communication/testing, retention and producer obligations as then applicable.
- Keep tax/compliance rules versioned by effective date.

### Acceptance
- Explicit documented build-vs-integrate decision.
- No production invoice path claims VeriFactu compliance without verified evidence.
- Test/compliance evidence recorded before live enablement.

### AUDIT_CLOSURE
A future auditor cannot find an improvised or falsely compliant fiscal subsystem.

## AO-23 — Tax / VAT / AEAT Operations

**Status:** NOT_STARTED
**Depends on:** AO-21, AO-22
**Priority:** P0 Compliance
### Work
- VAT/tax-period operational views based on accounting/fiscal-system records.
- Filing calendar, obligations, statuses, source documents and reconciliation checks.
- Export/preparation views for accountant/advisor.
- No automatic tax/legal conclusion from an LLM.
- Tax rules/configuration versioned by jurisdiction/effective date.

### Acceptance
- Admin shows due/complete/unknown states with evidence.
- Missing documentation cannot render a filing as complete.
- Human/accountant approval gates where required.

### AUDIT_CLOSURE
Tax operations are inspectable and controlled without turning AXENT into a tax authority.

# PHASE G — PREMIUM INTELLIGENCE / FRONTIER ADVISOR OPERATIONS

## AO-24 — Governed KPI & Measurement Registry

**Status:** NOT_STARTED
**Depends on:** AO-03, AO-05, AO-06
**Priority:** P1 Advisory
### Work
Define versioned measures for advisory/report use:
- question/decision served;
- formula/coding rule;
- source/instrument;
- scope/subject;
- observation window/freshness/sample;
- uncertainty and compatibility;
- interpretation limits and evaluation cases.

### Acceptance
- Model does not choose arbitrary KPI authority.
- Historical comparison rejects incompatible instrument definitions.
- Missing pillar renders NOT_MEASURED/INSUFFICIENT rather than zero.

### AUDIT_CLOSURE
Premium reports are measurement-governed rather than polished model opinion.

## AO-25 — Founder / Frontier Advisor Workbench

**Status:** NOT_STARTED
**Depends on:** AO-02, AO-24
**Priority:** P1 Advisory
### Work
Internal staff-only flow:
1. select authorized customer/Xeed;
2. choose period and versioned playbooks/KPIs;
3. inspect governed observations/history and gaps;
4. run deterministic measures first;
5. bounded model-assisted synthesis;
6. inspect evidence/uncertainty/counter-hypotheses;
7. human edit/approval;
8. versioned delivery/correction history.

### Acceptance
- Workbench cannot write AXIGLAND.
- Human edits are private advisory artifacts with authorship/version.
- Frontier provider has bounded typed input and no unrestricted database access.

### AUDIT_CLOSURE
Premium advisory reuses AXIGNAL's governed substrate instead of creating a second Brain.

## AO-26 — Premium Advisory Commercial Operations

**Status:** NOT_STARTED
**Depends on:** AO-11, AO-25
**Priority:** P1 Advisory
### Work
- Define actual package, cadence, Xeed allowance, meetings, response boundaries and human-hour cap.
- Quote/contract/subscription linkage through CRM/billing.
- Measure advisor time, variable cost, corrections, renewals and WTP.
- Separate advisory utility from epistemic correctness.

### Acceptance
- €995 or any launch price remains marked hypothesis until real paid evidence exists.
- Service cannot promise improved AXIGNAL measurement for paying.
- Advisor capacity/gross contribution visible.

### AUDIT_CLOSURE
Premium advisory has measured commercial and delivery economics rather than only a proposal.

# PHASE H — PORTABILITY AND AGENT OPERATIONS

## AO-27 — Admin Exports, Snapshots and Internal Admin MCP

**Status:** NOT_STARTED
**Depends on:** AO-03, AO-01
**Priority:** P1
### Work
- Versioned JSON/CSV/Markdown Admin snapshots.
- Schema/fingerprint/period/source metadata.
- Internal Admin MCP read-only by default with explicit scopes.
- `AGENT_SAFE` projections exclude PII, billing details, secrets and unnecessary private content.

### Acceptance
- Human UI/export/MCP read the same semantic Admin Projection.
- Export cannot bypass RBAC.
- Agent output cannot mutate Admin or AXIGLAND.

### AUDIT_CLOSURE
Automation can inspect Admin safely without becoming privileged truth authority.
# PHASE I — PRODUCTION HARDENING AND BUSINESS PROOF

## AO-28 — Admin Internal E2E

**Status:** NOT_STARTED
**Depends on:** AO-04 through AO-27 as applicable
**Priority:** P0

### Work
Execute one realistic internal operating path:

```text
acquisition source
→ CRM prospect
→ accepted customer/account
→ Stripe test/live subscription
→ Xeed entitlement
→ product use
→ Admin revenue/economics projection
→ invoice/accounting reference
→ governed fiscal status
→ support/governance/audit trace
```

plus an advisory path when implemented.
### Acceptance
- Every step uses owning production modules, not synthetic dashboard fixtures.
- Cross-domain references are traceable without merging authorities.
- Reload/restart continuity verified.
- Negative paths cover denied role, failed payment, missing accounting match and unavailable fiscal state.

### AUDIT_CLOSURE
Admin proves a real business operating loop, not disconnected panels.

## AO-29 — Admin Production Deployment, Security and Recovery

**Status:** NOT_STARTED
**Depends on:** AO-28
**Priority:** P0

### Work
- Deploy Admin behind staff-only authentication and controls appropriate to risk.
- Backup/recovery for Admin operational state.
- Secret rotation and incident playbook.
- Audit-log retention and tamper-evidence appropriate to chosen stores.
- Browser E2E for privileged/denied roles.
- Rollback without deleting financial/audit history.

### Acceptance
- Subscriber/public cannot discover or invoke privileged data/actions.
- Restore test succeeds.
- Critical command authorization/rollback paths verified.

### AUDIT_CLOSURE
Admin is a secured production system, not merely an internal route.
## AO-30 — Flywheel & Business Validation Observatory

**Status:** NOT_STARTED
**Depends on:** AO-11, AO-17, AO-26, AO-29
**Priority:** P0 Business

### Work
Build an evidence-backed view of:
- marginal cost vs reuse;
- time-to-first-material-Xignal;
- active-Xeed retention;
- free→paid conversion;
- additional-Xeed expansion;
- premium-advisory conversion/renewal;
- acquisition and human-review cost;
- gross contribution by cohort;
- WTP evidence and reasons for decline/cancel;
- FR-27 evidence ingestion where protocol permits.

### Acceptance
- Hypothesis vs measured evidence visually distinct.
- No “moat score” or universal health score.
- FR-27 can only move READY→DONE from qualifying empirical evidence, not Admin inference.

### AUDIT_CLOSURE
The next Frontier audit can judge AXIGNAL's business/flywheel from real cohort evidence rather than architecture or founder intuition alone.
## AO-31 — Deep Frontier Re-Audit Package

**Status:** NOT_STARTED
**Depends on:** AO-00 through AO-30
**Priority:** P0 Governance

### Goal
Request a new Frontier Advisor audit deeper than FR-31: product, architecture, security, Admin, business model, acquisition, unit economics, moat, flywheel, marketing, advisory, finance/fiscal boundaries and production UX.

### Work
- Freeze exact audit-base SHA(s) and deployed runtime/landing/Admin versions.
- Produce task matrix AO-00→AO-30 with primary evidence.
- Include FR-00→FR-31 history only as background; auditor evaluates current state fresh.
- Provide production E2E, security/RBAC, Stripe/billing, accounting/fiscal, acquisition/cohort, economics/flywheel and advisory evidence.
- Include every remaining UNKNOWN, DEFERRED, failed experiment and negative commercial result.
- Ask for independent reproduction and deeper red-team analysis without target score, pass/fail outcome or requested verdict.

### Acceptance
- Neutral audit request exists independently of implementation branch.
- No missing known blocker is hidden.
- CI/governance green on canonical audit base.
- Production versions and rollback evidence known.

### AUDIT_CLOSURE
A deeper Frontier Advisor audit can evaluate AXIGNAL as both an economic-intelligence product and an operating business from current evidence rather than proposals.
# 8. Recommended execution sequence

```text
AO-00
  ↓
AO-01 → AO-02
  ↓
AO-03
  ├→ AO-04
  ├→ AO-05
  ├→ AO-06
  └→ AO-07
       ↓
AO-08 → AO-09 → AO-10 → AO-11
   │
   └→ AO-12 → AO-14 → AO-15 → AO-16 → AO-17
            ↘ AO-13

AO-18 → AO-19
   ├→ AO-10
   ├→ AO-13
   ├→ AO-14
   ├→ AO-16
   └→ AO-21

AO-20 → AO-21 → AO-22 → AO-23
AO-24 → AO-25 → AO-26
AO-27
  ↓
AO-28 → AO-29 → AO-30 → AO-31
```

Parallelism is allowed only where dependencies and production risk are genuinely independent. Business-evidence tasks may continue collecting evidence while engineering proceeds, but they must not be declared DONE from synthetic data.
# 9. What this roadmap deliberately does not authorize

- turning AXIGLAND into an editable CRM/company profile;
- treating CRM prospect/customer state as public economic truth;
- ingesting private GSC/analytics/Stripe/accounting/tax data into shared AXIGLAND by default;
- arbitrary Admin SQL consoles or unrestricted agent database access;
- automatic canonical writes from Admin, AXENT, an LLM or a payment event;
- opaque universal company/customer/moat/quality scores;
- marketing automation that changes product truth or creates fake demand evidence;
- building a proprietary SIF/VeriFactu implementation without the explicit AO-22 architecture/compliance decision;
- declaring pricing, conversion, retention, unit economics or moat validated from synthetic/internal test data;
- exposing the founder/advisor workbench to subscribers as a normal product feature.

# 10. Definition of roadmap completion

This roadmap is complete only when all tasks have closure evidence and the following outcomes are true:
```text
ADMIN_V0_2_DOCTRINE                         DONE
ADMIN_RBAC_SECURITY                         VERIFIED
ADMIN_SHELL                                 VERIFIED_E2E
ADMIN_PROJECTION_RUNTIME                    DEPLOYED
COMMAND_CENTER                              VERIFIED
XEED_AXIGLAND_OBSERVABILITY                 VERIFIED
BRAIN_PROVIDER_OBSERVABILITY                VERIFIED
GOVERNANCE_POLICY_AUDIT                     VERIFIED
INTERNAL_CRM                                VERIFIED
CUSTOMER_SUBSCRIPTION_OPS                   VERIFIED
STRIPE_BILLING                              VERIFIED
UNIT_ECONOMICS                              MEASURED
GSC_ANALYTICS_MARKETING                     VERIFIED
FREE_BRIEF_FUNNEL                           PILOTED_WITH_REAL_USERS
INTEGRATIONS_API_OPS                        VERIFIED
FINANCE_ACCOUNTING                          RECONCILED
VERIFACTU_FISCAL                            COMPLIANCE_VERIFIED
FRONTIER_ADVISOR_WORKBENCH                  VERIFIED
ADMIN_MCP_EXPORTS                           VERIFIED
ADMIN_PRODUCTION_E2E                        VERIFIED
FLYWHEEL_BUSINESS_EVIDENCE                  MEASURED
DEEP_FRONTIER_REAUDIT_REQUEST               OPEN
```

A green CI build, a dashboard screenshot, a synthetic cohort or a Stripe test payment alone is not roadmap completion.
