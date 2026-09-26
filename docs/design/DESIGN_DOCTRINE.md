# AXIGNAL Design Doctrine

> Derived from and subordinate to the MASTER PRODUCT MODEL
> (`../product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`). This document
> does not duplicate the MASTER; it encodes the design constraints the MASTER
> implies. Where the two differ, the MASTER wins.

## What AXIGNAL is not

- a generic SaaS dashboard
- a CRM
- a LinkedIn clone
- a company directory
- a workflow application
- a chatbot with a graph attached
- a generic knowledge-graph viewer

(MASTER §2.1, §22, §32, §46.2, §46.35, §46.37, §48)

## What AXIGNAL is

- an instrument for observing the real economy
- economic cartography
- a living world
- evidence-driven
- temporal
- spatial
- exploratory
- explainable
- information-dense when appropriate

The central visual object will eventually be **AXIGLAND**. Normal dashboard
conventions must therefore not automatically dominate the product (MASTER §25).

## Brand semantics to preserve

| Term | Design meaning |
| --- | --- |
| **AXIGNAL** | The system. |
| **AXIGLAND** | The canonical economic world — the implicit sphere at the centre. |
| **AXENT** | The autonomous observing/investigating intelligence that traverses it. |
| **XIGNAL** | Persistent allocation of observation (not ownership, not a profile). |
| **FAXT** | Evidence-backed canonical fact. |
| **INXIGHT** | Derived interpretation. |
| **PATHX** | Explainable economic path. |

See `../architecture/TERMINOLOGY.md`.

### Isotipo

The AXIGNAL isotipo is an **X formed by two orbital trajectories around an
implicit sphere/world** (MASTER §4.8, §24):

```
trajectory A
      ╲
       ╲
        ╳   intersection / knowledge
       ╱
      ╱
trajectory B

     [implicit world = AXIGLAND]
```

- sphere/world → AXIGLAND
- orbital trajectories → observation / exploration
- intersection / X → economic intersections
- movement → continuous observation

Potential intersections to express: COMPANY × COMPANY · COMPANY × MARKET ·
CAPABILITY × DEMAND · PRODUCT × MARKET · EVIDENCE × CLAIM · ORGANIZATION × TIME.

Do not reduce the X to decorative typography.

## Epistemic UX

The UI must make epistemic distinctions understandable **without** turning
AXIGNAL into a scientific instrument panel (MASTER §15.4, §16, §18, §19, §21,
§25.3, §25.4). Preserve:

- classes: `OBSERVED`, `POTENTIAL`, `HISTORICAL`, `STALE`, `UNKNOWN`
- units: `FAXT`, `INXIGHT`, `PATHX`

The design layer must never visually imply:

- `UNKNOWN = FALSE`
- `POTENTIAL = OBSERVED`
- `INFERENCE = FACT`

Visual polish must not hide epistemic uncertainty. No raw internal scores (e.g.
"JEV confidence = 91.4%") may be surfaced as fake user-facing precision
(MASTER §19, §46.27).

## Provenance of this document

Encoded from MASTER §2.1, §4.8, §9, §16, §17, §18, §19, §21, §22, §24, §25, §26,
§32, §39, §46. Design intent here is directional; concrete UI is a later,
spec-driven feature — not part of the governance baseline.

## Human First cognitive constraints

Human First is a core product capability, not a cosmetic layer. Every material
subscriber-facing projection should lead with truthful human meaning, retain
scope and epistemic/temporal distinctions, and preserve a direct path to
derivation and evidence. Cognitive depth (`GLANCE`, `UNDERSTAND`, `REASON`,
`PROVE`) is semantic and directly navigable; it is not a required multi-screen
funnel. AXIGNAL performs joins it can already perform instead of asking people
to remember metrics or reconstruct relationships across disconnected views.

The same canonical object and truth serve different expertise levels. Plain
language changes explanation density, never epistemic state. `UNKNOWN != FALSE`,
`POTENTIAL != OBSERVED`, and historical state is not current state. Missing
provenance remains unknown; no retrospective rationale is invented.

Semantic family, epistemic state, temporal state, attention projection and
presentation archetype remain separate. Attention prioritization is a
projection, not canonical truth. No encoding uses color alone for epistemic
state. Specific colors, shapes, icons and motion remain hypotheses until tested
with users and assistive technology. AXENT can navigate and explain the current
object, but ordinary comprehension cannot depend on chat.

See [Human First Cognitive UX Doctrine](../product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md)
and ADR-0016. This document adds no UI or runtime implementation.
