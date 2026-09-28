# P0-HFX-00 Validation Record

This record is completed with command evidence after local validation. A pass
here establishes deterministic repository/source checks only; it does not
establish human visual acceptance or production persistence.

| Check | Required evidence | Result |
|---|---|---|
| Manifest repeatability | Two consecutive verify runs returned the same v1 aggregate | PASS — `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51` |
| Stable ordering | Unit test reverses configured inventory and compares result | PASS |
| Source byte sensitivity | Temporary-tree source and CRLF/LF mutations change aggregate | PASS |
| Generated-output exclusion | Temporary `dist/` and `node_modules/` files do not change aggregate | PASS |
| Missing-input failure | Temporary required-path omission fails closed | PASS |
| Unexpected-source behavior | Unlisted file under `src/v2/` fails closed | PASS |
| Golden Master untouched | Repeated external manifest verification returned the baseline digest | PASS |
| Projection specification | Matrix records all requested data and authority/unknown behavior; no projection code | PASS — reviewable contract only |
| Canonical local gates | `uv sync --frozen`, Ruff format/check, mypy, full pytest, Architecture Guard, governance | PASS — pytest 241 passed |
| Deterministic build | `uv build` | PASS — source distribution and wheel built; local artifacts removed |
| Graphify | AST update, multigraph diagnostics and hook status; no semantic model extraction | PASS — update/diagnostics exit 0; graph reports 6 dangling and 3 self-loop edges |
| Design System contracts | No frontend implementation changed; design/governance docs were checked | NOT_APPLICABLE — no frontend runtime contract tests exist in this repository |
| Local secret scan | `gitleaks` executable availability | NOT_AVAILABLE — executable is not installed; exact-head remote CI remains required |
| Human visual QA | Exact before/after comparison not established by machine inspection | REQUIRED |
