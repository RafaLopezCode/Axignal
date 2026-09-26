# Plan: P0-EOI-00 Economic Brain Doctrine

## Objective and boundaries

Converge product semantics, architecture decisions and communication around
MASTER §53, using documentation only. Keep PR #18, provider/corpus evidence and
all runtime files untouched. Do not start P0-EOI-01.

## Workstreams

1. Update the existing MASTER in place, preserving one authority and pin its
   new SHA-256.
2. Record opportunity and compounding decisions in ADR-0012/0013 and the index.
3. Add compact derived Constitution rules and operational AGENTS guardrails.
4. Align the subscriber experience, communication strategy, README, architecture
   summaries and graph-design guidance.
5. Create this Spec Kit record and perform semantic/scope consistency audit.
6. Run deterministic gates, Graphify refresh/diagnostics, audit diff and
   prohibited-call/secret-scope checks.
7. Commit one documentation-only slice, push the authorized branch and open
   one unmerged PR against `main`.

## Affected surfaces

MASTER/hash pin; product doctrine index; README/AGENTS/Constitution; ADR index
and ADR-0012/0013; architecture overview and any genuinely conflicting target
architecture; subscriber experience; communication strategy; AXIGLAND graph
design skill/reference; product slice README; this specification package.

## Rollback

Revert only the new documentation/governance files and corresponding MASTER
hash pin as one reviewed change. Preserve all unrelated local ignored files,
PR #18, experimental branches and historical evidence. Never use reset/clean
or inspect `.env` to roll back.

## Verification

Run `uv sync --frozen`, Ruff format/check, mypy, full pytest, Architecture
Guard, governance, `git diff --check`, Graphify update `--no-cluster` and
`graphify diagnose multigraph`. Record each result. If the known local ignored
`.env` governance finding is the sole failure, report it without reading or
touching `.env`. Do not invoke AXIGNAL runtime or any provider/model.
