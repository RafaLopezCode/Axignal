# 058 — Economic Operating Model and capability-specific economic reach

**Status:** IMPLEMENTED (pending CTO review) · **Date:** 2026-10-08 · **Decision:** ADR-0089
**Owner:** `application/economic_reach/` (model, derivation, relevance gate, exposure, research)
**Doctrine:** MASTER §15.1, §15.3, §15.4, §53.6, §53.7.

## Problem

AXIGNAL observed world demand and matched it to capabilities by code and by the Xeed's
attention market. It could not say "this happens in the world but not in this business's
economy", nor "this does not happen where you operate but it still affects you".

## Requirements

- FR-1 Derive, from governed public evidence only, per delivery channel (capability × mode):
  operating reach, plausible expansion and exposure paths, with provenance, epistemic state
  and currentness; UNKNOWN where nothing is evidenced.
- FR-2 An Economic Relevance Gate before Opportunity, composed of typed deterministic
  judgments (geographic reach, logistics, regulatory eligibility, market access, temporal
  actionability); no score, no model.
- FR-3 Out-of-garden events are not surfaced and are not deleted; surfaced ones stay POTENTIAL
  with an ExplanationTrace.
- FR-4 Exposure is a separate result type; it never becomes an Opportunity.
- FR-5 The garden evolves by evidence (as-of derivation) and its evidence is a continuity
  dependency (ADR-0088).
- FR-6 Research is not spent outside the garden of location-bound channels with known reach.
- FR-7 AXENT can explain relevance from the persisted trace.

## Acceptance

Archetypes (salon, language school, restaurant, installer, manufacturer, SaaS, consultancy,
ecommerce) behave as stated in `tests/economic_reach/`; 100 world events reduce to the
garden without deletion; the composition E2E surfaces only in-garden demand, shares the
garden across Tenants and turns an energy shock into exposure.

## Out of scope

CRM/profile editing, scoring engines, GIS/radius models, supply-chain twins, new sources,
production activation, model-based reach.
