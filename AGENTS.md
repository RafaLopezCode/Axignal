# AGENTS.md — AXIGNAL

Repository-level instructions for coding agents. Follow them unless a human
explicitly overrides them, and even then respect doctrine (below).

## Canonical facts

- Repository: `https://github.com/RafaLopezCode/Axignal`
- Local path: `D:\AXIGNAL\Axignal`
- Default branch: `main`
- Package manager: `uv` (Python 3.11+). No runtime dependencies yet.

## Read before you change anything

1. **Product-semantic changes:** read the MASTER FIRST:
   `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`.
2. **Engineering rules:** read `.specify/memory/constitution.md`.
3. **Decisions already made:** read the relevant ADRs in `docs/adr/`.
4. **Architecture:** read `docs/architecture/OVERVIEW.md` and
   `docs/architecture/TERMINOLOGY.md`.

Precedence is strict and fails closed:

```
MASTER PRODUCT MODEL
        ↓
ENGINEERING CONSTITUTION
        ↓
FEATURE SPEC
        ↓
PLAN
        ↓
TASKS
        ↓
IMPLEMENTATION
```

## Workflow

- Non-trivial features: use Spec Kit (`/speckit.specify` → `/speckit.clarify` →
  `/speckit.plan` → architecture review → `/speckit.tasks` → `/speckit.implement`
  → `/speckit.converge`). See `docs/governance/SPEC_KIT.md`.
- Before architectural changes: inspect Graphify
  (`graphify query`, `explain`, `affected`, `path`). See
  `docs/governance/GRAPHIFY.md`.
- After changes: run the deterministic gates (below) before proposing a merge.

## Hard rules

- **Architecture Guard is blocking.** `uv run architecture-guard --root .` must
  pass. Do not add suppressions to make it pass.
- **Never weaken a gate merely to get CI green.** Fix the code, not the gate.
- **Never convert UNKNOWN into FALSE.** Use `None`/`UNKNOWN`; never default.
- **Never promote inference to observation.** Observed requires evidence
  admission.
- **Never let user, agency or subscriber input directly mutate canonical truth.**
  Input directs attention only.
- **Never hard-wire AXIGNAL to one model provider.** Use
  `cognition/router` + `CognitiveProvider`; concrete SDKs only under
  `cognition/providers/`.
- **Never introduce CRM/workflow/sponsored functionality** without an explicit
  CTO change to the MASTER first.
- **Never add an `Edit company profile` capability.** Reevaluation, not editing.
- **Never rename canonical terms** (AXIGNAL, AXIGLAND, AXENT, XIGNAL, FAXT,
  INXIGHT, PATHX).
- **Do not touch other projects** (MERXAT, INKDIE, etc.), their runners or
  services. AXIGNAL governance is isolated.
- **Do not deploy production** from this repository without explicit
  authorization.

## Design intelligence (UI/UX)

AXIGNAL has two project-local design skills under `.opencode/skills/`:
`frontend-design` (visual direction) and `ui-ux-pro-max` (UX, IA, interaction,
accessibility, data-density). See `docs/design/UI_UX_SKILLS.md` and
`docs/design/SKILLS.lock.json` for pinned upstream revisions and update steps.

- They are **design intelligence, not product authorities**. Precedence:
  `MASTER → Constitution → ADRs/contracts → Feature spec → Design brief →
  UI/UX skills → implementation`. If a skill conflicts with the MASTER, the
  MASTER wins; if it conflicts with an architectural invariant, the architecture
  wins.
- Do not let design output invent product semantics, alter epistemic meaning, or
  add sponsored/ranking behaviour.
- Design constraints: `docs/design/DESIGN_DOCTRINE.md` and
  `docs/design/DESIGN_GOVERNANCE.md`.
- The graph architecture is accepted in ADR-0009: AXIGNAL owns graph
  projection and semantic cartography behind a replaceable renderer boundary;
  Sigma + Graphology are the initial renderer choice. This does not authorize
  graph runtime, production renderer dependencies or product UI. Read the
  logical target and evidence-backed current-state ledger linked from
  `docs/architecture/OVERVIEW.md` before architecture work.
- Installing/using design skills must not add LLM or network dependencies to
  required CI.

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

Required gates never depend on LLM output. Semantic Graphify extraction is
non-blocking.

## If requested work conflicts with doctrine

**Stop and report.** Quote the MASTER section and the conflicting request. Do not
implement, do not silently reinterpret doctrine, do not weaken a gate.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
