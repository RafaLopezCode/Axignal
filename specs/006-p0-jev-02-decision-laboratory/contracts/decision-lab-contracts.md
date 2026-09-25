# Decision Laboratory Contracts

## Evaluator

`StructuredEvaluator.evaluate(state, questions, requested_model) -> EvaluationResponse | EvaluationFailure`

The evaluator has no AXIGNAL production, data-store, authorization, routing, or canonical-write handles. Failures use safe categories; exception messages and response bodies are not persisted.

## Judgment normalization

- `ChoiceJudgment`: `selected`, `probabilities`, nullable `confidence`.
- `ScoreJudgment`: numeric `score`, `probabilities` by level, nullable `confidence`, and returned rubric/legend if present.
- `NoulJudgment`: `probability_yes` in `[0, 1]`; no separate confidence.
- `Usage`: nullable nonnegative input/output token counts.
- `EvaluatorMetadata`: source mode, requested/resolved model, SDK/adapter version, and nullable request/latency metadata.

Reject non-finite numbers, out-of-range values, invalid probability mass, unknown answer types, and missing required fields. Never synthesize a missing answer or probability.

## Experiment budget

Before the first provider call, validate fixed maxima for request count, question count, UTF-8 request-body bytes, and cost ceiling. Use the dated official input-token price and request-body byte count as a conservative preflight bound; actual provider token usage is still recorded as reported. No retries or parallel client requests in V0.1. Stop before any request that would exceed one declared maximum.

## Composition

Pure deterministic `compose(raw_judgments, deterministic_features, policy_version)` returns an experimental outcome/reasons and risk tags. Missing remains missing, unknown remains unknown, and provider failure remains operational. Composer has no canonical admission dependency.

## Result artifacts

Every result has a unique result ID and manifest. Create-only file semantics prevent overwrite. Replay/comparison inputs identify their source result IDs and never perform a provider call. Every report declares sample size, applicable/excluded/missing cases, metric applicability, limitations, and `SUPPORTED`, `NOT_SUPPORTED`, or `INCONCLUSIVE` only when an observation supports that judgment.
