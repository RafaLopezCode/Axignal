# AXIGNAL Product Doctrine

This directory holds the product doctrine. It is the highest engineering
authority in the repository.

## Canonical documents

| Document | Role |
| --- | --- |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` | **The single MASTER PRODUCT MODEL.** Semantic authority. Doctrine consolidated, including the 2026-09-26 economic brain doctrine. Do not replace, reinterpret, summarize away, or weaken. |
| `AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md.sha256` | Pinned content hash. Verified in CI. Changing the MASTER requires an explicit, reviewed change to this hash. |
| [`AXIGNAL_DIGITAL_REPRESENTATION_INTELLIGENCE_PRODUCT_SPEC.md`](AXIGNAL_DIGITAL_REPRESENTATION_INTELLIGENCE_PRODUCT_SPEC.md) | Proposed, pre-implementation product specification for the four DRI observation families; subordinate to MASTER §54. |

## Prepared execution goals (non-canonical, not yet authorized)

| Document | Role |
| --- | --- |
| [`AXIGNAL_BIDIRECTIONAL_INTELLIGENCE_EXECUTION_GOAL_2026-10-09.md`](AXIGNAL_BIDIRECTIONAL_INTELLIGENCE_EXECUTION_GOAL_2026-10-09.md) | CTO goal: bidirectional economic intelligence, JEV as bounded perception instrument, and evidence-backed constructive criticism. Execution only after spec 063 closure and explicit CTO instruction; never overrides MASTER, Constitution or ADRs. |

## Rules

- There is exactly one MASTER. Do not create competing MASTER documents.
- AXIGNAL is an economic brain, not an economic index. Economic cartography
  is cognitive substrate; explainable economic intelligence is the product.
- Economic Opportunity Intelligence and Compounding Economic Intelligence
  are inseparable core pillars; see MASTER §53.
- Digital Representation Intelligence connects search, generative,
  social/public conversation and public reputation/experience observations to
  the governed economic world; see MASTER §54. It does not authorize runtime.
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
