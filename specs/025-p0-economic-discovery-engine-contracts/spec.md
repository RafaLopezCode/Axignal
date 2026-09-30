# P0 — Economic Discovery Engine Canonical Contracts

**Status:** DOCTRINE/ARCHITECTURE BASELINE DEFINITION
**Authority:** MASTER; Economic Discovery Engine Doctrine; ADR-0024

## Objective
Turn doctrine into provider-neutral executable contracts and observability before performance optimization or production promotion.

## Required contract surfaces
1. ObservationRecord / ObservationSet.
2. SemanticRepresentation.
3. RetrievalRequest / RetrievalHit / RetrievalSet.
4. DeterministicFilterDecision.
5. DecisionStateBundle / StateContract / InformationRequirements / AnswerabilityResult.
6. ChoiceSpaceContract / ChoiceOption.
7. StructuredJudgment with complete distribution and provider provenance.
8. InterpretationPolicy / InterpretationResult.
9. InvestigationRequest / InvestigationResult.
10. Admission/DerivedOpportunity boundary.
11. DiscoveryRunTrace / CandidateLineage / StageMetrics.

## Non-negotiable properties
Immutable/versioned IDs and fingerprints; no provider type in domain semantics; explicit missingness/UNKNOWN; provenance/currentness retained; exact lineage at every stage; complete evaluator distribution retained; no implicit probability threshold; no implicit top-k doctrine; no canonical write from retrieval/evaluator output; independently versioned interpretation; replayable config and code SHA.

## Baseline V0 protocol
The first baseline MUST use documented provider behavior without tuning against evaluation labels. Record exact encoder, TurboQuant implementation/version/config, retrieval config, JEV model/version, state compiler, DecisionContract/ChoiceSpace, interpretation policy and SHA.

Split corpus into development/calibration and sealed evaluation before threshold/policy optimization. Current germination-v0.1 is a seed fixture, not promotion evidence.

## Required metrics by boundary
Observe->Represent: coverage, failures, stale/missing dependencies, latency/cost.
Represent->Retrieve: Recall@K/budget, first relevant rank, positive survival, latency, memory/compression, query cost.
Retrieve->Filter: positive retention, false-reject rate, rejection by rule_id, UNKNOWN preservation, cardinality reduction.
Filter->Compile: answerability, missing requirements, unresolved refs, state size, provenance/temporal coverage.
Compile->Choice: coverage failures, no-match/abstention, option cardinality, overlap/ambiguity, fingerprint.
Choice->Evaluate: typed validity, distribution, provider-defined confidence, labelled calibration/confusion, failures, latency/cost.
Evaluate->Interpret: policy output, distribution sensitivity, abstention/investigation, labelled action error.
Interpret->Investigate->Admit: research/evidence yield, rejection reasons, POTENTIAL/UNKNOWN retention, independently admissible writes.
E2E: useful-discovery recall/precision where labelable, provenance/explanation coverage, time/cost per useful discovery, first-loss attribution.

## Failure taxonomy
OBSERVATION_MISS | REPRESENTATION_LOSS | RETRIEVAL_MISS | FILTER_FALSE_REJECT | STATE_INSUFFICIENT | CHOICE_SPACE_MISS | EVALUATOR_MISCLASSIFICATION | INTERPRETATION_ERROR | INVESTIGATION_MISS | ADMISSION_REJECT | GROUND_TRUTH_AMBIGUOUS

## Promotion gates
No production promotion until contracts exist behind provider-neutral boundaries; architecture/governance gates pass; BASELINE V0 is reproducible; sealed evaluation exists; stage attribution is demonstrated; provider/model swap preserves authority; no doctrine contradiction remains.

## Current known deltas
- GerminationBudget.retrieval_k=50 is experimental configuration, not doctrine.
- Current run metrics are aggregate and lack candidate-level first-loss lineage.
- Claim-evidence SUPPORTED gate is narrower than economic opportunity reasoning.
- Current 12-case corpus is too narrow for promotion.
- Production encoder, acquisition/investigation adapter and persistence remain unresolved.
