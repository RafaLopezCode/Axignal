# El Observador — landing visual direction, 2026-10-10

Status: implemented and browser-verified candidate; **human visual acceptance pending**.
Base: canonical b51a54526da1fc48a6070712df0dd97fde81d6a6. Branch: codex/observer-landing-visual.
Independent of runtime evidence PR #192. No merge or production deployment.

## Authority and direction

The user's supplied character references and visual brief authorize this landing refinement.
Claude's canonical narrative, section order, copy, routes and CTA hierarchy remain intact.
MASTER, Constitution and design doctrine retain precedence. Impeccable / AXIGNAL Design
Director informed scoped layout and responsive QA; no design reference became product authority.
No subscriber, public demo, PublicShell, contracts, backend, translation catalog or canonical
character-renderer changes. All 88 bilingual copy pairs are unchanged (TypeScript AST comparison).

The composition widens to a 1600px stage with responsive gutters, retaining readable paragraph
measures. The actual labelled fictional product windows keep priority; the narrator accompanies
the adjacent idea in flow. Existing Bic Notes handwriting explains evidence, possibility and
unknown states. No extra slogans, new claims or ornamental annotations are introduced.

## Scene map

| Canonical block | Scene | Purpose / interaction |
| --- | --- | --- |
| Hero | discover | Calm investigation beside the invitation; tablet/notebook, blue monocle. |
| Choose organization | focus | Work table and map: a concrete focus for observation. |
| Observe and remember | memory | Filed evidence: continuity rather than a new chat each time. |
| Understand what matters | explain | Explain findings without granting them new authority. |
| AXENT | conversation | Dialogue beside the existing contextual explanation. |
| Proof: reach / evidence / unknown / time | strategy / research / unknown / time | Scene changes with the existing selected proof; time comparison remains interactive. |
| Professional uses | strategy / business / research / representation | Existing audience-specific poses, now retained in mobile layouts. |
| Trust | boundaries | Reading the rules beside the three unchanged commitments. |
| Pricing / portfolio growth | focus → connect | One focus becomes multiple contexts when capacity exceeds one; prices unchanged. |
| Closing | journey | Working with a laptop: continuity after starting with one organization. |

Assets: canonical /observer/narrative-v2 atlas, through existing FramedObserver. No new raster,
SVG illustration, crop or image manipulation. Beret, one blue monocle, free second eye, calm
dark linework and full silhouettes preserve the supplied identity. The reusable LandingGuide
is decorative; adjacent text carries meaning, so it introduces no duplicate screen-reader copy.
The hidden desktop sticky duplicate is inert, preventing keyboard focus in an aria-hidden tree.

## Implementation files

- apps/web/experience/components/landing.tsx: scene placement and inert sticky duplicate.
- apps/web/experience/components/landing-guide.tsx: landing-only reusable narrator wrapper.
- apps/web/experience/components/observer-landing.css: all selectors scoped to .observer-story.
- apps/web/experience/components/landing-extras.tsx: scene follows existing capacity selection.

No atlas, shared renderer, subscriber or canonical demo changes. No dependency or flag changes.

## Actual verification

Candidate: http://127.0.0.1:3857/ (HTTP 200, owned isolated Next server).
Browser: Codex in-app browser, rendered desktop 1440×1000, tablet 768×1024, mobile 390×844.
Screenshots were inspected after rendered state settled; capture names are linked below.
Additional boundary measurements: 1101, 641, 640, 390px; scrollWidth never exceeds viewport.
Six locales rendered: es/en/de/pt/fr/it; no horizontal overflow in the measured desktop states.

Proof keyboard arrows select the corresponding panel. July/October controls update the existing
fictional observation date. The evidence CTA opens /demo?signal=renovation&depth=prove and
shows the canonical illustrative sources and POTENTIAL explanation. Agency selection updates
copy and scene. Capacity 5 gives 29.75 EUR and the connect pose. Closing actions and characters
occupy distinct layout cells; silhouettes are retained on narrow screens. The decorative desktop
sticky duplicate has its inert attribute. No new motion; existing reduced-motion rules retained.
Console: no error entries; only expected development Fast Refresh reload warnings during edits.
This is a bounded browser functional/visual check, not a full assistive-technology certification.

- Frontend: 185 tests passed, typecheck passed, i18n 1762 entries / missing 0; production build passed
  (528 localized prerendered Knowledge pages).
- Ruff formatting/check passed; mypy 480 files passed; Architecture Guard and governance passed.
- AST-only Graphify refreshed; no model/API calls. Impeccable detect: empty findings array.
- Canonical backend b51a545 full suite independently validated in the runtime worktree:
  2090 passed, 7 documented environment/optional-SDK skips. No backend files changed here.
- No gates weakened or additional tests mirroring decorative markup introduced.

## Visual evidence

[Desktop hero](observer-landing-2026-10-10/desktop-hero.jpg) ·
[Tablet hero](observer-landing-2026-10-10/tablet-hero.jpg) ·
[Mobile agency](observer-landing-2026-10-10/mobile-agency.jpg) ·
[Temporal proof](observer-landing-2026-10-10/desktop-time.jpg) ·
[Memory](observer-landing-2026-10-10/desktop-memory.jpg) ·
[Trust](observer-landing-2026-10-10/tablet-trust.jpg).
[Locale measurements](observer-landing-2026-10-10/locales.json),
[Breakpoint measurements](observer-landing-2026-10-10/responsive.json).

## Remaining iteration and delivery state

Human/CTO visual acceptance remains pending; none of these captures is promoted to a Golden
Master. The next visual iteration, if requested, is pose prominence and section rhythm after
human review. Existing proof card aria-controls points at the canonical obs-depth name while
landing sheets lack that id; this incumbent shared-component relationship is documented rather
than changing subscriber/demo contracts in a visual-only slice.

IMPLEMENTED: landing composition and narrator system. PROBADO: deterministic frontend/gates
and bounded real browser interactions. INTEGRADO: local candidate only, CTO PR review pending.
DESPLEGADO: no production deployment. VERIFICADO E2E: local public landing, locale selection,
proof/time/audience/capacity interactions and navigation to the labelled canonical example;
no real subscriber authentication, live research or model-quality certification by this slice.

## User follow-up: advisory pricing presence

The user requested that the 995 EUR human advisory offer have presence comparable to the
subscription card above it. Landing-only CSS now gives the existing aside a white bordered
card, generous padding, a larger title and price, and a full-width blue contact action.
Its original text, amount, VAT statement, service scope and /contact destination are unchanged.
No React, catalog, calculator or product-contract changes.

Actual browser checks: desktop 1280×720 and mobile 390×844; the full card and its 50px+
contact button fit without horizontal overflow. The amount remains 995.00 EUR/month.
185 frontend tests, typecheck, i18n (1762 entries / missing 0), production build passed;
Impeccable detector returned no findings.
[Desktop pricing](observer-landing-2026-10-10/advisory-pricing-desktop.jpg) ·
[Mobile pricing](observer-landing-2026-10-10/advisory-pricing-mobile.jpg).
