# P0-JEV-03 Operator Quickstart

This is a live experiment. Run locally only after offline validation. Never run it in CI.

## Preflight

1. Confirm branch base is `551ba1a2e78d2768089b45a9e764403174a14755` and `.env` is ignored and untracked.
2. Confirm only the boolean `TYPESAFE_API_KEY_PRESENT=YES`; do not display the value.
3. Sync the frozen optional lab group and verify installed `typesafe-sdk==0.7.1`.
4. Run the offline Decision Laboratory validation and pilot contract tests.
5. Review the computed smoke budget (one request, one question, one concurrency, zero retries; preflight token count and monetary cost are `UNKNOWN`).

## Smoke gate

Invoke the explicit smoke phase once. It writes `docs/research/p0-jev-03/smoke-result.json` with create-only semantics. Inspect its safe contents and verify every smoke gate before invoking the experiment phase. Any failure or ambiguity ends the run; do not retry.

## Controlled run and replay

Only after smoke passes, invoke the experiment phase once. It is fixed to `claim-wording-ab@0.1.0`; it executes all five cases and both variants. Then replay the recorded result offline, verify digest and derived values, and complete `empirical-report.md`. No live command belongs in CI.
