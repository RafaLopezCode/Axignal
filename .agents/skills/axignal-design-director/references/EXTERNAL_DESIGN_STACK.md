# Curated External Design Stack

External tools are advisory and subordinate to AXIGNAL authority.

## 1. Anthropic frontend-design

Purpose: distinctive art direction, deliberate typography/layout/color, anti-template pressure.

Upstream: https://github.com/anthropics/skills/tree/main/skills/frontend-design

Use for: visual direction and creative specificity.
Do not use for: overriding Golden Master, HFX semantics, canonical data meaning or accessibility requirements.

## 2. Impeccable

Purpose: broad design craft workflow, critique/polish/adapt/harden, live browser iteration and deterministic anti-pattern detection.

Upstream: https://github.com/pbakaus/impeccable

Use for: craft floor, defect discovery, bounded polish.
AXIGNAL override: numeric/heuristic scores are advisory; they never constitute human acceptance or product truth.

## 3. UI UX Pro Max

Purpose: large pattern/design reference corpus and stack-specific guidance.

Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

Use for: reference search, accessibility/pattern alternatives, typography and framework guidance.
Do not let generated design systems replace AXIGNAL's accepted Design System.

## 4. Codex UI/UX Skill by atuizz

Purpose: project cognition, task/journey reasoning, frontend governance and quality gates.

Upstream: https://github.com/atuizz/codex-ui-ux-skill

Use for: cross-checking journey completeness and product-specific reasoning.

## 5. Vercel Web Interface Guidelines

Purpose: web interaction, copy, accessibility and implementation review.

Upstream: https://github.com/vercel-labs/web-interface-guidelines

Use for: web craft and accessibility audit.
Do not treat general web convention as authority over deliberate AXIGNAL cognitive navigation.

## 6. Browser verification

Preferred capabilities: actual browser interaction, screenshots, responsive checks, console/runtime inspection and deterministic E2E.

Relevant upstream:
- https://github.com/openai/plugins/tree/main/plugins/vercel/skills/agent-browser
- https://github.com/openai/plugins/tree/main/plugins/build-web-apps/skills/frontend-testing-debugging

Browser evidence is required for rendered frontend claims. Source inspection alone is insufficient.

## Adoption policy

Before installing/vendorizing an external skill:
1. verify upstream identity and license;
2. pin a version/commit where reproducibility matters;
3. inspect scripts before execution;
4. do not grant secrets or production credentials;
5. keep external skill code outside canonical domain/application truth;
6. record provenance;
7. prefer invocation/reference over copying when copying creates maintenance drift.

The curated stack is intentionally small. Adding overlapping skills requires evidence of a missing capability.
