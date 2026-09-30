# ADR-0037 — Initial Cognitive Load Progressive Disclosure

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 25, 26, 46, 55; ADR-0016, ADR-0035, ADR-0036.

## Context

FR-09 made Today the first-value layer and FR-10 separated AXENT continuity, but
the default subscriber view still exposed expert/governance mechanics at equal
visual priority with product value. The left sidebar permanently showed Scope,
Memory, Research and Uncertainty, including unavailable states; Xeed repeated a
private-scope label; every depth label was continuously visible; and AXENT could
surface several contextual question pills at once.

These controls are valid, but permanent visibility makes the user parse AXIGNAL
before receiving its value.

## Decision

Apply progressive disclosure without removing capability or changing canonical
meaning:

- Today and the active Xeed remain primary navigation.
- Expert/governance controls live under a closed-by-default **Advanced controls**
  disclosure and remain keyboard reachable.
- The compact rail keeps the advanced-control entry point but places it after
  the primary navigation spacer.
- Private Xeed scope remains available to assistive technology and governed
  context, but no longer competes as visible first-view copy.
- Cognitive depth remains directly keyboard/pointer accessible; only the active
  depth label is continuously visible, while the full scale appears on focus or
interaction.
- AXENT surfaces no more than two primary contextual question actions. Further
  available actions remain reachable through **More questions**. Unavailable
  synthetic actions are not first-view controls.
- The empty Workspace placeholder is removed because it carried no product
  capability or state.

No truth, evidence, temporal, Xeed, AXENT continuity or authorization semantics
are changed.

## Invariants

`PROGRESSIVE DISCLOSURE != CAPABILITY REMOVAL`

`FIRST VIEW != GOVERNANCE CONSOLE`

`HIDDEN FROM FIRST VIEW != UNKNOWN OR FALSE`

`DEPTH ACCESS REMAINS DIRECT`

`AXENT PRIMARY QUESTIONS <= 2`

## Consequences

The first view gives visual priority to the current value and current object
while retaining expert controls on demand. Keyboard users can open advanced
controls and expand depth without a pointer. This slice does not decide final
subscriber terminology or complete locale coverage; FR-12 owns that work.

## Non-goals

No canonical model, persistence, Context Broker, provider, production
deployment, mobile product redesign or accessibility-equivalent graph
projection is introduced here.
