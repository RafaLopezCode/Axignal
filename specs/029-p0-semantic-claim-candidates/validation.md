# Validation

**Branch:** feature/p0-semantic-claim-candidates
**Base:** main@1ccc2947

## Targeted

- semantic extraction: 9 PASS.
- semantic extraction + repository-boundary tests: 12 PASS.
- Ruff targeted: PASS.
- mypy targeted: PASS.

## Full deterministic gates

- `uv sync --frozen`: PASS.
- `ruff format --check .`: PASS — 450 files.
- `ruff check .`: PASS.
- `mypy`: PASS — 99 source files.
- `pytest`: PASS — 411 tests.
- Architecture Guard: PASS — no violations.
- `axignal-governance`: PASS — all gates.
- `git diff --check`: PASS.

## Hostile boundary review

- Result replay with a foreign `job_id`: rejected.
- Mutated job context that no longer matches the representation/contract: rejected.
- Application layer remains independent of cognition; the CognitiveJob adapter lives in `cognition.jobs`.

## Runtime boundary

No live model call or canonical write is claimed. The provider fixture proves the abstraction boundary only.