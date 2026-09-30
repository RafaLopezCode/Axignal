# AXIGNAL Frontier Reconciliation Roadmap — 2026-09-30

**Status:** ACTIVE EXECUTION CONTRACT
**Type:** Subordinate implementation roadmap; not product doctrine or architectural authority.
**Authority:** MASTER PRODUCT MODEL → Engineering Constitution → accepted ADRs → this roadmap.
**Repository baseline:** main @ d435da1fe5472fe527c9d4ee008887f3c8c295f7
**Frontier audit input:** D:\AXIGNAL\Asesor Frontera\AXIGNAL_FRONTIER_ADVISOR_2026-09-30_1750_FRONTIER.md
**Audit signatures:** GPT-6.1 / Codex, 2026-09-30 17:50 and UX extension 18:10 Europe/Madrid.
**Execution mode:** one active task at a time.

## 1. Purpose

This roadmap converts the Frontier Advisor architecture/moat audit and UI/UX audit into a finite sequence of governed engineering and product tasks. The objective is to remove or materially reduce every valid, evidenced weakness identified by the audits while preserving higher-order AXIGNAL doctrine.

A task is not DONE because code exists. Runtime/product work normally progresses through IMPLEMENTED → PROVED → INTEGRATED → DEPLOYED → VERIFIED E2E. Documentation-only tasks require source reconciliation, deterministic checks and integration.

## 2. Execution rules

1. Only one task may be IN_PROGRESS unless an explicitly independent external-evidence task is marked PARALLEL.
2. Do not start a later task to avoid closing the active task.
3. New architecture is allowed only when required by an accepted task and not already represented by a reusable contract.
4. Prefer reuse → repair → extend → consolidate → create.
5. Preserve ONE CANONICAL AXIGLAND; XEED != ORGANIZATION; XIGNAL != XEED; CLAIM != WRITE; FAXT != INXIGHT; RELATIONSHIP != PATHX; OBSERVED != POTENTIAL; UNKNOWN != FALSE; LEARNING_MEMORY != OBSERVATION_MEMORY != AXIGLAND; provider output != truth; EvidenceAdmission remains the canonical write firewall.
6. Product work preserves Human-First Cognitive UX and FIRST_MAP_WOW.
7. No provider name becomes core architecture.
8. No opaque score substitutes for inspectable state/reasoning.
9. No commercial outcome becomes epistemic truth.
10. Every task closes with evidence, not narrative.

## 3. Status model

NOT_STARTED · READY · IN_PROGRESS · BLOCKED · DONE · DEFERRED · REJECTED

**CURRENT_TASK = FR-19**

## 4. Frontier closure rule

Each task contains a FRONTIER_CLOSURE condition. At the next Frontier audit, that weakness must either no longer be observable, be correctly declared as an intentional deferred boundary, or have new evidence explaining why the recommendation was rejected.

# PHASE A — RECONCILE CURRENT TRUTH

## FR-00 — Refresh Architectural Gap Ledger

**Status:** DONE
**Priority:** P0  
**Goal:** make repository architecture documentation accurately reflect commits #55–61 and current main.

**Closure evidence (2026-09-30):**
- BASE_SHA: `d4939101621f25c38b61a4998392dcb0eac30a8a`
- WORK_BRANCH: `governance/fr-00-gap-ledger-refresh`
- reconciled A–Z status count: 26/26 entries, internally consistent
- bounded capabilities #55–61 listed explicitly with source/test/ADR evidence
- `uv run axignal-governance`: PASS
- `uv run architecture-guard --root .`: PASS
- `git diff --check`: PASS
- integration evidence: GitHub PR/merge recorded in repository history

### Frontier finding
The audit found P0-ARCH-01 materially stale: it still reports Source Acquisition and other components as absent even though recent slices implemented them.

### Work
- Reconcile docs/architecture/AXIGNAL_ARCHITECTURAL_GAP_LEDGER_P0_ARCH_01.md against current main.
- Update statuses/evidence for Observation Memory, Source Acquisition runtime, Document Representation / RichSubjectState, Semantic Claim Candidates, Prime Cognitive Control Plane, Xeed Bootstrap Controller, and Learning Memory V0.
- Preserve the ledger as a reconciliation snapshot, not implementation authority.
- Do not infer deployment from code existence.

### Acceptance
- Ledger SHA baseline updated.
- Every changed status cites actual source/tests/ADR.
- No stale NOT_IMPLEMENTED statement remains for #55–61 responsibilities.
- Governance/docs checks green.

### FRONTIER_CLOSURE
A future auditor must not be able to cite the ledger as contradicting current implementation state.

# PHASE B — FIX THE BRAIN GATES BEFORE AUTONOMY

## FR-01 — Replace Universal Bootstrap Minimum With Dimensional Handoff

**Status:** DONE
**Depends on:** FR-00  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `158588e7c6129b3ed9fbb0627bfcef38efd1cf78`
- WORK_BRANCH: `architecture/fr-01-dimensional-bootstrap`
- `BootstrapPolicy.initial_state_requirements` removed
- all declared semantic dimensions are explicitly assessed at bootstrap
- only answerable dimensions are handed to executable Prime work
- unresolved dimensions are preserved as explicit `BootstrapDimensionGap` with missing requirements
- known-source planning may continue for gaps without blocking useful Prime work
- ADR-0026 explicitly amended; FR-02 retains authority over whether a gap deserves research
- targeted tests: 19 PASS
- full pytest: 439 PASS
- mypy: PASS (105 source files)
- Architecture Guard: PASS
- governance: PASS
- git diff --check: PASS

### Frontier finding
Minimum bootstrap state can delay useful partial value and confuses field presence with decision sufficiency.

### Work
- Evolve BootstrapPolicy from universal initial-state completion toward minimal identity/authorization seed plus planning context.
- Let per-dimension contracts own answerability.
- Permit Prime handoff while unrelated dimensions remain UNKNOWN.
- Preserve explicit missing requirements and UNKNOWN != FALSE.
- Keep Bootstrap temporary.

### Acceptance
- Tests prove one answerable dimension proceeds while another remains NOT_ANSWERABLE.
- Bootstrap does not wait for unrelated state.
- Existing authorized-source and replay invariants remain intact.
- ADR-0026 is amended or superseded deliberately; no silent contradiction.

### FRONTIER_CLOSURE
Future audit cannot accurately say Bootstrap blocks all value until one universal state set is complete.

## FR-02 — Add Research Value Gate

**Status:** DONE
**Depends on:** FR-01  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `5c9bc1172c24ead9920c9a6d5be3df8be404c415`
- WORK_BRANCH: `architecture/fr-02-research-value-gate`
- deterministic `ResearchValueGate` implemented with explicit dispositions: `RESEARCH_NOW`, `RETAIN_UNKNOWN`, `DEFER`, `BLOCKED_BY_BUDGET_OR_RIGHTS`
- no opaque scalar score introduced
- decisions bound to canonical subject, exact state fingerprint, dimension and missing requirements
- Prime fails closed when a NOT_ANSWERABLE gap has no Research Value decision
- only `RESEARCH_NOW` can produce `PrimeRoute.ADAPTIVE_RESEARCH`
- low-value gaps remain UNKNOWN without research
- Bootstrap no longer escalates automatically when no answerable dimension/source exists
- ADR-0028 accepted and indexed
- targeted tests: 24 PASS before full-suite closure
- full pytest: 448 PASS
- mypy: PASS (106 source files)
- Architecture Guard: PASS
- governance: PASS
- git diff --check: PASS

### Frontier finding
NOT_ANSWERABLE → ADAPTIVE_RESEARCH risks researching every unknown and optimizing taxonomy completion instead of useful economic knowledge.

### Decision target
ANSWERABILITY != WORTH_RESEARCHING.

### Work
Introduce a deterministic, versioned gate between missing state and adaptive research. It must support RETAIN_UNKNOWN, RESEARCH_NOW, DEFER and BLOCKED_BY_BUDGET_OR_RIGHTS. Inputs may include explicit materiality/relevance, expected decision impact, reusable-knowledge potential, freshness need, known-source availability, bounded estimated cost, rights/capability constraints and no-progress history. Do not create a universal opaque scalar score.

### Acceptance
- NOT_ANSWERABLE no longer necessarily routes to research.
- Tests prove low-value missing state remains UNKNOWN without research.
- Routing remains deterministic and replayable.
- A model/provider cannot authorize its own research.

### FRONTIER_CLOSURE
Future audit cannot state that every knowledge gap automatically triggers adaptive research.

## FR-03 — Implement Budget and Stop Contract

**Status:** DONE
**Depends on:** FR-02  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `3ff5c28a50ef57b64106268e311d54cf83f51fd8`
- WORK_BRANCH: `architecture/fr-03-budget-stop-contract`
- provider-neutral `ExecutionBudgetPolicy / State / Delta / Decision` contracts implemented
- governed controller authorizes each next unit of work and refuses work after STOP
- explicit stop reasons cover monetary budget, requests, sources, deadline, retries, loops, no-progress and UNKNOWN cost
- UNKNOWN monetary cost remains UNKNOWN; zero is never fabricated
- cross-currency accumulation fails closed
- governed stop can be emitted to Learning Memory as `PARTIAL` with exact stop reason and measured cost/latency
- budget exhaustion preserves partial/UNKNOWN state and does not weaken evidence standards
- ADR-0029 accepted and indexed
- targeted tests: 12 PASS
- full pytest: 460 PASS
- mypy: PASS (108 source files)
- Architecture Guard: PASS
- governance: PASS
- git diff --check: PASS

### Frontier finding
Current source-count limits do not bound monetary spend, wall-clock time, retries, loops or no-progress.

### Work
Implement provider-neutral execution budget/stop contracts for bootstrap/research: monetary budget when measurable, request/source budget, latency/deadline budget, retry limit, loop/expansion limit, no-progress stop and explicit stop reason. UNKNOWN cost remains UNKNOWN. Budget may restrict compute; it must never lower truth/evidence standards.

### Acceptance
- Deterministic exhaustion/stop tests.
- No infinite/retry research loop possible through the governed executor.
- Stop reasons enter Learning Memory.
- Budget failure returns partial/UNKNOWN state, not fabricated completion.

### FRONTIER_CLOSURE
Future audit cannot truthfully report budget doctrine without an enforceable budget controller and stop reasons.

# PHASE C — PROVE ONE REAL BRAIN PATH

## FR-04 — Prime Execution Composition Root

**Status:** DONE
**Depends on:** FR-03  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `2386ab0644820efb00bdfc7dbb603d9e5d2ca748`
- WORK_BRANCH: `architecture/fr-04-prime-composition-root`
- one application-level composition root added at `application/economic_discovery/prime_execution.py`
- entry requires `AuthorizedXeedOrganization`, not raw subscriber organization identity
- real governed HTTP acquisition can be invoked through the source-acquisition port
- acquired observations flow through Observation Memory, deterministic HTML representation, RichSubjectState, optional semantic extraction, Prime routing, Research Value decisions, Budget/Stop authorization and mechanism executor ports
- concrete adapters remain outside application: `HttpSourceSensor`, `HtmlDocumentRepresentationAdapter`, `CognitiveSemanticExtractionAdapter`
- exact source/request/policy/observation/representation/state/semantic fingerprints retained in `PrimeExecutionTrace`
- execution-scoped Learning Event ids avoid retry/idempotency collisions
- acquisition, representation, semantic-extraction and Prime-executor failures are recorded before re-raise
- NO_CHANGE replay does not re-execute Prime
- budget STOP prevents subsequent work and records a PARTIAL Learning Event
- legacy `application/xeed_germination/semantic_flow.py` explicitly isolated from the Prime composition path
- ADR-0030 accepted and indexed
- targeted integration tests: 4 PASS
- full pytest: 464 PASS
- mypy: PASS (111 source files)
- Architecture Guard: PASS
- governance: PASS
- git diff --check: PASS

### Frontier finding
Strong local components exist, but no demonstrated composition root connects the full cognitive path.

### Work
Compose the smallest real orchestration path from authorized Xeed state through shared Observation Memory reuse, governed source acquisition when needed, Document Representation, RichSubjectState, grounded semantic candidates where required, dimensional answerability, Research Value Gate, Prime routing and deterministic / structured-evaluator-port / adaptive-research-port dispatch. Emit Learning Memory events per hop. No canonical admission is required merely to prove cognitive composition.

### Acceptance
- Integration tests use real application modules, not a parallel fake architecture.
- Trace contains state/policy/code/artifact fingerprints.
- Failures and NO_CHANGE are recorded.
- Legacy semantic_flow.py is isolated or retired deliberately.
- Architecture Guard green.

### FRONTIER_CLOSURE
Future audit finds a real composition root and cannot say #55–61 are only disconnected local pieces.

## FR-05 — Explainable Xignal Projection

**Status:** DONE
**Depends on:** FR-04  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `8a1422699a0bf28c9852fa62dd27ac56253e1d70`
- WORK_BRANCH: `architecture/fr-05-explainable-xignal`
- concrete non-canonical `domain.xignal.Xignal` payload implemented
- explicit subscriber-visible epistemic states: `OBSERVED`, `POTENTIAL`, `UNKNOWN`
- private `xeed_id` and canonical observed `subject_id` are distinct in the Xignal contract
- OBSERVED projection fails closed without canonical FAXT support created through EvidenceAdmission
- OBSERVED Explainable Basis must reference admitted FAXT evidence through `BasisDatum.evidence_ref`
- POTENTIAL and UNKNOWN remain explicit and never inherit OBSERVED semantics
- projection carries why-attention, semantic target, interpretation, currentness, source/time provenance, contradictions, unknowns, optional relationship/PATHX refs, Explainable Basis ref and policy version
- deterministic `XignalExplanationTrail` implements the supporting path required by Show how AXIGNAL knows
- sale probability and provider confidence are forbidden from masquerading as Xignal truth
- Xignal remains `is_canonical_truth = False`
- ADR-0031 accepted and indexed
- targeted Xignal/explanation tests: 9 PASS
- full pytest: 469 PASS
- mypy: PASS (113 source files)
- Architecture Guard: PASS
- git diff --check: PASS

### Work
Build the minimum subscriber-safe projection containing why attention is warranted, observed vs potential state, relevant relation/path, source/time/currentness, contradictions/unknowns, and an Explainable Basis reference. No sale probability or provider confidence may masquerade as truth. Projection cannot bypass EvidenceAdmission.

### Acceptance
- One integrated test produces an explainable Xignal from governed state.
- Show how AXIGNAL knows traverses supporting refs deterministically.
- UNKNOWN and POTENTIAL remain explicit.
- Xignal creation does not canonize model output.

### FRONTIER_CLOSURE
Future audit can inspect a real Xignal path instead of only contracts and candidates.

## FR-06 — End-to-End Evidence Narrative

**Status:** DONE
**Depends on:** FR-05  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `957213e92f9ec868326bf042dc1c0ac4231df22d`
- WORK_BRANCH: `architecture/fr-06-evidence-narrative`
- runtime-backed `EvidenceNarrative` resolver added in subscriber projection
- narrative resolves authorized Xignal lineage through canonical claim/optional relationship/PATHX, stored Observation Memory record, public source, observation time, contradiction and explicit unknown
- every Basis observation reference must resolve uniquely against the authorized canonical subject
- source reference must match the persisted observation source or projection fails closed
- immutable CAS artifacts are verified through an application-owned integrity port and concrete content-addressed adapter
- artifact verification correctly treats acquisition-envelope CAS identity separately from observed-content fingerprint
- UI DTO exposes no CAS refs, filesystem paths, peer IPs, headers or raw infrastructure identifiers
- deterministic `focus_step_id` / `return_focus_step_id` return to the parent Xignal
- exact Observation Memory replay reconstructs an equal narrative
- ADR-0032 accepted and indexed
- targeted narrative/Xignal tests: 7 PASS
- full pytest: 471 PASS
- mypy: PASS (115 source files)
- Architecture Guard: PASS
- git diff --check: PASS

### Work
Prove the product-grade causal path Xignal → relationship/claim → observation → source → time → what remains unknown. Preserve derivation and temporal context, provide deterministic return to parent focus, include currentness/contradiction where applicable, and never generate post-hoc explanations unsupported by lineage.

### Acceptance
- Integration test reconstructs the complete explanation path.
- Evidence reference resolves to actual stored observation/artifact.
- Trace survives replay.
- UI-consumable object leaks no raw infrastructure detail.

### FRONTIER_CLOSURE
The auditor's strongest positive UX pattern is backed by real runtime lineage, not only Golden Master fixtures.

# PHASE D — CLOSE THE FIRST-XEED PRODUCT LOOP

## FR-07 — First-Xeed Runtime Contract

**Status:** DONE
**Depends on:** FR-04, FR-05  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `ce816756b30ac3b708924f7fc9fc65c16d2c02a6`
- WORK_BRANCH: `architecture/fr-07-first-xeed-runtime`
- existing `XeedGerminationState` evolved as the single lifecycle authority; no parallel lifecycle model created
- explicit states implemented: `PLANTED`, `RESOLVING`, `OBSERVING`, `PARTIAL_READY`, `FIRST_XIGNAL_READY`, `LIVE`, `INSUFFICIENT_EVIDENCE`, `FAILED`, `BLOCKED`
- legal transition graph rejects fake progress such as `PLANTED → LIVE`
- every transition retains timezone-aware occurrence time and explicit reason code
- runtime controller requires `AuthorizedXeedOrganization` and consumes real `BootstrapPlan`, `PrimeExecutionTrace` and `ExplainableXignalProjection`
- real Prime progress can produce `PARTIAL_READY` without claiming a Xignal exists
- `RETAIN_UNKNOWN` / `DEFER` map to honest `INSUFFICIENT_EVIDENCE`, not failure or false
- budget/rights blocking and operational failure remain distinct explicit states
- first explainable Xignal identity is recorded immutably before `FIRST_XIGNAL_READY`
- readiness decisions are bound to Xeed id, first Xignal id, observation depth and lifecycle revision; stale/cross-state decisions fail closed
- FR-07 consumes readiness decisions but deliberately does not define Map Readiness policy; FR-08 owns that authority
- PARTIAL_READY can recover to LIVE through a later governed readiness decision without fabricating a second first Xignal
- ADR-0033 accepted and indexed
- targeted lifecycle/authority tests: 25 PASS after compatibility repair; focused lifecycle set: 11 PASS
- full pytest: 478 PASS
- mypy: PASS (116 source files)
- git diff --check: PASS

### Work
Implement the minimum real lifecycle using existing authorities where possible: PLANTED, resolving/observing, PARTIAL_READY, FIRST_XIGNAL_READY, LIVE, INSUFFICIENT_EVIDENCE, FAILED/BLOCKED. Do not create duplicate lifecycle concepts if an existing model already governs them.

### Acceptance
- An authorized Xeed can traverse the lifecycle.
- Partial state is a valid outcome.
- Insufficient evidence is represented honestly.
- No simulated truth or fake progress.

### FRONTIER_CLOSURE
Future audit can execute a first-Xeed flow instead of finding only disabled Plant Xeed controls and pre-populated experience.

## FR-08 — FIRST_MAP Readiness Policy

**Status:** DONE
**Depends on:** FR-05, FR-07  
**Priority:** P0

**Closure evidence (2026-09-30):**
- BASE_SHA: `8d3d4a5a575bce70d9d0515f73249185b516bfb6`
- WORK_BRANCH: `architecture/fr-08-first-map-readiness`
- deterministic qualitative `FirstMapReadinessPolicy` implemented; no scalar readiness score
- explicit dispositions: `FIRST_MAP_READY`, `PARTIAL_MAP`, `SPARSE_MAP`, `INSUFFICIENT_EVIDENCE`
- dimension answerability, Xignal readiness and FIRST_MAP readiness remain separate authorities
- a single non-UNKNOWN explainable Xignal with a grounded Evidence Narrative can make a partial world FIRST_MAP_READY
- POTENTIAL Xignal may qualify without being upgraded to OBSERVED
- zero observations → `INSUFFICIENT_EVIDENCE` with no fabricated promotion decision
- observations without first Xignal → `SPARSE_MAP`
- first Xignal with missing/mismatched/ungrounded narrative or UNKNOWN-only semantics → `PARTIAL_MAP`
- explicit contradictions and remaining unknowns are preserved and do not automatically block readiness
- node count, graph density and completion percentage are absent from the policy contract
- ready decisions bind to exact Xeed lifecycle state and are revalidated by FR-07 before LIVE promotion
- ADR-0034 accepted and indexed
- focused FR-08 + lifecycle tests: 14 PASS
- full pytest: 485 PASS
- mypy: PASS (117 source files)
- Architecture Guard: PASS
- git diff --check: PASS

### Work
Separate dimension answerability, Xignal readiness and Map Readiness. Define inspectable readiness reasons instead of one opaque score. Support useful partial map, honest sparse map and insufficient-evidence state.

### Acceptance
- A partial world can become FIRST_MAP_READY when at least one warranted, explainable output exists.
- Node count is not a readiness criterion.
- Sparse/empty outcomes have governed behavior.

### FRONTIER_CLOSURE
Future audit no longer classifies FIRST_MAP_WOW as aspirational because germination requires a fully populated world.

# PHASE E — HUMAN-FIRST PRODUCT SEQUENCE

## FR-09 — Insight-First Today

**Status:** DONE
**Depends on:** FR-05, FR-08  
**Priority:** P0 UX

**Closure evidence (2026-09-30):**
- BASE_SHA: `45566401808c322d64fb38f289ac9efb63022338`
- WORK_BRANCH: `architecture/fr-09-insight-first-today`
- provider-neutral `TodayProjection` / `TodayPolicy` added to subscriber projection
- explicit policy caps surfaced material items at 1–3; no score, node count, graph density or completion metric
- deterministic ordering prefers real change time when present, otherwise observation recency and stable identity
- Today items retain why-it-matters, epistemic state, currentness, observation/change time, proof ref and spatial focus ref
- partial and empty Today states are explicit; empty copy says observation is still underway
- subscriber Today no longer renders every FAXT or leads with a detail count
- synthetic fixture adapter surfaces at most three current observations and does not claim an unproven temporal change
- primary action is `Show how AXIGNAL knows`; in the current lab it focuses the same governed object and switches cognitive depth to Evidence without inventing lineage
- secondary action is human-first `View in map`; it deep-links with `recenter:false` so camera x/y/zoom are preserved
- Today receives a reversible comprehension-height panel so material items/actions are visible without scrolling; focused item restores normal map geometry
- 10-second comprehension protocol added at `docs/design/FIRST_VIEW_10_SECOND_COMPREHENSION_PROTOCOL.md`
- browser visual verification: Chrome 1440×1000 and 860×1000 PASS for hierarchy/responsive/visible actions
- browser interaction verification via Chrome DevTools Protocol: nominal fixture exposes exactly 3 primary + 3 secondary actions; Evidence action sets depth=3 and target focus; both actions preserve exact camera state
- ADR-0035 accepted and indexed
- focused projection/UI/server tests: 29 PASS
- final full pytest after browser-driven geometry refinement: 493 PASS
- Node syntax: PASS (`app.js`, `presentation.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS

### Frontier finding
The canvas asks users to parse the system before receiving the clearest value.

### Work
Make Today / What changed the default comprehension layer: 1–3 material items maximum by explicit policy; what changed; why it matters; epistemic state; time/currentness; primary Show how AXIGNAL knows action; deep-link into already focused AXIGLAND context. Do not turn Today into a conventional dashboard.

### Acceptance
- 10-second comprehension test protocol exists.
- First view is understandable without internal AXIGNAL vocabulary.
- Deep link preserves spatial context.
- Empty/partial state covered.

### FRONTIER_CLOSURE
Future UX audit cannot truthfully say the user must understand the map before discovering why it matters.

## FR-10 — AXENT Context/Continuity Separation

**Status:** DONE
**Depends on:** FR-09
**Priority:** P0 UX

**Closure evidence (2026-09-30):**
- scoped AXENT messages record Xeed, object kind/id and occurrence time
- current-focus conversation is rendered separately from prior investigation continuity
- focus changes retain prior transcript but cannot present it as current-object context
- prior investigations are visibly labeled and resumable only when their recorded object resolves inside the authorized current projection
- contextual AXENT question actions carry the active Xeed/object scope
- synthetic fixture messages are scope/time annotated; new interactions capture scope/time at creation
- ADR-0036 accepted and indexed
- Chrome 1440×1000 interaction check: focus change isolates current conversation, exposes one labeled prior investigation, and Resume restores the original scoped conversation
- focused UX/presentation tests: 24 PASS
- full pytest: 494 PASS using an external `--basetemp` because the Windows user temp root was ACL-denied
- Node syntax: PASS (`app.js`, `presentation.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS after removing generated local `.mypy_cache`
- production persistence/Context Broker remains deliberately outside FR-10; ADR-0017 boundary preserved

### Work
Separate active object/focus, current contextual actions, prior investigation/continuity and historical transcript. AXENT remains always available but may be compact/contextual rather than full conversation.

### Acceptance
- Changing focus never presents old investigation text as if it described the current object.
- Previous context is dated/labeled and resumable.
- Each new response records Xeed/object/time scope.
- No silent transcript deletion.

### FRONTIER_CLOSURE
Future auditor cannot reproduce the Germany-focus / France-greeting mismatch.

## FR-11 — Initial Cognitive Load Reduction

**Status:** DONE
**Depends on:** FR-09, FR-10
**Priority:** P1 UX

**Closure evidence (2026-09-30):**
- default sidebar no longer exposes an empty Workspace section
- Governance mechanics are retained under closed-by-default **Advanced controls**
- Xeed private-scope copy remains assistive/governed context but is no longer visually prominent
- compact rail preserves advanced access at secondary priority and opens/focuses the disclosure deterministically
- cognitive-depth scale keeps direct keyboard/pointer access while only the active label is permanently visible
- AXENT primary contextual actions are capped at two; further available actions remain reachable under **More questions**
- unavailable synthetic AXENT actions are not rendered as first-view controls
- ADR-0037 accepted and indexed
- before/after Chrome 1440×1000 comparison against pre-FR-11 main confirms hierarchy reduction without layout drift to Today, AXIGLAND, Timeline or AXENT
- narrow Chrome 860×1000 check confirms collapsed rail → Advanced controls expansion → summary focus
- keyboard focus on depth control reveals the full semantic-depth labels without requiring pointer hover
- focused FR-11/HFX presentation tests: 27 PASS
- full pytest: 497 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`app.js`, `presentation.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- production terminology/localization remains FR-12 scope

### Work
Move nonessential expert/governance controls out of first-view prominence, including Memory COGNITIVE, CLIENT · PRIVATE, Uncertainty HIDDEN and advanced controls not immediately needed. Keep depth/evidence/timeline progressively available. Reduce contextual pills to the smallest useful set.

### Acceptance
- First screen has explicit information hierarchy.
- Advanced controls remain reachable.
- No semantics lost.
- Before/after Golden Master comparison and accessibility pass.

### FRONTIER_CLOSURE
Future audit no longer identifies simultaneous permanent controls as a primary dashboardification defect.

## FR-12 — Subscriber Terminology and Locale Coherence

**Status:** DONE
**Depends on:** FR-11
**Priority:** P1 UX

**Closure evidence (2026-09-30):**
- subscriber terminology policy separates retained product vocabulary (AXIGNAL/AXIGLAND/Xeed/Xignal/AXENT), human descriptive labels and hidden internal ontology
- FAXT, INXIGHT, PATHX and EvidenceAdmission remain canonical but are excluded from universal subscriber chrome
- English and Spanish are complete supported subscriber locale catalogs with exact key parity
- Spanish now resolves as `es` instead of silently falling back to English
- German, Japanese and Arabic remain explicit QA layout previews only; they are not represented as complete product locales
- stale partial Spanish layout-stress catalog removed so Spanish has one copy authority
- runtime AXENT action labels, fixture role/status copy, account label and composer placeholder route through locale keys instead of hard-coded English
- loopback server allowlists the Spanish catalog asset
- SEO/GEO/AEO/AIO agencies remain first-class acquisition/use-case audiences under the Landing contract without being injected into universal subscriber chrome
- ADR-0038 accepted and indexed
- Chrome 1440×1000 synthetic dense scenario with persisted `es`: Today, Advanced controls, AXENT actions, More questions, Timeline, account label, composer placeholder, role/status copy all render in Spanish
- same browser check found no visible FAXT/INXIGHT/PATHX and no selected English control leakage; pageerror count = 0
- focused FR-12/HFX locale and presentation tests: 35 PASS
- full pytest: 501 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`locale-es.js`, `presentation.js`, `app.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS

### Work
Audit subscriber-facing terminology separately from canonical domain vocabulary. Preserve AXIGNAL/AXIGLAND/Xeed/Xignal/AXENT where product value warrants them; hide FAXT/INXIGHT/PATHX/internal epistemic jargon unless useful; eliminate mixed English/Spanish in a resolved locale; retain SEO/GEO/AEO agencies without reducing AXIGNAL to digital-representation monitoring.

### Acceptance
- Locale catalog covers all first-view/action/status copy.
- No unexplained mixed-language controls.
- Canonical meaning remains unchanged.
- Copy leakage tests updated.

### FRONTIER_CLOSURE
Future audit cannot cite mixed locale and excessive internal vocabulary as an onboarding barrier.

# PHASE F — SPATIAL UX, ACCESSIBILITY AND MOBILE

## FR-13 — Three-Level Spatial Legibility

**Status:** DONE
**Depends on:** FR-09
**Priority:** P1 UX

**Closure evidence (2026-09-30):**
- deterministic semantic zoom implemented with WORLD (<0.84), NEIGHBORHOOD (0.84–<1.55) and RELATION/PROOF (>=1.55)
- Fit/Reset targets WORLD at zoom 0.72; focus navigation targets NEIGHBORHOOD at zoom 1.22
- WORLD preserves every object mark but semantically suppresses non-priority labels and renders zero relationship lines
- NEIGHBORHOOD prioritizes focus/organization/directly connected labels and renders at most six direct-focus relationships
- RELATION/PROOF makes all labels semantically eligible subject to collision/off-screen decluttering and renders direct relationships plus one-hop context with a deterministic budget of twelve
- no synthetic semantic clusters are created; WORLD uses reversible visual aggregation only
- dense spatial fixture contains 17 objects and 24 relationships, so the visual budgets are exercised against a larger underlying graph
- visible/live spatial status reports scale plus visible label/relation counts and is bound to the AXIGLAND field with aria-describedby
- keyboard focus reveals any decluttered node label and restores full node contrast without hover
- relationship list remains independent of visual edge budgets: in WORLD the map renders 0 edges while the focus list exposes 8 relationship buttons in the dense fixture
- keyboard activation of a relationship-list item moves focus to the related object and enters NEIGHBORHOOD without page errors
- Chrome 1440×1000 dense scenario verified WORLD=1 visible label/0 edges; NEIGHBORHOOD=6 visible labels/6 edges; RELATION/PROOF=3 currently in-viewport labels/12 edges; Fit returns to WORLD
- visual review rejected the initial 24-edge RELATION/PROOF rendering as graph noise and reduced it to focus-first + one-hop budget 12
- focused FR-13/HFX presentation contracts: 33 PASS
- full pytest: 506 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`app.js`, `presentation.js`, `locale-es.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0039 accepted and indexed

### Work
Define/test WORLD, NEIGHBORHOOD and RELATION/PROOF scales. At each level define visible labels, clustering/aggregation, edge density, focus and accessible equivalent. No graph-for-graph's-sake.

### Acceptance
- Dataset-size stress fixtures.
- Labels do not carry equal visual weight.
- Keyboard focus and non-hover alternative.
- Semantic zoom deterministic.

### FRONTIER_CLOSURE
Future audit no longer finds overview label density as an unresolved core navigation flaw.

## FR-14 — Motion/Input Contract

**Status:** DONE
**Depends on:** FR-13
**Priority:** P1 UX

**Closure evidence (2026-09-30):**
- AXIGLAND wheel ownership is field-scoped rather than global; field controls/minimap/focus locator are excluded from canvas wheel capture
- plain wheel/trackpad pans; Ctrl/Command + wheel performs pointer-anchored zoom; Shift + primarily vertical wheel performs horizontal pan
- wheel delta normalization handles pixel, line and page delta modes
- surrounding UI retains native scroll: dense AXENT transcript browser test scrolled 0→420 px while AXIGLAND spatial level/status remained unchanged
- direct primary drag pans empty canvas; middle-button drag pans through a node without activating it (browser evidence: +90 px x / +40 px y, node remained unpressed)
- AXIGLAND field is keyboard focusable; arrows pan, Shift+arrows accelerate pan, +/- zoom, 0 fits WORLD, Home centers organization and R resets
- camera focus motion is explicitly 440 ms and reduced-motion applies the target camera immediately
- browser checks at 1440×1000 and 1280×720 confirm plain wheel pan, control-wheel pass-through, Ctrl-wheel zoom, keyboard pan/zoom/fit and zero page errors
- reduced-motion browser check confirms node focus enters NEIGHBORHOOD immediately without waiting for camera animation
- landing standard chapter transition reduced from 820 ms to 640 ms total with 620 ms artwork motion and coordinated copy timings that finish inside the transition
- landing backward navigation now reverses artwork and copy travel direction
- landing wheel pagination uses threshold + quiet-period hysteresis; simulated inertial tail advanced chapter 1→2 only, then a later deliberate gesture advanced 2→3
- landing reduced-motion removes spatial travel and uses a 120 ms opacity transition; browser computed art transform remained `none`
- wheel/trackpad, keyboard, touch and direct landing controls continue to converge on the same `goTo` state machine
- focused FR-14/FR-13/HFX/landing contracts: 44 PASS
- full pytest: 510 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`app.js`, `presentation.js`, `locale-es.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0040 accepted and indexed

### Work
Govern wheel zoom only when canvas owns input, page scroll outside canvas, trackpad, pan modifiers, keyboard controls, transition durations/easing, reduced motion and landing chapter transitions.

### Acceptance
- No accidental page/canvas navigation conflict.
- Reduced motion verified.
- Keyboard fallback for every critical spatial action.
- Browser tests at desktop/laptop.

### FRONTIER_CLOSURE
Future audit cannot reproduce non-premium or ambiguous wheel/motion behavior as an unresolved issue.

## FR-15 — Accessible Non-Graph Projection

**Status:** DONE
**Depends on:** FR-06, FR-13
**Priority:** P1

**Closure evidence (2026-09-30):**
- reader now includes a visible semantic non-graph projection generated from the same current subscriber projection/focus
- semantic structure includes ordered focus path, current focus, textual epistemic state, currentness, observation time, relationship list and evidence action
- non-graph relationship rendering is independent of FR-13 visual edge budgets and does not call `spatialEdges` or camera focus
- keyboard activation of a relationship updates focus without recentering the canvas and restores focus to the rebuilt semantic projection heading
- relationship state is explicitly textual (for example `Estado de la relación: Observado`) so critical state is not color-only
- evidence action fails closed when direct evidence access is not exposed; internal projection enums remain out of subscriber copy
- Chrome accessibility tree exposes non-ignored region `Relaciones y evidencia`, navigation `Ruta de foco`, semantic headings and native relationship/evidence buttons
- Chrome keyboard flow in dense scenario: focus relationship action → Enter → related focus/breadcrumb updated → semantic heading receives focus → evidence action expands and moves focus to evidence detail
- dense fixture exposes 8 non-graph relationship actions from organization focus while WORLD can render 0 visual edges
- reflow review at 1280, 640 (~200%) and 320 CSS px (~400%) keeps semantic projection visible with no horizontal overflow in the projection
- at <=680 px the legacy compact connection strip is hidden and the semantic projection remains the relationship authority; 320 px global body overflow reduced to viewport width
- focused FR-15/FR-14/FR-13/locale/HFX contracts: 42 PASS
- full pytest: 515 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`app.js`, `presentation.js`, `locale-es.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0041 accepted and indexed

### Work
Provide an accessible equivalent for material graph relations: hierarchical/list relationship view, focus/breadcrumb, evidence action, temporal state and non-color epistemic state.

### Acceptance
- Keyboard-only core task.
- Screen-reader-oriented semantic structure.
- 200%/400% zoom review.
- No critical state color-only.

### FRONTIER_CLOSURE
Future audit can verify a non-graph path to the same governed meaning.

## FR-16 — Mobile Value Subset

**Status:** DONE
**Depends on:** FR-09, FR-15
**Priority:** P1

**Closure evidence (2026-10-01):**
- mobile subscriber is now a deliberate reader-first product at <=680 CSS px rather than a shrunken AXIGLAND canvas
- mobile default path is Today → Xignal → Why it matters → Evidence → Timeline → contextual AXENT
- desktop AXIGLAND stage, workspace rail and desktop meridian are removed from the default mobile task; no mobile core step depends on hover, minimap or pan precision
- Today retains the same bounded material-item policy; mobile item action is subscriber-facing `Open Xignal` rather than `View in map`
- focused Xignal retains deterministic Why it matters copy derived from the same Today explanation policy
- Evidence mobile navigation focuses ADR-0041's existing semantic evidence boundary; no mobile-only evidence truth model is introduced
- Timeline mobile navigation exposes current observation/currentness state and explicitly states when historical timeline authority is not exposed
- AXENT is a contextual bottom sheet that preserves the current Xignal scope and remembers the mobile surface from which it was opened
- AXENT sheet uses dialog/aria-modal semantics while open, aria-hidden while closed, Escape close, focus restoration and Tab/Shift+Tab containment
- mobile header preserves Back plus current Xignal label; bottom navigation exposes Today, Evidence, Timeline and AXENT
- generic `navigate()` does not recenter AXIGLAND while the mobile breakpoint is active
- mobile primary actions use >=44 CSS px touch targets; bottom navigation targets are 50 CSS px
- Chrome touch/mobile flow verified at 390×844: Today → Open Xignal → Evidence → Timeline → AXENT → close → Back, with current Xignal context preserved and zero page errors
- Chrome 360×800 baseline verified: canvas/workspace hidden, mobile header/nav visible, 3 Today items present, no horizontal body overflow
- Chrome mobile screenshot review completed for Today, focused Xignal and AXENT sheet; layout is deliberate and readable rather than responsive-canvas compression
- focused FR-16/FR-15/FR-14/FR-13/FR-12/FR-09/HFX contracts: 51 PASS after preserving the exact FR-09 desktop deep-link contract
- final Chrome touch revalidation at 390×844 after FR-09 compatibility repair: Open Xignal → Evidence → Timeline → AXENT → close → Back; AXENT transform settled to open state, dialog/modal semantics correct, context preserved, no overflow, zero page errors
- full pytest: 520 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Node syntax: PASS (`app.js`, `presentation.js`, `locale-es.js`)
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0042 accepted and indexed

### Work
Do not shrink desktop AXIGLAND blindly. Mobile minimum: Today → Xignal → Why it matters → Evidence → Timeline → contextual AXENT. Full canvas is optional and must earn inclusion through task tests.

### Acceptance
- Core value task works on mobile viewport.
- No dependency on hover/pan precision.
- Drawers/sheets preserve back/context.
- Evidence path complete.

### FRONTIER_CLOSURE
Future audit can evaluate a deliberate mobile product rather than responsive CSS alone.

# PHASE G — MAKE LEARNING OPERATIONAL

## FR-17 — Emit Learning Events From Real Execution

**Status:** DONE
**Depends on:** FR-04
**Priority:** P1

**Closure evidence (2026-10-01):**
- first-Xeed bootstrap application now requires Learning Memory, execution identity and code SHA and appends a BOOTSTRAP event automatically
- bootstrap reuse count is derived from distinct observation ids in RichSubjectState; `build_bootstrap_plan()` no longer accepts caller-supplied reuse count
- source acquisition and Observation Memory ingestion are separate Learning Event kinds and causal phases
- successful source acquisition records the immutable CAS artifact ref, source policy identity/fingerprint and observation fingerprint
- Observation Memory ingestion derives inserted/no-change state, exact before/after state fingerprints, observation count and changed-field count from the real mutation
- representation derives dimensions-became-answerable from deterministic assessment before/after the actual RichSubjectState transition
- semantic extraction count remains derived from the normalized candidate set
- adaptive-research resolved-objective yield is derived from the governed Prime route plus actual made-progress result; the executor can no longer submit that count
- causal event ids are ordered within one execution as 00-bootstrap → 01-source → 02-ingestion → 03-representation → 04-semantic → 05-prime:<index>, so same-timestamp durable history remains reconstructible
- Prime budget stops retain the exact ADR-0029 stop reason; acquisition/ingestion/representation/semantic/Prime failures are appended before re-raise
- a retry uses a distinct execution id and produces a separate append-only failure event rather than overwriting the previous attempt
- LearningYield now retains `observations_reused`; SQLite persistence reads legacy payloads without that field as zero reuse
- UNKNOWN operational cost remains `LearningCost(amount_microunits=None)`; no zero-cost claim is fabricated
- E2E test proves one execution creates ordered BOOTSTRAP → SOURCE_ACQUISITION → OBSERVATION_INGESTION → REPRESENTATION → DETERMINISTIC_EVALUATION history with exact code/policy/artifact refs
- adaptive research integration test emits ADAPTIVE_RESEARCH and derives one resolved research objective from real work progress
- retry test retains two distinct failed SOURCE_ACQUISITION events with UNKNOWN cost
- focused FR-17/bootstrap/Prime/Learning/Execution Budget suite: 54 PASS
- full pytest: 529 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0043 accepted and indexed

### Frontier finding
Learning Memory is a sound store but is not yet automatically fed by integrated execution.

### Work
Emit append-only events for source acquisition, observation ingestion, structured evaluation, adaptive research, bootstrap, failures, NO_CHANGE and stop/budget reasons. Derive counts from actual execution whenever possible; do not accept caller-invented reuse/yield when derivable.

### Acceptance
- One E2E run creates a reconstructible Learning Memory sequence.
- Exact artifact/policy/code refs included.
- Missing cost remains UNKNOWN.
- Retry/failure events retained.

### FRONTIER_CLOSURE
Future audit cannot say Learning Memory is disconnected from execution.

## FR-18 — Replay Reference Completeness

**Status:** DONE
**Depends on:** FR-17
**Priority:** P1

**Closure evidence (2026-10-01):**
- every Learning Event now carries a typed replay classification: REPLAYABLE or NON_REPLAYABLE
- replayable events carry concrete named references rather than relying on fingerprints alone
- missing replay inputs require an explicit non-replayable reason code
- source acquisition replay captures immutable artifact ref, source policy id/fingerprint, observation fingerprint and code SHA
- Observation Memory ingestion replay captures immutable artifact, governed observation id/fingerprint, source policy refs and code SHA
- document representation replay captures source + representation artifacts, representation id/version, normalization version, source observation fingerprint, source policy fingerprint and code SHA
- deterministic Prime work is replayable from exact state fingerprint, routing-policy version, route and code SHA
- semantic extraction and structured/adaptive provider-bound work fail closed as NON_REPLAYABLE when exact model/harness identity is unavailable; provider/provider-version and other available refs remain retained
- bootstrap is explicitly NON_REPLAYABLE until the full governed plan payload is retained; plan/policy/state/code refs remain inspectable
- budget-stop events are explicitly NON_REPLAYABLE until exact controller policy/state payloads are retained; exact policy/state fingerprints and stop reason remain inspectable
- LearningReplayReference.require(name, expected) detects absent references and version/value mismatch explicitly
- SQLite persists replay disposition/references/reason; pre-FR-18 payloads remain readable as NON_REPLAYABLE: REPLAY_REFERENCE_NOT_RECORDED
- replay metadata stores references/versions rather than duplicating protected payloads; existing rights/privacy/retention boundaries remain authoritative
- representative E2E run proves captured source, ingestion, representation and deterministic evaluation replayability while bootstrap is explicitly classified non-replayable
- structured semantic/evaluator integration proves provider-bound work is not falsely promoted to replayable when model/harness refs are missing
- focused FR-18/FR-17/Learning/Prime/Bootstrap/Budget suite: 61 PASS
- full pytest: 536 PASS using external `--basetemp` to avoid the known Windows user-temp ACL issue
- Ruff format/check: PASS
- mypy: PASS (118 source files)
- Architecture Guard: PASS
- axignal-governance: PASS
- git diff --check: PASS
- ADR-0044 accepted and indexed

### Work
Guarantee replay identity for observation artifact, representation/compiler version, decision contract, state, provider/model/harness, interpretation policy, source policy and code SHA. Respect privacy/retention/rights.

### Acceptance
- Representative event can be replayed or explicitly classified non-replayable with reason.
- Fingerprint is not treated as replay by itself.
- Version mismatch is detectable.

### FRONTIER_CLOSURE
Future audit cannot correctly state fingerprint != replay as an unresolved Learning Memory flaw.

## FR-19 — Governed Policy Candidate / Replay / Shadow

**Status:** NOT_STARTED  
**Depends on:** FR-18  
**Priority:** P1

### Work
Implement offline-only immutable PolicyCandidate, baseline comparison, ReplayEvaluation, held-out organization/time split, ShadowPolicy with no side effects, counter-metrics and regression reporting. No automatic promotion.

### Acceptance
- Candidate cannot mutate production.
- Comparison preserves UNKNOWN/abstention.
- Negative/failed runs included.
- No sealed-label tuning.

### FRONTIER_CLOSURE
Future audit finds actual governed learning machinery rather than only an observational ledger.

## FR-20 — Policy Promotion / Rollback Gate

**Status:** NOT_STARTED  
**Depends on:** FR-19  
**Priority:** P2

### Work
Implement versioned human/governance promotion with evidence requirements, holdout, approval record, canary where applicable, rollback pointer and no history rewrite.

### Acceptance
- Production policy cannot self-promote from runtime yield.
- Rollback tested.
- Decision trace durable.

### FRONTIER_CLOSURE
Goodhart/reward-hacking risk is governed by explicit promotion boundaries, not only documentation.

# PHASE H — PROVIDER AND DECISION EVIDENCE

## FR-21 — StructuredEvaluatorPort Contract Evolution

**Status:** NOT_STARTED  
**Depends on:** FR-04  
**Priority:** P1

### Work
Finalize the provider-neutral evaluator boundary, including the unresolved distribution issue: selected option; optional provider distribution; explicit distribution availability; optional confidence only when provider semantics define it; replay reference; capability profile. Never fabricate 1/0 probabilities for providers that return only a selected choice.

### Acceptance
- Structured judgment semantics deliberately evolved/migrated.
- Contract supports Jev, Decisions-like and Luna-structured baselines without provider leakage.
- Tests preserve UNKNOWN.

### FRONTIER_CLOSURE
Future audit finds a real non-provider-specific evaluator contract suitable for bakeoff.

## FR-22 — Evaluator Decision Lab Bakeoff

**Status:** NOT_STARTED  
**Depends on:** FR-21, FR-19  
**Priority:** P1

### Work
Compare on the same versioned state/contracts: deterministic baseline where applicable, Luna structured, OpenAI Decisions if access/API terms permit, and TypeSafe Jev if rights/terms permit. Measure class errors, false OBSERVED/POTENTIAL, abstention/coverage, calibration when semantically valid, schema failure, latency, retries, known/unknown cost, language/context sensitivity and disagreement/error correlation.

### Acceptance
- No vendor declared winner without AXIGNAL-specific dataset evidence.
- Same input/compiler contracts.
- Costs measured or UNKNOWN.
- Results stored through experiment/Learning Memory artifacts.

### FRONTIER_CLOSURE
Future audit can reference AXIGNAL-specific evidence instead of provider marketing or architectural speculation.

# PHASE I — HIGH-RISK WORLD-MODEL FOUNDATIONS

## FR-23 — Identity Resolution Hardening

**Status:** NOT_STARTED  
**Depends on:** FR-04  
**Priority:** P1

### Frontier finding
Incorrect entity merge can poison shared AXIGLAND and many Xeeds.

### Work
Improve resolution beyond exact-name where justified; preserve ambiguity; add correction/reversal lineage; define merge/split policy; subscriber input remains attention/context, not truth authority.

### Acceptance
- Ambiguous identity fails closed or remains unresolved.
- Correction does not erase history.
- Shared observations cannot silently cross wrong entities.

### FRONTIER_CLOSURE
Future audit sees identity contamination as governed rather than an unbounded systemic risk.

## FR-24 — Rights / Reuse / Applicability Contract

**Status:** NOT_STARTED  
**Depends on:** FR-04, FR-23  
**Priority:** P1

### Work
Make reuse explicitly conditional on rights, provenance, currentness, scope/applicability and public/private boundary.

### Acceptance
- A reusable observation may still be rejected for current use.
- Private scope cannot leak into global world.
- STALE != FALSE and INACCESSIBLE != FALSE.

### FRONTIER_CLOSURE
Future audit cannot state shared reuse ignores rights/currentness/applicability.

## FR-25 — Temporal Currentness / Reobservation Core

**Status:** NOT_STARTED  
**Depends on:** FR-24  
**Priority:** P1/P2

### Work
Implement deterministic temporal-state transitions and reobservation requirements without erasing history.

### Acceptance
- CURRENT/STALE/UNKNOWN/HISTORICAL transitions tested.
- Reobservation appends history rather than overwriting it.
- Only affected dependent dimensions reevaluate.

### FRONTIER_CLOSURE
Future audit no longer describes temporal behavior as mostly timestamps without governed lifecycle.

# PHASE J — ECONOMICS, PRODUCT VALIDATION AND PRODUCTION

## FR-26 — Unit Economics Instrumentation

**Status:** NOT_STARTED  
**Depends on:** FR-17  
**Priority:** P1 PARALLEL once real runs exist

### Work
Measure by Xeed/cohort first-value cost, germination cost, maintenance/refresh cost, cost coverage, reuse ratio, fresh reuse ratio, time to first useful Xignal, evidence inspection, corrections and contribution-margin inputs. Do not infer willingness-to-pay from usage alone.

### Acceptance
- Missing cost never silently becomes zero.
- Shared/private cost attribution methodology explicit.
- Economics trace reaches underlying learning events.

### FRONTIER_CLOSURE
Future audit can inspect real cost/reuse evidence rather than calling unit economics wholly unknown.

## FR-27 — One Buyer / One Job Pilot Contract

**Status:** NOT_STARTED  
**Depends on:** FR-07, FR-09, FR-26  
**Priority:** P0 PRODUCT

### Work
Choose one concrete job/buyer hypothesis without redefining AXIGNAL. Measure whether the Xignal advances a decision, whether evidence is trusted/inspected, whether the user returns because something changed, willingness to pay and value of additional Xeeds. Commercial outcome never validates truth.

### Acceptance
- Pilot protocol and evidence exist.
- Failure is a valid documented outcome.
- Pricing remains hypothesis until observed.

### FRONTIER_CLOSURE
Future audit has real buyer/job evidence instead of only product thesis.

## FR-28 — Landing/Product Promise Reconciliation

**Status:** NOT_STARTED  
**Depends on:** FR-09, FR-27  
**Priority:** P1 UX/Product

### Work
Align landing with demonstrated product: observing economic brain, concrete external-change example, agencies included but not totalizing the definition, no unsupported capability claims, and visual promise matching app experience.

### Acceptance
- Landing → Plant Xeed → first value story coherent.
- No SEO/GEO-only narrowing.
- No capability claim unsupported by product/runtime evidence.

### FRONTIER_CLOSURE
Future UX audit no longer finds a major landing/product expectation gap.

## FR-29 — Production Runtime Integration

**Status:** NOT_STARTED  
**Depends on:** FR-06, FR-07, FR-17  
**Priority:** P0 before production claims

### Work
Integrate the proven vertical path in the actual app/runtime using real persistence/configuration. Before production inspect deployment/service/proxy/ports/persistence/version, isolate AXIGNAL from other projects, define rollback and protect secrets.

### Acceptance
- Exact deployed SHA known.
- Health/runtime verification complete.
- No cross-project runner/service/port reuse.
- Persisted observation/learning behavior verified.

### FRONTIER_CLOSURE
Future audit can inspect actual service integration instead of correctly reporting production as DESCONOCIDO.

## FR-30 — Production E2E: First Xeed → First Proof

**Status:** NOT_STARTED  
**Depends on:** FR-29, FR-09, FR-10  
**Priority:** GOAL

### GOAL
Verify in browser against production or explicitly production-equivalent environment: PLANT XEED → governed bootstrap → partial dimensional answerability → useful Xignal → Today → focused AXIGLAND → Show how AXIGNAL knows → evidence/currentness/UNKNOWN → Learning Memory event → return/reload continuity.

### Acceptance
- No demo/example data masquerading as real.
- UI loading/errors/insufficient-evidence states tested.
- Keyboard/responsive smoke completed.
- Exact trace from UI Xignal to observations.
- Learning Memory event linked.
- User can state what changed and why AXIGNAL believes it.

### FRONTIER_CLOSURE
The core findings of both Frontier audits are materially closed; FIRST_MAP_WOW is no longer merely aspirational for the tested path.

# PHASE K — FRONTIER RE-AUDIT

## FR-31 — Frontier Re-Audit Preparation

**Status:** NOT_STARTED  
**Depends on:** FR-30  
**Priority:** FINAL

### Work
Prepare current SHA, clean-tree evidence, validation output, task closure matrix, runtime/deployment evidence, UX screenshots/flows, unit-economics evidence where available and explicit remaining UNKNOWN/DEFERRED items. Do not tell the Frontier Advisor which conclusions to reach.

### Acceptance
- Every DONE task links evidence.
- Remaining gaps explicit.
- No stale roadmap status.
- Fresh independent audit requested using the same core criteria.

### FRONTIER_CLOSURE
The next report evaluates the evolved product rather than rediscovering already-known, already-fixed gaps.

# 5. Execution order

Strict default order:

FR-00 → FR-01 → FR-02 → FR-03 → FR-04 → FR-05 → FR-06 → FR-07 → FR-08 → FR-09 → FR-10 → FR-11 → FR-12 → FR-13 → FR-14 → FR-15 → FR-16 → FR-17 → FR-18 → FR-19 → FR-20 → FR-21 → FR-22 → FR-23 → FR-24 → FR-25 → FR-26 → FR-27 → FR-28 → FR-29 → FR-30 → FR-31

Dependencies may permit selected independent work, but sequence changes require an explicit roadmap edit with rationale. Do not skip P0 gates to accelerate cosmetic UI.

## 6. Global Definition of Done

For each task record:
- BASE_SHA
- WORK_BRANCH
- HEAD_SHA
- root cause
- changed files/contracts
- tests run and exact result
- Architecture Guard
- governance
- CI URL/run
- merge SHA
- deployment SHA where applicable
- E2E evidence where applicable
- remaining known gaps

Never use DONE when the actual state is only IMPLEMENTED.

## 7. Rejection criteria

A proposed change is rejected if it weakens EvidenceAdmission; makes model/provider output canonical; conflates Xeed with Organization; introduces a second AXIGLAND; turns UNKNOWN into FALSE; promotes POTENTIAL to OBSERVED without evidence; makes commercial engagement a truth signal; introduces an opaque universal score; converts AXIGNAL into CRM/workflow suite; optimizes benchmark/yield at the expense of epistemic correctness; or creates architecture solely because the Frontier Advisor suggested it.

## 8. Success condition

This roadmap succeeds when AXIGNAL can demonstrate, with real integrated evidence:

1. a Xeed reaches useful partial value without unnecessary completeness;
2. research happens only when worthwhile and bounded;
3. Prime executes through one governed composition path;
4. a Xignal is explainable to source/time/unknown;
5. the first user experience starts with meaning, not system complexity;
6. AXENT preserves current context and continuity without conflation;
7. Learning Memory records actual execution and enables replayable comparison;
8. provider selection is evidence-driven and replaceable;
9. world-model reuse is rights/currentness/applicability governed;
10. unit economics and one buyer/job hypothesis have real evidence;
11. the production first-Xeed-to-proof journey is verified E2E.

At that point AXIGNAL has not finished. It has crossed from architectural promise to a measurable, governed product loop.
