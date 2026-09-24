# ADR-0005: FAXT / INXIGHT / PATHX Separation

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §4.5, §4.6, §4.7, §15, §16.2, §16.5, §17, §18, §46.19, §46.20, §46.21, §46.22

## Context

Collapsing evidence-backed facts, derived interpretations, plausible-but-
unobserved relationships and multi-hop paths into one bag of "edges" produces
fake certainty and makes explanations impossible.

## Decision

- `FAXT` is an evidence-backed canonical unit; creation requires evidence
  admission.
- `INXIGHT` is derived, explainable knowledge; it must reference the FAXTs and
  relationships that support it and must degrade when they go stale.
- `PATHX` is an explainable economic path; it must not be collapsed into a single
  direct relationship.
- Observed and Potential relationships are distinct epistemic classes. Observed
  evidence outranks inferred compatibility.

## Consequences

- Potential relationships are never presented as real.
- Explanations can be traced from an INXIGHT down to FAXTs and PATHX edges.
- `UNKNOWN != FALSE` is preserved.

## Enforcement

- `domain/faxt`, `domain/inxight`, `domain/pathx`, `domain/relationships`.
- `tests/contracts/test_observed_vs_potential.py`,
  `test_inxight_not_faxt.py`, `test_faxt_requires_admission.py`.
- Projection packages must not import canonical writers (Architecture Guard).
