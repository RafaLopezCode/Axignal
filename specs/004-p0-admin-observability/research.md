# Research: P0-ADMIN-01 Admin Observability Contracts

**Status**: Supporting repository research; not product or architecture authority.\
**Checked**: 2026-09-25\
**Baseline**: `922ccf971644bddfe1b4f004e19d4d7c0cf1b917`

## Repository state and implementation evidence

The precheck found clean `main` at the required baseline and refreshed
`origin/main` to the same SHA before the feature branch was created. The existing
Admin product specification had SHA-256
`E9CEAFB1EB680CD7D954F661172652F49064AC996263D797F23C24C5C11C1796` before
reconciliation.

Implementation status is evidence-based; documentation alone does not make a
component implemented:

| Area | Status | Repository evidence and limits |
|---|---|---|
| Admin product definition | `PROPOSED` | `docs/product/AXIGNAL_ADMIN_PRODUCT_SPEC.md`; no Admin app/runtime found |
| Admin Projection, Admin MCP, event/metric/cost observability | `SPECIFIED_NOT_IMPLEMENTED` | Current Admin spec describes future behavior; no Admin projection, metric engine, cost observation type, telemetry integration, or operational event pipeline exists in source |
| Canonical AXIGLAND/domain | `PARTIALLY_IMPLEMENTED` | Domain models and contracts exist for Organization, FAXT, relationships, INXIGHT, PATHX, evidence admission and epistemic state; no durable integrated world runtime |
| Knowledge Frontier | `PARTIALLY_IMPLEMENTED` | `domain/knowledge_frontier/model.py` contains a primitive; full lifecycle/planning/economics linkage is absent |
| Cognitive boundary | `PARTIALLY_IMPLEMENTED` | Job/result types, `CognitiveProvider`, router, Echo adapter and deterministic batch packaging exist; no production model integration or full research loop |
| Source acquisition architecture | `ACCEPTED_NOT_IMPLEMENTED` | ADR-0010 accepts AXIGNAL-owned request/observation semantics; production source adapters/router are absent and engine selection remains open |
| Graph architecture | `ACCEPTED_NOT_IMPLEMENTED` | ADR-0009 accepts AXIGNAL-owned graph semantics and replaceable renderer boundary; Admin cannot treat renderer data as authority |
| JEV | `OPEN_DECISION` | No JEV runtime/selection is present; no threshold or provider is chosen |
| Subscriber interaction | `PROPOSED / PRE_IMPLEMENTATION` | Product/interaction specs define separate subscriber projection, canonical Ask AXENT naming and telemetry minimization |
| V2/V3 | `PROPOSED / PRE_IMPLEMENTATION` | Specs define future report and tenant-scoped private analysis; no runtime exists |

`domain/evidence/epistemics.py` contains an `Observability` epistemic-state
classification. It is not an Admin telemetry system. The codebase also has
deterministic governance and Architecture Guard tools; these are not product
Admin services.

## Authority reconciliation

Authority precedence used: MASTER → Engineering Constitution → accepted ADRs →
Logical Architecture Atlas → accepted domain architectures/strategies →
appendices → product/feature specs → plans/research.

| Authority | Reconciled boundary |
|---|---|
| MASTER / Constitution | One canonical AXIGLAND; observable economy only; no customer-business CRM/workflow; unknown is not false; deterministic evidence admission; provider replaceability; no direct user/model canonical mutation |
| ADR-0001 | No per-customer AXIGLAND or duplicate Organization truth |
| ADR-0002 | Demand-materialized graph; reuse and Knowledge Frontier are meaningful; unmaterialized is not nonexistence |
| ADR-0003 | User/subscriber input directs attention, not conclusions or canonical writes |
| ADR-0004 | XIGNAL is observation allocation, not ownership or edit permission |
| ADR-0005 | FAXT, INXIGHT, PATHX, relationship and evidence semantics remain separate |
| ADR-0006 | Provider/JEV are replaceable; provider output is not domain/canonical truth |
| ADR-0007 | Deterministic, offline-required gates and Graphify structural validation remain intact |
| ADR-0008 | Customer Operations is AXIGNAL first-party service state only; no CRM/workflow authority |
| ADR-0009 | AXIGNAL owns graph meaning/projection; renderer is mechanical and replaceable |
| ADR-0010 | SourceRequest/SourceObservation, policy and provenance belong to AXIGNAL; sources provide observations, not truth; no adapter selection here |
| Atlas / Brain architecture | Conceptual event flow can be modeled without choosing a queue; operational failure is distinct from epistemic state; metadata does not invent private business facts |
| Subscriber product / interaction | Admin and subscriber projections have separate purpose and authorization; canonical label is Ask AXENT — by AXIGNAL; telemetry/context must be minimized |
| Admin product spec | Existing proposal already covers first-party operations, metrics/lineage, research, exports and read-only MCP; it needs V2/V3 and private operational metadata contracts and clarification of event/observation semantics |
| V2 / V3 specs | V2 is a noncanonical report projection; V3 is tenant-scoped private analysis; Admin may observe lifecycle/cost/security metadata but not casually access private report/source content |
| Communication / Living Xeed | AXIGNAL communicates evidence, observability limits, and public/private boundaries; operational telemetry is not a public economic claim |

No higher-authority conflict or new ADR requirement was found. Open
implementation decisions remain open: event/storage/transport technology,
retention periods, shared/fixed-cost allocation, activation definition,
avoided-recompute valuation, alert thresholds, full RBAC mechanics and
provider/billing ingestion.

## Graphify reconnaissance

Graphify queries surfaced the Admin product specification, metric-lineage
section, MASTER, Atlas conceptual domain events/failure semantics, Brain
observatory, Knowledge Frontier, provider boundary, ADR-derived boundaries and
subscriber interaction architecture. The graph is a generated navigation aid,
not evidence that Admin runtime exists and not an authority source.
