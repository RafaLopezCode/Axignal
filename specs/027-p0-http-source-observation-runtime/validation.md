# Validation

**Branch:** `feature/p0-http-source-observation-runtime`
**Base:** `main@a00b1a3`

## Targeted

- Ruff: PASS.
- mypy for new application/pipeline packages: PASS.
- source acquisition + Observation Memory + planner: 32 PASS.
- Real loopback HTTP transport: PASS.
- source sensor → Observation Memory → Brain planner: PASS.

## External smoke

- Target: `https://example.com/`
- Policy: exact host/root HTTPS, 200 KB response cap, 5 s timeout, one redirect.
- Result: `BLOCKED_ENV_DNS` on the Windows workstation (`socket.gaierror 11001`).
- Network dispatch: none; policy gate failed closed before connection.
- No PASS is claimed for external TLS/public acquisition.

## Full deterministic gates

- `uv sync --frozen`: PASS.
- `ruff format --check .`: PASS — 431 files already formatted.
- `ruff check .`: PASS.
- `mypy`: PASS — 90 source files.
- `pytest`: PASS — 397 tests, using an isolated basetemp outside the repository.
- Architecture Guard: PASS — no violations.
- `axignal-governance`: PASS — all gates.
- `git diff --check`: PASS.

## Hostile security review

- Reject scheme/port mismatches (`https:80`, `http:443`) before dispatch.
- Reject layered percent-encoding that could make path authorization ambiguous after downstream decoding.
- Targeted source-acquisition tests after hardening: 19 PASS.
