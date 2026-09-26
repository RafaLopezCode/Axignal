# Feature Specification: P0-EOI-00 Economic Brain Doctrine

**Status:** Converged product doctrine; documentation-only slice.\
**Authority:** MASTER Product Model §§46, 53; ADR-0012 and ADR-0013.\
**Objective:** Canonize AXIGNAL as an observing economic brain whose core value is explainable Economic Opportunity Intelligence compounded through governed, reusable temporal knowledge.

## User scenarios & acceptance

### Story 1 — Discover relevant activity

As a subscriber, I need AXIGNAL to connect observable demand/activity to
capabilities, geography, reach, actors, time and evidence so that it can surface
what may deserve attention and explain why without claiming a customer or sale.

1. Latent demand is distinct from materialized economic activity.
2. General demand, projects, procurement and awarded projects are conceptual
   signal families; no signal alone establishes a customer or relationship.
3. A surfaced opportunity is derived, temporal, explainable and `POTENTIAL` by
   default; it is not FAXT, a lead, a customer or an observed relationship.
4. Procurement does not imply a customer; an award does not imply a
   subcontract; capability match does not imply commercial fit.
5. Geography is reasoning context and Economic Reach may differ per capability.
   Headquarters jurisdiction does not set total market reach.
6. Sensor selection considers capability, justified reach, activity geography,
   source coverage and temporal context. TED is an example, not a privileged
   source or domain.
7. No universal opaque opportunity score is permitted. Every surfaced
   opportunity needs a persisted explanation trace and supporting provenance.

### Story 2 — Reuse knowledge without compounding error

As a returning subscriber, I need AXIGNAL to reuse valid knowledge, compare it
with new observations, verify what may have changed and preserve history so
that research does not restart from zero or hide uncertainty.

1. Reuse retains provenance, epistemic state, dependencies and currentness.
2. Stale or changed knowledge is verified, reevaluated or marked stale/unknown;
   reuse is not permanent trust.
3. Upstream changes support downstream reevaluation without erasing history.
4. Compounding error remains an inspectable systemic risk.
5. Persistent governed economic understanding and reusable reasoning
   infrastructure are the moat hypothesis; low token cost is not the moat.

### Story 3 — Inspect AXENT reasoning

As a subscriber, I need Today, Explore, Evolution and Evidence to reveal
relevant economic activity, temporal change, opportunity dimensions and why a
signal appeared, while Ask AXENT researches missing context or preserves
unknowns rather than guessing.

## Functional requirements

- **FR-001:** The single MASTER defines the economic brain, opportunity and
  compounding doctrine; no competing MASTER is created.
- **FR-002:** Sensor, demand, capability-specific reach and opportunity remain
  conceptual semantics in this slice; no technical ontology explosion occurs.
- **FR-003:** Deterministic computation is preferred first; typed bounded
  judgment is used only when needed and answerability is satisfied.
- **FR-004:** Missing required context routes to AXENT research and then
  reevaluation, or remains unknown/abstained if insufficient.
- **FR-005:** Evaluators are replaceable, non-canonical and not live-authorized.
- **FR-006:** Opportunity explanations preserve temporal context, evidence,
  provenance, derivation, typed dimensions and uncertainty; post-hoc generated
  justification is prohibited.
- **FR-007:** User/subscriber activity directs attention, not canonical
  conclusions; no CRM/workflow behavior is introduced.
- **FR-008:** Compounding reuses valid knowledge with freshness and dependency
  controls; no metric targets or performance claims are invented.
- **FR-009:** README, Constitution, product, communication, architecture, ADR
  and graph-design skill semantics converge on the MASTER.
- **FR-010:** No runtime, production, provider, migration, dependency,
  deployment, source acquisition or UI implementation changes occur.
- **FR-011:** No Jev, TypeSafe, OpenAI or other external model calls or
  credential access occur during this slice.

## Key concepts

Economic Sensor; DemandSignal; latent/materialized demand; project/procurement
signal; Economic Reach; capability; derived Opportunity; Opportunity PATHX;
typed Economic Judgment; ExplanationTrace; governed reusable knowledge;
currentness; provenance; compounding error. These are semantic concepts only;
this spec does not require one Python class per concept.

## Assumptions

- The MASTER remains the only semantic authority and retains existing
  epistemic/CRM boundaries.
- Source coverage, legal rights, provider authorization and real-world
  opportunity performance are not established here.
- Measurement directions are future hypotheses, not current features.

## Out of scope

P0-EOI-01 contracts; any code or runtime; schema/migrations; source registry
implementation; TED/SAM.gov integration or crawlers; global sensors; subscriber
UI; Opportunity/DemandSignal/EconomicReach classes; live Jev/TypeSafe/provider
use; corpus, experiment, production, deployment or new rights research.

## Success criteria

- **SC-001:** All fixed clarifications in `clarifications.md` are represented
  consistently in MASTER, ADRs, Constitution/AGENTS, product, communication,
  architecture and design guardrails.
- **SC-002:** Opportunity remains derived and `POTENTIAL` by default with no
  procurement/customer, award/subcontract or capability/fit conflation.
- **SC-003:** Cognition is deterministic-first, answerability-gated,
  provider-replaceable and non-authoritative; missing information is researched
  or left unknown, not guessed.
- **SC-004:** Reuse preserves provenance, epistemic state, currentness,
  dependencies and temporal history.
- **SC-005:** All required deterministic gates and Graphify checks are recorded;
  no external cognitive/runtime calls or secrets are used.
- **SC-006:** One documentation-only commit and one unmerged PR are created
  against `main`; PR #18 remains unchanged.
