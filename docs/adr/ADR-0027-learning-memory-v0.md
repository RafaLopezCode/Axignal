# ADR-0027 — Governed Learning Memory V0

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; Constitution IX, X, XV, XVII; ADR-0013, ADR-0024, ADR-0025, ADR-0026.

## Context

AXIGNAL Prime can now observe, persist observations, compile rich state, route cognitive work and bootstrap a planted Xeed into the normal event-driven Brain. The next compounding capability is to retain operational evidence about what AXIGNAL tried, what changed, what it cost and how later evidence corrected earlier operational interpretations.

That memory must not become a second truth system, provider memory, opaque reward model or self-modifying policy engine.

## Decision

Introduce LearningMemory as a provider-neutral append-only application contract with a durable SQLite adapter. A learning event records:

- stable event/activity identity and code/policy version;
- canonical subject and optional Xeed attribution;
- mechanism family and optional provider/version;
- input/output and before/after state fingerprints;
- explicit outcome and reason code;
- measured cost/usage/latency with UNKNOWN distinct from measured zero;
- explicit output cardinalities (LearningYield);
- optional correction lineage to a prior learning event.

Exact replay is idempotent. Reusing an event id with different governed content fails closed. Corrections are new events and never overwrite history.

## Authority separation

LEARNING_MEMORY != OBSERVATION_MEMORY

LEARNING_MEMORY != AXIGLAND

LEARNING_EVENT != FAXT

OPERATIONAL_OUTCOME != ECONOMIC_TRUTH

MODEL LEARNING != AXIGNAL LEARNING

PROVIDER MEMORY != AXIGLAND MEMORY

MEASURED ZERO != UNKNOWN COST

CORRECTION != HISTORY REWRITE

Observation Memory retains governed world observations. AXIGLAND retains admitted/derived economic knowledge under its own authorities. Learning Memory retains operational evidence about AXIGNAL's own observation/reasoning process. No Learning Memory event may bypass EvidenceAdmission or mutate canonical economic state.

## Measurement without opaque scoring

V0 exposes deterministic summaries only: event/outcome counts, cost grouped by currency, unknown-cost count, known latency totals, explicit yield totals and correction count.

V0 deliberately defines no universal quality score, reward, source rank, evaluator rank, success probability or automatic optimization objective. Counts are observations, not value judgments. Cross-currency costs are never silently summed.

## Correction semantics

A correction event must reference an existing event for the same canonical subject. The original event remains immutable and inspectable. Correction means later operational evidence changed how AXIGNAL should interpret the prior operational result; it does not assert that either event is canonical economic truth.

## Bootstrap integration

A completed Xeed bootstrap attempt may emit a Learning Memory event bound to the exact BootstrapPlan.plan_fingerprint, policy version, state before/after, measured cost and observed yield. Recording the event grants no authority to update the bootstrap policy.

## Promotion boundary

Learning Memory V0 is observational. It MAY support offline comparison, replay, policy experiments and future proposal generation. It MUST NOT:

- change routing or bootstrap policy automatically;
- rewrite DecisionContracts or Choice Spaces;
- alter source authorization;
- promote a provider;
- change EvidenceAdmission;
- write FAXT/RELATIONSHIP/AXIGLAND state;
- treat subscriber retention or commercial outcome as epistemic truth.

Any future automated or semi-automated policy proposal/promotion mechanism requires a separate versioned contract and governance decision with held-out/replay evidence.

## Consequences

AXIGNAL can now accumulate its own process history without coupling learning to Luna, Decisions, Jev or any future provider. Cost/yield/correction evidence can survive provider replacement and can be compared against exact policy/code/state fingerprints.

This creates the minimum trustworthy substrate for later source economics, evaluator comparison, research-yield analysis and governed policy improvement while preserving the core rule: Python and explicit governance own policy; evidence authorities own truth.
