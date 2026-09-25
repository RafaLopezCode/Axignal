# Feature Specification: P0-JEV-01 Structured Decision Intelligence V0.1

**Feature Branch**: `architecture/p0-jev-01-v3`
**Created**: 2026-09-25
**Status**: Proposed; architecture complete, runtime pre-implementation.
**Input**: CTO execution order P0-JEV-01 V3.

## Scope and authority

Specify AXIGNAL-owned structured semantic evaluation: provider-neutral
decision contracts, an atomic and versioned Decision Grammar V0.1, a
minimum-sufficient Decision State Compiler, deterministic decision composition,
Knowledge Frontier / Research Planner integration, canonical admission
firewall, a Decision Laboratory and a governed grammar evolution loop.

This feature is subordinate to MASTER Product Model, Engineering Constitution,
accepted ADRs, Logical Architecture Atlas, Brain/Xeed Germination architecture,
and current product specifications. It does not change any higher authority.
TypeSafe Jev is the proposed initial replaceable evaluator implementation;
no production SDK, provider call, dependency, data store, production policy
threshold or runtime is added. The project-local official TypeSafe Skill is
tooling and not a product dependency. **Specified != implemented.**

AXIGNAL owns decision meaning and policy. A typed provider judgment is a
reusable semantic input, not a truth claim. Evidence admission remains the only
canonical gate.

## User scenarios and acceptance

### US1 — Evaluate an atomic semantic question (P1)

An AXIGNAL-owned workflow can ask a narrow question against a validated,
family-specific state using a typed and versioned contract.

**Acceptance**: each question has a decision class, semantic purpose, primitive,
criteria/rubric, state contract and paths, exclusions, no-match/unknown
semantics, epistemic meaning, consumer, version and calibration status. State
is minimized and validated. Independent questions may share one provider call;
answers do not condition each other.

### US2 — Preserve uncertainty and evaluator evidence (P1)

AXIGNAL can inspect raw typed judgments and recompose them under a later policy
without turning missing data or provider failures into negative facts.

**Acceptance**: Choice/Score distributions and evaluator-defined confidence,
Noul probability, model/version, usage and errors are preserved when actually
returned. Missing fields remain unknown. Operational failures are separate
from semantic unknown, contradiction, stale or insufficient outcomes.

### US3 — Compose a governed decision and route gaps (P1)

AXIGNAL's deterministic composer produces decision-class outcomes and, where
appropriate, a structured unresolved requirement for existing Knowledge
Frontier and Research Planner policy.

**Acceptance**: no global score or universal threshold; uncertainty alone does
not automatically create a research job; no duplicate frontier/planner; the
canonical admission gate remains separate. `SUFFICIENT` is not canonical.

### US4 — Evaluate the grammar without truth contamination (P1)

An offline Decision Laboratory can compare question/state/primitive/evaluator/
policy candidates against versioned synthetic or independently labeled cases.

**Acceptance**: 38 adversarial cases are specified; experiments record variable,
versions, labels and provenance, output, composition, review/outcome and usage
where known; no live API is required by CI. Mocks prove contracts/failure
handling, not Jev quality or calibration. Labels sourced only from model
outputs are rejected as independent truth.

### US5 — Evolve grammar through explicit governance (P2)

AXIGNAL can propose, compare, red-team and explicitly promote a versioned
candidate question/grammar.

**Acceptance**: production grammar cannot self-modify; Jev, Luna, AutoResearch
or a single metric cannot promote. Regression analysis includes costly
decision-class errors; version rollback is traceable.

## Functional requirements

- **FR-001**: AXIGNAL owns decision classes, grammar, state compiler,
  composition and policy; provider details remain behind an adapter contract.
- **FR-002**: Exact calculations, IDs, dates, counts, deterministic filtering,
  normalization, deduplication and hard invariants stay in code.
- **FR-003**: Every question evaluates one coherent, independently useful
  judgment and records primitive semantics, boundary cases and version.
- **FR-004**: State is named, validated, minimal and scoped to the decision
  family; it separates observation from inference and public from private.
- **FR-005**: Choice, Score and Noul are selected by answer meaning. Multi-label
  conditions use independent questions when appropriate. Choice/Score
  confidence and Noul probability are not interchangeable.
- **FR-006**: Same-request questions see the same state and do not see each
  other's answers. Only actual dependency justifies a follow-up evaluation.
- **FR-007**: Raw typed output retains the full distribution and relevant
  resolved model/version/usage/error metadata when available.
- **FR-008**: Unknown, missing, ambiguous, insufficient, stale, contradictory,
  not-observable, private, not-applicable and provider failure remain distinct.
- **FR-009**: Support and currentness are separate; contradiction is first-class;
  missing is never coerced to false/zero.
- **FR-010**: The composer is deterministic and policy-versioned. It does not
  mutate AXIGLAND or replace domain epistemic types.
- **FR-011**: A structured unresolved requirement projects to existing
  Knowledge Frontier only through AXIGNAL policy; the existing Research Planner
  decides whether and how to investigate.
- **FR-012**: Evaluator output cannot bypass evidence provenance, rights,
  temporal, identity, domain and admission controls for canonical writes.
- **FR-013**: Private evaluation remains within authorized tenant-scoped V3.1
  boundaries and cannot silently create public FAXT or trigger access requests.
- **FR-014**: Decision Lab experiments are reproducible, offline-capable and
  versioned. Usage/cost/latency missingness is represented explicitly.
- **FR-015**: Metrics are chosen per decision class; this feature sets no target
  values, global score or universal threshold.
- **FR-016**: Grammar candidates advance only through versioned offline
  comparison, regression analysis, adversarial review and explicit authority.
- **FR-017**: Admin observability is metadata-first and does not own decision
  semantics or expose secrets/private content by default.
- **FR-018**: Production CI requires no network, API key, live Jev, live Luna,
  customer-private data or nondeterministic semantic result.

## Non-goals

- Production Jev or Luna integration, service calls, adapter code, SDK
  dependency, credentials, OAuth or production evaluator/version selection.
- Durable Decision Ledger, DB schema/storage, migration, queue, API, telemetry
  vendor, budget service, model-training or classical-ML system.
- Knowledge Frontier, Research Planner, Source Router, evidence admission,
  Brain, V3.1, Admin, subscriber, V2, product doctrine or AXIGLAND redesign.
- Automatic grammar/question/policy/threshold/model promotion or self-editing.
- Use of production customer private data, secrets or live API calls in the
  fixture corpus or CI.

## Status semantics

The architecture and specification are proposed and pre-implementation.
The 38 case rows are synthetic behavioral expectations, not observed Jev
outputs or gold labels. No production Jev runtime is present. No experiment
has measured AXIGNAL Jev accuracy, calibration, latency, cost or value.
