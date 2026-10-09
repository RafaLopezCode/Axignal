# Validation ledger

Base verified against GitHub canonical main: `987ca9168fcad9a8aa12d43f6ec1386d0ca2abab`.
The canonical dirty checkout was left untouched; tests ran in the issue176 worktree.

| Check | Observed result |
| --- | --- |
| Baseline economic revocation regression | FAIL on the verified base: subscriber retained the persisted capability excerpt and whyPotential copy after rights removal. |
| Final targeted E2E and existing rights/minimization tests | 28 passed; the new issue176 module contains 15 cases including actual HTTP socket and OAuth/MCP. |
| Joint First Observation/economic/continuity/MCP regression | 139 passed. |
| Final full deterministic Python suite | 2038 passed, 6 skipped (5 POSIX-only on Windows; optional typesafe_sdk import). |
| Frontend typecheck | PASS; no frontend source changes. |
| Frontend tests | 162 passed. |
| i18n | 1539 entries, no missing locale entries. |
| Frontend build | PASS; 576 routes, including unchanged account/connect. |
| Actual before/after HTTP DTOs vs unchanged frontend schema | Both accepted. |
| Python deterministic package build | PASS: sdist and wheel. |
| Ruff format/check | PASS. |
| mypy | PASS, 475 source files. |
| Architecture Guard | PASS, no suppressions added. |
| All governance checks | PASS. |
| Graphify AST update/check-update/diagnose | PASS; offline extraction, no LLM or graph mutation to fix a gate. |

Reproduce the backend gates with `uv sync --frozen`, `uv run ruff format --check .`,
`uv run ruff check .`, `uv run mypy`, `uv run pytest`,
`uv run architecture-guard --root .`, `uv run axignal-governance` and `uv build`.
On this Windows host pytest used its isolated `--basetemp` under
`D:\AXIGNAL\issue176-tests`; it did not change collection or assertions.

Final hardening covers canonical-name/content separation, internal POU read
withdrawal, original-bound legacy refusal and physical raw retirement under a
wider grant. The final SHA and remote CI status/run links belong to the PR
metadata and CTO delivery; no self-referential commit SHA is recorded here.

All new observation sources and evaluator inputs are explicitly synthetic. Real
HTTP, auth/admission, persistence, AXENT and OAuth/MCP consumers execute. No live
Google login, real source/provider-quality evaluation, browser redesign audit or
production activation is claimed. No frontend or Claude-owned semantic files changed.
