# P0-CORE-05 Validation Record

This record must contain only commands actually executed for the final branch
HEAD. A green test suite does not establish additional subject ontology or
HFX-01 readiness.

| Check | Command / evidence | Result |
|---|---|---|
| Focused subject and identity contracts | 67 tests: organization/Xeed boundary, authorized FAXT membership, subject unknown preservation, and Observed/Potential separation | PASS |
| Frozen dependencies | `uv sync --frozen` | PASS — 14 packages checked |
| Ruff format | `uv run ruff format --check .` | PASS — 319 files already formatted |
| Ruff lint | `uv run ruff check .` | PASS |
| Mypy | `uv run mypy` | PASS — 61 source files |
| Full test suite | `uv run pytest --basetemp <unique temp directory> -p no:cacheprovider` | PASS — 252 passed; default pytest temp root was inaccessible, so an isolated authorized temp root was used |
| Architecture guard | `uv run architecture-guard --root .` | PASS — no violations |
| Governance | `uv run axignal-governance` | PASS — architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology |
| Graphify | FAXT query/explain/affected; `graphify update . --no-cluster`; `graphify check-update .`; `graphify diagnose multigraph --json` | PASS — update/check/diagnostics exited 0; diagnostics report 6 dangling edges and 3 self-loops in the derived graph; Graphify remains non-authoritative |
| Deterministic build | `uv build --out-dir <unique temp directory>` | PASS — sdist and wheel built; build dependency resolution required approved network access |
| Golden Master manifest | `tools/governance/golden_master_manifest.py --verify` against external V1 root | PASS — 27 files; `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51` |
| Secret safety | Local Gitleaks executable unavailable; governance hygiene passed. Exact-head remote secret scan remains required. | PENDING remote proof |
| Scope audit | `git diff --check`; changed files are limited to the CORE-05 spec/plan/tasks/validation and one evidence-only HFX matrix clarification; manifest V1 unchanged | PASS |
| Adversarial self-audit | A01=NO; A02=NO; A03=NO; A04=NO; A05=NO; A06=NO; A07=NO; A08=NO; A09=NO; A10=NO; A11=NO; A12=NO; A13=NO; A14=NO; A15=NO; A16=NO; A17=NO; A18=NO; A19=NO; A20=NO; A21=NO; A22=NO | PASS |
