# Validation record

Run on branch `research/p0-jev-04a-golden-corpus-authority`, based on `31045a233baf26884bed38facff7199ff8abf5ba`, on 2026-09-26. No code or runtime files changed.

| Gate | Result | Notes |
|---|---|---|
| `uv sync --frozen` | PASS | Used a task-specific cache under `%TEMP%` because the default global uv cache returned access denied. |
| `uv run ruff format --check .` | PASS | 250 files already formatted. |
| `uv run ruff check .` | PASS | All checks passed. |
| `uv run mypy` | PASS | 48 source files; no issues. |
| `uv run pytest` | PASS | 154 passed. Pytest used an external permitted `--basetemp` and disabled only its optional cache provider to avoid denied temp/cache locations; the full test set ran. |
| `uv run architecture-guard --root .` | PASS | No violations. |
| `uv run axignal-governance` | FAIL — known local exception | `hygiene` reports `.env` present and `no-generated-data` reports “secret file .env must not be present”. The file was not opened, read, staged, moved, deleted or modified. The other governance checks (`architecture`, `deps`, `docs`, `graphify`, `spec`, `terminology`) passed. |
| `git diff --check` | PASS | Verified after adding only this spec directory to the index; no whitespace errors. |
| `graphify query` / `explain` before | PASS WITH LIMIT | Query found the prior corpus/evidence context; exact question string had no matching node. |
| `graphify update . --no-cluster` | PASS | Documentation graph refreshed. |
| `graphify diagnose multigraph` | PASS WITH WARNINGS REPORTED | 3 self-loop edges; 0 missing/dangling endpoints, 0 exact duplicate edges, 0 unverified code nodes; 134 relation-variant groups (138 directed and 142 undirected collapsed edges); 12 producer suppression sites reported by diagnostic. |
| Corpus candidate JSON parse | PASS | Parsed as JSON. Annotation guide SHA-256 verified against the file bytes. |

The governance exception is reported as a failure, not converted to PASS. No `.env` contents were inspected.
