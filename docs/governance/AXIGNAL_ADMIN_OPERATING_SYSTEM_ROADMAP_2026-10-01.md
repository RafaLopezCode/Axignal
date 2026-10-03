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

**CURRENT_TASK = AO-22**

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

**Status:** DONE
**Depends on:** AO-00
**Priority:** P0

### Closure evidence (2026-10-01)
- ADR-0056 accepted: separate provider-neutral Admin identity/RBAC/session authority; subscriber `PrincipalTenantMembership` remains unchanged.
- `domain/admin_access/` implements 8 roles, explicit scopes, assurance/risk classes, secret-free authorization grants and Admin-only identity types.
- `application/admin_access/` implements an `AdminAuthenticationPort`, fail-closed session issuance/authorization, 8h default/12h max sessions, 15-minute fresh step-up, role revocation on every authorization, founder bootstrap/quorum rules and dual approval for critical actions.
- `pipeline/admin_access/` implements SQLite persistence with raw-token exclusion, hashed bearer credentials, session revocations and append-sequenced immutable privilege history.
- `tools/runtime/admin_access.py` provides the HTTP bearer guard future Admin routes must use; no Admin route is exposed by AO-01 itself.
- `AGENT_SAFE_READER` has exactly `admin:agent-safe:read` and no private customer/finance/system scope.
- Focused AO-01 security + contracts: 34 PASS.
- Full pytest: 731 PASS.
- Ruff format/check: PASS.
- mypy: PASS (146 source files).

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

**Status:** DONE
**Depends on:** AO-01
**Priority:** P0 UX

### Closure evidence (2026-10-01)
- ADR-0057 accepted: Admin reuses the AXIGNAL shell grammar and server-authorized navigation; client-side hiding is never authorization.
- `application/admin_shell/` provides the canonical 12-domain, scope-derived Admin navigation projection.
- `apps/web/admin/` implements the privileged left rail ? central operating surface ? AXENT shell using the existing AXIGNAL Design System/subscriber shell language.
- Admin operational/private state is explicitly distinguished from FAXT/Xignal/AXIGLAND truth.
- `/admin` and `/admin/<domain>` are server-protected: uncomposed Admin security plane ? 404; missing/invalid Admin credential ? 401; known denied domain ? 403; unknown domain ? 404.
- Rendered Admin HTML is `no-store`, CSP-protected and receives only a secret-free bootstrap projection; raw Admin tokens are never rendered.
- Role-limited navigation verified: SUPPORT sees Customers/CRM + Xeeds and cannot open Finance/Fiscal.
- Chrome desktop QA PASS: 1440?900 preserves left rail, central surface and AXENT; all 12 founder domains visible.
- Chrome mobile QA PASS: 390?844 has no horizontal page overflow, compact horizontally scrollable domain rail and reachable in-flow AXENT.
- Chrome interaction QA PASS: keyboard ArrowDown focus navigation and `/admin/finance-fiscal` deep-link context.
- Focused AO-02 + AO-01 + FR-29 contracts: 18 PASS.
- Full pytest: 735 PASS.
- Ruff format/check: PASS.
- mypy: PASS (148 source files).
- Architecture Guard: PASS.

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

**Status:** DONE
**Depends on:** AO-00, AO-01
**Priority:** P0

### Closure evidence (2026-10-01)
- ADR-0058 accepted: metadata-first append-oriented Admin observability runtime; no global event-sourcing authority.
- `domain/admin_observability/` implements typed Admin record classes, temporal/completeness/privacy envelope semantics and versioned projection snapshots.
- `application/admin_observability/` implements idempotent ingest, fail-closed conflicting replay, correction-by-supersession, historical `as_of` reconstruction and deterministic projection fingerprints.
- `pipeline/admin_observability/` implements durable SQLite record/snapshot persistence with append sequence independent of random IDs.
- P0-ADMIN-01 C01–C04 are now partially implemented by runtime; T011 marked implemented by AO-03.
- Exact replay cannot double-count; later corrections do not rewrite earlier historical projections; correction cannot change owning domain or record type.
- Logs, traces, Admin metrics, operational events and economic observations remain distinct record classes.
- Focused AO-03 + roadmap contracts: 13 PASS.
- Full pytest: 744 PASS.
- Ruff format/check: PASS.
- mypy: PASS (154 source files).
- Architecture Guard: PASS.

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

**Status:** DONE
**Depends on:** AO-03
**Priority:** P0

### Closure evidence (2026-10-01)
- `domain/admin_command_center/` defines versioned metric definitions/readouts with explicit unit, source projection, default window, methodology and completeness semantics.
- `application/admin_command_center/` composes 16 executive metrics exclusively from AO-03 `AdminProjectionSnapshot` read models; it does not query owning-domain tables or create a second KPI authority.
- Missing source projections and incomplete values remain `UNKNOWN`/`UNAVAILABLE`; numeric zero cannot be smuggled through an incomplete source. `PARTIAL` values preserve explicit exclusion/unknown reasons and lineage.
- Temporal comparison is fail-closed: methodology changes become `METHOD_CHANGED`, currency changes become `CURRENCY_CHANGED`, and future `as_of` snapshots are excluded from current executive state.
- `/admin` / `/admin/command-center` remains behind AO-01 server authorization and receives a secret-free Command Center bootstrap projection.
- Admin UI groups Business, Xeeds, System, AXIGLAND quality, Attention and Flywheel state and exposes `Why is this number here?` with definition, window, period, method, source projection/types/record IDs and unknown reason.
- Chrome desktop QA PASS at 1440×900: left rail, executive surface and AXENT remain coherent; 16 metric cards render and no horizontal overflow was observed (`scrollWidth == clientWidth`).
- Chrome compact/mobile-layout QA PASS: one-column metric layout activates below 700 px; headless Chrome's effective minimum viewport was 491 px and verified `scrollWidth == clientWidth` with all 16 cards rendered.
- Focused AO-04 tests/contracts: 10 PASS.
- Full pytest: 754 PASS.
- Ruff format/check: PASS.
- mypy: PASS (158 source files).
- Architecture Guard: PASS.
- `axignal-governance`: PASS in clean detached worktree at implementation commit `60374ef`.

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

**Status:** DONE
**Depends on:** AO-03
**Priority:** P0

### Closure evidence (2026-10-01)
- `domain/admin_xeed_observatory/` and `application/admin_xeed_observatory/` implement a deterministic AO-05 projection over governed Learning Memory plus AO-03 Admin envelopes; no route-local or canonical shadow store was introduced.
- Xeed diagnostics expose lifecycle, currentness, observation coverage, first activity/first useful Xignal timing, failed/partial execution, reuse/new observations, Xignals, canonical-admission events, direct cost coverage and separate shared/triggered/revenue attribution states.
- Missing lifecycle/currentness/coverage/shared/triggered/revenue owner evidence remains `UNKNOWN`; Learning Memory activity never fabricates those owning-domain states and missing cost never becomes free.
- Reuse is measured independently from newly added observations and canonical-admission events. `observations_reused` never counts as AXIGLAND growth, and learning-event admissions are explicitly not presented as current FAXT cardinality.
- AXIGLAND observability exposes explicit owner-record states for growth, currentness, provenance, contradictions and identity resolution. Future-dated learning/Admin evidence is excluded from the current `as_of` projection.
- `SqliteLearningMemory.all_events()` provides the chronological governed ledger required by the Admin read model without changing Learning Memory authority.
- `/admin/xeeds` and `/admin/axigland-quality` remain behind AO-01 server authorization and receive a secret-free AO-05 bootstrap. Per-Xeed and AXIGLAND lineage is inspectable from learning event IDs and Admin source-record IDs.
- Browser QA PASS: Xeeds and AXIGLAND Quality render in the existing privileged AXIGNAL shell at desktop width; the Xeed view visibly distinguishes known direct-cost evidence from UNKNOWN shared/triggered/revenue attribution.
- Compact-layout QA PASS at Chrome headless effective 491 px: one-column responsive layout, one governed Xeed card rendered and `scrollWidth == clientWidth`.
- Focused AO-05 semantic/contracts: 10 PASS; AO-05 + AO-02 shell regression set: 14 PASS.
- Full pytest: 764 PASS.
- Ruff format/check: PASS.
- mypy: PASS (162 source files).
- Architecture Guard: PASS.
- `axignal-governance`: PASS in clean detached worktree at implementation commit `310759f`.
- Production runtime deployment PASS: canonical functional merge `d3081d59c336fbf0cbf677b2952a877e22db93f8` replaced runtime `cb89cfe391a0ce6ba93bfc5e5b8a942795897769` through a new immutable `/srv/axignal/runtime/releases/<sha>` target; `/var/lib/axignal/runtime` persistence stayed outside the release and rollback preserved the prior release plus `/etc/axignal/runtime.env.pre-ao05-20261001T210646Z`.
- Production health PASS on loopback and external `/healthz`: exact AO-05 runtime SHA, `status=ok`, Observation/Learning stores healthy and public write surface closed; `runtimez` remained loopback-only with `1` Observation and `6` Learning events.
- Production AO-05 data-path PASS: the real persisted `xeed:production-first-proof:1` projected `6` Learning events, `1` newly added observation and `1` emitted Xignal. Lifecycle/currentness/coverage/shared/triggered/revenue and AXIGLAND owner-state dimensions remained `UNKNOWN/PARTIAL` where no authoritative AO-03 owner records exist rather than being fabricated.
- Production render proof PASS: the privileged AO-05 server render over the real production stores contained the Admin shell, `xeedObservatory` bootstrap, production Xeed, Learning lineage and `ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH` boundary.
- Production Admin HTTP exposure remains deliberately CLOSED: the concrete external Admin authentication provider/browser session transport is still unconfigured, so the runtime returns `404` for `/admin/xeeds`; public `https://axignal.com/admin/xeeds` resolves the public landing and does not expose the Admin shell. AO-05 deployment therefore does not weaken AO-01 fail-closed behavior or manufacture an unauthenticated operator backdoor.

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

**Status:** DONE
**Depends on:** AO-03
**Priority:** P0

### Closure evidence (2026-10-01)
- `domain/admin_brain_observatory/` and `application/admin_brain_observatory/` implement a deterministic provider-neutral AO-06 read model over governed Learning Memory plus AO-03 Admin envelopes. No cognitive shadow store or second Brain was introduced.
- C06/C07/C09/C10 semantics are preserved: Knowledge Frontier, research controls, provider/model usage, structured-evaluator observations, cost/latency, failure/abstention and unresolved gaps remain distinct from canonical economic truth.
- Provider slices are comparable only when `operation_class + policy_id + policy_version` match through an inspectable `comparison_key`; AO-06 creates no global provider score, rank, winner or hidden quality metric.
- Unknown provider identity, usage, price, latency, retry, abstention, budget or frontier state remains `UNKNOWN/PARTIAL`; missing cost is never free and missing usage is never zero activity.
- Learning Memory stop events with exact governed `ExecutionStopReason` values feed routing/stop/budget/no-progress/retry observability directly, preserving LearningEvent lineage instead of duplicating the same operational fact into Admin envelopes.
- Prime execution now propagates provider/provider-version from semantic extraction and provider-neutral `PrimeMechanismResult` into real Learning Events. Provider identity remains mutable execution policy and never establishes FAXT, Xignal or canonical correctness.
- Commercial/customer Admin records are outside the AO-06 cognitive projection and cannot relabel model correctness, abstention or provider performance.
- `/admin/axent-brain` uses the existing AO-01 authorized Admin shell and receives a secret-free `brainObservatory` bootstrap with Learning/Admin lineage.
- Browser QA PASS: desktop 1440 px renders execution evidence, research-control/Knowledge-Frontier state and two compatible provider slices; compact effective 491 px renders two provider cards with `scrollWidth == clientWidth`.
- Focused AO-06 + Prime + AO-02 + roadmap regression set: 25 PASS.
- Full pytest: 774 PASS.
- Ruff format/check: PASS.
- mypy: PASS (166 source files).
- Node Admin JS syntax: PASS.
- Architecture Guard: PASS.
- Production runtime deployment PASS: canonical merge `16b7d053ed0972899aa83869a60f40e4258b560a` replaced runtime `57f5f9c092d08b811912113a4d2462fb62069ec6` through a new immutable `/srv/axignal/runtime/releases/<sha>` target; `/var/lib/axignal/runtime` persistence remained outside the release and rollback preserved the prior release plus `/etc/axignal/runtime.env.pre-ao06-20261001T214253Z`.
- Production health PASS on loopback and external `/healthz`: exact AO-06 runtime SHA, `status=ok`, Observation/Learning persistence healthy and public write surface closed; production retained `1` Observation and `6` Learning events.
- Production AO-06 data-path PASS over real persisted evidence: `6` deterministic Learning events, `0` structured-evaluator events, `0` adaptive-research events, `0` provider-attributed events and `0` provider slices. Research objective/routing/stop/budget/no-progress/retry/abstention/Knowledge Frontier/unresolved-gap states remain `UNKNOWN` because production has no authoritative records for them; cost and latency coverage remain `PARTIAL` rather than fabricated complete telemetry.
- Production render proof PASS: the privileged server render over real production stores contains the AO-06 `brainObservatory`, `axent-brain` slug, real FR-30 Learning lineage and `ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH` boundary.
- Production Admin HTTP exposure remains deliberately CLOSED: the concrete external Admin authentication provider/browser session transport is still unconfigured, so loopback `/admin/axent-brain` returns `404`; public `https://axignal.com/admin/axent-brain` remains the public landing rather than exposing the Admin shell.

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

**Status:** DONE
**Depends on:** AO-01, AO-03
**Priority:** P0

### Closure evidence (2026-10-02)
- Reuses the existing FR-20 append-only `ActivePolicyStore` as policy authority; AO-07 does not create a second promotion/rollback mechanism or a shadow policy truth.
- Seven governed policy families are inspectable: execution budget, source acquisition, temporal currentness, retention, Prime/provider routing, canonical admission and alerting. Missing active policy evidence remains `UNKNOWN`.
- Policy-decision history projects actor, before policy/version, after policy/version, approval rationale and effective time directly from immutable FR-20 decisions.
- `AdminGovernanceService` is a bounded command router: it requires `admin:governance:manage` plus STEP_UP, requires an AO-01 dual-approval reference for CRITICAL commands, invokes the owning-service handler, then appends immutable result audit with actor, session, reason, scope, before/after refs and approval ref.
- Admin command targets never include a writable canonical store. `AXIGLAND_CANONICAL` and `FAXT_STORE` attempts are rejected before handler invocation as `UNSUPPORTED_CANONICAL_WRITE_TARGET` and retained in the immutable governance audit.
- AO-07 alert classes cover unsupported writes, stale coverage, source failure, provider failure, cost spike, payment failure, security incident and governance drift. Deterministically observable classes derive from Learning Memory/AO-03/audit; cost-spike and governance-drift remain `UNKNOWN` until explicit alert-policy/owner evidence exists rather than becoming false zeroes.
- `pipeline/admin_governance/SqliteAdminGovernanceAuditStore` is append-only/idempotent and rejects reuse of an audit ID with changed content.
- Runtime composition persists policy governance and privileged-action audit outside UI state and projects them only for the authorized `/admin/governance` domain.
- Governance UI exposes invariants, versioned policy registry, governed policy changes, alerts, privileged action audit and lineage without granting canonical-write authority.
- Browser QA PASS: desktop 1440 px and compact 491 px render Governance correctly; compact DOM has `scrollWidth == clientWidth`, seven policy cards and eight alert classes.
- Focused AO-07 + AO-02 regression set: 14 PASS.
- Full pytest: 784 PASS.
- Ruff format/check: PASS.
- mypy: PASS (172 source files).
- Node Admin JS syntax: PASS.
- Architecture Guard: PASS.
- Production runtime deployment PASS: canonical merge `efaa17a355ecd673517e38805484ba02a9bc6e02` replaced runtime `3fb818e6ef9703331b0ae6f054cacd4a95638c2c` through a new immutable release; rollback preserved the prior release and `/etc/axignal/runtime.env.pre-ao07-20261001T221018Z`.
- Production health PASS on loopback and external `/healthz`: exact AO-07 SHA, `status=ok`, Observation/Learning persistence healthy and public write surface closed; existing runtime evidence remains `6` Learning events and `1` Observation.
- Production governance persistence PASS: `policy-governance.sqlite3` and `admin-governance-audit.sqlite3` were created under persistent `/var/lib/axignal/runtime`, outside the immutable release tree.
- Production AO-07 projection PASS over real stores: seven policy families, eight alert classes, `0` active policies, `0` policy changes, `0` privileged audit records and `0` `UNSUPPORTED_CANONICAL_WRITE_TARGET` events. Policy state therefore remains `UNKNOWN` rather than defaulting a version.
- Production alerts preserve evidence boundaries: unsupported writes/source failures/provider failures/stale coverage/security incidents/payment failures are observed zero; `COST_SPIKE` and `GOVERNANCE_DRIFT` remain `UNKNOWN` because no explicit owner/policy signal exists.
- Production privileged render PASS: real production stores produce a secret-free `governance` bootstrap with `currentSlug=governance`, unsupported-write count zero, UNKNOWN policy state and the Admin/AXIGLAND authority boundary.
- Production Admin HTTP exposure remains deliberately CLOSED: loopback `/admin/governance` returns `404` while public `https://axignal.com/admin/governance` serves the public landing. No auth bypass or privileged write endpoint was added.

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

**Status:** DONE
**Depends on:** AO-00, AO-01, AO-03
**Priority:** P0 Business

### Closure evidence (2026-10-02)
- `domain/admin_commercial/`, `application/admin_commercial/` and `pipeline/admin_commercial/` implement AXIGNAL's private first-party commercial authority without creating a forbidden `crm` package or weakening Architecture Guard.
- The owning domain models explicit Prospect, Company, Contact, Opportunity, Deal, Note and Follow-up Task records with separate lifecycle states, acquisition source, consent basis, first-party provenance and immutable action audit.
- Prospect lifecycle is explicit (`NEW / QUALIFIED / DISQUALIFIED / CONVERTED`); conversion requires an explicit internal Company reference. Opportunity, Deal and Follow-up lifecycles preserve before/after audit and operator reason.
- Commercial provenance distinguishes `COMMERCIAL_CLAIM`, `USER_PROVIDED` and `PUBLIC_OBSERVATION_REFERENCE`; public-observation linkage is an explicit Organization ID reference plus mapping reason only, never semantic identity equivalence.
- Account conversion linkage is an external AO-09 account-ID reference only. AO-08 does not implement or become account/subscription authority.
- The application layer requires AO-01 `admin:commercial:write` for commercial mutation and `admin:customers:write` for account linkage. SUPPORT customer-read scope receives a reduced projection with no opportunity/note/audit/origin breakdown.
- Contact email/phone remain in the private owning store and are excluded from the Admin bootstrap and export. Commercial export is classified `PRIVATE_FIRST_PARTY`, requires `admin:commercial:read`, and declares `piiIncluded=false`.
- Contract evidence proves an AO-03 AXIGLAND Organization observation cannot create Prospect, Company, Contact, Opportunity or Deal records and cannot append commercial audit. AO-08 imports no Organization/FAXT/Relationship/Xignal/EvidenceAdmission writer.
- Runtime composition persists `admin-commercial.sqlite3` independently from AXIGLAND and projects it only for the authorized `customers-crm` Admin domain.
- Browser QA PASS: desktop 1440 px and compact 491 px render Customers / CRM, one full commercial scenario and explicit authority boundaries; compact DOM has `scrollWidth == clientWidth`, one company card and no visible contact PII.
- Focused AO-08 semantic/contracts + roadmap + AO-02 regression: 20 PASS.
- Full pytest after rebase onto current main: 804 PASS.
- Ruff format/check: PASS.
- mypy: PASS (178 source files).
- Node Admin JS syntax: PASS.
- Architecture Guard: PASS.
- Production runtime deployment PASS: canonical merge `f37e0c7b0c802e030d92a9f0da6519e6f11d4a5a` replaced runtime `c3435db728d1b6bbbd22f53185d8bc525770228e` through a new immutable release; rollback preserves the prior release plus `/etc/axignal/runtime.env.pre-ao08-20261002T000041Z`.
- Production health PASS on exact AO-08 SHA with Observation/Learning persistence healthy and public write surface closed.
- Production commercial persistence PASS: `/var/lib/axignal/runtime/admin-commercial.sqlite3` is created outside the immutable release tree.
- Production authority-boundary proof PASS over real stores: existing `1` Observation and `6` Learning events coexist with `0` Prospect, Company, Contact, Opportunity, Deal, Note, Task and commercial-audit records. Existing AXIGLAND/Learning evidence therefore does not silently create commercial relationships.
- Production privileged render PASS: `customers-crm` projects `PRIVATE_FIRST_PARTY`, `piiVisible=false`, all commercial counts zero and `ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH`.
- Production Admin HTTP exposure remains deliberately CLOSED under AO-01 until a concrete external Admin authentication/session transport is configured; no auth bypass was introduced for AO-08.

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

**Status:** DONE
**Depends on:** AO-08
**Priority:** P0 Business

### Closure evidence (2026-10-02)
- `domain/admin_customer_accounts/`, `application/admin_customer_accounts/` and `pipeline/admin_customer_accounts/` implement first-party AXIGNAL Account, AccountUser, Plan, Subscription and Xeed-entitlement authority as a separate operational domain from Organization/AXIGLAND.
- Account state is append-only event-sourced. Current state is reconstructed deterministically by replay of signup, user, subscription, plan-capacity, Xeed entitlement/revocation, suspend/reactivate/cancel, funnel, support and claim-review events.
- The current self-service plan is versioned as `SELF_SERVICE_V1 / MASTER-27-v1`: one included Xeed, current pricing hypothesis €9.95 base + €4.95 per additional Xeed. The model marks this as a pricing hypothesis; it is not billing evidence.
- Payment verification is `EXTERNAL_PENDING` and MRR remains `UNKNOWN/null` until AO-10. AO-09 rejects attempts to write funnel stage `PAID`, preserving billing authority for the Stripe integration.
- `EntitledXeedReader` adds a second server-side authorization gate after Principal/Tenant/Xeed ownership. Missing account, inactive account/subscription or absent Xeed entitlement fails closed even when tenant membership is valid.
- Xeed capacity is enforced deterministically; expansion/downgrade cannot invalidate active entitlements. Suspension blocks service access, reactivation restores eligible access and cancellation clears active Xeed entitlements.
- Customer 360 projects first-party service state, lifecycle, Xeed capacity/usage, funnel stages, support/correction/claim-review references and event lineage without exposing individual AccountUser principal IDs.
- Product-funnel stages are versioned observations. Exact activation semantics remain explicitly calibratable; no opaque activation/WOW score was introduced.
- Cohort read models are derived from signup month and replayed account state; measured revenue retention remains deferred to AO-10/AO-11.
- Runtime persists `admin-customer-accounts.sqlite3` independently from AXIGLAND, CRM and billing-provider state. Existing AXIGLAND/Admin observations cannot create Account or entitlement events.
- Admin Customers / CRM now presents AO-09 Account/Subscription authority separately above AO-08 Internal CRM. Browser QA PASS on desktop and compact 491 px; compact DOM has `scrollWidth == clientWidth`, one account card and MRR visibly UNKNOWN.
- Focused AO-09 + AO-08/AO-02/roadmap regressions: 27 PASS.
- Full pytest: 818 PASS.
- Ruff format/check: PASS.
- mypy: PASS (184 source files).
- Node Admin JS syntax: PASS.
- Production runtime deployment PASS: canonical merge `44f9b264a013b8d87d003ca21bf61c060c4fb383` replaced runtime `2098d2bc88ab641af5b474e31558c9aeccf7b02a` through a new immutable release; rollback preserves the prior release plus `/etc/axignal/runtime.env.pre-ao09-20261002T054629Z`.
- Production health PASS on exact AO-09 SHA with Observation/Learning persistence healthy and public write surface closed.
- Production account persistence PASS: `/var/lib/axignal/runtime/admin-customer-accounts.sqlite3` is created outside the immutable release tree.
- Production authority-boundary proof PASS over real stores: existing `1` Observation and `6` Learning events coexist with `0` customer-account events, `0` Accounts and `0` Xeed entitlements. Existing AXIGLAND/Learning evidence therefore does not silently create customer service state.
- Production Customer Operations projection PASS: `accountCount=0`, `totalEntitledXeeds=0`, `mrrEur=null`, `paymentAuthority=AO10_PENDING`.
- Production privileged render PASS: `customers-crm` contains the AO-09 customer projection, zero accounts, MRR UNKNOWN/AO10_PENDING and `CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE`.
- Production Admin HTTP exposure remains deliberately CLOSED under AO-01 until a concrete external Admin authentication/session transport is configured; no auth bypass was introduced for AO-09.
- Payment collection itself is NOT claimed by AO-09; AO-10 remains the authority for Stripe/payment verification and real revenue state.

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

**Status:** BLOCKED
**Depends on:** AO-09, AO-18
**Priority:** P0 Revenue

### Implementation / verification evidence
- Provider-neutral AO-10 billing domain/application/persistence is implemented with explicit AXIGNAL Account ↔ Stripe Customer ↔ Stripe Subscription mapping. Stripe Connect is not used.
- Canonical quantity contract is enforced: one base subscription quantity plus `max(0, xeed_capacity - 1)` additional-Xeed quantity. Xignal count is not a billing input.
- `checkout.session.completed` links the verified Stripe mapping but leaves payment `EXTERNAL_PENDING`; only verified billing events can move service payment state to `VERIFIED/FAILED`.
- Signed Stripe webhook ingress is bounded, replay-safe and ordered by provider event time. Duplicate delivery is idempotent and late-arriving older events cannot roll back newer payment/subscription facts.
- Provider-authenticated effects use `BillingAuthorityGrant`, not a fabricated Admin identity. AO-18 remains the integration authority: `stripe-billing` must be registered, enabled, webhook-capable, environment-matched and credential-metadata-usable before ingress is accepted.
- Xeed entitlement and Xeed service reads now fail closed unless billing is verified. MRR remains `UNKNOWN` and is explicitly deferred to AO-11.
- Focused AO-09/AO-10/AO-18 regression: 42 PASS. Architecture-specific recheck after boundary correction: 15 PASS. Final local repository validation: 853 PASS; ruff, mypy, Architecture Guard, axignal-governance and `git diff --check` PASS. Clean GitHub CI is still required.
- Connected Stripe context confirms AXIGNAL merchant `acct_1TybkH8feyjV8Pem` is LIVE. No live Stripe mutation or webhook enablement was performed.

### BLOCKER
A real Stripe sandbox/test context is not currently available through the connected Stripe account surface. AO-10 remains live-disabled and cannot be marked DONE until the required sandbox E2E is executed. This blocker is external evidence availability, not an implementation bypass.

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

**Status:** DONE
**Depends on:** AO-03, AO-08
**Integrates with:** AO-15 weekly-brief request linkage; AO-14/AO-17 may later consume the same observed-touch events.
**Priority:** P1 Growth

### Implementation / verification evidence
- AO-12 extends the existing private `admin_acquisition` domain with append-only `MarketingEvent` records and versioned `OBSERVED_TOUCH_V1` attribution; it does not create a second analytics authority.
- Anonymous activity uses a random session-scoped opaque reference stored only in browser `sessionStorage`; no cookie, localStorage identity, user-agent fingerprint or cross-device identity is used.
- Public ingestion is explicit allow-list and rejects name, email, company identity, free-text purpose, user/principal IDs and other person-identifying request fields.
- Landing location is reduced to path-only and referrer to origin-only before persistence; full query/referrer paths and IP/user-agent are not persisted.
- UTM/source/campaign tokens are bounded and missing values remain `UNATTRIBUTED`.
- Weekly-brief requests can be linked to prior observed-touch lineage by a separate marketing event without retroactively converting anonymous history into person/CRM identity. Telemetry failure cannot reject a valid AO-15 request.
- Admin acquisition projection exposes private aggregate event/session/source/campaign counts plus request-level observed source/campaign/event provenance, explicitly labeled non-causal.
- Public AO-12 ingress has an independent `AXIGNAL_ACQUISITION_EVENTS_ENABLED` gate, closed by default. Production Nginx exposes only the two exact AO-12 routes and does not add a generic `/api/` proxy.
- Focused AO-12 + AO-15 contracts: 23 PASS. Ruff and mypy: PASS.
- Browser QA PASS: with AO-12 enabled, landing chapter 14 persisted exactly LANDING_VIEWED + CHAPTER_VIEWED under one session-scoped opaque ref with youtube/video/launch UTM and path-only location; with AO-12 disabled, the same browser flow persisted zero marketing events.
- Full local repository validation PASS: 877 tests; Ruff format/check, strict mypy, Architecture Guard, axignal-governance and `git diff --check` all PASS.
- GitHub CI #310 PASS for PR #130: Graphify structural checks, secret scanning and deterministic validation all succeeded; PR #130 merged into `main` at `9822c4b0d4a352633b320a2d250d964a746efd39`.
- Production deployment PASS at the exact merged SHA: `axignal-prod-runtime` and `axignal-prod-landing` are healthy and labeled `9822c4b0d4a352633b320a2d250d964a746efd39`.
- Production collection remains deliberately dormant: external `GET /api/acquisition/status` returns `200 {"enabled":false,"model":"OBSERVED_TOUCH_V1"}`; external `POST /api/acquisition/events` returns 404; AO-15 request ingress also remains disabled.
- External browser verification PASS on `https://axignal.com/?c=14&lang=es&utm_source=production_qa&utm_medium=test&utm_campaign=ao12`: deployed DOM loads `marketing.js`, canonical pricing/newsletter content remains intact, and the disabled gate prevents telemetry writes.
- Post-visit persistence verification PASS: `admin_marketing_events=0` and `admin_acquisition_events=0`; existing first-proof (1), Learning Memory (6), Observation Memory observations (1) and fields (5) remain intact. Runtime/landing logs show no errors after cutover.
- AO-12 is therefore implemented, proved, integrated, deployed and verified E2E in its intentionally closed production state. Enabling collection remains a separate privacy/legal operational decision.

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

**Status:** DONE
**Depends on:** AO-12, AO-18
**Priority:** P1 Growth

### Completion evidence
- Versioned AO14_V1 first-party analytics events cover signup, first-Xeed, Today/evidence interaction, return behavior and growth linkage without storing subscriber content.
- Existing AO-12 landing/chapter/CTA observations remain the public-touch source; AO-14 adds opaque session/account/Xeed references rather than a second marketing event authority.
- Traffic is explicitly classified as HUMAN, BOT, AMBIGUOUS, INTERNAL or UNKNOWN. Human engagement is not inferred from opens when classification is unavailable.
- The growth read model traces observed landing/CTA → signup → first Xeed → return/use → paid behavior while stating explicitly that sequence/attribution is correlation, not causation.
- Analytics persistence is append-only and replay-safe; conflicting event-id reuse fails closed.
- AO-14/AO-17 focused contracts PASS together with AO-10/12/15/16 regression; final repository gates are recorded under AO-17 closure.

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

**Status:** DONE
**Depends on:** AO-08
**Integrates with:** AO-12 for later campaign/source attribution; AO-12 is not required for request/consent correctness.
**Priority:** P1 Growth

### Implementation / verification evidence
- Append-only `admin_acquisition` request lifecycle implemented with explicit request, coverage-review and newsletter-consent states.
- Public request surface is localized and can submit review requests without forcing newsletter consent; request-processing acknowledgement and newsletter consent remain separate versioned acts.
- Coverage acceptance/decline, clarification and suppression are privileged server-side operations; acquisition mutations require `admin:acquisition:write` plus STEP_UP assurance.
- Admin projection is private and PII-minimized: professional email and free-text purpose are not projected to the browser.
- No AO-15 path creates a free Xeed, AXENT entitlement, subscriber account or AXIGLAND write.
- Public ingress is closed by default behind `AXIGNAL_WEEKLY_BRIEF_REQUESTS_ENABLED=false`; production activation remains gated by verified legal-controller/contact data and privacy readiness.
- Browser QA PASS on real landing/Admin renderers at desktop and compact breakpoints.
- Focused AO-15 contracts: 15 PASS. AO-01/AO-02/AO-08/AO-15 regression: 28 PASS.
- Full local repository validation: 868 PASS; Ruff, mypy, Architecture Guard, axignal-governance and `git diff --check` PASS.
- GitHub CI PASS for PR #127 (implementation) and PR #128 (production route), both merged into `main`.
- Production deployment PASS at `5e9008d89efdc10d6a9790ed09a67ed6ceb3258e`: `axignal-prod-runtime` and `axignal-prod-landing` healthy and labeled with the exact deployed SHA.
- Production ingress remains deliberately dormant: external `GET /api/weekly-brief/status` returns `200 {"enabled":false}`; external `POST /api/weekly-brief/requests` returns 404. The two exact routes are proxied; no generic `/api/` exposure was added.
- Production browser/DOM verification PASS on `https://axignal.com/?c=14&lang=es`: canonical €9.95/+€4.95 pricing, Xignal non-billable copy, the localized free-weekly-observation strip and `Solicitar newsletter gratuita` CTA render from the deployed artifact.
- Restart/persistence verification PASS: new `admin-acquisition.sqlite3` exists with zero requests while existing first-proof, Learning Memory and Observation Memory counts remain intact; runtime/landing logs show no errors after cutover.
- Legal/privacy activation remains a separate operational gate: DONE here means the request/eligibility/consent capability is implemented, proved, integrated, deployed and verified in its intentionally closed production state; it does not authorize enabling collection before controller/contact/privacy readiness.

### Work
- Public `Solicitar newsletter gratuita` surface plus Admin `BriefRequest` accepted/declined review flow.
- Collect minimum company/domain, professional email and brief purpose; subject/company matching and clarification path.
- Objective fit/evidence-coverage criteria; acceptance is coverage review, not a subjective score of the company.
- Separate request-processing permission from affirmative newsletter consent and preserve notice/version/timestamp evidence.
- Decline/correction/retention/suppression/unsubscribe state; every delivery path rechecks suppression before send.
- No automatic free Xeed creation or AXENT entitlement; public copy must not present the newsletter as a free AXIGNAL plan.

### Acceptance
- Request != subscriber != customer != lead truth in AXIGLAND.
- Accepted request still requires affirmative newsletter consent.
- Ambiguous company identity fails to clarification.

### AUDIT_CLOSURE
The free acquisition hypothesis can be piloted without consent or ontology shortcuts.

## AO-16 — Evidence-Backed Weekly Brief Pipeline

**Status:** DONE
**Depends on:** AO-15, AO-05, AO-06, AO-18
**Priority:** P1 Growth

### Implementation / verification evidence
- AO-16 is implemented as a private acquisition projection over governed Observation Memory; it does not write AXIGLAND or call EvidenceAdmission.
- Composition admits zero to three CURRENT, public-reusable, subject/purpose-applicable observations after deterministic evidence deduplication. Zero eligible material observations produces explicit NO_MATERIAL_CHANGE; there is no quota filler.
- Every material item freezes observation/source/date/content fingerprint/currentness/observed-field summary plus why_may_matter and explicit UNKNOWN statements. The evidence fingerprint excludes interpretive wording.
- Optional model drafting can change only why_may_matter for already-selected evidence and is applied before the immutable issue snapshot is persisted; it cannot introduce an observation or rewrite source/date/currentness/observed fields.
- Pilot mutation requires private Admin admin:acquisition:write with STEP_UP. Private runtime routes support compose/approve/correct; no HTTP delivery route exists.
- Delivery service requires exact human approval, replays AO-15 consent/suppression eligibility immediately before provider work, requires an AO-18 healthy email:send connection, passes a delivery idempotency key to the provider and refuses duplicate issue delivery.
- SQLite issue/approval/delivery/correction records are durable and append-only; exact replay is idempotent and conflicting identity reuse fails closed. Corrections never rewrite the original issue.
- ADR-0064 records the authority boundary, pilot currentness policy and deliberately dormant production-send posture.
- Focused AO-15/AO-16 regression: 23 PASS. Final repository validation: 891 PASS; Ruff format/check PASS; mypy PASS across 216 source files; Architecture Guard PASS; axignal-governance PASS; git diff --check PASS.
- GitHub PR #136 merged green into canonical main as 04d1a5b93c80a1e5b9c8ef34a7165a7954393358; Deterministic validation, Secret scanning and Graphify structural checks PASS. Sourcery review was skipped by its external quota and is not a required gate.

### Production closure evidence (2026-10-02)
- Canonical main `4b69b57ccbcb61b2dccda4d33d46fee8d5461cde` passed GitHub CI before deployment.
- KVM2 production deployment completed through the isolated Docker Compose project `axignal-prod`; both `axignal-prod-runtime` and `axignal-prod-landing` reached and remained `healthy` with `RestartCount=0`.
- Loopback and external `/healthz` both report exact `code_sha=4b69b57ccbcb61b2dccda4d33d46fee8d5461cde`, `status=ok`, Observation/Learning persistence `ok`, `provider_ingress=closed` and `write_surface=closed`.
- Runtime has no published host port; Landing publishes only `127.0.0.1:18180 -> 8080`; systemd AXIGNAL runtime/landing remain inactive.
- Pre/post persistence counts remained unchanged for existing canonical/admin stores. AO-16 initialized `admin-weekly-brief.sqlite3` with issue/approval/delivery/correction tables empty at deployment.
- Landing, Legal, Privacy/RGPD, Terms and Knowledge routes returned HTTP 200 after cutover.
- AO-16 modules import successfully inside the production runtime. `/api/weekly-brief/status` is `enabled=false`; public request POST is 404; external Admin weekly-brief mutation paths are blocked by Nginx and direct runtime probes are 404 because the Admin security plane is not composed in production.
- No HTTP delivery route is exposed. External email sending remains deliberately dormant until AO-15 legal/privacy activation and an AO-18-governed email provider credential/adapter are configured and healthy, as required by ADR-0064.
- Pre/post deployment evidence is stored on the VPS under `/srv/axignal/docker/evidence/`; the prior `9822c4b0d4a352633b320a2d250d964a746efd39` release/images remain available for rollback.

### Work
- Up to three material evidence-backed items; fewer items or an explicit no-material-change issue when appropriate.
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

**Status:** DONE
**Depends on:** AO-14, AO-15, AO-16, AO-10
**Priority:** P1 Growth

### Completion evidence
- GrowthObservatoryProjection combines governed AO-12/14 analytics, AO-15 request/consent state, AO-16 delivery/correction history and AO-10 Stripe-owned payment/capacity facts without writing AXIGLAND.
- Request, acceptance, current consent, delivery, classified engagement, evidence clicks, recurring readership, explicit request→account linkage, paid conversion time and additional-Xeed attach are inspectable.
- Bot, ambiguous and internal engagement remain separate from human engagement. Evidence-click counts include human-classified events only.
- Premium-advisory inquiry/close, complaints, unsubscribe state, corrections and delivery costs are explicit observed commercial events rather than inferred product truth.
- Paid revenue and delivery cost are aggregated per currency; gross contribution is derived only inside the private commercial projection and currencies are never silently combined.
- Professional email, request purpose and subscriber content never enter the analytics event contract or browser-facing growth projection.
- Focused AO-17 contracts and AO-10/12/15/16 regression pass; deterministic repository validation is required before integration.

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

**Status:** DONE
**Depends on:** AO-01, AO-07
**Priority:** P0 Infrastructure

### Completion evidence
- Provider-neutral `domain/admin_integrations`, `application/admin_integrations` and append-only `pipeline/admin_integrations` registry implemented without credential bytes or a second secret authority.
- Definition, credential lifecycle and provider health remain separate; health freshness is explicit, `STALE` is derived, and out-of-order observations project by observation time rather than append order.
- Provider work fails closed for missing/disabled/wrong-environment/revoked/expired/unresolvable credentials, insufficient scopes, missing/non-healthy/stale health and future observations.
- Admin projection is read-only, scope-protected and secret-free; webhook URL/path stays server-side while browser receives only capability/configured metadata.
- Focused AO-18/AO-02/roadmap regression: 24 PASS. Full repository: 841 PASS. Ruff, mypy, Architecture Guard, axignal-governance and `git diff --check`: PASS.
- Browser QA PASS on the real Admin renderer at desktop and compact widths: Integration Registry renders governed Stripe fixture state, health/freshness and authority boundary without exposing the webhook path or credential material. Production deployment is not claimed by AO-18 and remains governed by the later production/deployment closure path.

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

**Status:** DONE
**Depends on:** AO-18
**Priority:** P1 Infrastructure

### Completion evidence
- Added a bounded canonical inventory of AXIGNAL public/internal/Admin API surfaces with explicit exposure, direction, schema version, integration reference and authority boundary.
- Added private operation telemetry for request count, HTTP status/error rate, latency, quota/rate-limit evidence and last observation. Missing metrics remain UNKNOWN rather than zero.
- Added a replay-safe SQLite webhook inbox storing only bounded metadata, payload fingerprint and payload size; request bodies, authorization headers and credential bytes are never persisted or projected.
- Webhook identity uses integration id, provider event id and payload fingerprint. Exact processed replay is recognized; same provider event with a different payload fails closed.
- Transient processing is bounded to a configured retry budget and transitions to DEAD_LETTER after exhaustion. Permanent failures are classified as REJECTED.
- Stripe webhook ingress verifies provider signature/account/environment before AO-19 replay handling, while AO-10 billing/account stores remain the final idempotent side-effect authority.
- Runtime HTTP responses automatically emit AO-19 operation observations for governed routes, including measured request latency and status without logging payload/header content.
- The existing Admin Integrations surface now renders API/Webhook Operations, webhook inbox/DLQ counts and endpoint health/schema/error/latency/quota visibility. There is no arbitrary request console.
- AO-19 focused runtime/contracts: PASS. AO-10/AO-18/runtime regression and full deterministic repository gates are required before integration.

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

**Status:** DONE
**Depends on:** AO-10
**Priority:** P0 Finance

### Completion evidence
- Added a private append-only financial-document domain distinct from AO-10 billing facts. INVOICE, PAYMENT, REFUND and CREDIT_NOTE are separate immutable records with account, currency, occurrence/recording time, source system/object/event, optional adapter reference and optional billing-event linkage.
- Verified Stripe invoice.paid now materializes two records: one INVOICE and one PAYMENT. Replay of the same provider event returns the already-materialized records and cannot duplicate or rewrite financial history.
- Stripe refund events materialize a separate REFUND record. PAYMENT_FAILED may materialize a failed PAYMENT reference without being treated as revenue.
- CREDIT_NOTE is append-only and must reference the prior record it corrects. The original invoice remains unchanged and inspectable.
- Tax basis is explicit: KNOWN requires net + tax = gross; otherwise tax values remain absent and the state is UNKNOWN/NOT_APPLICABLE. AXIGNAL does not infer VAT from Stripe amount alone.
- External accounting/fiscal documents can be appended only with finance write authority, STEP_UP assurance and an explicit adapter reference, preserving the future AO-21 provider boundary.
- Versioned export rows preserve source references and signed gross semantics; refunds and credit notes export as negative magnitudes while source records remain positive immutable magnitudes.
- Admin Finance / Fiscal renders the private financial document ledger, source references, tax-basis status, corrections and per-currency net document flow. The UI explicitly states that Admin is not the legal/fiscal system of record.
- Focused AO-10/AO-20 E2E and contract tests PASS; full deterministic repository validation is required before integration.

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

**Status:** DONE
**Depends on:** AO-20, AO-18
**Priority:** P0 Finance

### Completion evidence
- Chosen architecture: EXTERNAL_PROVIDER_ADAPTER_VIA_AO18. No AXIGNAL-owned accounting ledger is authorized. The concrete accounting vendor remains AO-18 integration configuration, not domain doctrine.
- Accounting imports require a registered, enabled AO-18 integration with credential metadata in CONFIGURED or ROTATION_DUE state. Disabled, missing or unconfigured adapters fail closed.
- Added versioned chart-of-accounts mappings across REVENUE, REFUND, PROCESSOR_FEE, SETTLEMENT, INFRASTRUCTURE_COST, BUSINESS_EXPENSE and TAX categories.
- Added immutable provider accounting-entry imports with source provenance, optional AO-20 financial-record linkage and optional processor-settlement linkage.
- Added processor settlement evidence with gross, fee and net invariants. Settlement reconciliation checks both imported settlement/fee entries and aggregate paid-minus-refund versus settled gross by currency.
- Added business/infrastructure cost imports with source references; unmapped imported costs remain explicit MISSING_ACCOUNT_MAPPING discrepancies.
- Reconciliation projects billed, paid, refunds, credit notes, settled gross, processor fees, settled net, accounted amounts and operating costs independently by currency.
- Unknown/unmatched financial records, accounting entries, amount/currency mismatches, mapping gaps and settlement mismatches enter an explicit discrepancy queue. Reconciliation never invents balancing entries.
- Period close is OPEN/BLOCKED/CLOSED. Any unresolved discrepancy blocks close; close requires an external accounting source reference.
- Finance mutations, imports, reconciliation runs, discrepancy resolutions and period evaluations emit Admin governance audit records with FINANCE target and finance-write authority.
- Admin Finance / Fiscal now shows the AO-21 adapter posture, configured accounting integrations, reconciliation totals, discrepancy queue and period-close state. It exposes no arbitrary journal-entry UI.
- Focused AO-18/AO-20/AO-21 contracts and runtime composition PASS; full deterministic repository gates are required before integration.

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
**Depends on:** AO-02, AO-09, AO-24
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
**Depends on:** AO-08, AO-10, AO-11, AO-25
**Priority:** P1 Advisory
### Work
- Implement the authorized launch package: €995/month + applicable VAT, one advisory-scoped Xeed, four weekly evidence-backed updates and one monthly strategic review; define response boundaries and human-hour cap from measured delivery.
- Quote/contract/subscription linkage through CRM/billing; update Stripe catalog, customer account projection, public pricing and a dedicated advisory landing from the same package contract.
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
