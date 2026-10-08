# ADR-0089: Economic Operating Model and capability-specific economic reach

- **Status:** Accepted for review (CTO)
- **Date:** 2026-10-08
- **Authority:** MASTER §15.1, §15.3, §15.4, §53.6 (reach depends on the capability), §53.7 (typed families, deterministic first, ExplanationTrace); Constitution; ADR-0049, ADR-0072, ADR-0088; Spec 059.
- **Scope:** the cognitive frontier between "what happens in the world" and "what belongs to this Xeed's economy", before an Opportunity reaches a subscriber.

## Context

The observation loop matched world demand to capabilities by classification code and then by the Xeed's *attention* market (operator-configured, e.g. `EU/ES`). Any capability matched anywhere inside that market: a Madrid installer saw tenders in Córdoba as its opportunities. `MarketScope` existed per Xeed, not per capability; `XeedMarketMap` classifies *who buys* (B2B/B2C/B2G), not *where and how* a capability is delivered; EB-04 `delivery_reach` compared exact strings for one project. Nothing represented exposure (being affected without operating somewhere).

## Decision

### What the garden is

The **Economic Operating Model** is a temporal, evidence-derived projection of how an Organization's capabilities reach customers. It is not an Organization attribute and not an editable profile.

1. **Reach belongs to the delivery channel = capability × delivery mode.** The same capability delivered at the provider's premises (Madrid) and online (Spain) has two reaches; two capabilities never share reach unless a site-wide statement says so (and then only POTENTIAL).
2. **Delivery mode decides which feasibility binds.** `PROVIDER_PREMISES` (customer comes: the premises are the reach), `CUSTOMER_SITE` (provider travels: an office is *not* reach, no invented radius), `SHIPPED` (logistics, customs), `REMOTE` and `DIGITAL` (distance does not bind; jurisdiction/market access does; digital is not global).
3. **Three scopes, never collapsed.**
   - *Operating reach* — stated service areas and, for premises channels, premises; OBSERVED when the statement names the capability, POTENTIAL when site-wide or stale.
   - *Plausible expansion* — the Organization's own preparatory acts (a facility being opened, regional hiring); always POTENTIAL; demand observed somewhere is never expansion evidence.
   - *Exposure* — a transmission path driver → channel (energy, fuel/travel, freight/customs, local regulation, digital platform, supply) → delivery channel. Not a wider circle: the driver's locus is irrelevant. Exposure is never an Opportunity.

### Authority

Evidence (governed observations in Observation Memory) → deterministic extraction with explicit cues (`application/economic_reach/derive.py`, versioned cue lists and a versioned place gazetteer) → typed claims with provenance and currentness → deterministic gate. A bare place name (brand, headquarters, demonym) never creates reach; vans or a factory do not prove national reach; supplier geographies feed exposure, never customer reach. Subscriber or operator attention directs observation and never enters the model. Models (Luna, JEV) are not authority: they may later answer an UNRESOLVED family as a bounded, replaceable evaluator; they cannot create or widen reach.

### The Economic Relevance Gate

Per channel, typed judgments for GEOGRAPHIC_ECONOMIC_REACH, LOGISTICS_FEASIBILITY, REGULATORY_ELIGIBILITY, MARKET_ACCESS_FEASIBILITY and TEMPORAL_ACTIONABILITY. Each has an outcome (COMPATIBLE, INCOMPATIBLE, UNRESOLVED, NOT_APPLICABLE) and an epistemic state (OBSERVED, POTENTIAL, UNKNOWN). INCOMPATIBLE requires explicit evidence (an Organization's own exclusion, a governed WITHDRAWN qualification, a closed window); missing evidence is UNRESOLVED. The decision scope is OPERATING_REACH, PLAUSIBLE_EXPANSION, UNRESOLVED_REACH, NOT_ACTIONABLE or OUTSIDE_XEED_REACH; the best channel wins by a fixed order, not a score. An event naming a place broader than the reach is UNRESOLVED, not outside.

Relevance is not truth and not priority: an OUTSIDE event stays in global memory for every other Xeed and is only counted in the Xeed's projection. UNRESOLVED events are surfaced with explicit gaps, bounded (3 per projection) when some reach is known, so growth stays discoverable.

### Integration

- The subscriber opportunity projection applies the gate after provenance checks; surfaced opportunities stay POTENTIAL and carry the ExplanationTrace, the garden summary and filtered counts travel with the snapshot.
- The garden's evidence is a declared continuity dependency (ADR-0088): changed or stale reach owes recomputation through the existing T12 queue.
- Research planning drops actions only for location-bound channels with evidenced reach outside the action's market; unknown reach and remote/digital channels are never pruned.
- AXENT's grounded corpus receives the trace, the garden and the filter counts, so "why am I (not) seeing this?" is verbalized from persisted structure.
- `MarketScope` stays the attention/participation market; `XeedMarketMap` stays the higher buyer-relationship projection; `SourceDescriptor.covers` stays "where a source can observe". None is duplicated.

## Consequences

- Scale, languages, data residency, payment and partner delivery are not modeled yet; the family/claim structure admits them as new claim kinds without changing the gate's contract.
- Production has no governed driver source; exposure assessment is wired (`drivers=()`) and inert until one is authorized.
- Cue lists and the gazetteer are versioned data; extending them changes derivations deterministically and is visible in the model fingerprint.
