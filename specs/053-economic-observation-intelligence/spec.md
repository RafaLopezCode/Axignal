# 053 — Economic Observation Intelligence Layer (first vertical)

**Status:** IMPLEMENTED (first vertical) · **Date:** 2026-10-06
**Doctrine:** MASTER §53.2 (economic sensors and registry), §53.3 (derived
opportunity), Sensor Router v0 and Global Procurement Sensor spec (unmerged
`cto/brain-procurement-adapters`), whose routing invariants this feature adopts.

## Problem

AXIGNAL observes a Xeed's public surface generically. It cannot decide *where*
to look next for a given economic question, so specialised evidence (for example
a compatible public tender) is never reached, and when sources are added the
temptation is a sector → list-of-sites mapping. MASTER §53.2 requires sources
to be selected by question, coverage, time and quality, with TED as one sensor,
never an architecture.

## Outcome

A deterministic, inspectable control plane that turns observed context into a
governed observation plan and stops on its own:

```
observation → capability/family hypotheses (POTENTIAL, evidence-bound)
            → economic questions → evidence requirements
            → source capabilities × geography × capability codes
            → ObservationStrategy (ordered, explained, budgeted)
            → adaptive loop (observe → learn what to observe → stop)
            → POTENTIAL opportunity candidates + coverage map + human brief
```

## Requirements

1. Business families and capabilities are multi-valued hypotheses with state,
   ordinal strength, evidence spans and stability; never canonical truth.
2. Questions declare evidence requirements; sources declare evidence kinds,
   geography, query dimensions, rights, cost, cadence, reliability, failure
   modes and alternatives. Routing matches question requirements to source
   capabilities; no sector or source name appears in routing logic.
3. Geography and buyer/job targets are routing inputs: the same capability in
   another market yields another plan.
4. Priority is a dominance ordering over explicit ordinal dimensions
   (economic value, information gain, source quality, cost) with reasons. No
   universal scalar (MASTER §53.3).
5. Only ADOPTED registry sources are routable. Discovered sources enter as
   CANDIDATE and need an adoption gate (rights declared, tested, fit, cost).
6. The loop is budgeted and stops deterministically: sufficient evidence, no
   marginal gain, budget exhausted, sources exhausted, irreducible uncertainty.
7. Findings can create follow-up actions (adaptive observation) only through
   versioned deterministic rules.
8. Operational learning per source capability (yield, duplicates, failures,
   cost) adjusts routing quality within bounds; it never becomes truth.
9. Outputs: POTENTIAL opportunity candidates with missing context; an evidence
   coverage map (OBSERVED / POTENTIAL / STALE / UNKNOWN per question × market);
   a Human First brief answering "why did AXIGNAL look there?".
10. Nothing writes canonical state; source → acquisition → evidence →
    interpretation → validation → admission stays intact. UNKNOWN ≠ FALSE.

## Acceptance

- Two Xeeds with different capabilities/markets get different strategies
  (questions, sources, query codes, cadence); a B2C Xeed gets no procurement.
- E2E: generalist observation finds no opportunity; the specialised route finds
  POTENTIAL candidates, adapts once from award evidence, then stops.
- Benchmark versus "run every adopted source for every question".
- TED adapter parses the real Search API v3 response shape; no network in CI.

## Out of scope (this slice)

Live production scheduling, persistence of strategies, non-procurement source
adapters, EvidenceAdmission of procurement facts, frontend components.

## Authorized product wiring extension — 2026-10-06

The CTO delivery connects accepted outputs to the existing subscriber reading
and cognitive registry. It adds no economic evaluator or canonical writer.
Authorized, persisted opportunity snapshots retain exact tenant/focus/subject,
POTENTIAL, capability and demand source references, missing requirements and
their observation/currentness clocks. The read refreshes evidence before
publication; missing authority or provenance abstains. Real sources can power
provenance and change lenses without inventing trends, maps or commercial fit.

The subscriber reading and AXENT compose and validate the same real facts on
server and client, bound to revision, family and temporal cut. Illustrative
Panorama retains explicit fixtures; a real reading never falls back to them.
Acceptance: future observations excluded, cross-tenant/focus access denied,
unknown requirements preserved, evidence reachable on desktop/narrow screens.
Production execution remains gated by configured authorized sources and ports;
controlled tests cannot establish live acquisition, login or payment readiness.
