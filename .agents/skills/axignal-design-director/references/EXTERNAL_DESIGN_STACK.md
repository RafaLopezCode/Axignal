# Curated External Design Stack

External tools are advisory and subordinate to AXIGNAL authority. Current adoption, exact pins, license, install/security surface, and decisions live in [`DESIGN_TOOLCHAIN.lock.json`](../../../../docs/design/DESIGN_TOOLCHAIN.lock.json). This file explains routing, not product authority.

## 1. Anthropic frontend-design

Purpose: distinctive art direction, deliberate typography/layout/color, anti-template pressure.

Upstream: https://github.com/anthropics/skills/tree/main/skills/frontend-design

Use for: visual direction and creative specificity.
Do not use for: overriding Golden Master, HFX semantics, canonical data meaning or accessibility requirements.

## 2. Impeccable

Purpose: broad design craft workflow, critique/polish/adapt/harden, live browser iteration and deterministic anti-pattern detection.

Upstream: https://github.com/pbakaus/impeccable

Use for: craft floor, defect discovery, bounded polish.
Status: referenced, not installed. Its installer modifies project agent configuration/hooks and its first command may fetch/cache executable code. Consider installation only after a separate review of that surface. AXIGNAL override: numeric/heuristic scores are advisory; they never constitute human acceptance or product truth.

## 3. UI UX Pro Max

Purpose: large pattern/design reference corpus and stack-specific guidance.

Upstream: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

Status: installed as a pinned local corpus with a thin Codex entry point. Use selectively for a concrete question: reference search, accessibility/pattern alternatives, typography and framework guidance.
Do not let generated design systems replace AXIGNAL's accepted Design System.

## 4. Codex UI/UX Skill by atuizz

Purpose: project cognition, task/journey reasoning, frontend governance and quality gates.

Upstream: https://github.com/atuizz/codex-ui-ux-skill

Status: rejected for this toolchain. Its journey/recovery reasoning overlaps HFX and the Design Director; helper-generated governance would duplicate existing authority surfaces. Reconsider only if a demonstrated gap remains.
Use for: none by default.

## 5. Vercel Web Interface Guidelines

Purpose: web interaction, copy, accessibility and implementation review.

Upstream: https://github.com/vercel-labs/web-interface-guidelines

Status: referenced, not copied or installed. Use for a targeted web craft/accessibility review when relevant.
Do not treat general web convention as authority over deliberate AXIGNAL cognitive navigation.

## 6. Browser verification

Preferred capabilities: the Codex host's actual browser interaction for this task; capture rendered evidence and inspect responsive behavior, keyboard/focus, and runtime errors. Host tooling is not pinned by this repository. Playwright remains an optional referenced fallback, not a dependency; install browsers only for a concrete repeatable automation need.

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
8. do not run remote installers, hook setup, or downloaded executables automatically; any install is a separately reviewed change.

## Task routing

- `PRESERVE`: Golden Master + HFX + real-browser comparison; no exploratory art direction.
- `EXTEND`: read AXIGNAL authority first, then route only the relevant art direction, UX reference, or web craft guidance.
- `EXPLORE`: require explicit authorization and isolate the prototype from accepted surfaces.

Do not load the entire stack in one task. Human visual acceptance remains a separate gate regardless of automated critique.

The curated stack is intentionally small. Adding overlapping skills requires evidence of a missing capability.
