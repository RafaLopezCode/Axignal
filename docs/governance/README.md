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
| [AGENT_AUTONOMY_AND_DELEGATION_CONTRACT.md](AGENT_AUTONOMY_AND_DELEGATION_CONTRACT.md) | Binding two-tier delegation and agent-authority contract for frontier vs. guided agents. |
| [AXIGNAL_FRONTIER_RECONCILIATION_ROADMAP_2026-09-30.md](AXIGNAL_FRONTIER_RECONCILIATION_ROADMAP_2026-09-30.md) | FR-00→FR-31 product/architecture reconciliation history and closure evidence. |
| [AXIGNAL_ADMIN_OPERATING_SYSTEM_ROADMAP_2026-10-01.md](AXIGNAL_ADMIN_OPERATING_SYSTEM_ROADMAP_2026-10-01.md) | AO-00→AO-31 implementation contract for Admin, business operations, acquisition, finance/fiscal control and deep re-audit. |

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
