# ADR-0045 — Governed Policy Candidate, Replay and Shadow

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0025, ADR-0027, ADR-0043, ADR-0044.

## Context

FR-17 connected Learning Memory to real execution and FR-18 made replayability explicit. AXIGNAL can therefore compare policy behavior on retained operational evidence, but doing so introduces a Goodhart/self-modification risk if a candidate can see sealed holdout outcomes, mutate production, drop negative cases or promote itself.

FR-19 establishes an offline-only governed learning boundary. It creates actual policy-experiment machinery without creating a production-promotion path. Production promotion and rollback remain FR-20.

## Decision

Introduce immutable PolicyCandidate, HeldOutPolicySplit, PolicyReplayInput, ReplayEvaluation, ShadowPolicy and PolicyComparisonReport contracts.

### Immutable candidate

A PolicyCandidate records candidate identity, policy family, exact baseline identity/version, candidate version, code SHA, sealed split identity/fingerprint, creation time, development event ids and versioned parameter values.

A candidate has `production_authority = False`. There is no promotion method or production mutation port in this module.

Candidate construction accepts development evidence only. If any supplied event belongs to holdout or falls outside the development side of the sealed split, construction fails closed.

### Organization + time holdout

HeldOutPolicySplit separates both organizations and time:

- development organization ids must be disjoint from holdout organization ids;
- development evidence must occur at or before development_end_at;
- holdout evidence must occur at or after holdout_start_at;
- development_end_at must precede holdout_start_at.

The split has a deterministic fingerprint and a candidate is permanently bound to that exact split.

### No sealed-label tuning

Shadow evaluators do not receive the original LearningEvent.

They receive PolicyReplayInput containing only:

- event identity;
- subject identity;
- occurrence time;
- mechanism/kind;
- input fingerprint;
- FR-18 replay references.

Historical outcome, reason code and output fingerprint are deliberately excluded from the evaluator input. Those fields remain available only to the comparison layer for counter-metrics.

Therefore a challenger cannot tune its answer from the sealed historical result through the governed interface.

### Replay gate

Only FR-18 `REPLAYABLE` events are evaluated by baseline and candidate evaluators.

`NON_REPLAYABLE` events remain in the comparison report as explicit NON_REPLAYABLE cases with their reason. They are not silently dropped and no synthetic decision is fabricated.

### Shadow execution

ShadowPolicy receives immutable replay input plus pure evaluator ports. It has no repository, EvidenceAdmission, Observation Memory, AXIGLAND or active-policy mutation capability.

Evaluator exceptions are converted into explicit FAILED shadow decisions and retained in the report.

### UNKNOWN and abstention

PolicyDecision has explicit states:

- VALUE;
- UNKNOWN;
- ABSTAIN;
- FAILED.

UNKNOWN and ABSTAIN cannot carry a fabricated value.

Counter-metrics explicitly report when a candidate converts baseline UNKNOWN or ABSTAIN into VALUE. These are epistemic regressions, not improvements.

### Counter-metrics

The comparison report exposes descriptive counters rather than one opaque score:

- total/evaluated/non-replayable holdout cases;
- source failed cases;
- baseline/candidate UNKNOWN counts;
- baseline/candidate ABSTAIN counts;
- baseline/candidate FAILED counts;
- UNKNOWN lost;
- abstention lost;
- newly introduced failures;
- value disagreements.

`regression_count` is limited to explicit safety regressions: UNKNOWN lost + abstention lost + failure introduced. A value disagreement is reported separately and is not declared better or worse without an external governed label contract.

### Negative and failed runs

Historical FAILED Learning Events and NON_REPLAYABLE events remain in the held-out report. FR-19 does not optimize by dropping inconvenient cases.

## Invariants

OBSERVED_EXECUTION != POLICY_CANDIDATE

POLICY_CANDIDATE != PRODUCTION_POLICY

SHADOW_RESULT != PRODUCTION_POLICY

POLICY_CANDIDATE => PRODUCTION_AUTHORITY_FALSE

SHADOW_POLICY => NO_PRODUCTION_SIDE_EFFECTS

HOLDOUT_EVIDENCE != CANDIDATE_CONSTRUCTION_INPUT

SEALED_HISTORICAL_OUTCOME != EVALUATOR_INPUT

NON_REPLAYABLE != DROPPED_CASE

UNKNOWN != VALUE

ABSTAIN != VALUE

FAILED_RUN != EXCLUDED_RUN

VALUE_DISAGREEMENT != QUALITY_VERDICT

AUTOMATIC_PROMOTION = FORBIDDEN

## Consequences

AXIGNAL now has a governed offline learning loop that can freeze a candidate from development evidence, replay only eligible held-out evidence, run a no-side-effect shadow comparison and report explicit counter-metrics/regressions.

This is sufficient experimentation machinery for FR-19 but intentionally insufficient to mutate production. FR-20 must introduce the separate human/governance promotion and rollback gate.

## Non-goals

This ADR does not promote policies, define canary deployment, choose a universal reward function, create a model-training loop, permit sealed-label tuning, change EvidenceAdmission or write canonical AXIGLAND state.
