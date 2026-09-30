# ADR-0024 — Measurable Economic Discovery Engine

**Status:** PROPOSED
**Date:** 2026-09-30
**Authority:** MASTER §§14–16, 19, 35, 53; Economic Discovery Engine Doctrine; Constitution IV–X, XVI–XVII

## Decision
AXIGNAL adopts a provider-neutral measurable chain:
OBSERVE -> REPRESENT -> RETRIEVE -> FILTER -> COMPILE_STATE -> BUILD_CHOICE_SPACE -> STRUCTURED_EVALUATE -> INTERPRET -> INVESTIGATE -> ADMIT.

Every boundary is a versioned contract and attribution point. Provider choices, retrieval budgets, probability thresholds and benchmark heuristics are configuration/policy, never architectural semantics.

## DecisionContract bundle
Structured evaluation is invalid unless the run identifies DecisionContract + StateContract + InformationRequirements + ChoiceSpaceContract + AnswerabilityGate + StateFingerprint + QuestionFingerprint + EvaluatorVersion. Exact provider payload is replayable. Raw provider output and full distribution remain separate from AXIGNAL interpretation.

## Choice-space rule
Choice spaces are AXIGNAL-owned semantic assets. They MUST include abstention/no-match when supplied alternatives may not cover reality. A selected choice is relative to the supplied space and cannot establish coverage.

## Measurement contract
Every run emits append-only trace: run/config/code IDs; input/output cardinality per stage; per-candidate lineage/rejection; rank/similarity; deterministic rule IDs; state/question/choice fingerprints; raw typed distribution; interpretation policy/version/output; investigation/admission outcome; observable cost/latency.

Ground-truth benchmarks compute stage-level positive retention and first-loss attribution. End-to-end score alone is insufficient.

## Experimental discipline
1. Build documentation-conformant BASELINE V0 before optimization.
2. Separate development/calibration from sealed evaluation.
3. Change attributable variable families independently when feasible.
4. Never tune against sealed labels.
5. Preserve negative/failed runs.
6. No threshold is canonical until independently validated and explicitly promoted.

## Consequences
Current retrieval_k=50, SUPPORTED-only germination gate and 12-case corpus remain experimental evidence. TurboQuant stays behind SemanticIndex. JEV stays behind a provider-neutral structured evaluator. Foundation LLMs/AXENT may research/propose inputs but cannot bypass deterministic compilation, answerability, interpretation or EvidenceAdmission.

## Rejected alternatives
Vector top-k directly becomes opportunity; JEV directly writes truth; universal SUPPORTED/NOT_SUPPORTED; opaque opportunity score; fixed 50% rule across Choice Spaces; benchmark optimization without stage attribution.
