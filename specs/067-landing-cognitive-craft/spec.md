# 067 — Landing: focus, evidence and deliberate motion

Created: 2026-10-12. Branch: `codex/067-landing-cognitive-craft`.
Authority: MASTER §§1.1, 25, 53–55; Constitution; ADR-0016/0017;
spec 060; incumbent public layout and brand assets.

## User intent and clarification

Improve the landing's visual impact while improving, never sacrificing, UX.
The user explicitly chose to amplify Fraunces, AXIGNAL blue, the monocle and
El Observador rather than replace the visual identity. GSAP is optional;
tool choice must follow the interaction's need. No production deployment.

## User stories and acceptance

P1 — Understand the promise at first glance. Existing approved hero copy and
CTA names remain; a focused fictional example replaces the dense hero grid.
One finding is readable with its nature and date. All lanes remain reachable;
no item is silently reclassified or transformed into canonical truth.

P1 — Inspect why. A visible control reveals the original example's reasoning
and evidence using the existing product body and synthetic evidence provider.
Changing moment never shows a finding before its availability date. A changed
moment is presentation state only, and selected content stays valid.

P2 — Understand the three steps without a long compulsory scroll sequence.
All three explanations are visible, and the visitor can select the matching
example state directly. Scroll remains native; no autoplay or fake progress.

P2 — Use every control by keyboard and touch. Labels, native buttons, focus
styles, announcement of user-selected content, reduced motion, narrow layouts
and six locales are required. Motion must not delay or hide actions.

## Success criteria

- Hero contains one primary finding, with immediate access to the other lanes.
- No arbitrary universal score, generated business claim or new source.
- Existing signup/demo links, pricing, public frame and funnel events survive.
- No horizontal overflow at desktop/mobile widths or long locale labels.
- Actual browser evidence covers selection, time, proof and keyboard paths.
- No animation loops or scroll interception introduced; reduced motion removes
  spatial effects without removing content or controls.
- Required deterministic gates pass before any integration.
- Human visual acceptance remains explicit; “perfection” is not claimed by QA.

## Non-scope

Subscriber/Admin redesign, canonical writes, authentication, payments, research
providers, new illustrations, new economic data, production deployment.
