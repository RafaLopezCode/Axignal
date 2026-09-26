# AXIGNAL

AXIGNAL is an observing economic brain, not an economic index. It observes,
understands, remembers, connects, compares and reasons over the observable
economy to surface explainable economic activity and potential opportunities
while preserving evidence, uncertainty, provenance and time. It maintains
**AXIGLAND**, one canonical, temporal, governed economic memory that
materializes and deepens on demand. Economic Opportunity Intelligence and
Compounding Economic Intelligence are inseparable product pillars; economic
cartography is their cognitive substrate. Users may **Xignal** any organization
— assigning persistent computational observation — but they direct AXIGNAL's
attention, never its conclusions. AXIGNAL is not a CRM, business social
network, SEO/GEO agency, editable directory, or wrapper around a foundation
model. The full doctrine is the MASTER PRODUCT MODEL.

Economic opportunities are derived and `POTENTIAL` by default: project or
procurement signals do not establish a customer or relationship, and a
capability match does not establish commercial fit. The map is a projection;
it is not the final product.

## Canonical repository and path

- Repository: `https://github.com/RafaLopezCode/Axignal`
- Local development path: `D:\AXIGNAL\Axignal`
- Default branch: `main`

## Governance stack

| Concern | Where |
| --- | --- |
| Product doctrine (semantic authority) | `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` |
| Engineering Constitution | `.specify/memory/constitution.md` |
| ADRs | `docs/adr/` |
| Architecture Guard | `tools/architecture_guard/` |
| Deterministic governance checks | `tools/governance/` |
| Graphify (repo knowledge graph) | `docs/governance/GRAPHIFY.md` |
| Spec Kit (spec-driven lifecycle) | `.specify/`, `.opencode/commands/`, `docs/governance/SPEC_KIT.md` |
| Design intelligence (UI/UX skills) | `.opencode/skills/`, `docs/design/UI_UX_SKILLS.md` |
| Deterministic CI | `.github/workflows/ci.yml`, `docs/governance/DETERMINISTIC_CI.md` |

## Architecture (boundaries)

```
apps/web/        presentation boundary (no features yet)
domain/          canonical economic world (innermost layer)
pipeline/        discovery, normalization, entity resolution, evidence, features
cognition/       jobs, router, providers, batch
tools/           governance enforcement
tests/           architecture, contracts, unit
```

Dependency direction and invariants: `docs/architecture/OVERVIEW.md`.

## Development lifecycle

1. Read the MASTER, the constitution and relevant ADRs.
2. Non-trivial features go through Spec Kit (`/speckit.specify` → `clarify` →
   `plan` → architecture review → `tasks` → `implement` → `converge`).
3. Keep changes inside the declared boundaries.
4. Run deterministic validation before proposing a merge.

## Deterministic validation

```powershell
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run architecture-guard --root .
uv run axignal-governance
```

All required gates are deterministic; none requires a model or a secret.

## Where things live

- **MASTER:** `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`
  (hash-pinned in the sibling `.sha256` file; verified in CI).
- **ADRs:** `docs/adr/`.
- **Graphify refresh:** `graphify update . --no-cluster` (structural,
  offline), then `graphify diagnose multigraph`; hooks via
  `pwsh -File scripts/install-graphify-hooks.ps1`. Semantic label/extract is
  optional and non-blocking.

## What constitutes ENGINEERING_READY

- MASTER is canonical, present and hash-verified.
- Graphify, Spec Kit, Architecture Guard and deterministic CI are installed and
  configured.
- Architecture contracts are enforceable and pass.
- All deterministic gates pass locally and in remote CI.
- No unresolved doctrine conflict.

## Non-negotiables

No product features are implemented during the governance bootstrap
(constitution P0). No deployment. No touching other projects. The map cannot be
bought; observation can. `UNKNOWN` is never `FALSE`. Observed is never inferred.
Users choose where AXIGNAL looks; AXIGNAL independently decides what the evidence
supports.
