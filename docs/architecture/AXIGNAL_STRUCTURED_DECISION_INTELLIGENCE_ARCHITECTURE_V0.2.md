# AXIGNAL Structured Decision Intelligence Architecture V0.2

**Status:** Accepted experimental architecture; deterministic reference controls implemented.
**Production implementation:** None. No provider runtime, call path, dependency, migration or behavior change is authorized.
**Supersedes for future design:** V0.1 only where this document explicitly amends it; V0.1 historical evidence is retained.

## Purpose and scope

This version prevents syntactically valid but semantically insufficient state from being treated as a valid decision request. It defines AXIGNAL-owned contracts around replaceable structured evaluators. The current implementation under `experiments/decision_lab/` validates contracts and synthetic fixtures offline; it does not call a provider.

The relationship to canonical authority remains:

```text
AXIGLAND / admitted evidence projection
  → AXIGNAL decision intent and DecisionContract
  → information requirements and family StateContract
  → deterministic assembly, normalization, validation, serialization, fingerprint
  → pre-provider AnswerabilityGate
  → primitive and answer-space validation
  → (separately authorized) replaceable structured evaluator
  → raw typed judgment
  → deterministic versioned composition
  → AXIGNAL policy
  → independent evidence admission / canonical authority
```

Each arrow is an ownership boundary. Answerability is not truth or expected quality. A model judgment is not a FAXT, INXIGHT, PATHX, canonical admission, research plan or action.

## Decision and state contracts

A versioned `DecisionContract` identifies family, semantic target, question ID/version, primitive, answer space, information requirements, state-contract version, uncertainty meaning, composition policy, authority boundary and evaluation status. The contract is AXIGNAL-owned and provider-neutral.

V-next declares distinct contracts for:

- `CLAIM_EVIDENCE_SUPPORT`: explicit claim proposition, one or more actual evidence passages, provenance, and a temporal reference when currentness is in scope.
- `ENTITY_ALIGNMENT`: two distinct named entity records, discriminating identity attributes, semantic evidence and provenance. Deterministic exact-ID comparisons precede model evaluation.
- `ECONOMIC_RELATIONSHIP`: two endpoints, explicit relationship proposition and direction, semantic evidence and provenance, plus time context when required.

Requirements are explicit and check declared information shape: presence, non-empty content, cardinality, pairwise arguments, provenance, direction and conditional time reference. They do not claim to understand whether evidence supports the question.

## State compilation

V-next keeps five named stages: (1) assemble referenced source content, (2) normalize/copy JSON-safe state without filling defaults, (3) validate the family state contract, (4) canonical serialize, (5) fingerprint serialized bytes. Missing records produce `UNRESOLVED_REFERENCE`; IDs are not substituted for content. `ABSENT`, `EMPTY`, `UNKNOWN`, `UNAVAILABLE`, `NOT_APPLICABLE` and `PRESENT` are distinct states where represented.

Legacy `decision-state.v0.1` remains a historical compiler/replay contract. V-next does not rewrite old request bytes or fingerprints.
The V0.1 live lab path is now replay-only: its questions have no registered V-next DecisionContract and are rejected before credential lookup/provider construction. Historical result replay remains available under V0.1 semantics.

## Answerability and primitive validation

The deterministic AXIGNAL `AnswerabilityGate` returns `ANSWERABLE` or `NOT_ANSWERABLE` with stable reason codes. It proves only minimum declared information sufficiency. A failed gate prevents provider eligibility and prevents model-quality interpretation for that case. The gate does not fetch evidence, infer truth, call Jev or plan research.
The existing experimental TypeSafe adapter independently checks that each question has a registered V-next `DecisionContract`, matches its primitive and passes answerability before importing/calling the SDK. The generic V0.1 CLI and P0-JEV-03 one-off smoke/experiment entrypoints are replay-only; replay remains unchanged.

Choice contracts require distinct options with defined meanings, declared mutual exclusivity and a declared coverage strategy. Score requires a domain-specific ordered rubric. Noul requires an explicit proposition and present arguments; its probability remains Noul uncertainty. No generic confidence conversion or global threshold is allowed.

## Judgment, composition and authority

The experimental V-next composer retains raw value, primitive, distribution/probability, optional provider confidence, model/evaluator identifiers and usage as reported. The derived decision result is separate and identifies a versioned composition policy. Missing raw metadata stays unknown. Neither raw nor derived results have canonical authority.

## Decision Laboratory

Each case record must bind golden target and provenance, contract/question/state/compiler versions, answerability verdict/reasons, primitive, pinned model metadata, raw judgment when one exists, composition policy/result, metrics and failure attribution. Only answerable single-target cases enter model-quality metrics. An experiment testing state sufficiency must predeclare that variable and report answerability outcomes separately from quality.

V-next synthetic corpus tests structural cases only. It is not an independently adjudicated real-world quality dataset and supports no statistical validation claim. Existing 42-case V0.1 corpus and P0-JEV-03 artifacts remain unchanged.

## Failure classes and experiment readiness

Failure attribution distinguishes input/state, missing information, question, primitive/options, judgment, composition/policy, SDK/service/network/authentication, model drift, calibration, evaluation design and label errors. Each attribution identifies its basis: deterministic, human-adjudicated, experimentally inferred or unknown. Detection is not presumed.

The offline Experiment Validity Gate fails closed on any missing contract, fixture, provenance, control, model/SDK, budget/retry, policy, evaluation, held-out, authority or secret boundary. Passing is eligibility only; separate CTO authorization is always required. Current preregistration is `LIVE_EXPERIMENT_ELIGIBLE=NO` because the fixture corpus lacks independent golden provenance; `LIVE_EXPERIMENT_AUTHORIZED=NO`.

## Security and operations

External passages are untrusted data, not instructions. No content triggers tool calls, URLs, research or policy changes. The experimental modules have no provider, AXIGLAND-writer, evidence-admission or canonical-writer import. No keys or network are needed for deterministic validation. Costs/usage not supplied by the provider remain unknown; a dated public estimate is not invoice evidence.

## Versioning and rollback

V0.1 is historical. V-next grammar, family state contracts, composer policy, corpus, and experiment definition are separately versioned. Any held-out reassignment or question/state change creates a new version and preregistration. Rollback removes V-next experimental modules/docs without touching P0-JEV-03 records or V0.1 artifacts.
