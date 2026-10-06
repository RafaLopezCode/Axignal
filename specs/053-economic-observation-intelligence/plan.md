# 053 — Plan

## Architecture

```
OPPORTUNITY_INTELLIGENCE (families: procurement, public investment, grants,
planning/permits, private projects, regulation-driven demand, buyer expansion)
   └─ family → abstract SourceCapability → SourceRegistry.resolve(capability,
      jurisdiction) → concrete SourceDescriptor (ADOPTED | CANDIDATE) → adapter
```

- `application/observation_intelligence/` (pure, deterministic, no network):
  `contracts` (hypotheses, questions, capabilities, jurisdictions, sources),
  `catalog` (versioned lexicon, questions, sources), `registry` (resolution,
  adoption gate, discovery requests), `understanding` (capability/family
  hypotheses from observed text), `coverage`, `strategy` (dominance-ordered
  actions, routing decisions, gaps), `loop` (budgeted adaptive loop, demand
  interpreters per evidence type, deterministic stop), `learning`, `human`
  (per-family opportunity cards).
- `pipeline/observation_intelligence/ted.py`: TED Search API v3 adapter, one
  implementation of PUBLIC_PROCUREMENT for jurisdiction `EU`.
- Jurisdictions are paths (`EU/ES/ES5/ES52`, `US/US-CA`); each adapter maps
  them to its own place codes. Classification schemes (CPV, NAICS, PSC) stay
  separate; a source receives only the codes in schemes it supports.

## Decisions

- Priority: ordinal dominance (value, information gain, source quality, cost),
  then OBSERVED markets, then stable id. No universal scalar (MASTER §53.3).
- Unknown rights or cost ⇒ ineligible. Only ADOPTED sources are routable.
- Matching is narrow-only (notice code inside a capability code); sibling codes
  revealed by awards are explicit adjacency with their own basis.
- Closed calls are demand evidence, not opportunities.
- Rejected tools: semantic/similarity caches and near-duplicate reuse (grounding
  risk); gateway prompt caches (never hit, lock-in). Trafilatura deferred.
