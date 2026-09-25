# Feature Specification: Subscriber Experience Interaction Contracts

**Feature Branch**: `feature/p0-interaction-01`\
**Created**: 2026-09-25\
**Status**: Proposed\
**Input**: CTO execution order, P0-INTERACTION-01

## Scope and authority

This feature specifies future subscriber-facing projections over canonical
AXIGLAND. It is subordinate to the MASTER Product Model, Engineering
Constitution, accepted ADRs and Logical Architecture Atlas. It does not approve
a new architecture decision, prove a runtime, or authorize implementation.

**Human First. AXENT when needed.** The subscriber must understand the product
without learning AXIGNAL's internal ontology or prompting an LLM for basic
comprehension. Subscriber Experience and internal Admin are distinct,
separately authorized projections. Neither UI, model response, export nor MCP
surface is canonical AXIGLAND authority.

## User scenarios and acceptance

### US1 — Understand the current world and what changed (P1)

A subscriber opens Today and sees a small, explainable set of material changes,
then follows an item to its explanation and evidence.

**Independent acceptance**: A contract review can trace each displayed change
to authorized AXIGLAND state, materiality policy, time bounds and evidence, and
can represent no change, unknown, stale, contradictory and unavailable states
without inventing certainty.

1. Given an authorized Xeed and a prior visit cursor, when material changes
   exist, then Today presents them with their time interval, reason for
   materiality and inspectable references.
2. Given no eligible changes, when Today is projected, then it distinguishes
   “no material change found” from unknown or failed evaluation.
3. Given a change that is stale, disputed or unresolved, when it is shown, then
   its epistemic/currentness state remains explicit.

### US2 — Follow germination and explore an understandable first map (P1)

A subscriber follows real Xeed construction state and receives a concise,
evidence-backed first reveal before choosing a map, relationship, timeline or
other representation.

**Independent acceptance**: Every user-visible germination state maps to
observed operational/domain state; no timer or percentage can imply work or
readiness that has not occurred.

1. Given partial germination, when progress is projected, then completed,
   active, blocked, unknown and unavailable stages are distinguishable.
2. Given map readiness, when the first reveal is presented, then “What AXIGNAL
   learned”, “What AXIGNAL found” and “What AXIGNAL did not expect” link to
   inspectable backing state and never use an opaque WOW score.
3. Given a question about connections, ownership, change or uncertainty, when a
   representation is selected, then the projection suits that question; graph
   is not assumed to be universal UI.

### US3 — Ask AXENT about authorized context (P1)

A subscriber invokes **Ask AXENT — by AXIGNAL** from a current view or selected
objects. The request is grounded in the smallest useful authorized projection.

**Independent acceptance**: Context construction is account/Xeed-scoped,
minimized, typed by interaction class and linked to source state. The answer
distinguishes AXIGNAL-backed facts from interpretation and cannot write
canonical truth.

1. Given a supported EXPLAIN, ANALYZE, COMPARE or EXPLORE question, when context
   is available, then the response identifies its scope and references.
2. Given insufficient evidence, when a question needs new evidence, then the
   interaction offers a governed research escalation or states the limitation;
   it does not fabricate an answer.
3. Given a user challenge, when submitted, then it creates a Claim Review signal
   for independent reinvestigation, not a canonical edit.

### US4 — Inspect evidence and preserve a portable projection (P2)

A subscriber drills from a discovery through explanation, derivation, FAXTs,
evidence and source, or exports a scoped temporal Xeed / queries through an
authorized Product MCP surface.

**Independent acceptance**: Every hop preserves identity, temporal scope,
epistemic status and authorization; export/MCP output is explicitly a
projection and cannot mutate AXIGLAND.

## Functional requirements

- **FR-001**: The system MUST derive subscriber views from one canonical
  AXIGLAND and MUST NOT grant canonical authority to a UI or projection.
- **FR-002**: Basic product comprehension MUST work without LLM assistance;
  cognitive assistance MUST be contextual and on demand.
- **FR-003**: Subscriber and internal Admin projections MUST remain separate in
  purpose, scope and authorization.
- **FR-004**: Today MUST define deterministic eligibility, materiality,
  deduplication, ordering and time-window semantics; no opaque aggregate score
  may determine materiality.
- **FR-005**: Germination MUST project real state and preserve DISCOVERING,
  VERIFYING, SUPPORTED, CONTRADICTED, UNRESOLVED, STALE and UNKNOWN distinctions.
- **FR-006**: First Map readiness and reveal MUST be evidence-backed and MUST
  precede or accompany a comprehensible entry to the larger map.
- **FR-007**: Representation MUST be selected by cognitive question; graph is
  one AXIGNAL projection, not a universal subscriber layout.
- **FR-008**: Temporal projections MUST support “as of” reconstruction and
  report currentness, intervals and known limitations without silently
  overwriting history.
- **FR-009**: Material and surprising items MUST expose “Why am I seeing this?”
  through deterministic derivation/evidence references.
- **FR-010**: PATHX presentation MUST distinguish an explainable path from a
  direct relationship and expose its ordered, inspectable supporting steps.
- **FR-011**: Ask AXENT MUST use the canonical name **Ask AXENT — by AXIGNAL**
  and accept only authorized, minimal structured context assembled for a
  declared interaction class.
- **FR-012**: Ask AXENT responses MUST distinguish supported state, analysis,
  uncertainty and missing evidence; model output MUST NOT become a FAXT or
  canonical write.
- **FR-013**: Requests for new evidence MUST enter a separately governed
  research objective/loop; users direct attention, never conclusions.
- **FR-014**: A subscriber challenge MUST initiate independent Claim Review
  investigation, never directly modify canonical truth.
- **FR-015**: Authorization MUST scope subscriber context and outputs to the
  account/Xeed. Secrets, unnecessary PII and unrelated subscriber data MUST NOT
  enter model context or telemetry.
- **FR-016**: Xeed.md, Xeed.json and Product MCP MUST expose explicitly scoped,
  versioned read projections; external agent output MUST NOT mutate AXIGLAND.
- **FR-017**: Cognitive provider/model identity MUST remain policy under the
  CognitiveProvider/ModelRouter boundary. GPT-6 Luna is the current default
  policy only, not domain authority or permanent provider lock-in.
- **FR-018**: Cognitive and UX telemetry MUST use interpretable measures,
  preserve lineage and uncertainty, and MUST NOT assert causality without
  evidence. `UNKNOWN_COST != ZERO_COST`.
- **FR-019**: Failures, denied access, empty results, unknown state, stale state,
  contradiction, degradation and retry MUST have distinct contract outcomes.
- **FR-020**: This P0 slice MUST remain documentation-only: no production UI,
  cognitive API, Batch/Responses runtime, Brain, JEV, Source Router, Product
  MCP, Xeed export runtime, database migration or production dependency.

## Edge cases

- Subscriber authorization changes between context assembly and response:
  invalidate/recheck authorization before releasing output.
- A projection has zero objects because it is truly empty versus because
  retrieval failed or access was denied: return distinct states.
- Evidence conflicts or is stale: preserve contradiction/currentness; do not
  select a winner in UI/model presentation absent policy-backed state.
- An older temporal snapshot lacks fields now available: declare projection
  version and as-of scope; do not backfill as historical observation.
- Model/tool call returns malformed, unsupported or ungrounded output: reject
  or degrade to a safe limitation response; do not silently promote it.
- User asks outside authorized scope or for new facts: deny or escalate without
  widening data scope implicitly.
- Cost is missing: report unknown, not zero.

## Key conceptual entities

See `data-model.md`. These are projection concepts, not database schemas.

## Success criteria

- **SC-001**: All 15 contracts in the architecture document have defined
  producer/consumer responsibility, required semantics, failure/unknown
  behavior and authority boundary.
- **SC-002**: Each requirement maps to one or more contracts and has an
  inspectable documentation-level acceptance condition.
- **SC-003**: No contract treats unknown as false, model output as canonical
  truth, user input as evidence, or user challenge as a direct edit.
- **SC-004**: The documentation names interpretable UX and cost measures while
  prohibiting opaque WOW/materiality scores and unsupported causal claims.
- **SC-005**: Repository inspection confirms no runtime, dependency, migration
  or implementation evidence was added by this slice.

## Assumptions and deferred decisions

- Existing canonical domain and provider boundaries remain authoritative.
- GPT-6 Luna / OpenAI mappings are current policy snapshots; validate again at
  implementation time.
- Concrete HTTP/MCP schemas, storage, event names, retention periods, auth
  mechanism, UI components, thresholds and runtime SLOs are deliberately not
  selected here. Define them in authorized implementation slices after these
  semantic contracts receive review.
- All metrics are observations; product causality requires separate evidence.
