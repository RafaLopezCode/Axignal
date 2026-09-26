# Feature Specification: P0-HFX-00 Human First Cognitive UX Doctrine

**Status:** Canonized product doctrine and target architecture; documentation-only, pre-implementation.  
**Authority:** MASTER §55; Constitution XIX–XXII; ADR-0016 and ADR-0017.  
**Objective:** Converge Human First research and doctrine into AXIGNAL's canonical artifacts without starting runtime/UI/persistence implementation.

## User scenarios and acceptance

### Story 1 — Understand one object at the right depth

As an AXIGNAL subscriber, I need the same governed object to make sense in
plain language and remain inspectable in technical depth so that expertise
changes detail, not truth.

1. Human-facing material output begins from its meaning and why it matters.
2. `GLANCE → UNDERSTAND → REASON → PROVE` is semantic depth, not a required
   wizard; direct navigation to evidence, evolution, comparison and AXENT is
   possible.
3. A professional metric exposes plain meaning, technical definition and
   interpretation boundary where material.
4. Specialist access to method, denominator, scope, instrument/version, sample,
   comparison and evidence preserves parent object/context.

### Story 2 — Understand a joined output without mental joins

As a user, I need AXIGNAL to present a truthful cross-domain meaning it has
already derived, while preserving constituent dependencies, so I can
understand what matters without visiting disconnected modules and comparing
from memory.

1. A composite never becomes a FAXT merely through presentation.
2. If evidence, comparability or scope is missing, the composite preserves
   uncertainty instead of fabricating a join.
3. Every material composite can navigate to its derivation/evidence.

### Story 3 — Resume an investigation and know why

As a returning user, I need AXIGNAL to restore the question, then-state,
unresolved items and changes since I last looked; if it recorded why I began,
I need the actual provenance, not a plausible generated narrative.

1. Continuity (where/what/open/changed) is distinct from provenance (why and
   what triggered attention).
2. Missing origin stays `UNKNOWN`; no model inference backfills it.
3. Current knowledge never rewrites the historical epistemic state.
4. Reconstruction is limited by retained revisions, evidence rights and
   deletion policy; the system states when history is incomplete.

### Story 4 — Protect multi-client consultancy scope

As a consultant managing many organizations within one tenant, I need each
private AXENT retrieval to resolve the active client before retrieval so one
client's context cannot appear in another client's investigation.

1. Private scope is tenant → client context → Xeed → thread/object.
2. Client context is distinct from canonical organization identity.
3. Default scope is the active client; portfolio retrieval is explicit,
   authorized and visibly attributed.
4. Similarity, URL parameters and model output never authorize or silently
   switch client. Stale responses from a prior client are not rendered.

### Story 5 — Inspect AXENT's explanation and uncertainty

As a subscriber, I need AXENT to navigate to the real object, derivation and
evidence while keeping uncertainty and source scope visible, so explanation
supports verification rather than persuasion.

1. AXENT is contextual navigation, not the only route to basic comprehension.
2. It has no direct database credentials or arbitrary SQL access.
3. It consumes the minimum authorized typed context after deterministic
   routing; unknown origin and unsupported claims remain unknown.

### Story 6 — Review accessible visual meaning

As a subscriber, including a user with accessibility needs, I need epistemic,
temporal and attention meaning to remain understandable without color-only
coding or graph-only interaction.

1. UNKNOWN is not false/zero; POTENTIAL is not OBSERVED; historical is not
   current. These are not collapsed into one status.
2. Color is never the only epistemic channel.
3. Future production targets WCAG 2.2 AA and COGA-informed manual/user review;
   conformance and automated tests alone do not prove cognitive usability.
4. Exact colors, icons, charts, graph layout, motion and density remain
   hypotheses until tested.

## Functional requirements

- **FR-001:** One MASTER canonizes Human First as a core product capability
  while preserving one canonical AXIGLAND and existing DRI four-family doctrine.
- **FR-002:** Expertise may change explanation depth/density but never canonical
  truth or epistemic state.
- **FR-003:** Cognitive Compression preserves material scope, epistemic/temporal
  qualification, denominator, contradiction and evidence access.
- **FR-004:** Semantic depth is directly navigable and preserves object/focus
  context; it is not a mandatory linear screen sequence.
- **FR-005:** Information taxonomy is human-level and is not a 1:1 backend
  ontology/navigation mapping.
- **FR-006:** Material output has conceptual identity, meaning, why-it-matters,
  independent epistemic/temporal/attention axes, useful metric context,
  derivation, unknowns, evidence and navigation.
- **FR-007:** No mental join is delegated when AXIGNAL already governs the
  join; composite outputs preserve dependency/provenance.
- **FR-008:** Attention is a projection and must not become truth or an opaque
  canonical priority score.
- **FR-009:** Continuity and cognitive provenance remain distinct; unavailable
  origin remains `UNKNOWN`; historical then-state is not overwritten.
- **FR-010:** AXIGLAND, Xeed germination context and private cognitive state are
  separate authorities; private state does not mutate canonical truth.
- **FR-011:** Private routing resolves tenant/client/Xeed/user/thread
  authorization before retrieval. Portfolio mode is explicit and separately
  authorized.
- **FR-012:** Future AXENT reads use typed Context Broker operations, never
  arbitrary SQL/direct DB access or model-generated scope.
- **FR-013:** PostgreSQL/pgvector is documented as a hypothesis requiring
  workload/security benchmark; no database is selected by this slice.
- **FR-014:** Research identifies empirical evidence, established guidance,
  AXIGNAL inference, CTO hypothesis and canonical AXIGNAL decision separately.
- **FR-015:** Research protocol covers representative expertise groups,
  comprehension, epistemic accuracy, navigation, evidence, resumption,
  trust calibration, multi-client isolation and cognitive accessibility.
- **FR-016:** No runtime, provider, UI, schema, migration, embedding,
  dependency or deployment is created.
- **FR-017:** No AXIGNAL runtime/provider calls, live Jev, TypeSafe key access
  or unrelated slice start occurs.

## Assumptions and scope

- P0-DRI-00 is on main; four DRI families are already in MASTER §54.
- PR #18 is independent and must remain OPEN/unmerged/untouched at its
  authorized SHA.
- HCI publications inform limits and study questions; they do not show an
  AXIGNAL result.
- Exact visual semantics and technical persistence remain open pending
  prototype/workload evidence.
- Source-pack documents are reference input only and are not repository
  deliverables.

## Out of scope

Dashboard/UI/prototype, frontend routes/components, accessibility runtime,
database schema or RLS policies, migrations, pgvector enablement, embeddings,
memory broker/router runtime, AXENT tools/actions, telemetry, analytics,
providers, experiments calling models, production deployment, P0-HFX-01/02,
P0-DRI-01, P0-EOI-01 and P0-JEV-04.

## Success criteria

- **SC-001:** MASTER §55 is the one durable product authority; pinned hash is
  updated and no second MASTER is created.
- **SC-002:** Constitution/ADRs/Subscriber Experience/Design Doctrine and
  governance converge without contradiction or UI implementation.
- **SC-003:** Cognitive compression, semantic zoom, navigation, continuity,
  provenance, amortization, Interpretation Debt, Expertise Tax, no mental
  joins, meaning-before-metrics, evidence-on-demand and accessibility are
  represented accurately with hypotheses labeled.
- **SC-004:** Human taxonomy and conceptual Human Output Contract preserve
  separate semantic, epistemic, temporal, attention and archetype axes.
- **SC-005:** Three authorities, multi-client routing, portfolio authorization,
  typed AXENT boundary, event/checkpoint model and deletion tests are specified.
- **SC-006:** HCI research includes primary/official sources, limitations and
  clear separation of external evidence from AXIGNAL hypotheses.
- **SC-007:** User research protocol includes all future acceptance scenarios
  A–J and repeatable benchmark tasks.
- **SC-008:** Full deterministic gates, documentation-only scope audit and
  Graphify checks are recorded; one unmerged PR is opened against `main`, exact
  head CI is green, PR #18 remains unchanged and no next slice begins.
