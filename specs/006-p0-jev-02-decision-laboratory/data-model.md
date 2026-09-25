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

Definition fixes hypothesis, family, cases/split, grammar/state/policy variants, repetitions, measures, model, declared budgets, stop conditions, experiment type, independent variable, controlled dimensions, and predeclared evaluation criteria. The validator enforces the declared single-variable comparison. Result identity is content-digested and create-only; its reproducibility manifest records the git revision, definition version/digest, corpus and grammar versions, exact question versions, compiler and state variant versions/fingerprints, policy and evaluator/SDK versions, requested/resolved model, case IDs, repetitions, and execution mode. Results retain normalized raw judgments, failures, compositions, class-scoped metrics, usage/cost/latency where known, and a live/recorded/fixture evidence label. Criteria snapshots and their digest are immutable with the completed result.

Preflight request bytes are measured independently of token usage. Preflight tokens and monetary cost are `UNKNOWN`. Provider-reported input-token usage may be estimated under an explicit versioned pricing-policy record; invoice cost remains `UNKNOWN` without billing evidence.

Outcome criteria are declared before execution. The deterministic evaluator emits `SUPPORTED` or `NOT_SUPPORTED` only when a justified predeclared minimum effect and sufficient valid evidence exist. Operational failure, critical regression, incompatible semantics, insufficient cases, or absent effect threshold produce `INCONCLUSIVE` with reasons.

The relationship atomic strategy has a versioned deterministic experimental composer for REL.PRESENCE, REL.TYPE, REL.TIME, and REL.CONTRADICTION. It retains each raw judgment, preserves contradictory/unresolved state, and has no canonical admission authority.

## Label and privacy rules

Only deliberately constructed synthetic properties are deterministic ground truth. Ambiguous, contradictory, and no-answer-by-design cases use their explicit label status rather than an invented class. Prior model output is never a label. All V0.1 records use `SYNTHETIC_PUBLIC`; no live/private user data is accepted into the corpus loader.
