# P0-JEV-01 Conceptual Data Model

**Conceptual only.** This document defines relationships and semantics, not a
database schema, JSON wire format, ORM, event store or retention policy.

```text
DecisionGrammarVersion 1 ──* DecisionQuestionVersion
DecisionQuestionFamily 1 ──* DecisionQuestionVersion
DecisionStateContract 1 ──* StructuredDecisionState
StructuredDecisionState 1 ──* EvaluationAttempt
EvaluationAttempt 1 ──* RawStructuredJudgment
RawStructuredJudgment * ──1 EvaluatorVersion / capability profile
RawStructuredJudgment * ──1 DecisionCompositionPolicyVersion
DecisionCompositionPolicyVersion + judgments → StructuredEvaluation
StructuredEvaluation ──0..* MissingInformationRequirement
MissingInformationRequirement ──policy projection→ KnowledgeFrontier
LabCase + ExperimentDefinition → ExperimentResult
GrammarCandidate + ExperimentResult + RedTeam + authority decision
    → proposed GrammarPromotionDecision
```

## Aggregates and shared value semantics

- **DecisionQuestionVersion**: stable ID/family/class, version, primitive,
  complete semantic instructions and criteria, state contract/path references,
  exclusions, boundary/no-match/unknown behavior, consumer, epistemic meaning,
  calibration status and lifecycle metadata.
- **DecisionStateContract / StructuredDecisionState**: versioned family shape;
  required fields and privacy/evidence classes; compiled values with source
  references; observation/inference and unknown/missing distinctions. Compiler
  output is an evaluation input, never canonical admission.
- **EvaluatorVersion / EvaluatorCapabilityProfile**: evaluator implementation,
  requested alias and resolved model ID where available, API/response schema
  version, known limitations with source/review date, and empirical limitations
  by AXIGNAL question/state family. No alias stability is assumed.
- **RawStructuredJudgment**: discriminated Noul, Choice or Score value;
  probabilities/distribution and provider-defined confidence; question/version
  and evaluation references; timestamp and usage when available. Invalid or
  absent data is not repaired by default values.
- **EvaluationAttempt**: state/question/evaluator references, attempt
  lifecycle, operational error category, bounded retry metadata, resolved
  provider version and usage. Raw payload is optional and subject to separate
  privacy/retention policy.
- **DecisionCompositionPolicyVersion / StructuredEvaluation**: deterministic
  policy revision; outcome class and explicit reasons; evaluated dimension
  statuses; contradiction/currentness/support separate; unresolved
  requirements; no global confidence field.
- **MissingInformationRequirement**: unresolved decision dimension, reason,
  supporting/contradicting references, temporal/privacy/observability context
  and possible resolvers. AXIGNAL policy determines if it projects to the
  existing Knowledge Frontier.
- **DecisionLedgerEntry** (future): audit references connecting state,
  grammar/questions, evaluator, raw judgments, policy, composed result,
  research, canonical effect, review and later outcome, minimized and retained
  under future policy.
- **LabCase / ExpectedOutcome**: synthetic or independently labeled case;
  decision class, non-customer evidence reference/data fixture, label value,
  label provenance/authority/confidence, tags, privacy class and time context.
  A model output alone cannot establish an independent label.
- **ExperimentDefinition / ExperimentResult**: one controlled variable,
  same-case comparison, sample/holdout, versions, metric scope, output and
  review/outcome; usage/cost/latency nullable where unknown.
- **GrammarCandidate / GrammarPromotionDecision**: proposed diff and rationale,
  experiment/report references, regression and red-team evidence, decision
  authority, resulting lifecycle/version and rollback reference.
- **AdminEvaluationProjection**: minimized operational metadata derived from
  owning evaluation records; not a second decision authority and no private
  text/secrets by default.

Question version, grammar version, state compiler version, evaluator/model
version and policy version evolve independently. A replay is possible only
where exact content is retained and privacy/retention policy permits it.
