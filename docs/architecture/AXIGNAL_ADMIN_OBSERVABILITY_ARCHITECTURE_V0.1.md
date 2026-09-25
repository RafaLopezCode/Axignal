# AXIGNAL Admin Observability Architecture V0.1

**Status:** PROPOSED\
**Implementation status:** PRE_IMPLEMENTATION\
**Classification:** PROPOSED_ADMIN_OBSERVABILITY_ARCHITECTURE\
**Feature:** P0-ADMIN-01 (`specs/004-p0-admin-observability/`)

This reference defines future observability semantics for AXIGNAL Admin. It is
subordinate to the MASTER Product Model, Engineering Constitution, accepted
ADRs, Logical Architecture Atlas and accepted domain architectures. It does
not approve an infrastructure choice, runtime, API, persistence model, UI,
Admin MCP implementation or operational command. **Specified != implemented.**

The normative contract catalogue is
[`observability-contracts.md`](../../specs/004-p0-admin-observability/contracts/observability-contracts.md).

## 1. Purpose and scope

AXIGLAND makes the observable economy inspectable. Admin makes AXIGNAL itself
inspectable. Admin must be able to show what happened, why it happened, what it
cost, what knowledge changed, what remains unknown and which policy governed a
decision—through evidence and lineage rather than opaque dashboard arithmetic.

This architecture covers proposed observability for V1, the research and
canonicalization loop, subscriber operations, V2, and future V3 private
operations. Those systems emit or own their own facts. Admin consumes bounded,
authorized references and measurements, then builds a projection. These domains
are semantic responsibilities, not deployment or microservice boundaries.

It does not select event sourcing, a queue, telemetry SDK, storage engine,
metrics vendor, logging backend, tracing backend, or JEV/provider/source
implementation.

## 2. Authority and state ownership

```text
DOMAIN / SERVICE OWNERS
  canonical AXIGLAND | source acquisition | cognition | JEV | billing |
  Xeed lifecycle | V2 | V3 private plane | governance
          ↓ emit typed events, observations, and stable references
AXIGNAL OBSERVABILITY CONTRACTS
          ↓ validate meaning, temporal state, scope, and lineage
OPERATIONAL / ECONOMIC / EPISTEMIC / GOVERNANCE PROJECTIONS
          ↓ authorize and minimize
ADMIN PROJECTION
  human view | JSON | CSV | Markdown | future read-only Admin MCP
```

AXIGLAND remains the only public economic authority. Admin operational state
may be authoritative for the operational measurements it owns (for example,
job lifecycle, provider observations, cost observations, account/subscription
state, system health and governance events). That ownership does not make Admin
authority for public economic truth, canonical identity/relationships/FAXTs,
public INXIGHTs/PATHXs, or private customer business truth.

Admin is a projection, not a domain authority, canonical writer, CRM, workflow
application, private-data browser, generic analytics dashboard, or replacement
for observability infrastructure. Admin operations must call the owning domain
service through a future separately authorized command contract; Admin may not
directly edit canonical truth.

## 3. One model, distinct observation classes

Use a small semantic vocabulary. Concrete implementations may choose different
wire names while preserving these distinctions:

| Concept | Meaning | It is not |
|---|---|---|
| `OperationalEvent` | A typed record that a bounded operation/state transition occurred | A log line or canonical domain event by default |
| `TemporalEvent` | An AXIGLAND domain-owned transition for a canonical entity, with prior/new state references and evidence references where applicable | A generic Admin operational event or infrastructure lifecycle record |
| `EconomicObservation` | A measured or explicitly unknown usage/cost observation with source and time | A provider log line, invoice truth without authority, or a free/zero default |
| `EpistemicTransition` | A reference to a domain-owned epistemic/currentness state transition | An Admin-authored state or FAXT |
| `ProviderUsageObservation` | A provider-neutral usage, latency, outcome or cost reference | Provider identity as domain authority |
| `AdminMetricObservation` | A versioned derivation over named observations and a time window | Source evidence or an unexplained dashboard number |
| `AdminProjection` | An authorized, versioned read model for an operator or internal agent | The source event store or domain of record |

**LOG != DOMAIN EVENT. METRIC != SOURCE EVENT. TRACE != CANONICAL EVIDENCE.**
An operational record may link to domain events or evidence by stable reference;
it does not replace them. An `OperationalEvent` is not an AXIGLAND
`TemporalEvent` unless the owning canonical domain explicitly records a
canonical entity transition under its own evidence and admission rules. An
Admin/job/provider lifecycle event alone cannot create or imply a
`TemporalEvent`. Observability does not mandate event sourcing or an append-only
event ledger.

## 4. Shared record envelope

Where relevant, an event or observation should carry a minimal envelope:

```text
record_id
record_type
schema_version
producer / owning_domain
occurred_at?
observed_at?
effective_at?
recorded_at
correlation_refs[]?
causation_ref?
subject_refs[]?
policy_refs[]?
outcome_state
data_completeness: KNOWN | PARTIAL | UNKNOWN | UNAVAILABLE | NOT_APPLICABLE
unknown_reason?
provenance_refs[]?
privacy_class / authorization_scope
```

Fields are optional when inapplicable or unavailable; absence must not be
silently converted to an empty fact or numeric zero. Every identifier is a
scoped reference, not a command or authorization token. Avoid copying source
payloads, subscriber conversations, model prompts/responses, private documents,
credentials, or chain-of-thought into the envelope.

## 5. Correlation, causality, time and lineage

Correlation answers “which records belong to this investigation?” Causation
answers “which decision or event directly caused this record?” Preserve the
distinction. Correlation identifiers may include account, Xeed, research run,
question, job, source request, observation, cognitive task, decision,
canonicalization, report and connection references, but no record must carry
every identifier. Use explicit typed references and link edges; do not infer
causality from shared IDs or temporal proximity alone.

Preserve `occurred_at`, `observed_at`, `effective_at`, `recorded_at`,
`started_at` and `completed_at` as different meanings. A missing time remains
unknown; do not compress temporal meaning into `created_at`. Historical
projection must be “what was known when,” with policy/projection versions and
known data gaps.

Material Admin metrics must be traceable through a versioned definition, input
observations, aggregation/attribution policy, source records and time window.
Canonical lineage remains domain-owned: graph element → derivation → FAXT /
relationship → evidence → source observation. Admin shows links, not a second
canonical evidence ledger.

## 6. Epistemic and operational state

Keep operational failure separate from epistemic insufficiency, policy denial,
security denial, contradictory evidence, expected unknown and private or
unobservable knowledge. Use canonical epistemic/currentness vocabulary where
it applies (`OBSERVED`, `DECLARED`, `INFERRED`, `CORROBORATED`, `CONTRADICTED`,
`STALE`, `UNKNOWN`; and `CURRENTLY_OBSERVED`, `HISTORICAL`, `STALE`,
`UNKNOWN_CURRENTNESS`). Do not create a competing public truth taxonomy.

Telemetry completeness is separately represented as `KNOWN`, `PARTIAL`,
`UNKNOWN`, `UNAVAILABLE` or `NOT_APPLICABLE`. In particular:

- `UNKNOWN_COST != ZERO_COST`;
- `MISSING_COST != FREE`;
- infrastructure failure does not imply a false economic claim;
- budget exhaustion does not imply falsehood;
- an unobserved knowledge gain does not mean no knowledge was gained.

No synthetic percentages, magic scores or universal knowledge/quality/JEV
thresholds are introduced. Attention classes must link to inspectable state,
reason and lineage.

## 7. Cost, attribution, knowledge and reuse

`COST_PER_ACTIVE_XEED_MONTH` remains Admin's primary recurring unit-economic
metric, decomposable into sourced cost and activity categories. Its denominator
is an active customer-facing Xeed-month under a separately governed activation
definition. MASTER §42 also defines `COST_PER_LIVE_XIGNAL`, whose unit is the
monthly cost of maintaining a persistent Xignal observation allocation
(MASTER §4.4 and §7). These are distinct metrics with distinct units and scopes;
do not substitute, combine, or convert their denominators without a separately
governed mapping. Cost records
may refer to source acquisition, cognitive providers, Batch/Standard API modes,
JEV, deterministic and graph compute, storage, exports, Product MCP, V2 reports,
V3 connectors/normalization/private analysis and attributable infrastructure.
No historical or mutable provider price is invented or made doctrine.

Distinguish:

- **Triggered cost**: measured cost of the operation that incurred it.
- **Attributed cost**: a derived allocation to a Xeed/account/job/report under
  a named, versioned policy.
- **Shared cost**: observed cost with shared allocation semantics; never silently
  pushed into marginal cost.
- **Avoided recompute**: a reuse/counterfactual observation, not a negative
  monetary charge or directly measured cost saving unless a method supports it.

An attribution result references the underlying cost observations and policy.
Do not sum triggered and attributed representations of the same cost as if both
were separate spend. `UNKNOWN_COST` is not zero. Exact shared-cost allocation,
activation denominators and avoided-recompute valuation remain open decisions.

Knowledge gain is a decomposable observation over domain-owned outcomes such
as admitted FAXTs, corroboration, resolved gaps/contradictions, discovered or
verified relationships, renewed currentness, reusable evidence or material
updates. It does not define a universal “knowledge score,” assert causal impact,
or turn an Admin event into a canonical fact. Reuse distinguishes new
computation, reused evidence, reused canonical knowledge, avoided research and
refresh/currentness work. The reuse flywheel remains a hypothesis until
measured with a declared method.

## 8. Private-data and V3 boundary

V3 is `PROPOSED / PRE_IMPLEMENTATION`. Future Admin may observe metadata such as
connection/adapter health, authorized capability and scope references,
revocation/retention/deletion state, operational costs, report lifecycle and
security events. **Operational visibility is not private-content access.**

Admin projections and default Admin MCP results exclude private source payloads,
documents, CRM opportunity content, private financial details, strategy,
prompts, model context and Private Findings. Content inspection, if a future
separately governed capability allows it, requires separate authorization,
minimum scope and auditable access. Observability must not become a shadow
customer-data warehouse. No V3 private observation, finding or model output
may write canonical AXIGLAND.

## 9. Projection and interaction domains

The projection supports Command Center; first-party Business & Customer
Operations; Xeed; AXENT/research; AXIGLAND/data quality; economics; system and
providers; governance and audit; and cross-cutting Admin projections. These are
not service boundaries. Customer Operations refers only to AXIGNAL's own
accounts, subscriptions, billing, use, support, claims, exports and Product MCP
usage. It has no CRM objects, sales workflow or outreach authority (ADR-0008).

Human operators and future authorized agents consume the same semantically
consistent projection. Human understanding does not depend on an agent. Admin
MCP is separate from Product MCP, internal, bounded, least-privilege and
read-only by default; it cannot query private V3 content or write AXIGLAND by
default. Export authorization, scope and retention apply to every projection.

## 10. Instrumentation before first runtime

The feature contract catalogue classifies instrumentation as
`MUST_EMIT_FROM_FIRST_RUNTIME`, `SHOULD_EMIT` or `OPTIONAL_LATER`. At minimum,
future producers must preserve record identity/version, correct temporal
semantics, owning domain, correlation/causation when applicable, outcome and
completeness/unknown reasons, policy/version references, privacy scope, and
stable lineage references. The first relevant runtime must also emit lifecycle,
research/source/provider/JEV decision, canonicalization, usage/cost, knowledge
gain/reuse, security/governance and V2/V3 operation metadata when those
capabilities exist.

Emitting an observation does not authorize the operation it describes.
Research triggers do not authorize canonical writes. Every canonical transition
continues through the owning domain's evidence admission and policy gate. Admin
actions are observed separately and must route through domain authority.

## 11. Decisions intentionally open

This proposed architecture does not decide event transport, persistence,
retention periods, metrics backend, trace/log vendor, alert thresholds, full
RBAC implementation, Admin UI layout, exact billing ingestion, allocation of
shared/fixed costs, avoided-recompute valuation, activation semantics, or
provider/source/JEV implementation. Exact wire schemas and deployment topology
belong to separately authorized implementation design. No new accepted ADR is
required to state these semantic boundaries; if implementation evidence later
requires a new architectural choice, record it through the ADR process.

## 12. Invariants

```text
ADMIN_IS_PROJECTION_NOT_DOMAIN_AUTHORITY
ADMIN_DOES_NOT_WRITE_CANONICAL_TRUTH_DIRECTLY
NO_MATERIAL_ADMIN_METRIC_WITHOUT_LINEAGE
UNKNOWN_COST_NOT_ZERO
MISSING_COST_NOT_FREE
ADMIN_OPERATIONAL_VISIBILITY_NOT_PRIVATE_CONTENT_ACCESS
OBSERVABILITY_NOT_SHADOW_DATA_WAREHOUSE
NO_RESEARCH_TRIGGER_HAS_CANONICAL_WRITE_AUTHORITY
ADMIN_ACTION_DOES_NOT_BYPASS_DOMAIN_AUTHORITY
CUSTOMER_OPERATIONS_IS_FIRST_PARTY_AXIGNAL_SERVICE_STATE_ONLY
LOG_IS_NOT_DOMAIN_EVENT
METRIC_IS_NOT_SOURCE_EVENT
TRACE_IS_NOT_CANONICAL_EVIDENCE
SPECIFIED_IS_NOT_IMPLEMENTED
```
