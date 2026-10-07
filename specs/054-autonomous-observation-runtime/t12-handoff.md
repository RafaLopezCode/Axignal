# T12 — Scheduler implementation handoff

Branch: `codex/autonomous-runtime-t12`. Base: `4df7edfe77825d39216d178392bcc23b35078477`.
Integration and canonical deployment are separate CTO actions; this branch does
not authorize either. Exact final candidate SHA, PR, gate totals and preflight
artifact paths are recorded in the PR's validation section.

## Mechanism and operating contract

The existing systemd timer wakes the existing one-shot runtime at 03:17 UTC,
with persistent catch-up and up to 15 minutes of jitter. Business cadence and
next-due decisions remain in `run_daily_tick`; no second engine or generic
scheduler is introduced. The runner resolves the deployed release's exact image
and invokes `tools.runtime.observation_daily` once. It passes no model secrets,
publishes no port and runs with UID 33, a read-only root and bounded resources.

Activation uses `AXIGNAL_OBSERVATION_RUNTIME_ENABLED=true` in the root-owned
`/etc/axignal/observation-runtime/scheduler.env`, plus valid server-owned attention
and enrollment. Absent/false is DISABLED; absent files are NOT_CONFIGURED with
zero child work. Configuration never invents tenants, identity, rights or truth.
After CTO cutover, `install-observation-scheduler.sh --install` validates and
installs the existing units, preserves config and enables the timer. `--check`
validates without installing. Neither command moves `current`.

Host flock plus a stable container name serialize wakeups. SQLite retains
mandatory token fencing and denies any concurrent live tick across UTC midnight.
Elapsed time is checked before acquisition/recomputation and every commit;
expired tokens cannot write even without a takeover. The service's hard lifetime
is 30 minutes, below the one-hour lease, with an own-worker Docker stop on exit.
The existing daily runtime budget is 900 seconds, 60 requests and 40 actions;
UNKNOWN cost remains unroutable and produces zero source calls.

Invocation start/end and redacted aggregate outcomes persist alongside tick,
budget, receipts and pending recomputation in `observation-runtime.sqlite3`.
`--status` reads without creating a database or exposing tokens, tenant/focus
identifiers, raw evidence or exception messages. Interrupted invocation records
remain unfinished; recovery waits for expiry and preserves committed spend and
receipts. A crash before retrieval receipt persistence can repeat a public read;
there is no exactly-once external-effects claim.

Rollback: set the flag false, disable/stop the timer, stop its one-shot service.
Retain data and enrollment; do not erase the store to force a same-day retry.
See `deploy/production/README.md` for commands and the first authorized real tick.

## Changed files

- `application/observation_runtime/{ports,tick}.py`: lease validation boundary,
  elapsed authority and explicit unknown-cost handling.
- `pipeline/observation_runtime/sqlite_store.py`: cross-day fencing and operational
  invocation/status persistence; no canonical AXIGLAND writer.
- `tools/runtime/observation_daily.py`: same runtime/Brain entry with redacted audit
  and operator status; CLI accepts explicit arguments for embedded callers.
- `deploy/production/`: existing service/runner, opt-in config example, installer
  and runbook. The existing timer cadence is unchanged.
- `tests/observation_runtime/test_scheduler_{runtime,deployment}.py`,
  `tests/integration/test_autonomous_observation_brain.py` and
  `tests/integration/test_observation_daily_entrypoint.py`: discriminants below.
- This feature's spec, plan, tasks and handoff evidence.

## Validation discriminants

- Real subprocess disabled/status/no-work/restart/same-day replay.
- Two actual concurrent tick invocations: one worker, no duplicate requests.
- Expiry before child work, live cross-day denial and stale-owner write rejection.
- Abrupt process death, durable unfinished audit and recovery after expiry.
- UNKNOWN source cost: zero requests; existing exhausted/scoped-budget cases.
- Source failure backoff/circuit and committed-receipt resume remain covered.
- Forty controlled days with fresh stores, and the real subscriber Brain E2E
  parametrized through direct and scheduled entries, including tenant denial,
  new POTENTIAL opportunity, restart and no refetch on subscriber read.
- Five stdlib unittest cases in the exact Linux candidate, including actual shell
  runner to runtime entry, overlapping wakeups, bad config and Docker failure.

The isolated preflight uses a SHA-named release/image, fresh candidate-only data,
empty enrollment/attention, an own container name and `network=none`. It checks
installer syntax, disabled/no-work/replay/status and candidate lease recovery.
Candidate HTTP health uses separate data, no ports and no secrets, then stops its
own container. This demonstrates deployability and safe no-work behavior; it
does not claim a real subscriber observation happened in canonical production.

## Reconciliation with dependent features

| Feature | T12 relationship | Deliberately remaining work |
|---|---|---|
| 050 subscriber Brain | Reuses authorized canonical runtime, membership and replay projection | Open EB-04 variable-cost/concurrency and broader frontend tasks are not closed by T12 |
| 053 economic observation intelligence | Reuses registry, TED adapter, strategies, findings and opportunity projection | T9/T10 sources and broader T11 strategy/coverage persistence remain open; the daily scheduler slice is delivered in 054 |
| 055 tenant-grounded AXENT | No provider calls or AXENT changes | T10 research-request consumption and T11 model production enablement remain open |
| 054 autonomous observation | Closes daily scheduler implementation/testing | T13 source adoption remains open with honest UNKNOWN families |

## Canonical production boundary

The observed production SHA was
`ca6866f9586507a9984c7b63cf48e4dfad773353` at both `current` and Docker
`DEPLOYED_SHA`. Canonical landing/experience/runtime container IDs started with
`e87b7d21ef38`, `87bef69e7018`, `11f9ed0ba510`; all stayed healthy during preflight.
No unit installation, canonical timer start, configuration write, mutable
production mount, merge, main update or cutover is part of this handoff.

T12 implemented/tested; integration in main: NO, pending CTO. Canonical
deployment: NO, pending CTO. T13 remains open. First real authorized production
tick remains a CTO deployment acceptance action, not a source-adoption blocker.
