# Spec Kit in AXIGNAL

GitHub Spec Kit provides the spec-driven development lifecycle. Installed with
its official CLI:

```powershell
uv tool install specify-cli
specify init --here --integration opencode
```

Version: `specify-cli 1.0.11`, integration `opencode`, scripts `powershell`.

## Lifecycle

```
SPECIFY
  ↓
CLARIFY
  ↓
PLAN
  ↓
ARCHITECTURE REVIEW
  ↓
TASKS
  ↓
IMPLEMENT
  ↓
VERIFY
  ↓
CONVERGE
```

Agent skills live in `.opencode/commands/` (`/speckit.specify`,
`/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.clarify`,
`/speckit.analyze`, `/speckit.checklist`, `/speckit.converge`).

## MASTER precedence

- The Spec Kit constitution is `.specify/memory/constitution.md`. It points to
  the MASTER as upstream semantic authority.
- `/speckit.plan` runs a **Constitution Check** gate. Treat it as mandatory.
- No generated feature spec, plan or task may override the MASTER.
- If a feature spec conflicts with the MASTER: **FAIL CLOSED**. Stop, report the
  conflict, and do not implement.

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

## Deterministic backstop

Spec Kit gates are agent-driven. The repository's deterministic gates
(`uv run axignal-governance`, Architecture Guard, contract tests) are the hard
backstop and are required for merge. See
[DETERMINISTIC_CI.md](DETERMINISTIC_CI.md).

## Feature directories

Specs live under `specs/NNN-short-name/spec.md` (sequential numbering). The
active feature is recorded in `.specify/feature.json` (gitignored, local).
