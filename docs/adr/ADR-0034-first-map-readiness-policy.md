# ADR-0034 — FIRST_MAP Readiness Policy

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§1, 9, 10, 46; ADR-0031 through ADR-0033.

## Context

FR-07 introduced a truthful Xeed runtime lifecycle but deliberately left FIRST_MAP readiness policy undefined. Without that policy, LIVE promotion would either remain aspirational or drift toward opaque heuristics such as node counts, completion percentages or hidden model confidence.

## Decision

Introduce `application/xeed_germination/readiness.py` as the deterministic FIRST_MAP readiness authority.

Readiness is qualitative and inspectable. It emits one of:

- `FIRST_MAP_READY`;
- `PARTIAL_MAP`;
- `SPARSE_MAP`;
- `INSUFFICIENT_EVIDENCE`.

There is no scalar readiness score.

`DIMENSION ANSWERABILITY != XIGNAL READINESS != FIRST_MAP READINESS`

`MORE NODES != BETTER MAP`

`PARTIAL WORLD != INCOMPLETE PRODUCT`

## FIRST_MAP_READY

A partial world may become FIRST_MAP_READY when all of the following are true:

- the Xeed has at least one real observation;
- a real first Xignal has been recorded in the lifecycle;
- the supplied Xignal projection exactly matches that Xeed, canonical subject and first-Xignal identity;
- the Xignal is not epistemically UNKNOWN;
- an Evidence Narrative exists for that exact Xignal;
- the narrative contains at least one grounded economic step such as claim, relationship, PATHX, observation, contradiction or source.

A POTENTIAL Xignal may satisfy FIRST_MAP readiness when it is explainable and grounded. It remains POTENTIAL; readiness does not upgrade its epistemic state.

## Honest non-ready outcomes

`INSUFFICIENT_EVIDENCE` means no real observation exists yet. No LIVE-promotion decision is fabricated.

`SPARSE_MAP` means observations exist but no first Xignal exists yet. This is an honest map state, not failure.

`PARTIAL_MAP` means a first Xignal exists but the product proof is not yet sufficient—for example missing projection, UNKNOWN-only Xignal, missing/mismatched narrative or no grounded narrative step.

These outcomes preserve useful partial work rather than forcing artificial completion.

## Contradictions and unknowns

Explicit contradictions and remaining unknowns do not automatically block FIRST_MAP readiness. Hiding them would make the product less epistemically honest.

When present, the readiness reasons explicitly record that contradictions and/or unknowns were preserved.

`CONTRADICTION PRESENT != MAP NOT READY`

`UNKNOWN PRESENT != FALSE`

## Runtime lineage

Verified runtime artifact lineage is recorded as a positive reason when present, but FIRST_MAP readiness does not require every observation to expose a raw artifact. The Evidence Narrative remains the governed lineage authority.

## No node-count criterion

The policy contract has no `node_count`, minimum-node threshold, graph-density target or completion percentage. A single high-value explainable signal may be more useful than a large weak graph.

## Lifecycle handoff

When FIRST_MAP_READY is reached, the policy produces a `FirstXeedReadinessDecision` bound to the exact Xeed lifecycle state:

- xeed_id;
- first_xignal_id;
- observation_depth;
- lifecycle revision;
- policy id/version;
- explicit reason codes.

FR-07 then validates that decision again before allowing LIVE promotion. Stale decisions fail closed.

## Non-goals

FR-08 does not define visual WOW quality, browser animation, node layout, UI copy, persistence/API transport or business conversion metrics. It defines the minimum governed product-readiness contract only.

## Consequences

FIRST_MAP_WOW no longer requires a fully populated world. AXIGNAL can surface a sparse but useful and explainable first map quickly, remain honest when evidence is insufficient, and avoid optimizing for arbitrary graph size.