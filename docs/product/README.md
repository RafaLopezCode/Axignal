# AXIGNAL Product Doctrine

This directory holds the product doctrine. It is the highest engineering
authority in the repository.

## Canonical documents

| Document | Role |
| --- | --- |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` | **The single MASTER PRODUCT MODEL.** Semantic authority. Doctrine consolidated, including the 2026-09-26 economic brain doctrine. Do not replace, reinterpret, summarize away, or weaken. |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md.sha256` | Pinned content hash. Verified in CI. Changing the MASTER requires an explicit, reviewed change to this hash. |

## Rules

- There is exactly one MASTER. Do not create competing MASTER documents.
- AXIGNAL is an economic brain, not an economic index. Economic cartography
  is cognitive substrate; explainable economic intelligence is the product.
- Economic Opportunity Intelligence and Compounding Economic Intelligence
  are inseparable core pillars; see MASTER §53.
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
