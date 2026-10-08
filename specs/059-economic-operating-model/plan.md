# 058 — Plan

```
Observation Memory (EB-06, as of cut)
  → derive_operating_model  (cues + gazetteer, versioned; claims with evidence/currentness)
  → EconomicOperatingModel  (per capability × mode: operating / expansion / exclusions;
                             constraints; exposure paths)
  → assess_demand           (typed family judgments → RelevanceScope + ExplanationTrace)
  → project_observation_opportunities (surface / count; garden summary; exposure)
  → subscriber read · continuity dependencies (reachSourceIds) · AXENT corpus
  → prune_research          (plan reader: no spend outside location-bound gardens)
```

Files: `application/economic_reach/{model,places,derive,relevance,exposure,research,summary}.py`;
integration in `application/observation_intelligence/subscriber_projection.py`,
`application/subscriber_projection/subscriber_runtime.py`,
`application/subscriber_continuity/derive.py`, `application/axent/grounded/corpus.py`,
`tools/runtime/subscriber_observation.py`. No store, table or migration: the garden is
derived on demand from Observation Memory and persisted only inside existing snapshots.
