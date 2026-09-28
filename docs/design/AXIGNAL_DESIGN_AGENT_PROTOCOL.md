# AXIGNAL Design Agent Protocol

**Status:** Tooling/process protocol; subordinate to MASTER, Constitution, ADRs, feature specs and accepted Golden Master.
**Purpose:** Make AI-assisted design materially better without granting an AI authority over AXIGNAL product truth or human visual acceptance.

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

## Integration rule

The canonical repository skill is `.agents/skills/axignal-design-director/SKILL.md`. External design skills remain replaceable advisory providers. This mirrors AXIGNAL's broader architecture: models/providers assist; governed deterministic/human authority decides.
