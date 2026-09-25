# Feature Specification: P0-JEV-Deep-Recon Reconciliation

**Status:** Implemented as an experimental reference slice; pending CTO review.
**Authority:** ADR-0011; subordinate to MASTER, Constitution and accepted ADRs.
**Production status:** Pre-implementation. This slice adds no production behavior or provider call path.

## Objective

Make the experimental Decision Laboratory incapable of treating successful serialization as proof that a semantic request contains the information required by its question. Preserve exact historical V0.1/P0-JEV-03 interpretation and replay.

## Requirements

1. Define a versioned provider-neutral DecisionContract and separate claim/evidence, entity-pair and economic-relationship StateContracts.
2. Resolve evidence references explicitly; unresolved references fail closed. Keep assembly, normalization, state validation, serialization and fingerprinting separate.
3. Validate declared information and primitive/answer-space contracts deterministically before provider eligibility.
4. Keep answerability distinct from truth, expected model quality, composition and canonical authority.
5. Preserve primitive-specific raw uncertainty and versioned deterministic composition.
6. Create a new immutable grammar and synthetic evidence-bearing V-next corpus with evaluator-only labels.
7. Exclude unanswerable/no-single-label cases from quality metrics; attribute failures with an explicit evidence basis.
8. Provide an offline experiment validity gate, locked held-out policy and preregistration. Current live eligibility is NO; live authorization is NO.
9. Leave historical V0.1 files and P0-JEV-03 evidence untouched.
10. Reject future provider execution through the historical V0.1 lab route before credential lookup; preserve offline V0.1 replay.

## Out of scope

Production Jev/TypeSafe or Luna/OpenAI integration, live calls, database or deployment, canonical writes, evidence admission, Knowledge Frontier/Research Planner, AXENT/AXIGLAND/Xeed/AXENT runtime, UI, and any following slice.

## Acceptance

Deterministic tests establish contract shape, content/reference requirements, missingness distinctions, pairwise/endpoints/time validation, primitive rules, raw uncertainty retention, metric exclusion, fail-closed experiment eligibility, historical evidence presence and absence of provider/canonical-writer imports. All repository-required deterministic gates pass. No claim of model quality or statistical validation is made.
