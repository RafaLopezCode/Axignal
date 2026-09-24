# Deterministic CI

All **required** merge gates are deterministic and offline. None calls a model or
requires a secret. Nondeterministic semantic extraction never blocks a merge.

## Local validation

```powershell
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run architecture-guard --root .
uv run axignal-governance
```

`uv run axignal-governance` runs: hygiene, terminology, docs, spec, deps,
no-generated-data, architecture and (if the `graphify` binary exists) graphify.

## Required gates

| # | Gate | Command |
| --- | --- | --- |
| 1 | Repository hygiene | `uv run axignal-governance hygiene` |
| 2 | Formatting | `uv run ruff format --check .` |
| 3 | Lint | `uv run ruff check .` |
| 4 | Strict typecheck | `uv run mypy` |
| 5 | Unit tests | `uv run pytest tests/unit` |
| 6 | Contract tests | `uv run pytest tests/contracts` |
| 7 | Architecture tests | `uv run pytest tests/architecture` |
| 8 | Architecture Guard | `uv run architecture-guard --root .` |
| 9 | Spec / constitution consistency | `uv run axignal-governance spec` |
| 10 | Forbidden dependencies | `uv run axignal-governance deps` |
| 11 | Canonical terminology | `uv run axignal-governance terminology` |
| 12 | Secret scanning | `gitleaks detect` (CI: `gitleaks/gitleaks-action`) |
| 13 | Deterministic build | `uv build` |
| 14 | Graphify structural checks | `graphify update <root> --no-cluster`, `graphify diagnose multigraph --json`, `graphify hook install && graphify hook status` |
| 15 | Docs / reference integrity | `uv run axignal-governance docs` |
| 16 | No generated/raw/private data | `uv run axignal-governance no-generated-data` |

## Graphify: blocking vs non-blocking

- **Blocking (deterministic):** structural extraction (`graphify update`
  performs local AST extraction with no LLM and no API key),
  `graphify diagnose multigraph`, and hook presence.
- **Non-blocking (semantic):** LLM-based semantic extraction / community labeling
  (`graphify extract`, `graphify label`). It requires an external model and must
  not gate merges. Run it explicitly and commit nothing heavyweight.

## Runner policy

AXIGNAL uses GitHub-hosted runners initially. No MERXAT, INKDIE or other project
runner labels may be referenced. If a self-hosted runner is introduced it must be
**AXIGNAL-exclusive**.
