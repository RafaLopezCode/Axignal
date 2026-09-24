# AXIGNAL Design Governance

> Design intelligence is subordinate to product doctrine. If a design
> recommendation conflicts with the MASTER, the MASTER wins. If it conflicts
> with an architectural invariant, the architecture wins.

## Precedence (fail closed)

```
AXIGNAL MASTER PRODUCT MODEL
        ↓
ENGINEERING CONSTITUTION
        ↓
ADRs / ARCHITECTURE CONTRACTS
        ↓
FEATURE SPEC
        ↓
DESIGN BRIEF
        ↓
UI/UX SKILLS  (frontend-design, ui-ux-pro-max)
        ↓
IMPLEMENTATION
```

The installed skills (`docs/design/UI_UX_SKILLS.md`) are **design intelligence**.
They never invent product semantics, never override the MASTER, and never
authorize changes the architecture forbids. On conflict: stop and report.

## Responsibility boundaries

| Skill | Owns | Must not |
| --- | --- | --- |
| `frontend-design` | Visual direction, art direction, composition, typography, hierarchy, spatial rhythm, motion language, interaction polish, distinctive identity, avoiding generic SaaS / generic AI aesthetics, deliberate visual systems, production-quality frontend execution. | Invent product semantics; redefine epistemic meaning; override IA or accessibility. |
| `ui-ux-pro-max` | Information architecture, interaction design, usability, accessibility, responsive behavior, navigation, cognitive load, UX heuristics, interface consistency, component/state behavior, empty/loading/error states, data-density management, dashboard ergonomics. | Override the MASTER; trade truthfulness for polish; add sponsored or ranking manipulation. |

`ui-ux-pro-max` should challenge visual decisions that reduce usability.
`frontend-design` should push toward exceptional visual quality without inventing
product meaning.

## Design quality bar

A future AXIGNAL surface is **rejected** if it is merely any of: "clean",
"modern", "professional", "good-looking", "standard shadcn", "standard dark SaaS".
Those are the baseline floor, not the target.

The target is: **distinctive, legible, semantic, exploratory, precise,
memorable, fast, accessible.** The interface should communicate "I am looking
into a living economic world" without sacrificing usability.

## shadcn/ui boundary

shadcn/ui may be used as **infrastructure** for commodity interactions. It must
not become AXIGNAL's visual identity. These product-defining surfaces must have
custom design and must not be constrained to default shadcn aesthetics:

AXIGLAND · XIGNAL lifecycle · FIRST_MAP construction · FAXT presentation ·
INXIGHT presentation · PATHX visualization · temporal exploration · economic
relationship inspection.

## Graph UX — reserved problem

No graph engine is selected here. AXIGLAND graph visualization is a first-class
product surface and requires a later, dedicated **`GRAPH_ENGINE_BAKEOFF`**
(engine choice, performance, accessibility, LOD strategy).

The following mappings are **hypotheses to test, not frozen decisions**, and must
not be implemented now:

```
NODE SIZE      → economic relevance
DISTANCE       → relational proximity
SHARPNESS      → evidence certainty
HALO           → temporal activity

EDGE WIDTH     → materiality
EDGE OPACITY   → evidence strength
EDGE PATTERN   → epistemic class
EDGE DIRECTION → economic direction

ZOOM           → semantic level of detail
CLICK          → recenter
PATHX          → economic trajectory
TIMELINE       → temporal reconstruction
```

## FIRST_MAP_WOW truthfulness

FIRST_MAP_WOW is a P0 product problem (MASTER §9). The map-construction
experience may expose only truthful progress derived from real system state
(e.g. "Organization identified", "Capabilities discovered", "Corporate structure
investigated", "Observed relationships resolved", "Evidence verified").

Forbidden: fake progress, theatrical fake loading, fabricated findings. Visual
spectacle must correspond to real system state. `UNKNOWN` is not `FALSE`;
`POTENTIAL` is not `OBSERVED`; inference is not fact.

## Deterministic CI independence

Installing design skills must not make required CI depend on an LLM or on skill
execution. Required gates remain deterministic and offline
(`docs/governance/DETERMINISTIC_CI.md`). The `ui-ux-pro-max` search scripts are
local, offline, stdlib-only, and are never invoked by required CI.

## Validation after design-skill changes

- Both skills discoverable and their `SKILL.md` readable.
- `frontend-design`/`ui-ux-pro-max` frontmatter `name` matches directory.
- Deterministic repository validation, Architecture Guard, tests, typecheck,
  lint and build all pass.
- No global configuration changed; installation is project-local.
