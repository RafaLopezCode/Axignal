# P0-JEV-01 Architecture Quickstart

This is a review guide for a **proposed architecture**, not an executable Jev
integration. Do not add `typesafe-sdk`, set a key, or run a live API call as
part of this slice.

## Reading path

1. Read [the proposed architecture](../../docs/architecture/AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md).
2. Check official semantic and API evidence in
   [TypeSafe research](../../docs/research/AXIGNAL_P0_JEV_01_TYPESAFE_RESEARCH.md).
3. Review AXIGNAL owners/conflicts in
   [the opportunity map](../../docs/research/AXIGNAL_P0_JEV_01_OPPORTUNITY_MAP.md).
4. Review conceptual contracts and the 38 synthetic adversarial cases in
   [decision contracts](contracts/decision-contracts.md).

## Future experiment record outline

Before a later authorized experiment, record the case corpus and label
provenance, a single intended comparison variable, decision class, baseline
and candidate grammar/state/evaluator/policy versions, raw typed outputs,
composition, review/outcome, token usage/cost/latency only where returned, and
all failures. Use only data approved for the experiment. Keep `jev-called`,
recorded response, mock, generative-model simulation, and synthetic expectation
as visibly different experiment modes. No simulation may invent Jev outputs or
probabilities.

## Current verification status

The 38 catalogue rows are scenario expectations for future deterministic
contract tests; they are not executed fixtures or model results. Required CI
must remain offline and keyless. Production runtime, live validation,
calibration, and canonical write integration remain absent.
