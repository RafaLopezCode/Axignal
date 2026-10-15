# Persistent AXENT and evidence inside the canonical canvas

## Scope and clarification

The user requests a separate UI/UX branch: AXENT's sidebar stays fixed and clean,
evidence emerges in a bottom sheet inside the canvas, and a blue handwritten
annotation reads “Consulta a Axent →”. “Bic” means ballpoint handwriting (human
confirmation, 2026-10-15). The change must reach every dashboard through the one
canonical Observatory used by Admin, account and demo. Backend work is limited
to necessary wiring; the existing read and AXENT contracts already suffice.

## Acceptance

- The desktop AXENT rail occupies a stable column before, during and after
  evidence inspection. Its conversation scrolls independently and its composer
  remains reachable. Keep the current AXENT component, scope, transport and
  evidence-grounded answers unchanged.
- Finding details and the evidence tab use a bottom sheet confined to the canvas;
  neither occupies nor covers the AXENT rail or portfolio navigation.
- Preserve URL selection, back/forward, family filters, scope, dates, sources,
  epistemic states, unknowns, technical evidence and the existing source links.
- Sheet close and Escape restore focus; the background canvas cannot receive
  obscured keyboard focus. Desktop AXENT remains usable while inspecting proof.
  Mobile retains accessible contextual AXENT and usable evidence without
  requiring a narrow desktop rail. Honor reduced motion and safe areas.
- Reuse the existing local Bic Notes font. The annotation is an accessible
  action pointing to AXENT, with the requested Spanish text and localized copy.
- No new API, provider, dependency, synthetic operational fallback, production
  mutation or deployment. Demonstration data retains its existing labeling.
- Validate account/demo/Admin parity, frontend tests/types/i18n/build, relevant
  browser interactions at wide/narrow sizes and repository deterministic gates.
  Regression impossibility cannot be guaranteed; report measured evidence.

## Authority

MASTER §§4.3/55, Constitution, ADR-0016/0017/0042, HFX, current Observatory tokens
and accepted interface are authoritative. EXTEND only the explicitly requested
placement and annotation; preserve product semantics. Taste Skill excludes app
screens and does not supply a replacement visual system. Human visual acceptance
remains pending after implementation and automated QA.
