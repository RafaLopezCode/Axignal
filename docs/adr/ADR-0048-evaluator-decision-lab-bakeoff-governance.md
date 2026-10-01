# ADR-0048 — Evaluator Decision Lab Bakeoff Governance

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14–16, 19, 35, 53; ADR-0011, ADR-0024, ADR-0045, ADR-0047.

## Context

FR-21 established a provider-neutral evaluator contract but did not provide AXIGNAL-specific comparative evidence. FR-22 requires a controlled bakeoff over the same versioned inputs/contracts while respecting provider access, rights, sealed labels, cost truth and the P0-JEV-04A authority gate.

Open PR #18 remains the governing Jev corpus authority record and explicitly concludes `BLOCKED_NO_VALID_CORPUS`; it also prohibits provider calls for that benchmark until rights/use and corpus gates are resolved. No lower-level task may bypass that restriction.

## Decision

AXIGNAL adopts `experiments/decision_lab/bakeoff_vnext.py` as the governed FR-22 comparison runner.

### Same-input contract

The runner compiles the existing vNext synthetic corpus through the existing Decision Lab compiler. Every candidate is bound to one immutable input manifest containing:

- case id/family;
- DecisionContract id;
- state-contract version;
- compiler version;
- compiled-state fingerprint;
- answerability status.

All candidate rows carry the same manifest SHA-256.

Provider-visible state excludes expected outcomes, label provenance and evaluator-only notes.

### Candidate execution states

A candidate is one of:

- EXECUTED;
- BLOCKED;
- UNAVAILABLE.

BLOCKED/UNAVAILABLE candidates are preserved in the result artifact rather than simulated.

For the 2026-10-01 FR-22 run:

- deterministic baseline: EXECUTED;
- Luna structured: UNAVAILABLE — no governed API adapter/authorized model binding in the repository;
- OpenAI Decisions: UNAVAILABLE — access/API terms not established in the governed repository evidence;
- TypeSafe Jev: BLOCKED — P0-JEV-04A `BLOCKED_NO_VALID_CORPUS` from open PR #18.

These statuses are dated experimental evidence, not permanent claims about vendor capability.

### Deterministic baseline

The deterministic baseline may only use existing deterministic AXIGNAL rules. It cannot read expected labels.

On the current 14-case synthetic corpus, 11 cases are answerable but none contains the verified identifier evidence required by the currently implemented deterministic entity rule. Therefore the baseline answers 0 and abstains on all 11 answerable cases.

Coverage 0 is retained as evidence; no heuristic is invented to improve apparent performance.

### Measurement

Each candidate result exposes the FR-22 measurement families:

- class errors / classification when scoreable;
- false OBSERVED/POTENTIAL status;
- coverage and abstention;
- calibration only when semantically valid distributions exist;
- schema failures;
- latency;
- retries;
- cost knowledge and amount;
- language/context sensitivity;
- disagreement/error correlation.

When a metric cannot be measured from the executed evidence, the artifact records NOT_MEASURED / NOT_AVAILABLE / UNKNOWN with an explicit reason. Missing measurement is never coerced to zero.

False OBSERVED/POTENTIAL is not computed in this lab because FR-22 does not perform an OBSERVED/POTENTIAL projection. That absence is explicit.

Language/context sensitivity is not computed because the frozen corpus has no governed paired variants. Disagreement/error correlation is unavailable because fewer than two provider evaluators executed.

### Cost truth

Unknown provider cost remains `UNKNOWN` with no amount/currency. The local deterministic baseline is `NOT_APPLICABLE` for marginal provider monetary cost, not a claim of zero total compute cost.

COST_UNKNOWN != ZERO

### Calibration

Calibration is calculated only when a real provider distribution with valid semantics is present under ADR-0047. A selected choice alone never becomes a one-hot distribution for calibration.

### Result artifact

The governed run is stored as:

`experiments/decision_lab/artifacts/fr22-evaluator-bakeoff-v1.json`

It is a standard `decision-lab-result` with an immutable result digest and can be verified by the existing Decision Lab artifact reader.

Result id:

`c94e07b04f7733476b09b382a5bfe961a833ac5f7c9b7d2954bc1e6dd79f78ad`

### No winner

No vendor winner is declared. There is insufficient comparable executed provider evidence, and the synthetic vNext corpus is structural evidence rather than statistical or real-world quality evidence.

Vendor marketing is not substituted for missing runs.

## Invariants

SAME_INPUTS => SAME_COMPILED_MANIFEST

SEALED_LABELS != PROVIDER_INPUT

BLOCKED_PROVIDER != SIMULATED_PROVIDER

UNAVAILABLE_PROVIDER != FAILED_PROVIDER

COST_UNKNOWN != ZERO

MISSING_METRIC != ZERO

CALIBRATION => VALID_PROVIDER_DISTRIBUTION_SEMANTICS

FAILED_OR_BLOCKED_RUN != DROPPED_RUN

NO_COMPARABLE_PROVIDER_EVIDENCE => NO_VENDOR_WINNER

EXPERIMENT_RESULT != POLICY_PROMOTION

EXPERIMENT_RESULT != CANONICAL_TRUTH

## Consequences

Future audits can reference an AXIGNAL-specific immutable result artifact that proves the exact current comparison boundary instead of relying on vendor claims. When provider authorization/access becomes valid, the same manifest and runner can accept real candidate records without changing the measurement semantics.

## Non-goals

This ADR does not unblock P0-JEV-04A, create a natural golden corpus, authorize any provider call, rank vendors, promote policy, alter EvidenceAdmission or write AXIGLAND.
