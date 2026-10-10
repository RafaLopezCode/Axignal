# Landing spatial audit — 2026-10-10

Mode: PRESERVE / Persuade. User authority: audit the whole landing and optimize spatial
coherence across devices, including the preceding annotated requests. MASTER, Constitution,
accepted design doctrine and incumbent narrative remain authoritative. Applied project
Impeccable layout/adapt and Design Director; Product Design Audit supplies screenshot-first
flow assessment. An independent read-only spatial assessment corroborated the root causes.

## Findings and implemented repairs

| Flow step | Observed imbalance | Final disposition | Status |
| --- | --- | --- | --- |
| 1. Header and first understanding | Shell rails narrower than chapters; fixed illustration column compressed the caption | One 1600px stage and gutter for header, chapters, closing and footer; caption can wrap alongside its guide without collapsing to a sliver; hero example has explicit available width | Repaired; rendered desktop/mobile |
| 2. How observation works | Repeated mobile illustrations used large isolated vertical blocks; minimum example heights left excess empty space; AXENT followed a released sticky window too closely | Compact illustration-plus-note pairs on phone; static touch examples with 240px minimum for sparse modes; explicit 24px end separation and 64px AXENT margin on desktop; centered AXENT inner composition | Repaired; rendered desktop/tablet/mobile |
| 3. Understand the proof | Narrator below a tall sticky product panel created lower-right weight and could exceed laptop height; evidence tab was selected first | Narrator supports the left tabs; product stage is static; reach is the initial selection; tablet groups tabs/guide above example; phone stacks without hiding content | Repaired; initial state and arrow-key transition verified |
| 4. Choose an audience | 320px illustration left too little tablet text space; mismatched collapse points caused a density cliff | 280px desktop/240px tablet footprint with a readable text column, then one-column phone composition; notes accompany audience changes | Repaired; default and agency state verified |
| 5. Trust | Heading/figure and commitments inherited additive margins | Shared section/group spacing; commitments follow their heading group once; mobile guide and note are one compact pair | Repaired; all commitments remain visible |
| 6. Pricing | Tablet introduction left a large unused lateral area; advisory offer had weak presence | Tablet explanation and narrator share a balanced row above calculator; phone uses equal narrator/note columns; advisory keeps its full white card, large price and contact action | Repaired; 25 organizations = 128.75 EUR/month, then reset to 1 |
| 7. Final invitation and footer | Parent/button margins accumulated; old illustration aspect ratio created an empty-height wrapper | One 24px row rhythm, no duplicated CTA top margin, intrinsic guide height and shared footer rails | Repaired; mobile closing wrapper defect confirmed and removed |

## Spatial contract

- Maximum stage 1600px, gutter `clamp(24px, 3.5vw, 64px)`, phone gutter 20px.
- Chapter boundaries 64–96px on desktop, 64px tablet and 52px phone; major internal groups
  32–48px. Small figure/text groups use 16–24px. Closing title/actions use one gap.
- Narrator footprint 280px desktop and 240px tablet. Phone pairs use equal flexible columns,
  preventing a narrow text sliver even at 320px; numbered-step guides span the available row.
- Portrait optical corrections: journey/unknown 78%, discover/representation 90% of their
  illustration column. Props and character anatomy inherently differ; equal SVG bounds are
  not claimed to guarantee anatomically identical character sizes.
- Scrolly and proof examples use static one-column compositions below 1100px. Narrator scale
  changes at 900px; pricing becomes one column there while its explanation and illustration
  remain paired. At 700px the supporting narrator layouts become compact phone groups.
- Preserve asymmetric text/evidence hierarchy where it supports reading; do not force identical
  column widths across different content. No filler claims, hidden product content or new art.

## Rendered evidence and coverage

Actual runtime: http://127.0.0.1:3857/, owned isolated worktree, synthetic example explicitly
labelled fictional. Chrome supported viewport overrides were used because IAB resizing returned
success while remaining at 1280x720. Actual CSS `innerWidth`/`innerHeight` were measured rather
than inferred from requested dimensions. Chrome's existing 90% zoom was preserved; screenshot
pixel dimensions consequently differ from CSS dimensions. Temporary viewport override reset.

Final mechanical matrix: 320x800, 390x844, 767x1024, 1024x767, 1280x720 and 1743x1244.
Every measured viewport has `scrollWidth == clientWidth` and no non-fixed landing element
outside the horizontal viewport; the header/hero/footer inner rails match at every size.
The desktop overview was captured at 1440x900. These are browser device classes, not a claim
to have tested every physical device, browser engine, assistive technology or WCAG criterion.

Six locales (es/en/de/pt/fr/it) rendered at 390px; all six also checked at 320px after the
final narrow-column repair: no overflowing narrator notes or page width. Mobile navigation
opens/closes, all locale options work, initial proof reaches `proof-tab-0`, ArrowRight updates
selection/panel label and focuses `proof-tab-1`, and the first tab is restorable. Agency
selection updates its explanation. Pricing shortcuts update both amount and organization
count. Existing route destinations, fictional epistemic labels and evidence links remain.
No captured console errors; two expected development Fast Refresh reload warnings.

Full-document screenshots record spatial order; a sticky window records one scroll state,
not every step. They are complementary to individual viewport captures and DOM measurements.
Lazy narrator assets were loaded by walking the page for final captures. The initial mobile
full-document baseline contains some not-yet-loaded illustrations and is labelled accordingly;
its occupied bounds still demonstrate the former layout footprint. No visual acceptance or
new Golden Master is implied.

| Evidence | Artifact |
| --- | --- |
| Before tablet, loaded scenes | [baseline](observer-landing-2026-10-10/before-tablet-768.png) |
| Before phone, partial lazy assets | [baseline](observer-landing-2026-10-10/before-mobile-390.png) |
| Final desktop overview | [1440px](observer-landing-2026-10-10/final-desktop-1440.png) |
| Final proof composition | [1743px document crop](observer-landing-2026-10-10/final-desktop-proof.png) |
| Final tablet overview | [767px](observer-landing-2026-10-10/final-tablet-768.png) |
| Tablet pricing detail | [pricing](observer-landing-2026-10-10/final-tablet-pricing.png) |
| Final phone overview | [390px](observer-landing-2026-10-10/final-mobile-390.png) |
| Phone introduction detail | [hero](observer-landing-2026-10-10/final-mobile-hero.png) |
| Final width/rail matrix | [JSON](observer-landing-2026-10-10/layout-matrix.json) |
| Six locales at 390 and 320 | [390](observer-landing-2026-10-10/language-matrix.json), [320](observer-landing-2026-10-10/language-matrix-320.json) |

## Implementation boundary and validation

Touched implementation: landing.tsx (initial proof and guide grouping/notes), landing-guide.tsx
(optional decorative note), landing-extras.tsx (pricing guide), observer-landing.css (scoped
spatial system). No shared shell implementation, canonical demo/subscriber UI, backend,
contracts, schema, catalog, factual copy, prices or CTA destinations changed. No new dependency. TypeScript AST comparison retains all 63 pre-existing literal bilingual
pairs in landing.tsx; four additional distinct note pairs reuse existing catalog messages.

Frontend: typecheck PASS, i18n 1762 entries / missing 0, 185/185 tests, production build PASS
with 528 localized prerendered Knowledge pages. Ruff format/check PASS; strict mypy PASS
(480 files); Architecture Guard and governance PASS; AST-only Graphify refreshed. Impeccable
CSS detector reports no findings. Backend full suite PASS: 2090 passed, 7 skipped in 657.78s using the isolated temp directory.
The skips are the existing optional SDK/POSIX-environment exclusions; no tests or gates changed.
The first backend attempt had 937 setup errors due to Windows access denied on the existing
`pytest-of-usuario` directory, not assertion failures in landing code. It was repeated without
changing tests/gates, using a verified previously nonexistent temporary directory under the
AXIGNAL audit workspace.

Delivery state: IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY.
Human visual acceptance pending CTO. Candidate locally running; changes not integrated into
main, not deployed to production and not promoted to a Golden Master. PR #193 review only.
