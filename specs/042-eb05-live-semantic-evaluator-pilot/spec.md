# EB-05 — Live Semantic Evaluator Pilot

**Status:** IMPLEMENTATION SLICE / LIVE EXECUTION GATED
**Authority:** MASTER → Constitution → ADR-0011/0047/0048 → Economic Brain Execution Roadmap
**Roadmap slice:** EB-05

## Purpose

Extend the existing Decision Lab vNext/FR-22 runner with reproducible multi-axis
measurement mechanics while preserving its governed inputs, answerability and
provider-neutral boundaries. This spec does not authorize live calls.

## Authorized implementation

- Keep the vNext compiler, DecisionContracts, Choice/Noul/Score semantics,
  deterministic baseline and immutable FR-22 result contract.
- Provide fixture-only single and batch comparison mechanics over identical
  compiled, answerable inputs. Provider-visible records contain state and
  contract identity only; labels, severity tags and expected outcomes stay
  evaluator-only.
- Record exact request identity, per-dimension coverage/risk, abstention,
  severe errors, schema failures, latency, usage and explicit unknown cost.
- Preserve failure/degradation records without exception bodies or implicit
  batch-to-single fallback. Offline replay remains separate from execution.
- Expose current live eligibility: TypeSafe Jev is BLOCKED by
  `P0_JEV_04A_BLOCKED_NO_VALID_CORPUS`; Luna and OpenAI Decisions remain
  UNAVAILABLE until governed adapters and authorized bindings exist.
- Correct malformed distribution validation in the existing experimental
  normalizer; invalid, non-finite, boolean or non-normalized distributions fail
  closed.

## Invariants

- Choice, Noul and Score retain primitive-specific meaning; no universal score.
- ANSWERABILITY precedes judgment; UNKNOWN is never FALSE.
- OBSERVED is never POTENTIAL; CLAIM is never WRITE.
- Replay identity binds exact compiled inputs, evaluator version and execution
  mode. Measured latency is result evidence, not part of request identity.
- Missing usage/cost remains UNKNOWN; no provider result gains canonical write
  authority.
- Synthetic fixtures prove harness mechanics only, not provider quality.

## Exit criteria for this authorized slice

- Offline tests prove same-input single/batch comparison, label isolation,
  answerability filtering, per-dimension measurements, failure preservation,
  replay identity and malformed-distribution rejection.
- A reproducible preflight artifact retains current provider eligibility and
  does not simulate blocked/unavailable providers.
- Live quality/cost evidence and provider selection remain blocked until ADR-0048
  corpus/use gates and applicable provider authorization are resolved.
