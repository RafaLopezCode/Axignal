# Feature Specification: P0-ADMIN-01 Observability Contracts

**Feature Branch**: `feature/p0-admin-01`\
**Created**: 2026-09-25\
**Status**: Proposed\
**Input**: CTO execution order, P0-ADMIN-01

## Scope and authority

Specify the minimum coherent observability contracts that future AXIGNAL
runtimes must emit and the future AXIGNAL Admin projection may consume. This is
a documentation, product-specification and architecture slice. It does not
implement an Admin UI/runtime, telemetry pipeline, event store, APIs, Admin MCP,
JEV, Brain, Luna, source adapters, Xeed germination, V2 or V3.

This feature is subordinate to the MASTER Product Model, Engineering
Constitution, accepted ADRs, Logical Architecture Atlas, accepted domain
architectures and product specifications. It introduces no accepted ADR or
infrastructure choice. **Specified != implemented.**

AXIGLAND remains public economic authority. Admin is an authorized projection
of AXIGNAL-owned operational/economic/governance observations. It cannot write
canonical truth, manage customer business workflows, or browse private V3
content by default.

## User scenarios and acceptance

### US1 — Diagnose operational state with lineage (P1)

An authorized operator can move from an attention item or material metric to
its definition, time window, source observations, attribution policy and
owning job/run/provider references.

**Acceptance**: the projection identifies its schema/version/scope and
completeness; metrics expose numerator/denominator, source records, time window,
attribution, exclusions, unknown components and computation version where
applicable; missing cost is not presented as zero.

### US2 — Distinguish operational failure from epistemic state (P1)

An operator can tell a provider failure from insufficient evidence, policy
denial, security denial, contradiction, stale knowledge, private/unobservable
knowledge and expected unknown.

**Acceptance**: operation outcome and domain epistemic/currentness state are
separate typed references; system failure never becomes a false economic claim.

### US3 — Explain unit economics and knowledge reuse (P1)

An operator can inspect `COST_PER_ACTIVE_XEED_MONTH`, distinguish triggered,
attributed and shared cost, and see the evidence for reuse or avoided
recomputation claims.

**Acceptance**: cost amount, usage, currency and pricing authority can be
unknown independently; allocation references a versioned policy; reuse is not
counted as new knowledge; counterfactual savings are not represented as
negative observed spend.

### US4 — Inspect V2/V3 operations without changing their authority (P1)

An operator may eventually inspect V2 report/AEAP lifecycle and V3 connector,
authorization and security metadata.

**Acceptance**: V2/V3 remain proposed/pre-implementation until runtime evidence
changes their status; private content is excluded from Admin and Admin MCP by
default; telemetry grants no canonical write authority.

### US5 — Human and agent inspect the same bounded projection (P2)

An authorized human and a future internal agent can access the same semantic
Admin projection using separately governed permissions.

**Acceptance**: Admin MCP is distinct from Product MCP, read-only by default,
least-privilege and metadata-minimized; neither surface can mutate AXIGLAND.

## Functional requirements

- **FR-001**: Admin MUST be a projection over owning-domain events and
  observations, not a source of domain or canonical truth.
- **FR-002**: Every material metric MUST have a versioned definition and
  inspectable lineage to input observations, policies and a time window.
- **FR-003**: Operational events, economic observations, epistemic transitions,
  logs, metrics, traces and canonical evidence MUST remain distinct.
- **FR-004**: Correlation and causation MUST be separately represented; IDs are
  optional when irrelevant and MUST NOT imply causation by co-occurrence.
- **FR-005**: Temporal meaning MUST distinguish occurrence, observation,
  effectiveness, recording, start and completion times where relevant.
- **FR-006**: Xeed and research lifecycle projections MUST be derived from real
  state and MUST NOT fabricate progress percentages or readiness.
- **FR-007**: Knowledge Frontier telemetry MUST preserve unresolved, insufficient,
  private/unobservable, contradictory, stale, resolved and unresearched states.
- **FR-008**: Research triggers MUST allocate attention only and MUST NOT grant
  canonical write authority.
- **FR-009**: Source observability MUST use AXIGNAL-owned request/observation
  semantics and treat source results as observations, not truth.
- **FR-010**: Cognitive usage MUST preserve `CognitiveProvider`/`ModelRouter`
  abstraction, policy references and minimized usage/outcome metadata; provider
  output MUST NOT become canonical truth.
- **FR-011**: JEV telemetry MUST be implementation-neutral, decision-class scoped
  and must not impose a universal threshold or expose hidden reasoning.
- **FR-012**: Canonicalization observability MUST reference the domain admission
  and policy decision, supporting evidence and state transition; Admin MUST NOT
  perform the write.
- **FR-013**: Cost telemetry MUST represent triggered, attributed, shared and
  avoided-recompute semantics without double counting or false precision.
- **FR-014**: Knowledge gain and reuse MUST remain decomposable, referenced and
  epistemically bounded; no universal opaque score is permitted.
- **FR-015**: Customer Operations MUST cover only AXIGNAL's own service state
  and MUST NOT acquire CRM/workflow authority (ADR-0008).
- **FR-016**: V2 observability MUST remain report-local and noncanonical; V3
  observability MUST be metadata-first, tenant-scoped and private-content
  separated.
- **FR-017**: Security/governance events MUST be auditable without carrying
  secrets, credentials or unrestricted private payloads.
- **FR-018**: Admin read, export, Admin MCP and future command capabilities MUST
  be separately authorized and least-privilege; operations must route through
  owning domain services.
- **FR-019**: Retention and minimization MUST distinguish operational,
  economic, audit, security, private metadata and private-content references;
  exact periods remain open.
- **FR-020**: First-runtime mandatory instrumentation MUST be explicit and
  must not require a selected vendor, event bus or telemetry SDK.

## Non-goals

- Admin human UI, backend, API, operational commands or Admin MCP runtime.
- Database, schema, migrations, event bus, event-sourcing platform, telemetry
  SDK, OpenTelemetry topology or metrics/logging backend.
- Provider, source-engine or JEV selection/integration.
- V2/V3, Brain, Luna, subscriber, Xeed germination, report or connector runtime.
- Complete RBAC, retention periods, alert thresholds, billing ingestion or
  fixed/shared-cost allocation methodology.

## Status semantics

The existing Admin product specification, V2/V3 specs and this feature remain
`PROPOSED / PRE_IMPLEMENTATION`. Contract completeness describes documentation
only. Runtime status must be established from source and deterministic tests.
