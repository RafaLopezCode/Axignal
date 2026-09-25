# Conceptual Observability Model

These concepts describe proposed record meaning. They are not database tables,
ORM models, persisted schemas, API wire formats or implementation evidence.
Their detailed semantic contracts are in
[`contracts/observability-contracts.md`](contracts/observability-contracts.md).

| Concept | Meaning | Authority / relation |
|---|---|---|
| `OperationalEvent` | A typed, versioned statement that a bounded operational transition occurred | Emitted by owning service; distinct from log, metric and canonical domain event |
| `TemporalEvent` | AXIGLAND-owned canonical entity transition with prior/new state and evidence references where applicable | Recorded only by its canonical owner; an operational event does not imply one |
| `EconomicObservation` | Measured or explicitly unknown usage/cost with time and pricing/source authority references | Measurement record; not an invoice unless the billing source establishes that authority |
| `EpistemicTransition` | Reference to a domain-owned epistemic/currentness transition | Admin observes; owning domain controls the state |
| `CorrelationLink` | Optional scoped relation joining records in one investigation | Association alone does not prove causation |
| `CostObservation` | Usage and/or monetary amount, operation/category, attribution class, time, currency and unknown reason | Provider-neutral; may have amount and usage independently known/unknown |
| `CostAttribution` | Derived allocation from one or more CostObservations under a versioned policy | Derived metric input; not additional spend; avoid double counting |
| `KnowledgeGainObservation` | Decomposed outcome references such as admitted FAXTs, resolved gaps or renewed currentness | References domain evidence; not a universal score or causal claim |
| `ReuseObservation` | Reused evidence/knowledge, avoided research or recompute, or refresh work | Counterfactual savings remain method-dependent and are not negative cost |
| `MetricDefinition` | Versioned metric name, unit, formula semantics, inputs, filters, unknown handling and attribution method | Defines calculation; cannot hide missing inputs |
| `MetricObservation` | Value/state for a definition and time window with input/derivation references | Projection/measurement, never source evidence |
| `ProviderHealthObservation` | Provider availability, latency, errors and operational status | Provider health is not domain truth |
| `AdminProjection` | Authorized, minimized, versioned read model shared semantically across human/export/agent projections | Not canonical state, event store or private-data warehouse |
| `AdminActionAudit` | Authorized operation request/result routed through a domain owner | Audit/operation record; cannot directly mutate AXIGLAND |
| `PrivateOperationalMetadata` | Tenant-scoped connection/scope/health/cost/retention/security references for V3 | Not private source content or PrivateFinding; no Admin content access by default |

## Shared invariants

- Missing and not-applicable are different; neither means zero.
- Occurrence, observation, effective and recorded time remain distinguishable.
- Correlation does not imply causation.
- Domain-owned state is referenced, not copied into Admin as a new authority.
- `UNKNOWN_COST != ZERO_COST`; `MISSING_COST != FREE`.
- Triggered, attributed, shared and avoided-recompute semantics remain distinct.
- Private V3 content is excluded from Admin projection and Admin MCP by default.
- Records are minimized; secrets, prompts, raw private payloads and hidden
  reasoning are not copied for convenience.
- Contract/version/policy references make later replay or explanation possible
  without embedding complete policy documents in each record.
