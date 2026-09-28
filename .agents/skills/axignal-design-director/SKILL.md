---
name: axignal-design-director
description: Governed design-director workflow for AXIGNAL subscriber-facing UI/UX. Use for design, redesign, implementation, critique, polish, responsive work, accessibility, visual QA, Golden Master comparison, or any change that can alter human comprehension. AXIGNAL doctrine and accepted visual evidence outrank external design guidance.
---

# AXIGNAL Design Director

## Mission

Produce distinctive, exceptionally crafted AXIGNAL interfaces while preserving product truth, Human-First Cognitive UX, epistemic semantics, and accepted visual authority.

This skill is an orchestrator, not an independent source of product truth.

## Authority order — fail closed

1. `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`
2. `.specify/memory/constitution.md`
3. Accepted ADRs, especially ADR-0016/0017 and graph architecture ADRs
4. Active feature spec / plan / task
5. Accepted Golden Master and its deterministic source manifest
6. AXIGNAL Design System / incumbent accepted tokens and components
7. This skill
8. External design skills, heuristics, libraries and model taste

If a lower authority conflicts with a higher one, stop and preserve the higher authority. Never reinterpret doctrine to obtain a prettier result.

## Non-negotiable AXIGNAL design invariants

- AXIGNAL is a cognitive economic cartography, not a dashboard, CRM, workflow suite or generic SaaS shell.
- The user directs attention, never truth.
- `UNKNOWN != FALSE`; `POTENTIAL != OBSERVED`; `FAXT != INXIGHT`; `RELATIONSHIP != PATHX`; historical != current.
- Color is never the only carrier of epistemic meaning.
- Material outputs retain a navigable path to derivation/evidence.
- Human meaning precedes metrics and internal ontology.
- Cognitive depth is directly navigable: `GLANCE → UNDERSTAND → REASON → PROVE`; never force it as a wizard.
- AXENT is persistent contextual intelligence, not merely a chatbot and not a UI-action log.
- Navigation/focus state, evidence trace, timeline and AXENT transcript are distinct records.
- Golden Master is visual/behavioral authority only; it cannot create canonical truth.
- No fixture semantics, coordinates, labels or visual groupings may be promoted into domain truth.
- Human visual acceptance is required for material visual changes. Automated scores are advisory only.

## Required workflow

### 0. Establish design mode

Classify the task as one of:

- `PRESERVE`: implementation/refinement must remain lossless to accepted Golden Master.
- `EXTEND`: new surface must inherit AXIGNAL visual grammar without altering accepted surfaces.
- `EXPLORE`: explicitly authorized design exploration; never silently replaces accepted authority.

Default to `PRESERVE` when touching an accepted subscriber surface.

### 1. Build product cognition before code

State briefly from repository evidence:

- surface and primary human task;
- user entry state and first meaningful decision;
- success and recovery path;
- semantic objects visible;
- epistemic/temporal states visible;
- required evidence/provenance path;
- active Golden Master/design authority;
- unsupported data that must remain unavailable/unknown;
- desktop/mobile interaction risks.

Do not design an unknown product from category conventions.

### 2. Separate truth from presentation

Before adding a visible concept classify every datum:

`CANONICAL_DIRECT | CANONICAL_DERIVED_DETERMINISTIC | PRESENTATION_STATE | UNKNOWN_UNSUPPORTED | FIXTURE_ONLY`

Only the first two may be represented as governed economic knowledge. Presentation state never becomes canonical truth. Unsupported stays unsupported.

### 3. Shape before build

For material work, resolve:

- information hierarchy;
- cognitive focus and attenuation;
- semantic zoom/depth;
- navigation continuity and reversibility;
- evidence access;
- empty/loading/error/unknown states;
- keyboard/pointer/touch behavior;
- responsive behavior;
- accessibility beyond color;
- motion purpose and reduced-motion behavior.

Prefer product-specific spatial/cognitive structure over conventional dashboard composition.

### 4. External design intelligence — advisory layer

External skills may be consulted for craft, never authority. Use the minimum useful set:

- Anthropic `frontend-design`: art direction, specificity, typography, composition, anti-template pressure.
- Impeccable: shape/critique/polish/harden/adapt and deterministic anti-pattern detection.
- `ui-ux-pro-max`: broad pattern, typography, accessibility and framework reference.
- `atuizz/codex-ui-ux-skill`: product-cognition and journey-quality cross-check.
- Vercel Web Interface Guidelines: web interaction/accessibility craft.
- Browser/Playwright tooling: rendered interaction and screenshot verification.

Do not install or import an external design system that overwrites AXIGNAL tokens or Golden Master authority. Pin versions/commits when vendoring anything. Review license and provenance first.

### 5. Implement the smallest coherent change

Reuse → repair → extend → consolidate → create.

Preserve incumbent AXIGNAL typography, geometry, tokens, components and interaction grammar unless the task is explicitly `EXPLORE`. Avoid speculative abstractions and generic component-library defaults.

### 6. Rendered verification is mandatory

A frontend change is not verified from JSX/CSS or unit tests.

Run the actual surface in a browser and inspect at minimum:

- accepted desktop viewport(s);
- relevant narrow/mobile viewport(s);
- initial state;
- primary interaction path;
- focus/back/forward/home or equivalent continuity where relevant;
- evidence/provenance path where relevant;
- empty, unknown, unavailable and error states affected by the change;
- keyboard focus and accessible names;
- reduced motion when motion changed;
- browser console/runtime errors;
- real or contract-faithful data, never visually convenient fake truth.

Capture deterministic screenshots when possible.

### 7. Visual convergence

For `PRESERVE`, compare against the accepted Golden Master. Treat unexplained geometry, typography, spacing, hierarchy, copy, interaction or motion deltas as defects.

For `EXTEND`, compare adjacent accepted surfaces for grammar consistency.

Use bounded passes:
1. inspect desktop + narrow view;
2. batch defects by root cause;
3. repair;
4. one confirmation pass.

Do not burn time in endless subjective polishing.

### 8. Human acceptance gate

Automation may report defects, deltas and evidence. It MUST NOT declare a material AXIGNAL visual change accepted.

Final state before human acceptance:
`IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING`.

Only explicit human acceptance can close the visual gate.

## Anti-generic-AI constraints

Reject category-interchangeable output: generic SaaS dashboards, gratuitous card grids, arbitrary gradients, decorative metrics, fake activity feeds, oversized marketing typography inside product UI, excessive rounded containers, meaningless glassmorphism, and animation without cognitive purpose.

Do not ban techniques categorically. A technique is valid when it serves AXIGNAL's cognitive model and accepted visual language.

Ask: “Could this screen belong to an unrelated SaaS after changing the logo?” If yes, specificity is insufficient.

## AXIGNAL self-growth principle

AXIGNAL should use its own governed design process as an observation loop:

`human intent → governed product context → design hypothesis → implementation → rendered evidence → critique → correction → human acceptance → reusable design knowledge`

Only accepted, non-sensitive, provenance-bearing design knowledge may become durable project guidance. Model critique is a proposal, never canonical design truth.

## Completion report

Report:

- MODE: PRESERVE / EXTEND / EXPLORE
- AUTHORITY_READ
- CHANGE
- BROWSER_QA
- GOLDEN_MASTER_DELTA
- ACCESSIBILITY
- EPISTEMIC_INVARIANTS
- AUTOMATED_GATES
- HUMAN_VISUAL_ACCEPTANCE
- STATUS: IMPLEMENTED / PROBADO / INTEGRADO / DESPLEGADO / VERIFICADO_E2E as actually evidenced

Never claim a stage not directly verified.
