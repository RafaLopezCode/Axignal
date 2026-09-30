# ADR-0029 — Execution Budget and Stop Contract

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0025, ADR-0026, ADR-0027, ADR-0028.

## Context

FR-02 established that NOT_ANSWERABLE does not imply RESEARCH_REQUIRED. Once research is warranted, AXIGNAL still needs a hard, provider-neutral mechanism that bounds how much work may continue.

Existing timeouts and source limits are local implementation details. They do not form one governed execution authority, do not produce a common stop reason, and do not ensure that research/retry loops terminate predictably.

## Decision

Introduce a deterministic Execution Budget and Stop Contract owned by AXIGNAL.

The policy may bound:

- measured monetary spend in one explicit currency;
- request count;
- source count;
- elapsed wall-clock budget;
- retries;
- loop/expansion count;
- consecutive no-progress steps;
- whether UNKNOWN monetary cost must fail closed.

The controller evaluates current usage before another unit of work is allowed.

`BUDGET != TRUTH STANDARD`

`STOP != FAILURE OF EVIDENCE`

`UNKNOWN COST != ZERO COST`

`PARTIAL != COMPLETE`

## Stop reasons

The governed stop reasons are explicit and replayable:

- MONETARY_BUDGET_EXHAUSTED
- REQUEST_BUDGET_EXHAUSTED
- SOURCE_BUDGET_EXHAUSTED
- DEADLINE_EXCEEDED
- RETRY_LIMIT_REACHED
- LOOP_LIMIT_REACHED
- NO_PROGRESS
- COST_UNKNOWN

Once a stop decision is reached, the governed controller refuses to record or authorize another execution step.

## Cost semantics

Measured monetary cost is accumulated only when it remains measurable and currency-compatible. If cost becomes UNKNOWN, AXIGNAL preserves UNKNOWN rather than converting it to zero.

A policy may explicitly require stop-on-UNKNOWN-cost. Otherwise other non-monetary limits continue to bound the run.

Cross-currency accumulation is invalid and fails closed.

## Learning Memory

A governed stop may be recorded as a Learning Memory event with:

- PARTIAL operational outcome;
- exact policy id/version;
- exact usage-state fingerprint;
- explicit stop reason;
- measured cost/latency where known;
- no fabricated successful yield.

A stop event is operational evidence only. It grants no canonical or policy-promotion authority.

## Integration boundary

FR-03 defines the reusable budget authority and controller. FR-04 owns the composition root that applies it across actual Prime execution.

Existing HTTP/source-specific timeouts remain local safety controls and do not replace this application-level budget authority.

## Consequences

Any future research or observation executor can be made finite by construction without coupling budget logic to Luna, Decisions, Jev, HTTP, browser automation or another provider.

Budget exhaustion preserves partial state and UNKNOWN. It never weakens evidence standards to satisfy a cost target.
