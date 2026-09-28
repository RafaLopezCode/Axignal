# AXIGNAL Design Agent Protocol

**Status:** Tooling/process protocol; subordinate to MASTER, Constitution, ADRs, feature specs and accepted Golden Master.
**Purpose:** Make AI-assisted design materially better without granting an AI authority over AXIGNAL product truth or human visual acceptance.

Codex discovers the orchestrator at `.agents/skills/axignal-design-director/SKILL.md`. It is the routing entry point. Small bridges under `.agents/skills/frontend-design/` and `.agents/skills/ui-ux-pro-max/` delegate to the pinned shared sources under `.opencode/skills/`; they do not duplicate the upstream corpus. Adoption and supply-chain facts are recorded in [DESIGN_TOOLCHAIN.lock.json](DESIGN_TOOLCHAIN.lock.json).

## Design pipeline

```text
MASTER / CONSTITUTION
        ↓
HFX + ACTIVE FEATURE SPEC
        ↓
GOLDEN MASTER / DESIGN SYSTEM
        ↓
AXIGNAL DESIGN DIRECTOR
        ↓
external craft intelligence (advisory)
        ↓
implementation
        ↓
real browser evidence
        ↓
deterministic + heuristic critique
        ↓
bounded correction
        ↓
HUMAN VISUAL ACCEPTANCE
        ↓
accepted reusable design knowledge
```

## Why this exists

Coding agents are strong at implementation but can converge on category-average UI, overfit generic component libraries, or judge quality from source code. AXIGNAL requires product-specific cognitive cartography and truthful epistemic presentation. The process therefore separates four authorities:

1. **Product truth:** MASTER/Constitution/domain contracts.
2. **Cognitive UX:** HFX and accepted feature specifications.
3. **Visual truth:** accepted Golden Master/Design System.
4. **Craft advice:** external skills, model critique, heuristics and automated detectors.

Only the first three can constrain AXIGNAL. Craft advice proposes improvements.

## Self-growth loop

AXIGNAL can improve AXIGNAL without circularly granting itself truth authority.

Allowed loop:

```text
OBSERVE USER/PRODUCT PROBLEM
        ↓
FORM DESIGN HYPOTHESIS
        ↓
BUILD PROTOTYPE/CHANGE
        ↓
OBSERVE RENDERED BEHAVIOR
        ↓
DETECT/CRITIQUE
        ↓
HUMAN ACCEPT / REJECT / CORRECT
        ↓
STORE ACCEPTED DESIGN KNOWLEDGE + PROVENANCE
        ↓
REUSE IN FUTURE DESIGN WORK
```

A model-generated preference, critique score, click pattern or visual detector result is evidence/input, not canonical design truth. Sensitive psychological profiling must not be inferred from navigation.

## Quality gate

Material UI work cannot close from code review alone. Required evidence is proportional to scope, but normally includes rendered desktop and narrow states, primary interactions, affected edge states, accessibility checks, console/runtime health, and Golden Master delta where applicable.

Automated tools may say `PASS` for their own bounded checks. They may not say `HUMAN_ACCEPTED`.

Use the bounded loop `RENDER → INSPECT → BATCH ROOT CAUSES → REPAIR → CONFIRM`. A third pass needs a concrete observable defect. Record browser, viewport, route/state, and evidence path for a smoke or visual check. Never treat source inspection as rendered proof, and never expose secrets in screenshots or browser state.

## Capability routing

| Mode | Route |
| --- | --- |
| `PRESERVE` | Golden Master + relevant HFX contract + browser comparison; external creative direction is out unless explicitly in scope. |
| `EXTEND` | AXIGNAL authority + only the relevant craft/UX/web references. |
| `EXPLORE` | Explicit authorization + isolated lab + human review; no automatic promotion. |

The orchestrator chooses only the smallest relevant capability set. The toolchain lock distinguishes installed, referenced, and rejected tools and records their provenance and executable/network surface. An external installer, hook, or downloaded executable is never run automatically.

## Integration rule

The canonical repository skill is `.agents/skills/axignal-design-director/SKILL.md`. External design skills remain replaceable advisory providers. This mirrors AXIGNAL's broader architecture: models/providers assist; governed deterministic/human authority decides.
