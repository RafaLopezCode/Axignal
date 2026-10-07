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

## T12 deployment closure

Reuse the existing `axignal-observation-daily.timer` (03:17 UTC, persistent,
15-minute jitter) and bounded one-shot Docker runner. The timer only wakes
`tools.runtime.observation_daily`; `run_once` / `run_daily_tick` retain cadence,
enrollment authorization, budget, acquisition, replay and recomputation authority.
No frontend, source adoption, provider activation, Product MCP or PilotGrant change.

- A root-owned EnvironmentFile supplies the existing enabled flag; absent/false
  stays disabled. Installation preserves existing config and never writes `current`.
- Host `flock` and a stable worker container name serialize scheduler invocation;
  the existing SQLite lease/fencing remains mandatory within the runtime. A live
  lease blocks another UTC day too; elapsed time invalidates expired authority
  before child acquisition/recomputation and at every durable step.
- Service lifetime (30 minutes) is below the one-hour lease; the existing daily
  runtime budget is 900 seconds. `ExecStopPost` stops only this worker on timeout.
- Summarized invocation metadata is stored in the same operational SQLite file;
  `--status` opens it read-only. Logs omit enrollment identifiers, exception text,
  evidence and credentials. Interrupted attempts retain an unfinished record.
- Discriminants: real subprocess no-work/restart/replay; actual shell runner to
  one runtime entry in Linux; overlapping invocations; expiry before fan-out;
  midnight overlap; killed process recovery; unknown-cost zero calls; redacted
  errors; existing multi-day/partial failure tests and real subscriber Brain E2E
  through the scheduled entry.

Constitution check: only operational persistence/deployment is extended, with
application → domain and pipeline → application boundaries unchanged. No canonical
writer, inferred identity, private cross-tenant reuse or new source authority.
Persisted receipts deduplicate committed acquisitions. A kill between retrieval
and durable receipt may require a repeated public read; this does not authorize a
duplicate canonical write or promise exactly-once external effects.
