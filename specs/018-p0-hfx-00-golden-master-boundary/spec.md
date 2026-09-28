# P0-HFX-00 — Golden Master Reproducibility and Subscriber Boundary

**Status:** CTO-authorized specification and governance evidence
**Authority:** MASTER §§3–7, 15–21, 24–26, 55; Constitution; ADR-0003,
ADR-0005, ADR-0009, ADR-0016–0020
**Implementation boundary:** source manifest tooling and tests; no subscriber
projection runtime

## Objective

Record a deterministic, reviewable source identity for the accepted executable
DeepSeek V2 Golden Master and define the exact anti-corruption boundary by
which authorized global FAXTs could later be presented to a subscriber.

This specification does not accept a new visual design, authorize a new
canonical read path, or claim production integration. Hash equality is source
identity evidence only. The human remains the final visual acceptance
authority.

## Authority and status distinctions

- **Canonical AXIGNAL decisions:** MASTER, Constitution and accepted ADRs.
- **Empirical HCI evidence:** bounded to the cited study/task/population in the
  existing HFX research synthesis; it does not prove AXIGNAL outcomes.
- **CTO hypotheses:** Cognitive Jevons, Interpretation Debt, Human Cognitive
  Amortization and Expertise Tax minimization as product effects remain
  hypotheses, not measured results.
- **Architectural recommendation:** a read-only Subscriber Projection in the
  application layer between authorized canonical reads and presentation.
- **Golden Master authority:** visual, behavioral, geometric, typographic,
  motion, interaction and perceptual hierarchy only. It is not authority for
  canonical truth, relationships, identity, access, provenance, history or
  persistence.

## Requirements

### Source identity

1. Verify the external source only through the versioned v1 manifest. Do not
   infer or reproduce the historical digest's unknown recipe.
2. The manifest must have an explicit path inventory, byte policy, ordering,
   hash construction, exclusions, symlink policy, missing-file behavior and
   unexpected-source behavior.
3. The external root must be an invocation argument, never a committed
   user-specific product setting.
4. Tests use isolated temporary source trees. The actual Golden Master stays
   read-only.

### Subscriber boundary

1. The projection consumes `AuthorizedXeed` and its complete
   `tuple[AuthorizedXeedFaxt, ...]` from
   `AuthorizedXeedFaxtCollectionReader`; it does not accept raw IDs as
   authority, global FAXT collections, or frontend-filtered world data.
2. Place the future deterministic, read-only projection assembler in the
   application layer. The web surface renders its output and owns ephemeral
   presentation state; React does not interpret domain semantics.
3. Preserve `XeedId`, `OrganizationId` and `FaxtId` as separate identities.
   Labels, localized strings and coordinates never act as identity.
4. Every production datum belongs to exactly one class:
   `CANONICAL_DIRECT`, `CANONICAL_DERIVED_DETERMINISTIC`,
   `PRESENTATION_STATE`, or `UNKNOWN_UNSUPPORTED`. `FIXTURE_ONLY` is a source
   evidence classification and cannot enter production projection truth.
5. Only deterministic derivations with an explicit governed rule may be
   `CANONICAL_DERIVED_DETERMINISTIC`. No model, heuristic, fixture, predicate
   naming convention or presentation geometry may create meaning.
6. Collection membership is not a semantic relationship or provenance.
   Evidence references are not Evidence access rights.
7. `UNKNOWN`, missing values, unsupported fields and incomplete authority stay
   visibly unknown/unavailable; do not coerce to false, empty-as-negative, or a
   guessed label.

### Human context and continuity

- Preserve the established Human First concepts: Cognitive Compression,
  Semantic Zoom, Cognitive Navigation, Cognitive Continuity, Cognitive
  Provenance, Human Cognitive Amortization, Interpretation Debt and Expertise
  Tax minimization. Their AXIGNAL outcome claims remain hypotheses until
  representative product research validates them; none is a runtime metric
  established by this slice.
- The Human Output Contract remains conceptual, not a wire schema. Meaning,
  state, measure, understanding, reasoning, proof, navigation, continuity and
  provenance remain separate responsibilities as described in the existing
  HFX doctrine.
- Keep AXIGLAND, Xeed germination context and private cognitive continuity as
  separate authorities, as MASTER §55 and ADR-0017 require.
- Semantic family, epistemic state, temporal state, attention projection and
  output archetype remain independent dimensions.
- `GLANCE → UNDERSTAND → REASON → PROVE` is cognitive depth. It is not an
  epistemic stratum mapping.
- Focus navigation, epistemic trace, timeline, transcript and interaction
  state remain different records. UI selection and navigation events do not
  become AXENT transcript.
- For consultancy use, private retrieval is client-scoped by default;
  portfolio scope requires separately explicit authorization. No Context
  Broker, Context Router, memory, database or embedding runtime is specified
  here.
- ADR-0017's PostgreSQL plus pgvector direction remains an unselected
  architectural hypothesis. This slice adds no database, extension, embedding,
  broker or multi-client router implementation.

## Identity and collection contract

The conceptual root carries a private `XeedId` context and the referenced
global `OrganizationId` as separate values. The optional `Xeed.label` is a
presentation label, not a canonical Organization name. The current CORE
contracts do not expose an authorized Organization-name reader to this
projection. Missing organization display name therefore remains
`UNKNOWN_UNSUPPORTED` unless another approved read contract supplies it.

For FAXTs, the current model supplies global `FaxtId`, string `subject_id`,
`predicate`, `object_or_value`, `epistemic_state`, `currentness`,
`observed_at`, `evidence_refs`, and `contradictions`. `subject_id` is not a
typed `OrganizationId` and cannot be equated with the Xeed's Organization.
Preserve the original object and values. Do not dereference evidence refs,
interpret string IDs, or treat a reference as an edge.

The complete field-by-field contract and HFX-01 status are in
[`integration-matrix.v1.md`](integration-matrix.v1.md).

## HFX-01 go/no-go

**HFX_01_READY=NO.** The authorized collection contract is real and test/dev
read behavior exists, but production persistence and writing do not. The
present Golden Master graph binds fixture nodes to cardinal zones and fixture
edges. CORE-03 supplies neither those classifications nor semantic edges;
FAXT subject identity is also untyped and there is no projection-authorized
Organization-name read. Reusing the fixture or guessing these mappings would
misrepresent canonical state. A future HFX-01 authorization must first provide
an honest, human-accepted presentation for unsupported dimensions or separately
authorize and govern the missing canonical contracts. This does not block
canonical-contract integration work using test/dev authority in a later
authorized slice; it blocks claiming a faithful, real-data Golden Master graph
today.

## Reality levels

| Level | Established here |
|---|---|
| `CANONICAL_CONTRACT_REAL` | Yes: distinct identities, authorized Xeed read, explicit FAXT references, complete scoped FAXT collection. |
| `TEST_DEV_STORAGE` | Yes: in-memory authorities support deterministic tests/dev. |
| `PRODUCTION_REAL` | No: authentication adapter, production persistence and reference writer are not implemented. |

## Non-goals

No projection implementation, React AXIGLAND integration, API, schema,
migration, database selection, PostgreSQL/pgvector, embeddings, graph engine,
Context Broker/Router runtime, provider, model/Jev call, source integration,
production writer/persistence, visual redesign, deployment, or HFX-01 work.
