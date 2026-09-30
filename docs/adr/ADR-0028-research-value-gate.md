# ADR-0028 — Research Value Gate

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0025, ADR-0026, ADR-0027.

## Context

FR-01 separated dimensional answerability from global bootstrap completeness. That exposed a
second architectural problem: a dimension can be NOT_ANSWERABLE without being worth
researching now.

Automatically mapping every knowledge gap to adaptive research would optimize completeness
rather than useful economic knowledge, increase cost, encourage loops, and blur the
distinction between UNKNOWN and actionable uncertainty.

## Decision

Introduce a deterministic, versioned Research Value Gate before any
`PrimeRoute.ADAPTIVE_RESEARCH` authorization.

The gate emits exactly one of:

- `RESEARCH_NOW`
- `RETAIN_UNKNOWN`
- `DEFER`
- `BLOCKED_BY_BUDGET_OR_RIGHTS`

Research worth is not represented as one opaque score. V0 evaluates explicit signals and
governance constraints:

- materiality;
- expected decision impact;
- reuse potential;
- freshness need;
- rights permission;
- capability availability;
- budget permission or UNKNOWN budget;
- no-progress evidence.

`ANSWERABILITY != WORTH_RESEARCHING`

`UNKNOWN != RESEARCH_REQUIRED`

`RESEARCH_VALUE != TRUTH_VALUE`

## Fail-closed routing

A NOT_ANSWERABLE Prime work item MUST carry a Research Value decision bound to the same
canonical subject, exact state fingerprint, dimension, and missing requirements.

Without that decision, Prime fails closed.

Only `RESEARCH_NOW` may produce `PrimeRoute.ADAPTIVE_RESEARCH`. The other dispositions
retain the gap without an execution route.

Providers/models cannot authorize their own research. The gate is AXIGNAL-owned,
deterministic Python policy.

## Bootstrap

When no initial dimension is answerable and no explicit known source can progress the
bootstrap, Bootstrap no longer escalates automatically to adaptive research. It consumes
the same Research Value decisions:

- any warranted `RESEARCH_NOW` may authorize adaptive research;
- otherwise blocking takes precedence over defer;
- defer takes precedence over retain-unknown;
- pure low-value gaps remain UNKNOWN.

Known-source deterministic acquisition may still proceed without adaptive-research
authorization because source candidate != adaptive research and dispatch remains governed
by source policy.

## Replay and provenance

Research Value decisions preserve:

- subject;
- state fingerprint;
- dimension;
- exact missing requirements;
- policy id/version;
- context fingerprint;
- explicit reason codes.

Prime propagates that provenance in its work item.

## Non-goals

FR-02 does not implement monetary budgets, hard retry/loop/deadline limits, or runtime
execution stopping. FR-03 owns those mechanisms.

It also does not create provider selection, canonical admission, or a universal
information-value score.

## Consequences

AXIGNAL can preserve UNKNOWN deliberately when research has insufficient value, defer work
without falsifying absence, and block research for governance reasons while keeping the
gap visible and replayable.

Adaptive intelligence becomes an explicitly warranted resource rather than the default
reaction to missing information.
