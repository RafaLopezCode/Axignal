# AXIGNAL Architectural Gap Ledger — P0-ARCH-01

**Reconciled against:** `d4939101621f25c38b61a4998392dcb0eac30a8a`
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
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `application/economic_discovery/planner.py` computes dimension work from state requirements and changed dependencies; `application/economic_discovery/prime.py` deterministically routes impacted dimensions through versioned policies; tests in `tests/economic_discovery/test_planner.py` and `test_prime.py` cover those contracts.
- `MISSING_CAPABILITY`: A governed Research Value Gate, materiality/value-of-information policy, rights-aware prioritization, executable research-job creation, cost/no-progress integration, and explicit defer/retain-UNKNOWN decisions.
- `DEPENDENCIES`: Research triggers, Knowledge Frontier, budget controller, source capability, current canonical knowledge.
- `AUTHORITY_BOUNDARY`: May schedule permitted investigation; cannot determine canonical truth. Prime routing remains AXIGNAL/Python-owned.
- `FUTURE_SLICE`: Frontier roadmap FR-02/FR-03/FR-04.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; partial planning exists, but autonomous research remains blocked until value/budget/stop gates exist.

### E — Budget Controller

- `DOMAIN`: Compute and economic policy.
- `TARGET_RESPONSIBILITY`: Enforce monetary, source, token, expansion, loop, and deadline budgets with marginal-value stopping.
- `CURRENT_STATUS`: `SPECIFIED_NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `XeedGerminationState.expansion_budget` and `BatchPackager.max_batch_size` exist, but no budget controller or cost accounting exists.
- `MISSING_CAPABILITY`: Shared budgets, authorization, reservation/accounting, enforcement, and stop-reason records.
- `DEPENDENCIES`: Research planner, Xeed, source/cognitive providers, reuse policy.
- `AUTHORITY_BOUNDARY`: Allocates permitted compute only; budget or subscription cannot lower canonical truth standards.
- `FUTURE_SLICE`: Research/compute orchestration, separately authorized.
- `BLOCKING_OR_NONBLOCKING`: Nonblocking for this reconciliation; required before autonomous compute.

### F — Source Router / Source Acquisition

- `DOMAIN`: Observation/acquisition.
- `TARGET_RESPONSIBILITY`: Select permitted source capabilities and acquire observations through replaceable source adapters.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `ARCHITECTURE_STATUS`: `SOURCE_ACQUISITION_ARCHITECTURE=ACCEPTED_AND_PARTIALLY_IMPLEMENTED` (ADR-0010 plus PR #56).
- `ENGINE_SELECTION`: Governed HTTP acquisition is implemented for explicitly authorized public sources; broader source routing and browser acquisition remain open/deferred.
- `RUNTIME_STATUS`: `SOURCE_HTTP_RUNTIME=IMPLEMENTED_BOUNDED`; `GENERAL_SOURCE_ROUTER=NOT_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `application/source_acquisition/contracts.py`, `application/source_acquisition/runtime.py`, the governed HTTP transport/CAS path under `pipeline/source_acquisition/`, and `tests/source_acquisition/test_http_source_runtime.py` implement policy-bound public HTTP acquisition, redirect re-authorization, public DNS/IP controls, immutable raw-artifact references, conversion to GovernedObservation, Observation Memory ingestion and dependency-aware work planning.
- `MISSING_CAPABILITY`: Multi-capability source router, rights/applicability model beyond current public-source policy, browser adapter if justified, integrated budget/stop accounting, and production orchestration across research jobs.
- `DEPENDENCIES`: Research planner, budget/rights policy, evidence/provenance, Observation Memory.
- `AUTHORITY_BOUNDARY`: Sources provide observations, not truth or instruction authority; acquisition never bypasses EvidenceAdmission.
- `FUTURE_SLICE`: Frontier roadmap FR-03/FR-04/FR-24.
- `BLOCKING_OR_NONBLOCKING`: HTTP acquisition itself is implemented and tested; general autonomous source routing remains incomplete.

### G — Evidence Ledger / Provenance

- `DOMAIN`: Evidence and provenance.
- `TARGET_RESPONSIBILITY`: Preserve raw observation, source/artifact, time, acquisition path, normalization, claim, and decision lineage.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/evidence/admission.py` defines canonical Evidence admission; governed source acquisition preserves immutable raw-observation references and request/policy fingerprints; persistent Observation Memory retains observation/source/time/content fingerprints; DocumentRepresentation/RichStateDatum preserve observation/representation/source/time lineage; semantic candidates bind representation/contract/result fingerprints. Legacy `pipeline/evidence/ledger.py` remains an in-memory primitive, not the whole provenance architecture.
- `MISSING_CAPABILITY`: Unified durable evidence/provenance projection across acquisition → representation → candidate → judgment → explanation → admission, source-rights/applicability metadata, and complete replay references for every hop.
- `DEPENDENCIES`: Source acquisition, Observation Memory, representation, semantic evaluation, canonical admission.
- `AUTHORITY_BOUNDARY`: Evidence/provenance support decisions; existence, grounding or lineage alone is not canonical admission.
- `FUTURE_SLICE`: Frontier roadmap FR-06/FR-18/FR-24.
- `BLOCKING_OR_NONBLOCKING`: Material provenance primitives are implemented; the end-to-end evidence narrative and rights/replay closure remain incomplete.

### H — Python deterministic intelligence

- `DOMAIN`: Deterministic processing and control plane.
- `TARGET_RESPONSIBILITY`: Intake, normalization, identity/state canonicalization, temporal/features, answerability, next-action routing and stop computation.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: Existing normalization/entity-resolution/features primitives are now complemented by persistent Observation Memory state reconstruction, deterministic DocumentRepresentation → RichSubjectState compilation, dependency-aware planner work, market planning, Prime mechanism routing, Bootstrap source selection and Learning Memory summaries. Tests cover these contracts independently.
- `MISSING_CAPABILITY`: Richer identity resolution, dimensional sufficiency beyond field presence, Research Value Gate, enforceable budget/stop controller, complete temporal/currentness engine, integrated execution/composition and policy promotion gates.
- `DEPENDENCIES`: Evidence/provenance, canonical domain models, rich state, research state, versioned policy contracts.
- `AUTHORITY_BOUNDARY`: Python governs deterministic mechanisms/routing; deterministic policy is not evidence and cannot bypass canonical admission.
- `FUTURE_SLICE`: Frontier roadmap FR-01 through FR-04, FR-20 and FR-23 through FR-25.
- `BLOCKING_OR_NONBLOCKING`: Substantial deterministic control-plane primitives exist; the full closed loop remains incomplete.

### I — Cognitive provider and evaluator boundary

- `DOMAIN`: Cognition/provider orchestration.
- `TARGET_RESPONSIBILITY`: Send bounded semantic or adaptive cognitive work through replaceable adapters without canonical write or routing authority.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `cognition/jobs/model.py`, provider/router/batching primitives and the Echo fixture remain; semantic extraction now defines a provider-neutral grounded proposal contract and cognition job bridge; Prime defines DETERMINISTIC / STRUCTURED_EVALUATOR / ADAPTIVE_RESEARCH mechanism families while explicitly keeping concrete providers outside the control plane.
- `MISSING_CAPABILITY`: Production adaptive-research executor, final StructuredEvaluatorPort semantics, live evaluator/provider adapters, retries/fallback/shadow behavior, capability negotiation and integrated execution.
- `DEPENDENCIES`: Rich state, semantic contracts, Prime, evidence/provenance, provider abstractions.
- `AUTHORITY_BOUNDARY`: Model/evaluator output is proposal/judgment only; providers cannot choose their own routing or write canonical state.
- `FUTURE_SLICE`: Frontier roadmap FR-04, FR-21 and FR-22.
- `BLOCKING_OR_NONBLOCKING`: Provider-neutral cognitive contracts exist; production evaluator/research execution remains incomplete.

### J — Structured State Builder

- `DOMAIN`: Deterministic state construction.
- `TARGET_RESPONSIBILITY`: Convert normalized observations/representations into validated structured state for bounded decision evaluation.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `application/source_representation/contracts.py` defines DocumentRepresentation/RichStateDatum/RichSubjectState; `application/source_representation/runtime.py` deterministically compiles explicit represented semantics into provenance-preserving rich state and computes state deltas; `tests/source_representation/test_document_representation.py` verifies the contract. Grounded semantic candidates in `application/semantic_extraction/` are separately bound to exact representation/contract fingerprints.
- `MISSING_CAPABILITY`: Complete decision-family state compilation, contradiction/source-diversity/currentness features, per-dimension sufficiency beyond field presence, and the integrated executor that supplies bounded evaluators.
- `DEPENDENCIES`: Governed observation/representation, evidence/provenance, semantic contracts.
- `AUTHORITY_BOUNDARY`: Constructs decision input only; state construction and semantic candidates are not canonical admission.
- `FUTURE_SLICE`: Frontier roadmap FR-01/FR-04/FR-21.
- `BLOCKING_OR_NONBLOCKING`: RichSubjectState exists and is tested; complete evaluator-ready state composition remains partial.

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
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `TypingDimensionContract.state_requirements`, `DimensionDisposition.NOT_ANSWERABLE`, planner `missing_requirements`, Prime routing and Bootstrap missing-state output provide an explicit, replayable representation of some answerability gaps. Epistemic/currentness enums and `KnowledgeFrontier` remain separate supporting primitives.
- `MISSING_CAPABILITY`: Rich reason codes for contradiction/staleness/rights/unobservability, evidence-quality diagnostics, resolver/value policy, and a unified decision-gap representation spanning structured evaluation and research.
- `DEPENDENCIES`: Rich state, typed dimension contracts, Knowledge Frontier, temporal/currentness, evaluator results.
- `AUTHORITY_BOUNDARY`: Represents uncertainty; it must not coerce UNKNOWN to FALSE or rewrite canonical state.
- `FUTURE_SLICE`: Frontier roadmap FR-01/FR-02/FR-25.
- `BLOCKING_OR_NONBLOCKING`: Basic missing-requirement analysis exists; materiality/research-worth and richer uncertainty remain incomplete.

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
- `REPOSITORY_EVIDENCE`: `XeedGerminationState` has `last_observed_at` and `next_observation_at`; no scheduler, job queue, or reobservation dispatch code was found.
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
- `TARGET_RESPONSIBILITY`: Represent an observation objective and persistent focus with governed bootstrap, budgets, expansion, readiness, and LIVE cultivation.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `domain/xeed/model.py` implements canonical Xeed identity; `domain/xeed/germination.py` retains shallow germination state; `application/xeed_germination/bootstrap.py` now implements a temporary authorized bootstrap plan over RichSubjectState, bounded known-source selection, explicit missing requirements, replay-stable fingerprints and handoff into Prime; `tests/xeed_germination/test_bootstrap.py` covers reuse, handoff, escalation, source isolation and replay.
- `MISSING_CAPABILITY`: Dimensional handoff instead of the current universal bootstrap minimum, Research Value Gate, enforceable cost/stop budgets, productive executor, Map Readiness, persistent LIVE scheduling and an integrated Xignal lifecycle.
- `DEPENDENCIES`: Organization identity, RichSubjectState, Prime, Research Value Gate, Budget Controller, Map Readiness.
- `AUTHORITY_BOUNDARY`: Xeed authorizes attention; Bootstrap plans observation; Xignal is emergent attention/signal. None is canonical truth authority.
- `FUTURE_SLICE`: Frontier roadmap FR-01 through FR-08.
- `BLOCKING_OR_NONBLOCKING`: Temporary bootstrap planning is implemented; productive first-Xeed-to-Xignal lifecycle remains incomplete.

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
- `TARGET_RESPONSIBILITY`: Combine governed economic state, private context, and view parameters without allowing private context to mutate AXIGLAND.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `apps/web/subscriber/` contains the subscriber demo/reference shell and interaction code; HFX presentation contracts/tests define subscriber-safe projection semantics and explicitly separate presentation from canonical truth. The Frontier UX audit verified the demo/Golden Master as a reference experience, not a connected production read model.
- `MISSING_CAPABILITY`: Real query/read-model composition from governed runtime state, persisted private cognitive continuity, live Xeed switching/planting, explainable Xignal feed, and production integration.
- `DEPENDENCIES`: Explainable Xignal/evidence projections, user/Xeed context, privacy boundary, product runtime.
- `AUTHORITY_BOUNDARY`: Subscriber context affects view/attention only; no canonical write authority.
- `FUTURE_SLICE`: Frontier roadmap FR-05 through FR-16 and FR-29/FR-30.
- `BLOCKING_OR_NONBLOCKING`: Reference/demo projection exists; integrated subscriber runtime remains incomplete.

### Y — Brain Telemetry / Learning Memory

- `DOMAIN`: Internal operations/observability and governed process learning.
- `TARGET_RESPONSIBILITY`: Observe economics, evidence yield, uncertainty, reuse, temporal freshness, readiness, route outcomes, cost, latency and corrections without turning process metrics into truth.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: `application/economic_discovery/learning_memory.py` defines provider-neutral append-only LearningEvent/Cost/Yield/Summary contracts; `pipeline/learning_memory/sqlite_store.py` provides durable replay-safe SQLite persistence; `application/xeed_germination/learning.py` binds bootstrap outcomes to exact plan/policy/state fingerprints; `tests/economic_discovery/test_learning_memory.py` covers persistence, idempotency, conflict, corrections, UNKNOWN-vs-zero cost, chronology, UTC and concurrent replay.
- `MISSING_CAPABILITY`: Automatic emission from the real integrated executor, complete artifact/harness replay references, per-hop first-loss attribution, production metrics/alerts, offline PolicyCandidate/Replay/Shadow evaluation and governed promotion/rollback.
- `DEPENDENCIES`: Real execution path, research/cognition/source events, temporal/reuse state and policy versions.
- `AUTHORITY_BOUNDARY`: Learning/operational events diagnose AXIGNAL process only; they cannot mutate AXIGLAND, EvidenceAdmission or production policy automatically.
- `FUTURE_SLICE`: Frontier roadmap FR-17 through FR-20 and FR-26.
- `BLOCKING_OR_NONBLOCKING`: Durable Learning Memory V0 is implemented; operational instrumentation and policy learning remain incomplete.

### Z — Provider abstractions

- `DOMAIN`: Replaceable source, cognition, evaluator, and cartography organs.
- `TARGET_RESPONSIBILITY`: Keep provider/library details behind AXIGNAL-owned contracts and domain-independent identities.
- `CURRENT_STATUS`: `PARTIALLY_IMPLEMENTED`.
- `REPOSITORY_EVIDENCE`: Cognitive provider protocol/router/Echo adapter exist in `cognition/`; governed source acquisition now uses AXIGNAL-owned request/observation contracts; semantic extraction is provider-neutral and normalizes untrusted proposal payloads; Prime routes by mechanism family rather than provider. Architecture Guard forbids concrete model SDK leakage and provider canonical writes.
- `MISSING_CAPABILITY`: Final StructuredEvaluatorPort semantics, live evaluator adapters/bakeoff, broader source capability router, renderer adapter, real provider lifecycle/retries and integrated execution tests.
- `DEPENDENCIES`: Cognition jobs, source acquisition, Prime, structured evaluation, graph projection/cartography.
- `AUTHORITY_BOUNDARY`: Provider IDs/results cannot define canonical identity, routing authority or truth. Model agreement is not evidence corroboration.
- `FUTURE_SLICE`: Frontier roadmap FR-21/FR-22 plus later renderer/source work when justified.
- `BLOCKING_OR_NONBLOCKING`: Provider-neutral boundaries are materially implemented; live provider adoption and comparative evidence remain incomplete.

## Recent governed runtime reconciliation — PRs #55–61

These slices post-date the original Atlas reconciliation and cut across multiple A–Z domains. They are listed explicitly so the ledger does not hide implemented runtime behind older broad-domain wording.

| Slice | Current status | Direct repository evidence | Still missing |
| --- | --- | --- | --- |
| Persistent Observation Memory (#55) | `IMPLEMENTED` as bounded runtime capability | `application/economic_discovery/observation_memory.py`, durable SQLite adapter under `pipeline/observation_memory/`, `tests/economic_discovery/test_observation_memory.py` | full product composition, rights/applicability policy, production storage guarantees |
| Governed HTTP Source Observation (#56) | `IMPLEMENTED` as bounded HTTP acquisition capability | `application/source_acquisition/`, `pipeline/source_acquisition/`, `tests/source_acquisition/test_http_source_runtime.py` | general source router, browser capability if justified, integrated budget/research execution |
| Document Representation + RichSubjectState (#57) | `IMPLEMENTED` as deterministic representation/state capability | `application/source_representation/`, `tests/source_representation/test_document_representation.py` | full decision-family sufficiency/currentness/conflict compilation |
| Grounded Semantic Claim Candidates (#58) | `IMPLEMENTED` as candidate-only semantic extraction boundary | `application/semantic_extraction/`, `cognition/jobs/semantic_extraction.py`, `tests/semantic_extraction/test_semantic_claim_candidates.py` | live provider/evaluator integration, entailment/decision composition, canonical admission |
| Prime Cognitive Control Plane (#59) | `IMPLEMENTED` as planning/routing contract | `application/economic_discovery/prime.py`, `tests/economic_discovery/test_prime.py`, ADR-0025 | execution composition root, Research Value Gate, structured/adaptive executors |
| Temporal Xeed Bootstrap Controller (#60) | `IMPLEMENTED` as temporary planning contract | `application/xeed_germination/bootstrap.py`, `tests/xeed_germination/test_bootstrap.py`, ADR-0026 | dimensional handoff, budgets/stops, real dispatch/lifecycle integration |
| Governed Learning Memory V0 (#61) | `IMPLEMENTED` as observational ledger/store | `application/economic_discovery/learning_memory.py`, `pipeline/learning_memory/sqlite_store.py`, `tests/economic_discovery/test_learning_memory.py`, ADR-0027 | automatic per-hop emission, replay completeness, policy-candidate/shadow/promotion machinery |

`IMPLEMENTED` in this table is deliberately narrower than an A–Z domain status: it means the named slice capability exists and is deterministically tested. It does not mean the full Brain, product journey, production deployment or target domain is complete.

## Status counts

Counts cover the 26 broad domains A–Z above; they do not count individual classes or support tooling.

| Status | Count |
| --- | ---: |
| `IMPLEMENTED` | 0 |
| `PARTIALLY_IMPLEMENTED` | 16 |
| `SPECIFIED_NOT_IMPLEMENTED` | 6 |
| `ACCEPTED_NOT_IMPLEMENTED` | 3 |
| `OPEN_DECISION` | 1 |
| `EXPERIMENTAL` | 0 |
| `RETIRED` | 0 |
| **Total** | **26** |

The graph-engine bakeoff is experimental research evidence, not an implemented AXIGLAND graph runtime. Cosmos remains historical bakeoff evidence only; it is removed from the current harness and is not a production-eligible dependency.

## Closed-loop coverage in the target and repository

The target loops are explicitly specified in Atlas §§61–66. The repository now implements multiple bounded segments of the research/reuse path — governed acquisition, persistent Observation Memory, representation, rich state, semantic candidates, Prime planning, Bootstrap and Learning Memory — but it still does not execute the complete product/research loop end to end. Graphify indexes the Atlas and this ledger as architecture documents; that makes target paths queryable as documentation, not proof of runtime composition.

| Loop | Target definition | Current code coverage | Status in Graphify architecture knowledge |
| --- | --- | --- | --- |
| Research | Atlas §61: gap → question → acquisition → Python₁ → Luna → Python₂ → JEV → policy or structured gap → Python₃/Luna targeted acquisition. | Governed HTTP acquisition, persistent observations, rich state, grounded candidates, answerability planning, Prime routing and temporary Bootstrap exist; Research Value Gate, enforceable budget/stop, live structured/adaptive executors and connected composition root remain absent. | Target loop explicitly indexed; partial runtime evidence linked here. |
| Observation | Atlas §62: canonical state → time/decay → reobservation → frontier/research → uphold/revise/retire/unresolved. | Currentness/time fields and XeedGerminationState timestamps only; no decay engine or scheduler. | Target loop explicitly indexed; runtime absent. |
| Map Readiness repair | Atlas §63: readiness failure → dimension gap → targeted research → canonical state → readiness. | No readiness gate or repair path. | Target loop explicitly indexed; runtime absent. |
| Claim Review | Atlas §64: challenge → request/trigger → independent reinvestigation → evidence outcome. | No Claim Review runtime. No direct canonical path is implemented; direct edit authority is prohibited by doctrine. | Target loop explicitly indexed; direct-write transition prohibited. |
| Graph expansion | Atlas §65: Hop0 → valuable Hop1 → selective Hop2 → gaps → information-gain research/stop. | No graph projection/expansion runtime. `KnowledgeFrontier.candidate_expansions` is a field only. | Target loop explicitly indexed; runtime absent. |
| Reuse | Atlas §66: new question → reusable/current canonical knowledge or gap/stale → research → learn for later reuse. | Persistent Observation Memory supports subject reuse and idempotency; Bootstrap accepts existing RichSubjectState/reuse evidence, but rights/currentness/applicability-aware reuse lookup and integrated research short-circuit remain incomplete. | Target loop explicitly indexed; partial runtime evidence linked here. |

## Cognitive authority and direct-write paths

The Atlas's target cognitive flow is **Sources → deterministic Stage 1 → bounded replaceable contextual cognition when needed → deterministic Stage 2 and answerability → replaceable structured evaluator only when required and eligible → AXIGNAL Policy Gate, or (insufficient) structured gap → AXENT research → Source Router → new evidence**. The current repository now contains a bounded source runtime, persistent Observation Memory, deterministic DocumentRepresentation/RichSubjectState compilation, grounded semantic candidate normalization, typed answerability/planning, Prime routing and temporary Xeed Bootstrap. It still lacks the integrated composition root, Research Value Gate, enforceable budget/stop controller, production structured evaluator and adaptive-research executor required to close that loop.

- `CLAIM_REVIEW_DIRECT_CANONICAL_PATH=NO`: no Claim Review runtime exists; the Atlas explicitly prohibits this edge.
- `MODEL_DIRECT_CANONICAL_PATH=NO`: `StructuredResult.is_canonical_truth` is false; FAXT/observed relationships require `EvidenceAdmission`.
- `SOURCE_DIRECT_CANONICAL_PATH=NO`: governed acquisition adapters now exist, but they produce observations only; `EvidenceAdmission` remains required for canonical FAXT/observed-relationship writes and sources have no direct canonical authority.
- `RENDERER_CANONICAL_AUTHORITY=NO`: ADR-0009 and graph-design contracts keep renderer types/authority outside canonical domain.
- `ORGANIZATION_CONSTRUCTION_SURFACE`: `Organization` is directly constructible. No persistence or app write route exists in the current source tree, so a live external canonical-write path was not demonstrated. Guarded persistence is a future prerequisite, not something inferred from this model.

## Other current repository evidence

- **Implemented support boundaries:** Architecture Guard (`tools/architecture_guard/`), deterministic governance (`tools/governance/`), Graphify, Spec Kit, existing design skills, and CI are engineering/governance systems, not AXIGLAND runtime domains.
- **Subscriber reference/demo app:** `apps/web/subscriber/` contains tracked static/reference implementation and HFX interaction code. It is not evidence of a connected production subscriber read model; the Frontier UX audit observed demo/example-data and disabled real-Xeed actions.
- **Cognitive test adapter:** `EchoProvider` is deterministic, offline boundary evidence, not a real model integration.
- **Batch packaging:** `BatchPackager` chunks jobs in memory; it does not queue or submit asynchronous provider batches.
- **Dependencies:** `pyproject.toml` and `uv.lock` contain no Sigma, Graphology, Cosmos, scraper, JEV, or model-provider runtime integration.
- **Dependency-direction findings:** Architecture Guard reports zero violations at this baseline. No provider SDK imports occur in `domain/`; provider adapters are bounded under `cognition/providers/`.
- **Current-to-target contract gap:** trigger intake, full budget/stop enforcement, scheduler, complete canonical writer/policy expansion, Map Readiness, production evaluator/adaptive-research execution and integrated telemetry emission remain gaps. Learning Memory V0 now supplies an observational process ledger, but not full operational telemetry/policy learning.

## Open decisions and architecture conflicts

`ARCHITECTURE_AUTHORITY_CONFLICT=NONE_FOUND` between this subordinate Atlas and the MASTER, Engineering Constitution, or accepted ADRs.

Open decisions recorded by Atlas §70 remain open except where later accepted/implemented slices now provide bounded evidence. In particular, governed public HTTP acquisition is no longer wholly open, while broader source capability routing/scoring, browser acquisition if justified, evaluator selection/API, richer entity resolution, persistence/graph storage, queues/orchestration, batch sizing, budget/readiness thresholds, observation frequencies, event transport, notification provider, and final public/commercial UI remain unresolved or only partially implemented. These are not resolved by Graphify or by this ledger.

`DEPENDENCY_DIRECTION_VIOLATIONS=0` at the verified baseline. Recent runtime slices #55–61 are explicitly reconciled above so they are not mistaken for missing target responsibilities or for complete end-to-end product runtime.

## Graphify representation limits

The pre-reconciliation Graphify graph contained 1,700 nodes and 2,666 edges, with no structural diagnostic errors. Queries surfaced source and documentation nodes, including `EvidenceAdmission`, `EvidenceLedger`, `CognitiveProvider`, the graph design skill, and architecture guard tests. The graph is generated from code/docs and includes extracted and inferred edges; it has no repository-owned typed schema for `CURRENT_STATUS`, authority ownership, negative/prohibited edges, or closed-loop state transitions. It cannot by itself prove status or represent every prohibition as a machine-enforced relation.

The smallest supported reconciliation is therefore: canonical Atlas + evidence-linked gap ledger + normal structural Graphify refresh/query. Atlas sections define distinct target loops and boundaries; ledger entries state implementation status, supporting source, and missing capability. Graphify indexes these documents but remains a derived navigation aid. Generated `graphify-out/` content remains ignored and untracked.
