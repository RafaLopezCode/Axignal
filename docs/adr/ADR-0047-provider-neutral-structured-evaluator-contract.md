# ADR-0047 — Provider-Neutral Structured Evaluator Contract

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14–16, 19, 35, 53; Constitution IV–X, XVI–XVII; ADR-0011, ADR-0024, ADR-0025, ADR-0044.

## Context

The existing StructuredJudgment contract required a probability distribution and only optionally carried confidence/replay metadata. That shape was too strong for providers or structured-output mechanisms that return a selected choice without a calibrated distribution. Treating a selected choice as an implicit one-hot distribution would fabricate probability semantics and contaminate later calibration, comparison and policy decisions.

ADR-0024 required a raw typed distribution in every measurement trace. FR-21 supersedes only that universal-distribution assumption. Historical ADR-0024 records remain unchanged.

## Decision

AXIGNAL adopts a provider-neutral StructuredEvaluatorPort with explicit capability and availability semantics.

### Capability profile

Every evaluator declares an immutable EvaluatorCapabilityProfile containing:

- profile id/version;
- distribution capability: NEVER / OPTIONAL / ALWAYS;
- confidence capability: NEVER / OPTIONAL_PROVIDER_DEFINED;
- replay-reference support.

The profile has a deterministic fingerprint. Provider names are not architectural semantics.

### Request

StructuredEvaluationRequest binds the evaluation to:

- DecisionContract identity;
- state fingerprint;
- question fingerprint;
- ChoiceSpace fingerprint;
- exact option ids.

### Judgment

StructuredJudgment always carries:

- selected option;
- evaluator identity/version;
- exact contract/state/question/choice fingerprints;
- capability profile;
- explicit distribution availability;
- explicit confidence semantics;
- replay reference;
- optional provider distribution;
- optional provider confidence.

### Distribution semantics

DistributionAvailability is AVAILABLE or UNAVAILABLE.

If UNAVAILABLE, distribution must be empty. AXIGNAL must not synthesize a one-hot distribution from the selected option.

If AVAILABLE, the distribution must be non-empty, finite, normalized, uniquely labelled, contain the selected option and be permitted by the capability profile.

SELECTED_CHOICE != PROBABILITY_DISTRIBUTION

UNKNOWN_DISTRIBUTION != ONE_HOT_DISTRIBUTION

### Confidence semantics

Confidence is permitted only when ConfidenceSemantics is PROVIDER_DEFINED and the capability profile permits provider-defined confidence.

No universal confidence interpretation or threshold is introduced.

CONFIDENCE => PROVIDER_DEFINED_SEMANTICS

### Replay

The production-facing structured evaluator boundary requires replay-reference capability. A returned judgment must carry a concrete replay reference.

This reference identifies the exact provider/request-response artifact boundary; it does not give the evaluator canonical truth authority.

### Boundary validation

`evaluate_structured()` validates the returned judgment against the request and declared runtime profile:

- capability profile equality;
- DecisionContract identity;
- state fingerprint;
- question fingerprint;
- ChoiceSpace fingerprint;
- selected option membership;
- distribution labels inside the ChoiceSpace.

A provider adapter cannot silently answer a different state/question/choice space and still pass the boundary.

### UNKNOWN and abstention

UNKNOWN/UNRESOLVED/ABSTAIN remain ordinary AXIGNAL-owned ChoiceSpace options where the DecisionContract defines them. A choice-only evaluator can select such an option while distribution and confidence remain unavailable.

UNKNOWN != FALSE

UNKNOWN != LOW_PROBABILITY

### Relationship to downstream contracts

DimensionEvaluation is a downstream cognitive projection and EvidenceSupportJudgment is the separate evidence-admission support-judge contract. FR-21 does not merge or redefine those boundaries.

## Provider compatibility

The contract supports three capability patterns without embedding vendor names:

1. selected-choice only, no distribution, no confidence;
2. selected choice plus optional distribution, no mandatory confidence;
3. selected choice plus real distribution and optional provider-defined confidence.

These patterns are sufficient for the currently contemplated structured-output, Decisions-like and Jev-like bakeoff adapters. FR-22 will compare concrete providers on the same AXIGNAL contracts and data.

## Invariants

SELECTED_CHOICE != PROBABILITY_DISTRIBUTION

UNAVAILABLE_DISTRIBUTION => EMPTY_DISTRIBUTION

AVAILABLE_DISTRIBUTION => REAL_PROVIDER_DISTRIBUTION

UNKNOWN_DISTRIBUTION != ONE_HOT_DISTRIBUTION

CONFIDENCE => PROVIDER_DEFINED_SEMANTICS

PROVIDER_CAPABILITY != AXIGNAL_TRUTH

PROVIDER_NAME != CORE_ARCHITECTURE

JUDGMENT_PROVENANCE != OPTIONAL

STRUCTURED_EVALUATION => REPLAY_REFERENCE

UNKNOWN != FALSE

## Consequences

FR-22 can now compare heterogeneous evaluators without forcing them into fake common probability semantics. Calibration metrics may only be computed when a provider actually supplies a semantically valid distribution/confidence signal.

## Supersession

This ADR supersedes ADR-0024 only where ADR-0024 implied that every structured evaluation emits a raw typed distribution. The corrected rule is: every run emits the selected choice and explicit uncertainty availability; raw provider distribution/confidence are retained when actually supplied and semantically defined.

## Non-goals

This ADR does not select a winning provider, define calibration thresholds, promote provider output to canonical truth, alter EvidenceAdmission, or run the FR-22 bakeoff.
