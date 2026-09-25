# Decision Laboratory Data Model V0.1

All models are experimental records. None is canonical AXIGNAL domain truth.

## GoldenCase

- `case_id`, `case_version`, `decision_family`
- Synthetic `evidence`, structured `source_state`, and `candidate`
- `expected_outcome` or null when no single answer is justified
- `label_status`: `DETERMINISTIC_GROUND_TRUTH`, `AMBIGUOUS_BY_DESIGN`, `CONTRADICTORY_BY_DESIGN`, `NO_EXPECTED_SINGLE_ANSWER`
- `label_authority`, `label_provenance`, `temporal_context`, `edge_case_tags`, `privacy_class`, `notes`

## DecisionQuestion and Grammar

Question identity is `(question_id, question_version)`; grammar has its own version. Each entry stores family, primitive, complete instructions and criteria, required state-contract/compiler versions, relevant state paths, semantic meaning, exclusions, interpretation, and experimental status. A changed definition must use a new version.

## StructuredDecisionState

`decision_family`, `state_contract_version`, `state_compiler_version`, typed minimal `payload`, deterministic canonical JSON, and SHA-256 `state_fingerprint`. Fingerprint input includes semantic state only and excludes key material, time-of-run, request IDs, and evaluator metadata.

## RawStructuredJudgment

- Choice: selected label, complete returned probability map, confidence only if returned.
- Score: score, rubric/level probabilities, confidence only if returned.
- Noul: returned probability of yes.
- All variants may reference question/version, requested/resolved model, adapter/SDK identity, usage, latency, and result source (`live`, `recorded`, or `fixture`). Absent provider metadata stays null/unknown.

## ExperimentDefinition / ExperimentResult

Definition fixes hypothesis, family, cases/split, grammar/state/policy variants, repetitions, measures, model, declared budgets, and stop conditions. Result contains immutable identity, git/corpus/grammar/compiler/policy/evaluator versions, state fingerprints, normalized judgments, failures, compositions, class-scoped metrics, usage/cost/latency where known, and a live/recorded/fixture evidence label.

## Label and privacy rules

Only deliberately constructed synthetic properties are deterministic ground truth. Ambiguous, contradictory, and no-answer-by-design cases use their explicit label status rather than an invented class. Prior model output is never a label. All V0.1 records use `SYNTHETIC_PUBLIC`; no live/private user data is accepted into the corpus loader.
