# 054 — Autonomous Fractal Evidence-Guided Observation Runtime

**Status:** IMPLEMENTED (runtime + E2E on controlled clock) · **Date:** 2026-10-07
**Doctrine:** MASTER §15.4 (UNKNOWN ≠ FALSE), §20 (currentness), §53.2–53.3
(sensors, derived opportunity), §54 (digital representation is observation).
Consumes spec 053 (Economic Observation Intelligence), FR-25 temporal
currentness, observation reuse and the governed source acquisition path.

## Problem

AXIGNAL could plan and run one bounded observation loop when asked. Nothing
woke it up, remembered what it had already looked at, let evidence age, spent
a daily budget or decided which branch of research deserved the next request.

## Outcome

One deterministic, model-free tick per UTC day:

```
DAILY TICK → claim day (idempotent lease) → entry leads for every family
  → aging without fetch (CURRENT → STALE → HISTORICAL; observed_at never moves)
  → due leads in tier order → route capability × geography → adopted source
  → reserve budget (global limits STOP, scoped limits skip) → acquire
  → fingerprint delta (new / changed / refreshed) → POTENTIAL candidates
  → bounded fractal expansion (family policy, depth, frontier caps)
  → persist step (fenced) → next_due / backoff → selective recomputation → STOP
```

## Invariants kept

- The control loop imports no model, evaluator, AXENT or provider (tested).
- A ResearchLead is attention, never evidence; a hint never becomes OBSERVED.
- OpportunityCandidate stays POTENTIAL; co-appearance never becomes a
  relationship; a recurring buyer is a question, not a customer.
- A family with no adopted source stays UNKNOWN with the routing reason
  (`NO_KNOWN_SOURCE`, `NO_ADOPTED_SOURCE:<pending sources and blockers>`).
- Operational state (frontier, schedule, spend, yield, fingerprints) lives in
  its own store; nothing here writes AXIGLAND. Website acquisitions go through
  the existing governed sensor → Observation Memory path.
- Operational learning moves routing order and cadence, never truth.

## Decisions (and where they improve on the proposal)

| Proposal | Chosen | Why it is better |
|---|---|---|
| Scheduler/queue infrastructure | One SQLite row per UTC day as a fenced lease; per-step atomic commits | Idempotency, resume and fencing with no new infrastructure; a worker that lost its lease cannot write |
| ResearchLead with priority score | Content-addressed lead + explicit tier (FIRST_OBSERVATION, FOLLOW_UP, STALE_EVIDENCE, SCHEDULED_REFRESH, LOW_YIELD) + stable tie-break | "Why spend here?" is `explain(lead)`; cyclic rediscovery merges into the same lead, so recursion cannot loop |
| Per-family acquisition | Shared acquisition key: one fetch serves every family that needs it (website → Presence, Value, Organization; awards → Markets, Relationships, Activity) | Reuse without double counting; each family keeps its own evidence rows and currentness |
| Expansion inside each family | Hints proposed by evidence, allowed only by the *target* family's policy, including cross-family rules (awards in Markets → regional demand in Demand; buyer in Relationships → buyer's open demand in Demand) | Fractal research across families without a generic crawler |
| Re-run evaluators on staleness | Recompute on **net** change per tick: material change → full family work; currentness transition → freshness-dependent dimensions only; aged-and-refreshed in the same tick → nothing | Removes the refresh round-trip cost while never globally skipping REFRESHED |
| Expansion from any finding | Only evidence new to the lead opens questions | Duplicates never grow the frontier |
| Loop expansion inside EOIL | EOIL loop executes one lead at depth 0; the frontier owns all expansion | One expansion mechanism, one budget |
| Fixed backoff | Per-family cadence and ceilings; Demand ceiling 3 days | Measured: 7 days saved 38 requests but delayed new demand by 4 days; 3 days finds it within one day of publication |

## Families

All ten canonical families have an explicit `FamilyObservationPolicy`:
entry points, economic questions, follow-up rules, depth, caps, cadence,
backoff ceiling, currentness policy, blocked recheck and stop conditions.
SEO/GEO are Presence follow-ups (search and generative visibility);
opportunities live in Demand; reviews/mentions in Reputation. New abstract
source capabilities: `PUBLIC_SEARCH_VISIBILITY`, `GENERATIVE_ANSWER_SURFACES`,
`PUBLIC_REVIEWS_AND_MENTIONS`, `ECONOMIC_FILINGS`, `SECTOR_CONTEXT`. They have
no adopted source yet, so those leads are blocked honestly.

## Real Brain wiring

`RecomputationPort` is implemented by `tools/runtime/observation_daily.py`
(`SubscriberBrainRecomputation`) over the canonical subscriber reobservation
entry: `ConfiguredSubscriberObservationPlanReader.observation_plan_for` →
`SubscriberEconomicRuntime.execute_observation_loop` → governed opportunity
projection → subscriber read. Membership and tenant are re-checked on every
call; capabilities come only from evidence admitted for the Organization.

- The canonical loop is fed by `RecordedFindingsPort`: a replay of the
  runtime's own real retrievals that answers a query only when an untruncated
  recorded query covers it, filtered with the new query's criteria and keeping
  the original retrieval time. Anything else is NOT_OBSERVED → UNKNOWN. No
  refetch, no second pipeline.
- Selective: only Demand/Markets material changes republish the projection,
  once per Xeed per tick; currentness alone is re-evaluated at read time;
  website families have no other governed consumer than Observation Memory.
- Replay uses no early sufficiency stop (it saves no request and would
  truncate the projection the subscriber reads).
- Committed daily acquisition receipts persist and are reused after a crash.
  A crash between public retrieval and receipt persistence can repeat that read;
  the scheduler does not claim exactly-once external side effects.

Production entrypoint `axignal-observation-daily` is off unless
`AXIGNAL_OBSERVATION_RUNTIME_ENABLED=true` and the operator provides the
existing market attention file plus an enrollment file (tenant, principal,
focus). Only TED (adopted, rights documented) is wired; the website needs an
operator FR-30 rights grant, so website leads stay blocked.

## Evidence

- `tests/integration/test_autonomous_observation_brain.py`: real subscriber
  signup, billing, focus and admitted capability evidence; daily ticks reach
  the Brain, the subscriber reading gains the new POTENTIAL opportunity,
  keeps earlier ones, adds zero source requests and survives restart.
- `tests/observation_runtime/test_runtime_e2e.py`: 40 controlled days, every
  tick a fresh process on the same files.
- `tests/observation_runtime/test_runtime_units.py`: budget scopes, crash and
  resume without repeated fetch, lease fencing, failure backoff and circuit,
  cyclic merge, model-free imports, policy coverage.
- `benchmark.json`: naive daily observer vs this runtime on the same world.

## Out of scope / UNKNOWN

- T12 supplies the existing systemd timer's production runner, opt-in config,
  bounded child lifetime, operational audit/status and installation runbook.
  Isolated candidate validation closes implementation/testing; integration
  and canonical deployment remain separate CTO actions.
- Adopted sources for reputation, search/generative visibility, filings,
  registries, regulation and funding: their families stay UNKNOWN.
- Website acquisition in production (needs an operator FR-30 rights grant)
  and an EB-04 economic output for website changes (no execution plan wired).
