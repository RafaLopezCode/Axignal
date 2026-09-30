# ADR-0046 — Policy Promotion and Rollback Gate

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0025, ADR-0027, ADR-0043, ADR-0044, ADR-0045.

## Context

FR-19 created an offline candidate/replay/shadow loop with no production authority. AXIGNAL still needed an explicit boundary for adopting a candidate without turning Learning Memory, runtime yield or shadow output into self-modifying production policy.

FR-20 introduces that boundary. Promotion is a human/governance decision over sealed evidence. Rollback is a new append-only governance decision, not history rewrite.

## Decision

Introduce `PromotionGatePolicy`, `GovernanceApproval`, `PolicyDecisionRecord`, `ActivePolicyRef`, `RolloutPlan`, `ActivePolicyStore`, `promote_policy()` and `rollback_policy()`.

### Promotion authority

`promote_policy()` requires all of the following:

- immutable FR-19 PolicyCandidate;
- exact FR-19 PolicyComparisonReport;
- explicit GovernanceApproval scoped to `PROMOTE`;
- versioned PromotionGatePolicy;
- explicit RolloutPlan;
- durable ActivePolicyStore;
- current active baseline matching the candidate baseline exactly.

Learning Memory, LearningYield, runtime outcomes and ShadowPolicy are not accepted as promotion-authority inputs.

RUNTIME_YIELD != PROMOTION_AUTHORITY

SHADOW_RESULT != PROMOTION_AUTHORITY

### Evidence integrity

The gate does not trust report counters supplied by a caller.

Before promotion it deterministically recomputes FR-19 counter-metrics from the sealed ReplayEvaluation set and requires exact equality with the report. A report with forged or stale counters fails closed.

REPORT_METRICS != CALLER_ASSERTION

The versioned gate then enforces:

- minimum evaluated holdout cases;
- maximum allowed non-replayable cases;
- zero governed regressions when configured;
- canary rollout when configured.

A value disagreement remains descriptive; FR-20 does not convert disagreement into a quality score.

### Explicit approval

GovernanceApproval binds:

- approval id;
- action (`PROMOTE` or `ROLLBACK`);
- exact candidate id/fingerprint;
- exact comparison fingerprint;
- exact promotion-gate id/version;
- APPROVE/REJECT decision;
- human/governance identity;
- timezone-aware approval time;
- rationale;
- exact target promotion decision for rollback.

A promotion approval cannot be reused for rollback. A rollback approval cannot target a different promotion.

Approval cannot predate candidate creation and a policy decision cannot predate its approval.

### Stale baseline protection

A candidate may promote only if its baseline id/version still equals the current active production pointer. A candidate created against an older baseline fails closed after another policy has become active.

### Canary

RolloutPlan supports DIRECT and CANARY. CANARY requires an explicit percentage from 1 through 99. DIRECT cannot carry a canary percentage.

A PromotionGatePolicy may require CANARY; a direct rollout then fails closed. FR-20 governs the rollout decision and durable plan. It does not implement infrastructure-specific traffic splitting.

### Durable active-policy state

The SQLite adapter stores:

- immutable policy decision history;
- current active-policy pointer;
- latest decision pointer.

`append_and_activate()` runs in one SQLite `BEGIN IMMEDIATE` transaction. It verifies:

- decision-id idempotency/conflict;
- current from-policy equality;
- previous-decision pointer equality;
- atomic decision append plus active-pointer movement.

Existing policy-decision rows are never updated or deleted.

### Initial baseline

`seed_active()` exists only to establish the pre-governance baseline once. It is idempotent only for the exact same baseline before any governance decision exists.

It cannot overwrite an initialized family and cannot run after governance history exists. Once the baseline is established, all policy movement is through governed decisions.

### Rollback

Rollback requires:

- an existing promotion decision;
- that promotion still being the current active policy;
- explicit `ROLLBACK`-scoped APPROVE record targeting that exact promotion;
- matching candidate/comparison/gate provenance.

Rollback appends a new PolicyDecisionRecord whose `to_policy` is the promotion's prior `from_policy`, with `rollback_of` and `previous_decision_id` preserved.

No promotion record is deleted or modified.

ROLLBACK != HISTORY_REWRITE

## Durable decision trace

Every promotion/rollback record retains:

- from/to policy refs;
- candidate/comparison fingerprints;
- gate id/version;
- approval id, action, approver, approval time and rationale;
- rollout mode/canary percentage;
- previous decision pointer;
- rollback target when applicable;
- deterministic decision fingerprint.

Reopening the SQLite store reconstructs the same current pointer and decision history.

## Invariants

POLICY_CANDIDATE != PRODUCTION_POLICY

RUNTIME_YIELD != PROMOTION_AUTHORITY

SHADOW_RESULT != PROMOTION_AUTHORITY

REPORT_METRICS != CALLER_ASSERTION

PROMOTION => EXPLICIT_APPROVE

PROMOTION => MATCHING_ACTIVE_BASELINE

PROMOTION => VERSIONED_EVIDENCE_GATE

REQUIRED_CANARY => CANARY_ROLLOUT

PROMOTION_APPROVAL != ROLLBACK_APPROVAL

ROLLBACK => EXACT_PROMOTION_TARGET

ROLLBACK != HISTORY_REWRITE

POLICY_DECISION_HISTORY = APPEND_ONLY

ACTIVE_POINTER_CHANGE => DURABLE_POLICY_DECISION

LEARNING_MEMORY != POLICY_AUTHORITY

## Consequences

AXIGNAL can now adopt an offline candidate through explicit governed evidence and can return to the prior active policy without erasing the promotion decision. Runtime learning remains observational and cannot self-promote.

FR-21 can evolve provider-neutral structured evaluator semantics without weakening the policy-governance boundary.

## Non-goals

This ADR does not define a universal reward score, automatically approve candidates, implement provider/model selection, implement infrastructure-specific canary traffic splitting, mutate EvidenceAdmission, or write canonical AXIGLAND state.
