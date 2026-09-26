# AXIGNAL Architectural Gap Ledger — P0-ARCH-01

**Reconciled against:** `092fe53dde0bae4e947cf29ba0eb0579e947eafb`
**Architecture input:** [AXIGNAL Logical Architecture Atlas V0.1](AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md)
**Atlas SHA-256:** `e168f3360890a4837192a1082ae3f9a01a6edc8a011d266d9fb89cd2c3dc274e`
**Purpose:** Distinguish source-evidenced current implementation from the accepted or specified logical target. This ledger is a reconciliation snapshot, not runtime architecture or an implementation backlog.

## Authority and evidence rules

Semantic and engineering precedence is **MASTER → Engineering Constitution → accepted ADRs → Atlas target architecture**. The Atlas is subordinate to those authorities. Repository source and deterministic tests are the evidence for implementation status; documentation can establish intended or accepted architecture but cannot prove that a component runs. Graphify is a generated, derived index and is not an authority.

No conflict was found between the Atlas and the MASTER, Constitution, or accepted ADRs. The repository-level `AGENTS.md` still contained a pre-bakeoff statement that graph visualization was unselected. That lower-level instruction drift was corrected to reflect accepted ADR-0009 while retaining its no-runtime/no-product-UI boundary.

Status taxonomy is used exactly as follows:

- `IMPLEMENTED`: the named logical responsibility has direct source and/or deterministic-test evidence in its intended boundary.
- `PARTIALLY_IMPLEMENTED`: some responsibility has source evidence, but the logical domain described by the Atlas is materially incomplete.
- `SPECIFIED_NOT_IMPLEMENTED`: the target responsibility is specified; no runtime implementation was found.
- `ACCEPTED_NOT_IMPLEMENTED`: accepted by an ADR as architecture, with no corresponding runtime implementation found.
- `OPEN_DECISION`: the architecture or implementation selection remains explicitly open; no runtime implementation was found.
- `EXPERIMENTAL`: present only as a bounded experiment, not product implementation.
- `RETIRED`: previously implemented or specified and explicitly removed/retired.

`CURRENT_STATUS` describes each broad logical domain as a whole, not whether an individual primitive exists. For example, evidence admission is implemented, but the Atlas's complete policy gate is not. A listed future slice is not authorized by this ledger.

## Component reconciliation

### A — Canonical AXIGLAND

- `DOMAIN`: Canonical economic world.
- `TARGET_RESPONSIBILITY`: One reusable, temporal, evidence-backed world with demand-driven materialization.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/organizations/model.py`, `domain/faxt/model.py`, `domain/relationships/model.py`, `domain/inxight/model.py`, `domain/pathx/model.py`; related contracts in `tests/contracts/`.
- `MISSING_CAPABILITY`: Durable canonical state, complete ontology, persistence/transaction boundaries, and integrated temporal materialization.
- `DEPENDENCIES`: Evidence/provenance, canonical policy, temporal state, entity resolution.
- `AUTHORITY_BOUNDARY`: AXIGLAND is canonical. User, subscriber, trigger, model, JEV, source, and renderer are not canonical authorities.
- `FUTURE_SLICE`: Separately authorized domain/persistence work.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; blocking before any claim of a complete runtime world.

### B — Research Trigger Intake

- `DOMAIN`: Research orchestration.
- `TARGET_RESPONSIBILITY`: Normalize Xeed, graph-expansion, gap, contradiction, temporal, anomaly, Claim Review, manual, source-change, and readiness triggers into attention requests.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: No `ResearchTrigger` type or trigger-intake module found. `domain/xignal/observation_seed.py` represents persistent observation allocation, not general trigger intake.
- `MISSING_CAPABILITY`: Typed trigger intake, deduplication, dispatch, and trigger lifecycle.
- `DEPENDENCIES`: Xeed/Xignal, Knowledge Frontier, temporal state, Claim Review, map readiness.
- `AUTHORITY_BOUNDARY`: Triggers direct attention only; they cannot write canonical state.
- `FUTURE_SLICE`: AXENT/research orchestration, after explicit authorization.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before research-loop runtime.

### C — Knowledge Frontier

- `DOMAIN`: Knowledge representation / projection.
- `TARGET_RESPONSIBILITY`: Represent useful known-versus-missing, stale, contradictory, or unaffordable knowledge and candidate research questions.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/knowledge_frontier/model.py` stores an organization, unresolved questions, stale claims, candidate expansions, and priority state.
- `MISSING_CAPABILITY`: Structured decision gaps, evidence and contradiction detail, information gain, cost/reuse/freshness dimensions, lifecycle, and research linkage.
- `DEPENDENCIES`: AXIGLAND facts, evidence, temporal currentness, research triggers and planner.
- `AUTHORITY_BOUNDARY`: A projection of what is unknown/stale; it cannot assert facts or write canonical state.
- `FUTURE_SLICE`: Research/Knowledge Frontier runtime, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before targeted research planning.

### D — Research Planner

- `DOMAIN`: Research orchestration.
- `TARGET_RESPONSIBILITY`: Choose worthwhile research from gaps, relevance, reuse, freshness, cost, rights, and stop conditions.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: No planner or research-priority implementation found; `pipeline/features/model.py` only holds separate feature signals.
- `MISSING_CAPABILITY`: Prioritization, job creation, reuse checks, and explicit stop decisions.
- `DEPENDENCIES`: Research triggers, Knowledge Frontier, budget controller, source capability, current canonical knowledge.
- `AUTHORITY_BOUNDARY`: May schedule permitted investigation; cannot determine canonical truth.
- `FUTURE_SLICE`: Research planning, after source architecture and explicit authorization.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before research orchestration.

### E — Budget Controller

- `DOMAIN`: Compute and economic policy.
- `TARGET_RESPONSIBILITY`: Enforce monetary, source, token, expansion, loop, and deadline budgets with marginal-value stopping.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `ObservationSeed.expansion_budget` and `BatchPackager.max_batch_size` exist, but no budget controller or cost accounting exists.
- `MISSING_CAPABILITY`: Shared budgets, authorization, reservation/accounting, enforcement, and stop-reason records.
- `DEPENDENCIES`: Research planner, Xeed, source/cognitive providers, reuse policy.
- `AUTHORITY_BOUNDARY`: Allocates permitted compute only; budget or subscription cannot lower canonical truth standards.
- `FUTURE_SLICE`: Research/compute orchestration, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before autonomous compute.

### F — Source Router / Source Acquisition

- `DOMAIN`: Observation/acquisition.
- `TARGET_RESPONSIBILITY`: Select permitted source capabilities and acquire observations through replaceable source adapters.
- `CURRENT_STATUS`: `ACCEPTED_NOT_IMPLEMENTED`.
- `ARCHITECTURE_STATUS`: `SOURCE_ACQUISITION_ARCHITECTURE=ACCEPTED_NOT_IMPLEMENTED` (ADR-0010, CTO accepted 2026-09-25).
- `ENGINE_SELECTION`: `SOURCE_ENGINE_SELECTION=OPEN_IMPLEMENTATION_DECISION`; initial HTTP and browser adapters remain deferred.
- `RUNTIME_STATUS`: `SOURCE_RUNTIME=NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `pipeline/discovery/` and `pipeline/enrichment/` contain package boundaries only; no production acquisition adapter, router, or source capability contract was found. The candidate harness and adapters are experimental evidence only.
- `MISSING_CAPABILITY`: Source contract, rights enforcement, routing/scoring, acquisition adapters, retry/failure state, and provenance attachment. The Atlas leaves stack and router scoring open.
- `DEPENDENCIES`: Research planner, budget/rights policy, evidence ledger, Python Stage 1.
- `AUTHORITY_BOUNDARY`: Sources provide observations, not truth or instruction authority.
- `FUTURE_SLICE`: Source runtime and implementation-time adapter selection require separate authorization; the accepted architecture does not authorize implementation.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; blocks acquisition runtime.

### G — Evidence Ledger / Provenance

- `DOMAIN`: Evidence and provenance.
- `TARGET_RESPONSIBILITY`: Preserve raw observation, source/artifact, time, acquisition path, normalization, claim, and decision lineage.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/evidence/admission.py` defines `Evidence`; `pipeline/evidence/ledger.py` is an append-only in-memory list; FAXT/relationship models retain evidence references.
- `MISSING_CAPABILITY`: Durable artifact/fingerprint storage, acquisition and normalization provenance chain, claim/decision links, source rights, and replay/idempotency handling.
- `DEPENDENCIES`: Source acquisition, deterministic preprocessing, canonical admission.
- `AUTHORITY_BOUNDARY`: Evidence supports decisions; evidence existence alone is not canonical admission.
- `FUTURE_SLICE`: Evidence/source runtime, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required for auditable acquisition and canonical writes.

### H — Python deterministic intelligence

- `DOMAIN`: Deterministic processing.
- `TARGET_RESPONSIBILITY`: Intake, normalization, identity/state canonicalization, temporal/features, next-action and stop computation.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `pipeline/normalization/text.py`, `pipeline/entity_resolution/resolver.py`, and `pipeline/features/model.py` provide text normalization, exact-name matching, and separate feature fields.
- `MISSING_CAPABILITY`: The Atlas's complete Python Stages 1–3, evidence parsing/fingerprints, richer resolution, state building, decision-gap analysis, information-gain/budget/stop computation.
- `DEPENDENCIES`: Evidence, canonical domain models, research state, policy contracts.
- `AUTHORITY_BOUNDARY`: Python makes data/state deterministic; it is not semantic truth authority and cannot bypass policy admission.
- `FUTURE_SLICE`: Python deterministic intelligence, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before the full cognitive loop.

### I — Cognitive provider and evaluator boundary

- `DOMAIN`: Cognition/provider orchestration.
- `TARGET_RESPONSIBILITY`: Send structured cognitive jobs through replaceable adapters; interpret evidence and targeted research without canonical write authority.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `cognition/jobs/model.py`, `cognition/providers/base.py`, `cognition/providers/echo.py`, `cognition/router/router.py`, and `cognition/batch/packager.py` implement job/result shapes, provider protocol, router, offline Echo adapter, and deterministic batching.
- `MISSING_CAPABILITY`: Any separately authorized contextual-cognition or structured-evaluator adapter, optional asynchronous submission/result lifecycle, operational retry/idempotency and an integrated deterministic-first research loop.
- `DEPENDENCIES`: Python preprocessing/state, evidence, provider abstraction, JEV contract.
- `AUTHORITY_BOUNDARY`: `StructuredResult.is_canonical_truth` is always false; model output must pass deterministic policy/evidence admission.
- `FUTURE_SLICE`: Explicitly authorized provider-neutral cognition and evaluator work after semantic contracts and preceding architecture decisions.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; runtime integration remains prohibited here.

### J — Structured State Builder

- `DOMAIN`: Deterministic state construction.
- `TARGET_RESPONSIBILITY`: Convert normalized candidates and evidence into validated structured state for bounded decision evaluation.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: FAXT, relationship, feature, and cognitive result models exist independently; no builder/orchestrator connecting them was found.
- `MISSING_CAPABILITY`: Unified typed state assembly, contradiction/source-diversity/currentness features, and validation before any bounded structured evaluator.
- `DEPENDENCIES`: Python Stage 2, evidence/provenance, canonical domain types.
- `AUTHORITY_BOUNDARY`: Constructs decision input only; construction is not canonical admission.
- `FUTURE_SLICE`: Python deterministic intelligence, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before JEV evaluation.

### K — JEV Decision Layer

- `DOMAIN`: Bounded decision evaluation.
- `TARGET_RESPONSIBILITY`: Evaluate explicit decision classes from structured state and return sufficient, insufficient, ambiguous, contradictory, stale, or blocked outcomes.
- `CURRENT_STATUS`: `OPEN_DECISION`.
- `REPOSITORY_EVIDENCE`: No JEV implementation, dependency, or integration API found; the Atlas explicitly leaves JEV selection/API open.
- `MISSING_CAPABILITY`: Typed economic decision contracts, decision taxonomy/calibration, separately authorized evaluator selection and bounded evaluation integration.
- `DEPENDENCIES`: Structured State Builder, evidence, decision policy.
- `AUTHORITY_BOUNDARY`: A replaceable structured evaluator may evaluate bounded decisions; its result is not an automatic canonical write. Jev is an experimental candidate only, not canonical authority or live-authorized.
- `FUTURE_SLICE`: P0-EOI-01 economic reasoning contracts; evaluator/provider decisions require separate rights and CTO authorization.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; selection must precede JEV runtime.

### L — Decision Gap / Uncertainty Analysis

- `DOMAIN`: Uncertainty representation.
- `TARGET_RESPONSIBILITY`: Preserve why a decision is insufficient, ambiguous, contradictory, stale, unobservable, or intrinsically uncertain, and identify possible resolvers.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: Epistemic and currentness enums plus `KnowledgeFrontier` exist; no structured `DecisionGap` analyzer/type was found.
- `MISSING_CAPABILITY`: Distinct reasoned gap fields, contradiction/source/currentness diagnostics, and resolver candidates.
- `DEPENDENCIES`: Structured state, JEV outcomes, Knowledge Frontier.
- `AUTHORITY_BOUNDARY`: Represents uncertainty; it must not coerce UNKNOWN to FALSE or rewrite canonical state.
- `FUTURE_SLICE`: JEV/Python decision-state work, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before uncertainty-driven research.

### M — Canonical Policy Gate

- `DOMAIN`: Canonical admission policy.
- `TARGET_RESPONSIBILITY`: Decide whether structured, provenance-backed outputs satisfy policy, rights, epistemic, temporal, identity, and idempotency requirements for canonical admission.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/evidence/admission.py` validates evidence type, attention-only source classes, reference, claim, and decision token; contract tests exercise FAXT and observed relationship admission.
- `MISSING_CAPABILITY`: Atlas-wide canonical commit gate, including rights, full temporal and class-specific policies, idempotency, and broader output types.
- `DEPENDENCIES`: Evidence ledger, structured state, JEV, temporal validation.
- `AUTHORITY_BOUNDARY`: AXIGNAL policy alone controls admission; no trigger, model, source, or JEV result may bypass it.
- `FUTURE_SLICE`: Canonical policy expansion, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; existing admission gate remains the only evidenced canonical path for FAXT/observed relationships.

### N — Canonical Knowledge Writer

- `DOMAIN`: Canonical state mutation boundary.
- `TARGET_RESPONSIBILITY`: Apply admitted canonical outputs with stable identity, provenance, idempotency, temporal history, and auditability.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `FAXT.create` and `ObservedRelationship.create` require admission; `Organization` is a public frozen dataclass in `domain/organizations/model.py`. No persistence/transactional writer was found.
- `MISSING_CAPABILITY`: Unified atomic writer and guarded persistence boundary. Direct `Organization` construction is a future authority surface to constrain before external canonical persistence; no live application write path was found.
- `DEPENDENCIES`: Canonical Policy Gate, evidence, canonical identity, temporal state.
- `AUTHORITY_BOUNDARY`: Only the policy-approved canonical writer may persist truth. The current Organization constructor alone is not evidence of a persistence path.
- `FUTURE_SLICE`: Canonical persistence/writer architecture, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this docs-only reconciliation; blocking before introducing an external canonical-write API.

### O — Temporal Engine

- `DOMAIN`: Temporal/currentness processing.
- `TARGET_RESPONSIBILITY`: Track validity, observation and verification times, currentness decay, temporal events, and revalidation without erasing history.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: FAXT and relationship models hold timestamps/currentness; `Currentness` exists in `domain/evidence/epistemics.py`.
- `MISSING_CAPABILITY`: Temporal interval engine, decay rules, event history, reobservation triggers, and uphold/revise/retire/unresolved processing.
- `DEPENDENCIES`: Canonical state, evidence time, Observation Scheduler, Knowledge Frontier.
- `AUTHORITY_BOUNDARY`: Unknown endpoints stay unknown; stale is not false; only new evidence/policy can revise canonical state.
- `FUTURE_SLICE`: Temporal/observation architecture, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before automatic currentness transitions.

### P — Observation Scheduler

- `DOMAIN`: Temporal orchestration.
- `TARGET_RESPONSIBILITY`: Schedule reobservation from currentness, policy, priority, budget, and explicit stop conditions.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `ObservationSeed` has `last_observed_at` and `next_observation_at`; no scheduler, job queue, or reobservation dispatch code was found.
- `MISSING_CAPABILITY`: Schedule computation, dispatch, idempotency, budget integration, and rescheduling after evidence outcomes.
- `DEPENDENCIES`: Temporal Engine, Research Planner, Knowledge Frontier, Budget Controller.
- `AUTHORITY_BOUNDARY`: Schedules observation only; it cannot mutate canonical truth.
- `FUTURE_SLICE`: Observation/AXENT orchestration, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before ongoing observation runtime.

### Q — Claim Review

- `DOMAIN`: Adversarial reinvestigation.
- `TARGET_RESPONSIBILITY`: Convert a challenge into an independent research trigger and resolve as upheld, revised, retired, or unresolved through evidence/policy.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: No Claim Review request, service, endpoint, or runtime module found. Existing admission rules prevent attention-only user signals from establishing canonical truth.
- `MISSING_CAPABILITY`: Review request lifecycle, independent reinvestigation, submitted-evidence semantics, and outcome projection.
- `DEPENDENCIES`: Research Trigger Intake, Knowledge Frontier, Research Loop, Canonical Policy Gate.
- `AUTHORITY_BOUNDARY`: No direct ClaimReviewRequest → canonical write path; review requests are not edits or truth authority.
- `FUTURE_SLICE`: Claim Review, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; no runtime or fake runtime test added.

### R — RepresentationSignal / RepresentationAnomaly

- `DOMAIN`: Representation intelligence.
- `TARGET_RESPONSIBILITY`: Represent evidence-backed public signals and anomalies as investigation leads distinct from AXIGNAL defects.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: No corresponding domain package/type found; Atlas §§35–36 provide the target concepts.
- `MISSING_CAPABILITY`: Signal/anomaly models, provenance, temporal/currentness, and trigger integration.
- `DEPENDENCIES`: Evidence, AXIGLAND state, Knowledge Frontier, Research Trigger Intake.
- `AUTHORITY_BOUNDARY`: An anomaly is not an AXIGNAL error and cannot write canonical state.
- `FUTURE_SLICE`: Representation intelligence, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation.

### S — Xeed / Xignal lifecycle

- `DOMAIN`: Persistent observation lifecycle.
- `TARGET_RESPONSIBILITY`: Represent an observation objective and persistent focus with budgets, expansion, readiness, and LIVE cultivation.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/xignal/observation_seed.py` implements `ObservationSeed`, `EXPANDING`/`LIVE`, shallow budget/timing fields; no Xeed model or germination state machine exists.
- `MISSING_CAPABILITY`: Xeed, lifecycle phases, scheduler/orchestrator, full budgets, readiness and notification; exact Xeed/Xignal lifecycle mapping remains open in the Atlas.
- `DEPENDENCIES`: Organization identity, Knowledge Frontier, Research Planner, Budget Controller, Map Readiness.
- `AUTHORITY_BOUNDARY`: Xignal/Xeed allocate attention and compute, not ownership or canonical authority.
- `FUTURE_SLICE`: Xeed lifecycle, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; lifecycle specifics remain open.

### T — Map Readiness

- `DOMAIN`: First-map quality gate.
- `TARGET_RESPONSIBILITY`: Evaluate readiness dimensions and route failing dimensions to targeted knowledge gaps before LIVE.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: The app is a boundary placeholder (`apps/web/README.md`); no readiness engine, score, gate, or tests were found.
- `MISSING_CAPABILITY`: Readiness dimensions/states, explanation coverage, thresholds, gap generation, and repair loop.
- `DEPENDENCIES`: AXIGLAND, graph projection, evidence, Knowledge Frontier, Research Loop.
- `AUTHORITY_BOUNDARY`: Readiness controls presentation/lifecycle state, not truth; thresholds remain open.
- `FUTURE_SLICE`: First-map/Map Readiness implementation, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before declaring a product map ready.

### U — AXIGLAND Graph Projection

- `DOMAIN`: Graph projection.
- `TARGET_RESPONSIBILITY`: Produce an AXIGNAL-owned projection from canonical AXIGLAND while preserving observed/potential/historical and evidence distinctions.
- `CURRENT_STATUS`: `ACCEPTED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: Accepted ADR-0009 and `.opencode/skills/axignal-graph-design/`; no projection runtime/package found.
- `MISSING_CAPABILITY`: Projection contract/runtime, query composition, and state-to-projection validation.
- `DEPENDENCIES`: Canonical AXIGLAND, semantic cartography, PATHX/relationship/evidence models.
- `AUTHORITY_BOUNDARY`: Projection is derived/read-only; it cannot become canonical truth.
- `FUTURE_SLICE`: Graph runtime, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; implementation explicitly not authorized.

### V — Semantic Cartography

- `DOMAIN`: AXIGNAL map semantics.
- `TARGET_RESPONSIBILITY`: Own semantic LOD, hierarchy, visual grammar, paths, focus, materialization, labels, accessibility, anomalies, and provenance explanation.
- `CURRENT_STATUS`: `ACCEPTED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: ADR-0009 accepts AXIGNAL ownership; the graph-design skill and 17 references encode design guidance; no runtime cartography package exists.
- `MISSING_CAPABILITY`: Semantic projection algorithms and validated user-facing behavior.
- `DEPENDENCIES`: Graph projection, canonical evidence-backed domain state, AXIGNAL graph-design doctrine.
- `AUTHORITY_BOUNDARY`: AXIGNAL owns map meaning; visual encodings cannot change canonical epistemic or temporal truth.
- `FUTURE_SLICE`: Graph runtime/design implementation, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; implementation explicitly not authorized.

### W — Renderer Adapter

- `DOMAIN`: Renderer boundary.
- `TARGET_RESPONSIBILITY`: Translate AXIGNAL-owned cartographic output into replaceable renderer mechanics; initial choice Sigma + Graphology.
- `CURRENT_STATUS`: `ACCEPTED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: ADR-0009 accepts a replaceable renderer contract; no Sigma/Graphology package, dependency, or adapter code found in `pyproject.toml`, `uv.lock`, or source.
- `MISSING_CAPABILITY`: Runtime renderer contract and adapter; renderer-specific mechanics remain below that boundary.
- `DEPENDENCIES`: AXIGNAL Graph Projection and Semantic Cartography.
- `AUTHORITY_BOUNDARY`: Renderer draws pixels only; no renderer types or semantics enter canonical AXIGNAL domain.
- `FUTURE_SLICE`: Graph runtime, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; production renderer remains prohibited here.

### X — Subscriber Projection

- `DOMAIN`: Subscriber/read projection.
- `TARGET_RESPONSIBILITY`: Combine canonical state, private context, and view parameters without allowing private context to mutate AXIGLAND.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `apps/web/README.md` defines a query/presentation boundary; no app source or subscriber projection type exists.
- `MISSING_CAPABILITY`: Projection/query runtime and isolated private-context storage/filters.
- `DEPENDENCIES`: AXIGLAND projections, user view parameters, privacy boundary.
- `AUTHORITY_BOUNDARY`: Subscriber context affects view/attention only; no canonical write authority.
- `FUTURE_SLICE`: Product projection/UI, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; product UI explicitly not authorized.

### Y — Brain Telemetry

- `DOMAIN`: Internal operations/observability.
- `TARGET_RESPONSIBILITY`: Observe economics, evidence yield, uncertainty, reuse, temporal freshness, readiness, and loop outcomes.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: No Brain runtime, metrics, trace, or telemetry package/workflow found; current CI validates code and structure only.
- `MISSING_CAPABILITY`: Event/metric schema, instrumentation, storage, dashboards, alerts, and privacy boundaries.
- `DEPENDENCIES`: Research, cognition, source, temporal, reuse, and Map Readiness events.
- `AUTHORITY_BOUNDARY`: Operational signals diagnose process; they do not define semantic truth.
- `FUTURE_SLICE`: Brain operations/observability, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation.

### Z — Provider abstractions

- `DOMAIN`: Replaceable source, cognition, and cartography organs.
- `TARGET_RESPONSIBILITY`: Keep provider/library details behind AXIGNAL-owned contracts and domain-independent identities.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: Cognitive provider protocol/router/Echo adapter exist in `cognition/`; no source contract/adapter or renderer adapter exists. Architecture Guard forbids concrete model SDKs outside `cognition/providers/` and prevents provider canonical writes.
- `MISSING_CAPABILITY`: Source and renderer contracts/adapters, real provider lifecycle, and broader integration tests.
- `DEPENDENCIES`: Cognition jobs, source acquisition, graph projection/cartography.
- `AUTHORITY_BOUNDARY`: Provider IDs/results cannot define canonical identity or truth. Sigma + Graphology remain replaceable and noncanonical.
- `FUTURE_SLICE`: Add only after the corresponding source or graph architecture slice is authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; no provider adoption is authorized here.

## Status counts

Counts cover the 26 broad domains A–Z above; they do not count individual classes or support tooling.

| Status | Count |
| --- | ---: |
| `IMPLEMENTED` | 0 |
| `PARTIALLY_IMPLEMENTED` | 10 |
| `SPECIFIED_NOT_IMPLEMENTED` | 11 |
| `ACCEPTED_NOT_IMPLEMENTED` | 4 |
| `OPEN_DECISION` | 1 |
| `EXPERIMENTAL` | 0 |
| `RETIRED` | 0 |
| **Total** | **26** |

The graph-engine bakeoff is experimental research evidence, not an implemented AXIGLAND graph runtime. Cosmos remains historical bakeoff evidence only; it is removed from the current harness and is not a production-eligible dependency.

## Closed-loop coverage in the target and repository

The target loops are explicitly specified in Atlas §§61–66. The codebase does not currently execute any end-to-end loop. Graphify indexes the Atlas and this ledger as architecture documents; that makes target paths queryable as documentation, not implemented runtime paths.

| Loop | Target definition | Current code coverage | Status in Graphify architecture knowledge |
| --- | --- | --- | --- |
| Research | Atlas §61: gap → question → acquisition → Python₁ → Luna → Python₂ → JEV → policy or structured gap → Python₃/Luna targeted acquisition. | Individual evidence, normalization, resolver, and provider primitives only; no connected loop. | Target loop explicitly indexed; status and code evidence linked here. |
| Observation | Atlas §62: canonical state → time/decay → reobservation → frontier/research → uphold/revise/retire/unresolved. | Currentness/time fields and ObservationSeed timestamps only; no decay engine or scheduler. | Target loop explicitly indexed; runtime absent. |
| Map Readiness repair | Atlas §63: readiness failure → dimension gap → targeted research → canonical state → readiness. | No readiness gate or repair path. | Target loop explicitly indexed; runtime absent. |
| Claim Review | Atlas §64: challenge → request/trigger → independent reinvestigation → evidence outcome. | No Claim Review runtime. No direct canonical path is implemented; direct edit authority is prohibited by doctrine. | Target loop explicitly indexed; direct-write transition prohibited. |
| Graph expansion | Atlas §65: Hop0 → valuable Hop1 → selective Hop2 → gaps → information-gain research/stop. | No graph projection/expansion runtime. `KnowledgeFrontier.candidate_expansions` is a field only. | Target loop explicitly indexed; runtime absent. |
| Reuse | Atlas §66: new question → reusable/current canonical knowledge or gap/stale → research → learn for later reuse. | Canonical models exist; no reuse lookup, deduplication, or research short-circuit runtime. | Target loop explicitly indexed; runtime absent. |

## Cognitive authority and direct-write paths

The Atlas's target cognitive flow is **Sources → deterministic Stage 1 → bounded replaceable contextual cognition when needed → deterministic Stage 2 and answerability → replaceable structured evaluator only when required and eligible → AXIGNAL Policy Gate, or (insufficient) structured gap → AXENT research → Source Router → new evidence**. In the current repository, normalization/exact-name resolution are partial Stage 1-like primitives; provider job/result abstractions and the Echo test adapter are not semantic cognition; domain models are not a Stage 2 builder; no production structured evaluator or Stage 3 research loop exists; the targeted return path is specified only.

- `CLAIM_REVIEW_DIRECT_CANONICAL_PATH=NO`: no Claim Review runtime exists; the Atlas explicitly prohibits this edge.
- `MODEL_DIRECT_CANONICAL_PATH=NO`: `StructuredResult.is_canonical_truth` is false; FAXT/observed relationships require `EvidenceAdmission`.
- `SOURCE_DIRECT_CANONICAL_PATH=NO`: no acquisition adapters exist; `EvidenceAdmission` rejects attention-only authorities and requires references/claims.
- `RENDERER_CANONICAL_AUTHORITY=NO`: ADR-0009 and graph-design contracts keep renderer types/authority outside canonical domain.
- `ORGANIZATION_CONSTRUCTION_SURFACE`: `Organization` is directly constructible. No persistence or app write route exists in the current source tree, so a live external canonical-write path was not demonstrated. Guarded persistence is a future prerequisite, not something inferred from this model.

## Other current repository evidence

- **Implemented support boundaries:** Architecture Guard (`tools/architecture_guard/`), deterministic governance (`tools/governance/`), Graphify, Spec Kit, existing design skills, and CI are engineering/governance systems, not AXIGLAND runtime domains.
- **Minimal app:** `apps/web/README.md` states the presentation/query boundary; there are no tracked app implementation files.
- **Cognitive test adapter:** `EchoProvider` is deterministic, offline boundary evidence, not a real model integration.
- **Batch packaging:** `BatchPackager` chunks jobs in memory; it does not queue or submit asynchronous provider batches.
- **Dependencies:** `pyproject.toml` and `uv.lock` contain no Sigma, Graphology, Cosmos, scraper, JEV, or model-provider runtime integration.
- **Dependency-direction findings:** Architecture Guard reports zero violations at this baseline. No provider SDK imports occur in `domain/`; provider adapters are bounded under `cognition/providers/`.
- **Current-to-target contract gap:** several target responsibilities (trigger, scheduler, policy, writer, readiness, telemetry) have no accepted runtime contracts or modules. They remain gaps; this slice adds no fake runtime types.

## Open decisions and architecture conflicts

`ARCHITECTURE_AUTHORITY_CONFLICT=NONE_FOUND` between this subordinate Atlas and the MASTER, Engineering Constitution, or accepted ADRs.

Open decisions recorded by Atlas §70 remain open, including the Source Acquisition stack and source/router scoring, JEV selection/API, Python library and entity-resolution choices, persistence/graph storage, queues/orchestration, batch sizing, budget and readiness thresholds, observation frequencies, event transport, notification provider, and final public/commercial UI. These are not resolved by Graphify or by this ledger.

`DEPENDENCY_DIRECTION_VIOLATIONS=0` at the verified baseline. `UNDOCUMENTED_CURRENT_COMPONENTS` were not found within the required product domains; current support tooling and the Echo/batch primitives are recorded above so they are not mistaken for target runtime.

## Graphify representation limits

The pre-reconciliation Graphify graph contained 1,700 nodes and 2,666 edges, with no structural diagnostic errors. Queries surfaced source and documentation nodes, including `EvidenceAdmission`, `EvidenceLedger`, `CognitiveProvider`, the graph design skill, and architecture guard tests. The graph is generated from code/docs and includes extracted and inferred edges; it has no repository-owned typed schema for `CURRENT_STATUS`, authority ownership, negative/prohibited edges, or closed-loop state transitions. It cannot by itself prove status or represent every prohibition as a machine-enforced relation.

The smallest supported reconciliation is therefore: canonical Atlas + evidence-linked gap ledger + normal structural Graphify refresh/query. Atlas sections define distinct target loops and boundaries; ledger entries state implementation status, supporting source, and missing capability. Graphify indexes these documents but remains a derived navigation aid. Generated `graphify-out/` content remains ignored and untracked.
