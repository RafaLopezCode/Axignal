# ADR-0052 — Unit Economics Instrumentation Over Learning Memory

**Status:** ACCEPTED
**Date:** 2026-10-01
**Decision scope:** FR-26
**Upstream authority:** MASTER §§49–50, §56.14, §56.16; Constitution XII, XV, XVII

## Context

AXIGNAL needs real Xeed/cohort economics without creating a second operational ledger or converting missing measurements into fabricated zeroes. FR-17 already established append-only `LearningEvent` evidence with measured cost, latency and yield. FR-26 therefore projects economics from those events and adds only the attribution/value observations that Learning Memory cannot infer by itself.

## Decision

Unit economics is a deterministic application projection over exact `LearningEvent` identities.

Each included event MUST have explicit `UnitEconomicsAttribution` declaring:

- lifecycle phase: `FIRST_VALUE`, `GERMINATION`, or `MAINTENANCE_REFRESH`;
- cost scope: `SHARED_CANONICAL` or `XEED_PRIVATE`;
- allocation method;
- allocated cost, or explicit unknown cost;
- fresh reuse count when observed;
- useful-Xignal count when explicitly observed;
- evidence-inspection count when explicitly observed.

Missing allocated cost remains `None`. Measured zero remains zero.

Shared cost cannot use direct/private attribution. Private cost cannot use a shared allocation method. Every economics row must trace to one exact Learning Event.

## Derived measures

AXIGNAL may deterministically derive first-value/germination/maintenance cost by currency, cost coverage, reuse ratio, fresh reuse ratio, time to first explicitly useful Xignal, evidence inspections, correction count, shared/private cost totals, Xeed/cohort aggregates, and contribution margin only when revenue, non-compute variable cost and compute cost are all known in one currency.

Ratios retain integer numerator/denominator rather than manufacturing precision.

## Invariants

```text
MISSING COST != ZERO
EMITTED XIGNAL != USEFUL XIGNAL
USAGE != WILLINGNESS TO PAY
SHARED COST != PRIVATE COST
ALLOCATION != RAW COST
MULTI-CURRENCY != SUMMABLE MONEY
COMMERCIAL OUTCOME != EPISTEMIC VALIDITY
ECONOMICS PROJECTION != CANONICAL TRUTH
```

FR-26 does not infer willingness-to-pay, truth, sale probability, or Xignal quality from usage.

## Consequences

Pricing validation can consume measured economics without contaminating epistemic state. Future real runs can gradually increase cost coverage while unknowns remain visible. Cohort aggregation sums raw counts before deriving ratios, avoiding averages-of-averages.

## Rejected alternatives

- **Treat unknown cost as zero:** rejected because it biases margin and cost coverage.
- **Count every emitted Xignal as useful:** rejected because emission is not demonstrated value.
- **Create a separate economics event store:** rejected because Learning Memory already owns execution evidence and duplicate ledgers drift.
- **Infer willingness-to-pay from usage:** rejected by product-validation doctrine.