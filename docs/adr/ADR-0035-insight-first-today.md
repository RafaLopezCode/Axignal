# ADR-0035 — Insight-First Today

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 25, 26, 46; ADR-0031 through ADR-0034.

## Context

AXIGNAL's governed Brain, explainable Xignals, evidence narrative and FIRST_MAP readiness now exist, but the subscriber UI still required the user to interpret the map before discovering the clearest immediate value. Today rendered every available FAXT and summarized quantity rather than material meaning.

## Decision

Introduce an insight-first Today comprehension layer.

`TODAY != DASHBOARD`

`TODAY ITEM COUNT <= 3`

`NO TEMPORAL DELTA != CHANGED TODAY`

`SHOW HOW AXIGNAL KNOWS = PRIMARY PROOF ACTION`

`VIEW IN MAP = CONTEXT-PRESERVING SPATIAL ACTION`

## Application contract

`application/subscriber_projection/today.py` owns a provider-neutral Today projection:

- `TodayPolicy` explicitly caps surfaced items at 1–3;
- no score, node count, graph density or dashboard metric is used;
- only material candidates are surfaced;
- ordering is deterministic by real change time when present, otherwise observation recency and stable identity;
- each item carries what changed / what is material now, why it matters, epistemic state, currentness, observation/change time, evidence-action reference and map focus reference;
- partial and empty states are explicit.

## Human-first copy

The first view avoids requiring internal AXIGNAL vocabulary. The default heading is ordinary-language value framing: `What deserves your attention now`.

The synthetic UX lab must not claim a temporal change when it only has a current observation. Such items are labeled `Current observation` rather than `changed today`.

## Actions

Each material Today item exposes two actions:

1. **Show how AXIGNAL knows** — primary proof action. In the current synthetic subscriber lab this reuses the existing governed focus and switches cognitive depth to Evidence; no post-hoc evidence narrative is fabricated.
2. **View in map** — secondary spatial action. It deep-links to the existing AXIGLAND focus without recentering the camera.

## Spatial continuity

Today is a comprehension layer over the same spatial world, not a separate dashboard route. Deep links preserve the current camera. Today temporarily receives additional vertical space so the material items and actions are visible without scrolling; opening an item returns the normal map geometry.

## 10-second protocol

`docs/design/FIRST_VIEW_10_SECOND_COMPREHENSION_PROTOCOL.md` defines the acceptance protocol. A first-time user must be able to identify what deserves attention, why it matters, the epistemic/currentness cue, the proof action and the map action after a ten-second exposure.

## Empty and partial states

If no material item is ready, Today states that AXIGNAL is still observing. Existing evidence that is not yet material does not become a fake insight. Empty does not mean false or nonexistent.

## Browser evidence

FR-09 was verified against the real loopback subscriber runtime in Chrome at desktop and narrow widths.

At 1440×1000 and 860×1000 the first material item, why-it-matters explanation, state/time and both actions are visible without requiring map interpretation.

Chrome DevTools Protocol interaction verification confirmed:

- exactly three surfaced Today items in the nominal synthetic scenario;
- primary action changes focus to the intended FAXT and sets depth to Evidence (`3`);
- secondary map action changes focus to the intended FAXT;
- both actions preserve the exact camera x/y/zoom state.

## Non-goals

FR-09 does not implement a conventional KPI dashboard, fabricate change events, redesign AXENT, create canonical writes, or replace the full AXIGLAND canvas.

## Consequences

The product can now lead with value before ontology. Users can understand why the current Xeed matters within seconds, then choose proof or spatial exploration without losing context.