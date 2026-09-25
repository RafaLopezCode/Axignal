# P0-JEV-03 Pilot Run Contract

## `smoke`

- Accepts no user-provided case, question, state, model, or retry parameters.
- Validates the exact existing corpus and grammar locks.
- Selects `CES-01-clear-positive`, `CES.SUPPORT.v1` version `v1`, primitive `CHOICE`, state variant `minimal@0.1.0`, and model `jev-1.13.0`.
- Enforces 1 request, 1 question, concurrency 1, retries 0, and current request-byte budget.
- Uses existing `TypeSafeLabEvaluator` and `normalize_judgment`.
- Writes one create-only safe JSON artifact at `docs/research/p0-jev-03/smoke-result.json`.
- A second attempt cannot overwrite the artifact. No retry option exists.

## Smoke gate

Only a passing authenticated response with compatible typed structure, safe serialization, model selection, correctly preserved probability/confidence/usage semantics, measured latency, replayable judgment, and no authority-boundary crossing permits phase `experiment`. Missing provider metadata is `UNKNOWN`; an unsafe or malformed answer fails. Failure or incompatibility halts this pilot without retry.

## `experiment`

- Accepts no sample, wording, model, policy, budget, threshold, or state override.
- Requires an existing passing smoke gate artifact and validates its digest.
- Runs the exact existing `claim-wording-ab@0.1.0` definition, five cases, two variants, one repetition, 10 requests maximum, 10 questions, concurrency 1, retries 0.
- Writes only the create-only result artifact. Any failure is retained; no case is silently removed.
- Does not run other experiments or promote any result.

## Replay

- Reads only safe local result artifacts.
- Makes no credential lookup and no network call.
- Verifies source digest and recomputes supported deterministic composition, metrics, and formal outcome.
- Writes a separate create-only replay artifact.
