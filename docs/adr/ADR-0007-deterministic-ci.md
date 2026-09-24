# ADR-0007: Deterministic CI

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §13, §14, §30, §46.28, §46.30; Engineering Constitution "Deterministic Validation Gates"

## Context

If required merge gates depend on nondeterministic model output, CI becomes
flaky, unreviewable and easy to weaken. The governance stack must make the wrong
AXIGNAL difficult to build, not merely detected sometimes.

## Decision

All required merge gates are deterministic and offline: repository hygiene,
formatting, lint, strict typecheck, unit tests, architecture tests, Architecture
Guard, spec/constitution consistency, forbidden dependencies, canonical
terminology, secret scanning, deterministic build, Graphify structural checks,
docs/reference integrity and no-generated-data. Semantic LLM-based Graphify
extraction is separate and non-blocking.

## Consequences

- Merge gates are reproducible and fail closed.
- No secret or API key is required for required gates.
- Semantic refresh cannot block a merge.

## Enforcement

- `.github/workflows/ci.yml`.
- `tools/governance/checks.py` and `tools/architecture_guard/guard.py`.
- `docs/governance/DETERMINISTIC_CI.md`.
