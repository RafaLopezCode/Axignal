# 054 — Plan

## Placement

- `application/observation_runtime/` — control plane (families, frontier,
  budget, ports, tick, acquirers, digest). Imports application/domain only.
- `pipeline/observation_runtime/sqlite_store.py` — operational persistence.
- `application/observation_intelligence/` — five new abstract source
  capabilities; `regional_follow_ups` made public for reuse.

## Reuse

| Need | Existing capability used |
|---|---|
| Currentness aging | `evaluate_effective_currentness` + `TemporalCurrentnessPolicy` |
| Routing | `SourceRegistry.resolve` (adoption gate, rights, cost) |
| Procurement acquisition and candidates | `build_strategy` + `run_observation_loop` + TED adapter |
| Award concentration follow-ups | `regional_follow_ups` |
| Website acquisition | governed `SourceRequest`/sensor + `ingest_source_observation` |
| Source yield | `OperationalLearning.adjusted_quality` |

## Risks

- Budget overrun by an adapter → each acquisition gets a request allowance
  equal to its reserved worst case; exceeding it raises.
- Duplicate daily work → day lease + per-step fenced commits + content-addressed
  leads and candidates.
- Unbounded expansion → family rule, depth (family and global), frontier cap
  per Xeed and family, each lead once per tick, new-to-lead gating.
