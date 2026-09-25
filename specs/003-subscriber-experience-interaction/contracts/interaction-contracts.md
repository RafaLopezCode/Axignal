# P0-INTERACTION-01 Contract Catalogue

**Status**: PROPOSED / PRE_IMPLEMENTATION\
**Authority**: Subordinate to MASTER, Constitution, accepted ADRs and Atlas.\
**Interpretation**: These contracts specify future responsibilities and
semantics; they are not executable interfaces or runtime evidence.

Shared requirements: every output is account/Xeed authorized, scoped and
versioned; canonical state remains AXIGLAND; unknown is not false; unsupported
or unavailable is not empty; model/user/export output is not canonical truth.

## C01 — Subscriber Projection

- **Producer**: AXIGNAL read/projection layer. **Consumer**: subscriber UI,
  Ask AXENT context builder, authorized portability/read adapters.
- **Must convey**: Xeed and organization identity; permitted scope; projection
  version; `as_of`/generated time; epistemic/currentness state; human-readable
  summary and references to underlying state.
- **Invariant**: human-first projection, not canonical mutation surface; only
  authorized account/Xeed data is included.
- **Failure/unknown**: distinguish empty, partial, stale, unknown, denied,
  unavailable and failed; disclose omitted/unsupported projection portions.

## C02 — Germination Projection

- **Producer**: real germination/domain/operational state; **consumer**:
  subscriber Today/onboarding surfaces.
- **Must convey**: actual stage/event, stage status, safe discoveries, blockers
  or knowledge gaps, currentness and readiness evidence. Human stage labels may
  map to resolving identity, capabilities, markets, structure, neighbourhood,
  open questions, verification, paths, representation evaluation and map
  readiness.
- **Invariant**: `GERMINATION_UI = PROJECTION(REAL_GERMINATION_STATE)`;
  no timer, synthetic percentage, DISCOVERING-as-SUPPORTED or LIVE-as-DONE.
- **Failure/unknown**: expose queued, active, partial, insufficient evidence,
  retrying, blocked, failed and unavailable distinctly; keep safe partial
  discoveries available with their epistemic state.

## C03 — Today / Attention / Material Change

- **Producer**: deterministic material-change policy over authorized state;
  **consumer**: Today and returning-user feed.
- **Must convey**: change type, affected object, before/after or event interval,
  materiality rationale, evidence/derivation references and deduplication
  identity. Candidate changes include relationships, evidence/currentness,
  contradictions, resolved gaps, PATHXs and representation signals/anomalies.
- **Invariant**: materiality is explicit, policy-backed and interpretable;
  ranking is not an opaque universal score and does not imply causality.
- **Failure/unknown**: say whether no material change was found or evaluation
  was unavailable/partial; do not present mere observation or LIVE state as
  material completion.

## C04 — Evolution / Temporal Projection

- **Producer**: temporal AXIGLAND read projection; **consumer**: Evolution,
  Today and contextual Ask AXENT.
- **Must convey**: selected instant/interval, valid/observed time distinctions
  supported by domain, changes, currentness and historical projection version.
- **Invariant**: preserve “what was known when”; later evidence does not silently
  rewrite earlier observation. A change is not asserted without comparable
  state and lineage.
- **Failure/unknown**: gaps, incomparable snapshots, stale state and unknown
  periods are explicit; never interpolate as observed fact.

## C05 — Evidence Drill-down

- **Producer**: AXIGNAL explanation/provenance projection; **consumer**:
  subscriber UI and Ask AXENT references.
- **Must convey**: Discovery → Explanation → Derivation → FAXTs → Evidence →
  Source, with stable references, supporting/contradicting state, source and
  observation time/currentness where available.
- **Invariant**: every material/surprising claim can answer “Why am I seeing
  this?”; cognitive explanation complements, never replaces, deterministic
  evidence inspection.
- **Failure/unknown**: missing, inaccessible, stale or contradictory links are
  declared; do not fabricate a source or collapse disagreement.

## C06 — Graph / Map Projection

- **Producer**: AXIGNAL-owned semantic cartography/projection; **consumer**:
  replaceable renderer adapter and other question-appropriate UI.
- **Must convey**: scoped nodes/relationships, semantic/epistemic classes,
  temporal/currentness information, focus/selection and references needed for
  detail inspection. Representation follows question: feed, map, graph,
  timeline, evidence, PATHX, corporate structure, uncertainty or anomaly view.
- **Invariant**: AXIGNAL owns meaning; renderer draws. Graph is a projection,
  not the entire subscriber UI. No graph hairball as success criterion.
- **Failure/unknown**: unknown, potential, observed, stale and contradictory
  relations remain distinct; renderer degradation does not alter domain state.

## C07 — PATHX Presentation

- **Producer**: authorized PATHX read projection; **consumer**: map, Explore,
  Evidence and Ask AXENT.
- **Must convey**: endpoints, ordered steps, constituent relationship
  references, direction/meaning, time/currentness, evidence and explainability.
- **Invariant**: PATHX is an explainable economic path, not proof of a direct
  relationship between endpoints.
- **Failure/unknown**: incomplete/stale/ambiguous step or evidence is shown;
  do not draw a completed path or claim directness from missing links.

## C08 — Ask AXENT Context

- **Producer**: AXIGNAL query/context builder; **consumer**: policy-selected
  CognitiveProvider. Input includes user question, current view, selected
  objects and authorized Xeed projection.
- **Must convey**: interaction class (EXPLAIN, ANALYZE, COMPARE, EXPLORE or
  DEEP_RESEARCH_REQUEST), purpose/scope, minimum relevant structured objects,
  FAXTs/INXIGHTs/PATHXs/evidence references, temporal/currentness,
  contradictions/gaps and authorization decision/reference.
- **Invariant**: `AVAILABLE_CONTEXT != REQUIRED_CONTEXT`; smallest useful
  structured context wins. Never send full Xeed by default, secrets,
  unnecessary PII or unrelated subscriber data.
- **Failure/unknown**: deny before retrieval if unauthorized; distinguish
  absent knowledge from retrieval/tool failure and insufficient context.

## C09 — Ask AXENT Response

- **Producer**: provider response mediated by AXIGNAL; **consumer**: subscriber
  UI. Canonical name: **Ask AXENT — by AXIGNAL**.
- **Must convey**: answer/limitation, request scope, distinction between
  referenced AXIGNAL state and analysis, inspectable references, uncertainty,
  and whether new evidence is required.
- **Invariant**: LLM output is not FAXT, canonical truth, or write authority;
  external model knowledge is not AXIGLAND. Responses are grounded in request
  context and cannot bypass authorization.
- **Failure/unknown**: malformed, ungrounded, unsupported or provider-failed
  output is rejected or clearly degraded; state uncertainty, never fill evidence
  gaps silently.

## C10 — Ask AXENT Research Escalation

- **Producer**: AXIGNAL interaction policy; **consumer**: separately governed
  AXENT closed research loop and subscriber status projection.
- **Must convey**: explicit research objective, user-directed attention,
  bounded scope, evidence gap, authorization and eventual evidence/structured
  state/JEV/policy outcome before any authorized canonical commit.
- **Invariant**: DEEP_RESEARCH_REQUEST cannot silently become a normal chatbot
  answer. User directs attention; user/model do not direct conclusions.
- **Failure/unknown**: unavailable, insufficient or inconclusive research
  remains unresolved; no evidence means no fabricated completion.

## C11 — Subscriber Authorization

- **Producer**: existing authorization authority; **consumer**: every
  subscriber projection, model context builder, export and Product MCP adapter.
- **Must convey**: principal, account/Xeed scope, permitted operation, decision
  and policy/version reference at the boundary. No detailed auth mechanism is
  selected here.
- **Invariant**: check before retrieval and release; subscriber context is
  account/Xeed scoped; private state cannot silently become public AXIGLAND;
  Ask AXENT cannot bypass AXIGLAND authorization; MCP requires explicit
  authorization.
- **Failure/unknown**: denied, indeterminate and unavailable policy decisions
  fail closed and remain distinguishable from empty results. Recheck before
  response release when scope may have changed.

## C12 — Portable Xeed

- **Producer**: export projection; **consumer**: subscriber or authorized
  external reader. Targets include Xeed.md and Xeed.json.
- **Must convey**: projection/schema version, generated time, organization/Xeed
  identity, authorized scope, temporal/currentness scope, selected objects,
  epistemic status and references/fingerprint where supported.
- **Invariant**: `PORTABLE_XEED_IS_PROJECTION_NOT_AUTHORITY`; export is scoped
  and temporal and cannot update AXIGLAND.
- **Failure/unknown**: partial export declares omissions and version; export
  failure does not change source state. No unsupported object is silently
  recast as fact.

## C13 — Product MCP Read

- **Producer**: separately authorized read/query adapter; **consumer**: external
  agent. Potential operations include organization, economic map, changes,
  INXIGHTs, observed/potential relationships, PATHX, corporate structure,
  representation signals/anomalies, FAXT/evidence, graph explanation, gaps and
  search.
- **Must convey**: operation, caller authorization, bounded query scope,
  projection version/time, epistemic status and references.
- **Invariant**: Product MCP is query surface, not canonical authority. No
  write tool is specified. External agent output cannot mutate AXIGLAND.
- **Failure/unknown**: deny unauthorized scope; distinguish empty, incomplete,
  stale, unknown and tool failure. Tool list is a candidate surface, not an
  implementation commitment.

## C14 — Cognitive Provider Policy

- **Producer**: versioned model policy under ModelRouter/CognitiveProvider;
  **consumer**: background and subscriber cognitive jobs.
- **Current mapping**: background cognitive role → OpenAI / GPT-6 Luna / Batch;
  subscriber role → OpenAI / GPT-6 Luna / Standard Responses. Deep research
  role remains policy-controlled and initially may map to Luna.
- **Invariant**: provider/model is not domain authority; model output is not
  canonical truth; selection is policy, not domain concept; change requires
  representative evaluation. Preserve provider abstraction. Luna does not
  direct AXIGNAL; AXIGNAL uses a model as cognitive metabolism.
- **Failure/unknown**: model/API availability, capability, policy version and
  price are external facts requiring runtime-time verification. No fallback
  silently changes policy or epistemic semantics.

## C15 — Subscriber Cognitive Telemetry

- **Producer**: cognitive request execution boundary; **consumer**: authorized
  operational/economic observability, never as subscriber truth.
- **Candidate measures**: request/Xeed/Xignal IDs (protected as needed),
  interaction class, selected object types, context object/token counts,
  cached/output tokens, provider/model/policy version/reasoning/processing mode,
  latency, estimated/actual cost, evidence-reference count, grounding status,
  follow-up/research escalation and outcome.
- **Invariant**: secrets and unnecessary PII excluded; access-controlled and
  minimized; preserve policy/measurement lineage; `UNKNOWN_COST != ZERO_COST`.
- **Failure/unknown**: incomplete telemetry is marked unavailable/unknown;
  do not impute zero or claim usefulness/causation without defined evidence.
- **Future interpretable measures**: subscriber AI cost per Xeed-month/active
  user, cost/tokens per Ask AXENT query, cached-context ratio, context reuse,
  cost per useful interaction. Usefulness needs a declared observable
  definition.

## UX measurement vocabulary

Candidate observations include time to first understanding/discovery/evidence
inspection/map interaction; germination watch/discovery-open rates; first map
open rate; discovery/evidence drill-down rates; Ask AXENT open/query/contextual
query/follow-up/evidence-open/deep-research rates; 7/30-day return; change feed
and evolution opens. Define denominators, windows, privacy and event lineage
before implementation. These are observations, not causal claims or an opaque
aggregate UX/WOW score.

## Explicitly not specified

No concrete API schema, event bus, database model, UI design system, operational
SLO, rate limit, model prompt, retrieval algorithm, storage/retention policy,
MCP server, authorization mechanism or runtime component is selected or
implemented here.
