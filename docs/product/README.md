# AXIGNAL Product Doctrine

This directory holds the product doctrine. It is the highest engineering
authority in the repository.

## Canonical documents

| Document | Role |
| --- | --- |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` | **The MASTER PRODUCT MODEL.** Semantic authority. Doctrine consolidated. Do not replace, reinterpret, summarize away, or weaken. |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md.sha256` | Pinned content hash. Verified in CI. Changing the MASTER requires an explicit, reviewed change to this hash. |

## Rules

- There is exactly one MASTER. Do not create competing MASTER documents.
- Engineering constraints are derived from the MASTER into
  `.specify/memory/constitution.md` (the Engineering Constitution).
- No feature spec, plan, task, or ADR may override the MASTER.
- If an implementation request conflicts with the MASTER: **fail closed**, stop,
  and report the conflict.

Precedence chain:

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
