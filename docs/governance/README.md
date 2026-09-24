# AXIGNAL Engineering Governance

This directory indexes the governance stack. The MASTER PRODUCT MODEL is the
semantic authority; everything here is derived from it and must not override it.

## Documents

| Document | Purpose |
| --- | --- |
| [DETERMINISTIC_CI.md](DETERMINISTIC_CI.md) | The required, deterministic merge gates and how to run them. |
| [ARCHITECTURE_GUARD.md](ARCHITECTURE_GUARD.md) | What Architecture Guard rejects and why. |
| [GRAPHIFY.md](GRAPHIFY.md) | Graphify scope, canonical vs generated artifacts, refresh and drift. |
| [SPEC_KIT.md](SPEC_KIT.md) | Spec-driven lifecycle and MASTER precedence. |

Related:
- Engineering Constitution: `.specify/memory/constitution.md`
- Product doctrine: `docs/product/README.md`
- ADRs: `docs/adr/README.md`
- Architecture: `docs/architecture/OVERVIEW.md`

## Precedence (FAIL CLOSED)

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

If any lower-ranked artifact conflicts with a higher-ranked one, the
lower-ranked artifact is wrong. Stop, report, and do not implement. Never weaken
a gate merely to get CI green.

## What "ENGINEERING_READY" means

- The MASTER is canonical, present and hash-pinned.
- Governance is installed/configured: Graphify, Spec Kit, Architecture Guard,
  deterministic CI.
- Architecture contracts are enforceable and pass.
- All deterministic gates pass locally and in remote CI.
- No unresolved doctrine conflict.
