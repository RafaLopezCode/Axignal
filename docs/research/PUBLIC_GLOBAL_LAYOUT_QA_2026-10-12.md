# Public global layout — 2026-10-12

## Scope and authority

Mode: PRESERVE for the landing; EXTEND its existing frame to public pages.
Authority: MASTER product model, Engineering Constitution, ADR-0016,
architecture overview/terminology, Design Doctrine/Governance, spec 060 and
the incumbent `observer-landing.css` geometry. This is a presentation repair,
not a product-semantic or domain change.

The visitor can move between learning about AXIGNAL, access, contact and
trust pages without reconstructing navigation. PublicShell now owns the
landing's header, main landmark and footer as it already owns those of signup,
login, contact, policies, GDPR and Knowledge. The landing retains its chapters
and interactions. There is one main landmark, including a keyboard skip target.

`public-layout.css` owns the incumbent landing maximum width (1600px), gutter
(`clamp(24px, 3.5vw, 64px)`, 20px below 700px) and background. The landing's
story variables reference those global variables. Forms and article reading
measures remain local to their contents. Short pages keep the footer at the
end of the viewport. Knowledge no longer adds a second outer gutter.

The authenticated Observatory, demonstration Observatory, Admin, internal
design lab and provider-independent root crash recovery are separate product
surfaces; this repair changes the shared public marketing frame.

## Browser QA

Chrome extension browser; local Next.js on `http://127.0.0.1:3820`.
Checked `/`, `/signup`, `/login`, `/contact`, `/policies`, `/gdpr`, and
`/knowledge` (redirects to `/es/knowledge`).
Additional wide-view checks: `/pricing`, `/policies/privacy`,
`/knowledge/basis/product-model`, `/es` and a missing route (404).

- Wide and narrow viewports: actual DOM widths 1600px and 433px. Browser
  zoom means requested viewport sizes 1440px and 390px differ from DOM widths;
  measurements above use actual DOM widths.
- One public header, one footer and one main landmark on every checked route.
- Header, content and footer share widths and gutters. Landing hero shares
  the frame; its main has no duplicate content padding.
- No horizontal document overflow on the checked routes at either width.
- Signup visually inspected in both layouts, including unavailable identity
  service state. No account creation or identity authorization was performed.
- Mobile menu opens, exposes navigation and language selection, closes with
  Escape and restores focus to its trigger.
- Console errors: none captured in the checked views.
- Desktop screenshot: `D:/AXIGNAL/_tmp/public-layout-qa/signup-desktop.jpg`.
  Mobile screenshot was displayed during QA; a later disk capture timed out.
  Temporary viewport override was reset after QA.

Golden Master delta: landing frame consolidated; its existing 1600px width,
gutter, typography, content and chapter actions retained. Adjacent public pages
inherit that geometry. No new economic datum, inference, evidence, provider,
billing authority or canonical mutation is introduced.

## Deterministic validation

- Frozen dependency sync: passed with Python 3.11.
- Ruff formatting/lint and mypy: passed.
- Frontend typecheck: passed.
- Frontend tests: 268 passed; SEO build checks: 8 passed.
- Next.js production build: passed, 585 generated pages.
- Architecture Guard: passed.
- AST Graphify update: completed; governance: all checks passed.
- Full pytest: 2178 passed, 7 skipped, 2 warnings, 670.02 seconds. Skips concern
  platform-specific deployment tests and unavailable optional dependencies.
  Test temporaries use `D:/AXIGNAL/_tmp/public-global-layout-tests` because the
  system temporary directory was unavailable to the first run.

Human visual acceptance: pending. The Design Director states: “Only explicit
human acceptance can close the visual gate.” Automated checks do not declare
visual acceptance. No production deployment was performed.
The user explicitly authorized commit, merge and push on 2026-10-12.
