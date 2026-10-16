# Feature Specification: Public landing ecosystem

**Feature Branch**: `codex/public-landing-ecosystem`
**Created**: 2026-10-16
**Status**: Implemented and deterministically validated; independent material fixes resolved; final human visual acceptance pending
**Input**: Build an exceptional public AXIGNAL website in an independent branch, after studying the product, with custom illustrations, ten data families and industry use cases. All three audiences matter; code first.

## Authority and scope

MASTER §§1.1, 27, 53–55 → Constitution → ADR-0053, ADR-0089, commercial and HFX contracts → this spec → design brief → invoked skills. Extend the acquisition surface, without changing the economic brain, private dashboards, Admin, AXENT or authentication. This specification updates the public IA from spec 060 for the explicitly requested family and industry journeys. Its epistemic, single-example, pricing and telemetry constraints remain binding. A composition choice never authorizes new product capabilities, production deployment or a merge.

## Clarifications

- Audience: the user confirmed all three are potential customers. The website must serve company decision makers, agencies and consultancies without making AXIGNAL an SEO-only product.
- Build path: the user chose code first with custom illustrations. Preserve the canonical monocle artwork, blue, Fraunces/Manrope and the established Observador character.
- Composition: three first-viewport HTML sketches are presented through the invoked Impeccable decision page. The user requested another round, then selected “Lo que haces y lo que se entiende” (`understanding`) in round 2; decision `23303bea`. The approved comp is `.impeccable/mocks/decision/round-2/understanding.png`.
- Operational data: no invented customers, results, quotes, statistics, business observations or operational measurements. Retain the existing canonical, explicitly fictional `/demo`; do not create another fictional company or dataset.

## User Scenarios & Testing

### User Story 1 — Understand and decide (P1)

A visitor understands what AXIGNAL does, whether it is for them, how evidence and memory help, how access works today and the next action.

**Independent test**: inspect the home at desktop and narrow width, navigate to the single example and the actual signup/contact flow.

1. Given a first visit, the first viewport explains economic observation from public evidence, names a useful action and does not require internal vocabulary.
2. Given a visitor who wants proof, every example action converges on `/demo`, with its existing honest labeling and supported deep links.
3. Given an interested visitor, the offer uses the governed reference price and explains the current invitation-based Design Partner programme; no fake checkout, promise of immediate access or fabricated receipt.

### User Story 2 — Discover the data families (P1)

A visitor sees all ten families and can understand the question each answers, the kinds of public evidence involved and the limits of coverage.

**Independent test**: compare the marketing catalog with `FAMILY_ORDER`, visit each family anchor and verify that its evidence and limitation remain visible without interacting.

1. All ten canonical family IDs appear once; no parallel taxonomy is invented.
2. Presence distinguishes Web, search and generative observations when actually measured; a mention is not a citation or endorsement.
3. A family without available evidence does not imply zero activity, absence of a capability or full market coverage.

### User Story 3 — Recognize an industry use (P1)

A visitor enters by sector and finds practical questions, relevant families, evidence requirements and limitations.

**Independent test**: navigate from the industry hub into each published sector; follow its family and example links and its return path.

Initial sectors: industry/manufacturing; construction/engineering; energy; logistics; professional services/consultancies; agencies/digital communication. These are editorial use contexts, not claimed customer case studies.

1. Industry questions are specific to capacities, delivery and observable context, without claiming guaranteed opportunities or commercial fit.
2. Consultancy and agency journeys support observing multiple organizations under the same product and governed additional-organization price.
3. Public representations are scoped observations, not SEO execution, reputation management, private analytics or a universal digital score.

### User Story 4 — Read and navigate accessibly (P1)

1. Six supported languages retain meaningful localized content and coherent route/metadata behavior.
2. Keyboard and touch visitors can operate navigation and the family/sector explorer with visible focus and correct controls.
3. Content remains accessible without motion; the reading path is available without JavaScript. No scroll hijacking or form-shaped decorative controls.

## Functional Requirements

- FR-001: Home, family hub and sector hub/detail pages share one public identity and explicit cross-links.
- FR-002: Public family content is typed against the existing canonical family IDs/order; labels explain human meaning.
- FR-003: Each family supplies an answerable question, evidence examples and a material limitation, with no coverage guarantee.
- FR-004: Each industry supplies specific decision questions and links to relevant families rather than duplicating generic sales paragraphs.
- FR-005: Preserve `/demo` as the only interactive public example and supported existing deep links.
- FR-006: Reuse governed prices and existing auth/contact status behavior; no new backend, payment activation or fake forms.
- FR-007: New public routes have canonical metadata, language alternatives where published, sitemap coverage and true 404 handling.
- FR-008: Preserve AO-12 named CTAs and existing disabled-by-default status gate; no new tracking authority, identity or cookies.
- FR-009: Scope CSS and components to public marketing; leave canonical dashboard, Admin and AXENT source untouched.
- FR-010: Every new raster has origin/prompt provenance, intentional crops, dimensions and bounded delivery sizes; generated art never substitutes for canonical brand artwork or evidence.
- FR-011: Provide desktop/mobile visual evidence and actual checks; human visual acceptance remains pending until given.

## Edge cases

Unsupported locale/sector/family; missing or unavailable source; unknown financial figures; stale observation; insufficient geographical reach; disabled contact/auth/measurement service; keyboard-only use; reduced motion; 320px viewport; long German headings; direct nested-route entry; no JavaScript. Unknown stays unknown. No absent integration becomes an observed negative.

## Success Criteria

- SC-001: All ten families and six distinct sector journeys are findable from public navigation and verified by deterministic content/routing checks.
- SC-002: No public claim implies synthetic operational data, real customers/results, universal coverage or observed commercial fit.
- SC-003: Primary paths home → family/sector → example/access work at desktop and narrow widths, with no clipped controls or horizontal overflow.
- SC-004: Existing deterministic Python, architecture/governance and frontend gates pass unchanged; existing auth, private and canonical dashboard contracts remain intact.
- SC-005: The chosen composition is implemented, browser-inspected, reviewed and documented; report the actual acceptance stage, not an unearned guarantee of zero regressions.

## Browser-comment refinement — 2026-10-16

Authorized: increase separation before the family strip; replace cross-industry artwork with the approved hero's paper/blue-gray editorial language across its shared consumers; unify Knowledge hub/articles with public header/footer while retaining reading layout and exact language routes; desktop header logo147×43; give login the signup action's width with transparent surface and no stroke; restore the governed weekly newsletter invitation through the existing real channel, preserving independent consent and availability states. No backend/API/consent-authority or private-app changes.

The later request for synthetic testimonials conflicts with public landing contract§13 (fake social proof and fabricated testimonials forbidden), communication strategy§31 and this feature's truth constraints. No synthetic testimonials will be presented as validation; this item is explicitly pending real authorized statements.

Logo followup: the human requires vector originals rather than resized PNG/JPG. Verify approved SVG hash, then reuse its exact two path geometries/transforms/fills inline in the public header/footer. No tracing, live-text substitute, recoloring, canonical asset edits or private Brand component changes. Retain the desktop147×43 box.
