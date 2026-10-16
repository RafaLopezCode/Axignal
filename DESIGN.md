---
name: AXIGNAL public landing ecosystem
description: Scoped record of the implemented public-understanding folio; subordinate to canonical AXIGNAL authorities.
colors:
  marketing-blue: "#354f98"
  marketing-action: "#21479f"
  marketing-ink: "#101727"
  marketing-muted: "#52617b"
  marketing-paper: "#f8fafc"
  marketing-line: "#dce4f2"
  marketing-tint: "#eaf1fc"
  action-hover: "#293f7f"
  button-secondary: "#fbfcfe"
  button-secondary-line: "#bdcbe6"
  annotation-ink: "#183c80"
  surface-white: "#fff"
  pricing-paper: "#edf2fb"
  evidence-paper: "#edf2fa"
  pricing-rule: "#c7d4e9"
typography:
  display:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(52px, 5vw, 86px)"
    fontWeight: 400
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(36px, 4.1vw, 64px)"
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "33px"
    fontWeight: 400
    lineHeight: 1.2
  body:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.75
  control:
    fontFamily: "Manrope, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.5
  advisory-title:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(32px, 3vw, 46px)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  advisory-price:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(48px, 4.2vw, 68px)"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.025em"
  folio-label:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(18px, 1.75vw, 30px)"
    fontWeight: 400
    lineHeight: 1.1
  folio-right-localized:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: "clamp(17px, 1.4vw, 26px)"
    fontWeight: 400
    lineHeight: 1.1
  annotation:
    fontFamily: '"Bic Notes", cursive'
    fontSize: "clamp(22px, 1.8vw, 29px)"
    fontWeight: 500
    lineHeight: 1.1
rounded:
  shortcut: "9px"
  control: "12px"
  illustration: "14px"
  calculator: "16px"
  circle: "50%"
spacing:
  gap-12: "12px"
  gap-16: "16px"
  mobile-gutter: "22px"
  inset-24: "24px"
  inset-26: "26px"
  inset-30: "30px"
  inset-32: "32px"
  inset-36: "36px"
  family-separation: "36px"
components:
  button-primary:
    backgroundColor: "{colors.marketing-action}"
    textColor: "{colors.surface-white}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "15px 24px"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
    textColor: "{colors.surface-white}"
  button-secondary:
    backgroundColor: "{colors.button-secondary}"
    textColor: "{colors.marketing-blue}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "15px 24px"
  button-secondary-hover:
    backgroundColor: "{colors.marketing-tint}"
    textColor: "{colors.marketing-blue}"
  advisory-panel:
    backgroundColor: "{colors.marketing-blue}"
    textColor: "{colors.surface-white}"
    rounded: "{rounded.calculator}"
    padding: "clamp(30px, 3.3vw, 48px)"
  button-advisory:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.marketing-blue}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "15px 24px"
  button-advisory-hover:
    backgroundColor: "{colors.marketing-tint}"
    textColor: "{colors.marketing-blue}"
  newsletter-channel:
    backgroundColor: "{colors.surface-white}"
    rounded: "{rounded.calculator}"
    padding: "32px"
  public-brand-header:
    width: "147px"
    height: "43px"
  public-brand-footer:
    width: "147px"
    height: "43px"
  public-locale-select:
    width: "112px"
  header-login:
    backgroundColor: "transparent"
    textColor: "{colors.marketing-blue}"
    rounded: "{rounded.control}"
    width: "148px"
  evidence-panel:
    backgroundColor: "{colors.evidence-paper}"
    rounded: "{rounded.control}"
    padding: "26px 30px"
  pricing-calculator:
    backgroundColor: "{colors.surface-white}"
    rounded: "{rounded.calculator}"
    padding: "36px"
  price-shortcut:
    backgroundColor: "{colors.surface-white}"
    textColor: "{colors.marketing-blue}"
    rounded: "{rounded.shortcut}"
  price-shortcut-selected:
    backgroundColor: "{colors.marketing-blue}"
    textColor: "{colors.surface-white}"
---

# Design System: AXIGNAL public landing ecosystem

## Overview
**Creative North Star: "Public-understanding folio"**

An annotated public document pairs AXIGNAL editorial type with cool paper, dark ink and blue observation marks. The approved white Observador and his monocle explain the offering; the illustration remains explanatory artwork, never evidence or a real customer observation.

Precise public controls sit alongside spacious reading sections, native disclosures and rule-separated catalogs. This records the implemented public landing ecosystem only: home, data catalog, industry hub and cases, pricing, public Knowledge hub/articles, newsletter channel, and their scoped public shell. It establishes no visual authority for the private app, Admin or AXENT.

**Key Characteristics:**

- Canonical AXIGNAL identity and calm blue controls.
- Fraunces reading hierarchy with Manrope controls and Bic annotations.
- Tonal paper sections and fine rules rather than elevated cards.
- Responsive public navigation and explicit evidence/limit explanations.

This is a scan-mode implementation record, not new global design authority. Source: `apps/web/experience/components/marketing.css`, `landing.tsx`, `marketing-{home-body,pages,shared}.tsx`, and public shell inheritance in `app/{globals,typography,public,public-layout,funnel}.css`. Direction: `.impeccable/questions/selected-direction.md`. Product context: `PRODUCT.md`; binding identity: MASTER §4.8, `docs/design/BRAND_ASSET_AUTHORITY_V2.md`, ADR-0022 and existing design governance. The root location is for tooling discovery, not global scope.

## Colors

The public palette uses AXIGNAL blue and action blue over cool paper, with dark ink for reading and muted ink for support. Frontmatter owns the extracted values; names retain the marketing stylesheet's boundary.

### Primary

- **AXIGNAL blue:** identity, navigation, observation symbols, selected shortcuts, keyboard outlines and the distinct human-advisory service panel.
- **Action blue:** primary public calls to action; the deeper action-hover tone supplies the implemented hover state.
- **Annotation ink:** handwritten explanatory links above the folio.

### Neutral

- **Dark ink / muted ink:** primary and supporting reading text.
- **Cool paper / white:** base surface and alternating reading regions.
- **Blue tint / pricing paper / evidence paper:** quiet separation of controls, pricing and evidence explanations.
- **Fine rule / pricing rule / secondary-control line:** section dividers and explicit control boundaries.
- **Secondary-control paper:** the quiet alternate action surface.

**The Public Scope Rule.** Apply this record only inside the public landing ecosystem. MASTER, Constitution, accepted ADRs and canonical brand/design authorities win on conflict.

## Typography

**Display Font:** Fraunces, with Georgia and serif fallbacks. **Body Font:** Manrope, with Arial and sans-serif fallbacks. **Annotation Font:** Bic Notes, with cursive fallback. These same font families remain locally served. Public Manrope and Bic Notes now use full-coverage WOFF2 exports (53,800 and 173,748 bytes respectively), preserving original cmap, metrics and variable axes; original TTFs and licenses remain. Fraunces WOFF2 is unchanged. Only Fraunces and Manrope are preloaded as the two critical faces. This is delivery optimization, not a type or brand substitution.

The frontmatter records the desktop hero, recurring section headline, audience title, section body, marketing action and annotation roles. These are observed roles, not a new universal scale. The public body normally reads at 70ch maximum. Catalog paragraphs use a 72ch maximum and a roomier line height (1.8); supporting text and captions use smaller contextual sizes.

The hero enters reading flow below 1280px, with display size `clamp(37px, 9.1vw, 60px)` and wrapping text spans. Public page intros use their own display size (`clamp(44px, 5.2vw, 78px)`, mobile 43px). At desktop widths from 1280px, Italian/French hero text uses `clamp(39px, 4vw, 76px)`; Spanish uses `4.9vw` between 1280px and 1439px. These corrections keep localized text inside its composition. The advisory title and price have their own contextual roles in the frontmatter; the price reduces to `clamp(38px, 10vw, 52px)` at 760px and below. The approved headline arrangement remains local to the hero.

**The Annotation Meaning Rule.** Use Bic handwriting for explanatory observation annotations; retain semantic text links and keep decorative connectors outside the accessibility tree.

## Layout

Full-width paper regions alternate with generous reading sections. Desktop section gutters use `max(5%, calc((100vw - 1320px) / 2))` and vertical padding (100px). The data catalog uses a sticky index beside a flexible article column; its container maximum is 1450px. Intro copy caps at 1500px. Supporting text stays measured rather than filling the viewport.

At 1279px and below, desktop navigation becomes a menu, the hero enters normal reading flow, section padding reduces to 75px, and the family strip changes from ten columns to five. Hero annotations become three text columns beneath the cropped illustration; desktop folio labels and connectors disappear. At 480px and below, annotations become three stacked rows, each pairing the title with supporting copy in a two-column `1fr / 1.5fr` grid (16px column gap and 18px row gap). From 761px through 1279px, hero art height uses `clamp(330px, 43vw, 480px)` and the family opening uses 45%/remaining columns, keeping the folio clear of the next section. At 760px and below, reading columns stack, the family strip becomes two columns, the sticky catalog index becomes a static two-column index, and section padding becomes 58px with the mobile gutter token. The family strip begins 36px after its introduction at desktop/tablet widths; the existing mobile rule resets this margin. From 1280px through 1519px, the compact desktop header uses `20% minmax(0, 1fr) auto` columns, a 1.5% column gap, 24px navigation gaps and 14px action gaps. The 380px rule tightens only the public header. A 1700px minimum rule adjusts the desktop hero copy position.

The 1505/635 hero canvas and positioned folio labels belong to the selected surface composition; do not reuse them as global layout primitives. Public Knowledge hub and articles use `MarketingShell` with `marketing-reading` and their existing locale route arrays; their reading gutters are preserved by excluding that class from the catalog full-width main override. The root application layout is unchanged. Knowledge cards explicitly use `min-width: 0`, `overflow-wrap: anywhere` and `hyphens: auto` inside this public reading shell so localized compound words can wrap without widening the grid. Shared public-shell styles also hide sign-in and header languages below 800px; the menu retains those destinations.

## Elevation & Depth

Paper tone, whitespace and fine rules carry the reading hierarchy. `marketing.css` adds no box shadows. Shared public dialog primitives retain their existing modal depth, and the inherited back-to-top utility uses a soft shadow (`0 8px 22px -12px rgb(20 28 58 / 40%)`). These exceptions do not authorize exporting raised treatments to public reading cards or changing the dialog system.

**The Flat Reading Rule.** Use paper tones, whitespace and rules for public reading sections; the marketing stylesheet adds no card shadows.

Hero text is crisp at first paint: the previous arrival animation, blur and vertical translation have been removed. Actions transition color over 0.18s; disclosure plus icons rotate over 180ms ease-out. Reduced-motion rules remove transitions and animation. Exact motion and breakpoints live in the sidecar, outside the token schema.

## Shapes

Controls use gently rounded corners; pricing shortcut, marketing action, illustration and calculator radii are distinct frontmatter tokens. Family symbols are circular. Evidence panels share the action radius. Most audience, catalog and industry content stays open with fine separators rather than enclosing every paragraph in a card. Curved blue SVG connectors are decorative diagram geometry, not interface glyphs or evidence states.

## Components

### Buttons

The primary action uses action blue, white text, the control type role and rounded control shape. A darker hover tone gives feedback without lifting the button. The secondary action uses quiet paper with a fine blue-gray border, becoming blue tint on hover. Desktop marketing actions have minimum height (58px); at the tablet breakpoint it becomes 48px with tighter padding and type, and mobile padding becomes 13px 16px.

Keyboard focus on public links, buttons, summaries and selects uses a blue outline (3px) offset by 5px. Inputs use the same width with a 4px offset. These selectors are scoped to the marketing surface; preserve the actual stylesheet cascade when extending the public shell.

### Cards / Containers

The calculator is a white inset panel with the calculator radius and desktop padding token; padding reduces to 26px at tablet width and 24px on mobile. Evidence explanations use tinted paper, the control radius and two-axis inset. Neither adds a marketing shadow. Audience and related-item content use rules and measured spacing.

### Human advisory

The separate human service has a canonical-blue panel with white Fraunces heading and prominent white price. Supporting copy and conditions use blue tint on blue. Its two-column grid uses `minmax(0, 1.35fr) minmax(0, 1fr)` with 36px/8% gaps, balanced vertical alignment and calculator-radius corners. Padding is contextual (`clamp(30px, 3.3vw, 48px)`). At 760px and below it becomes one column with padding (30px 24px), and its white CTA fills the available width.

The inverted action reads “Hablar del alcance” in Spanish, retains the real `/contact` destination, and changes to blue tint on hover. Its keyboard outline is white on the blue panel. This is a presentation emphasis for the existing separate service; amount, conditions and scope remain governed by application content and commercial authority rather than design tokens. The explicitly amended MASTER §27.4 sets the human service launch price to €295/month plus applicable VAT; the self-service base/additional prices remain unchanged. This amount is not a visual token.

### Inputs / Fields

Pricing uses a native labeled range input, full width with blue accent, a visible numeric output and a 36px input box. Shortcut buttons show selection with `aria-pressed`, blue fill and white text. There is no new text-field component in this ecosystem; do not invent a public form style from the calculator.

### Navigation

The compact canonical logo anchors the public header through `PublicBrandVector`, which embeds the original two SVG paths, groups, transforms and fills from the approved `Logo_Claro.svg`; it is never traced or converted through PNG/JPG. The same vector component renders in `MarketingFooter`; both placements use its default dimensions (147px × 43px) and shared responsive CSS variables. Its SVG is decorative inside the existing accessibly named brand link. Only these public consumers change; private `ui.tsx`/`Brand` and the canonical source SVG remain untouched. At 761px and above its rendered inline SVG box is exactly 147px × 43px with `object-fit: contain`; header and footer both use `--marketing-brand-width` / `--marketing-brand-height`. These become 142px / auto at 760px and below, then 124px / auto at 380px and below. Login and signup each use a 148px width and minimum width with 18px inline padding at those widths. Login is transparent with a one-pixel AXIGNAL-blue outline, with an underline on hover; signup keeps the primary action treatment. Desktop public links have 44px minimum interactive height; current location uses an underline. The marketing header is opaque and positioned relative, without its shared shell's backdrop blur. Below the navigation breakpoint, the existing accessible dialog carries public navigation and locale selection. The public native locale selector has width and minimum width (112px) with 8px inline padding; its label does not shrink. This preserves room for the native arrow and full locale names such as Português. The override is scoped to the marketing locale-route selector and establishes no private control rule. Footer links remain quiet blue text with hover underlines, including the localized home Newsletter fragment.

### Industry disclosures and family links

Native `details`/`summary` rows retain keyboard and no-script behavior. Fraunces summary text sits between fine rules; the Lucide plus rotates when expanded. Family links use the canonical outline icon family and include textual names and explanatory questions. Their circular icon grounds aid navigation without inventing new semantic states.

### Newsletter availability channel

The home page embeds the existing `WeeklyBriefChannel` in its `marketing` variant, within a two-column pale-paper section. The state panel and conditionally enabled form are white, with the calculator radius and inset-32 token; at 760px and below, columns stack with a 32px gap and panel padding becomes 26px 22px. Status titles use Fraunces (28px, 1.2); supporting state copy uses Manrope (15px). The retry action is an underlined blue text button; status feedback uses a polite live region.

Availability is real application state: checking, paused (`enabled === false`) or unavailable (`null` after checking). Only `enabled === true` reveals the existing request form and its separately optional, revocable newsletter consent. Retry checks availability again; it does not submit a request. This is the existing AO-15/AO-16 channel with no new backend authority or guarantee of research, acceptance or delivery. The footer links to its home fragment. Do not infer active availability from this visual record.

### Industry illustration

The shared `industries.webp` is a conceptual editorial panorama regenerated through ImageGen from the previous scene and approved hero references. Its provenance is recorded in the adjacent JSON; ivory paper, blue-gray ink/wash and the canonical white Observador align it with the hero. Preserve the whole scene in every public consumer: full width, automatic height, and contain behavior where specified. Do not reintroduce fixed-height/mobile cover crops or treat depicted facilities as observed customers. These image colors describe artwork; they do not expand the interface token palette. Public delivery uses six hashed small WebP derivatives (640/960/1440 for each of hero and industry artwork), plus two hashed full-size files copied byte-identically from the approved originals. The full scene, brand vectors and folio geometry remain unchanged. Only the ten explicitly allowlisted hashed image/font URLs receive year-long immutable caching. Public Next links disable speculative prefetch; navigation still loads the same destinations on demand. These are resource-delivery decisions, with no field Core Web Vitals or search-ranking claim.

### Public-understanding folio

The approved white Observador reads the large document. Three handwritten semantic links lead to the relevant family fragments; the labels are HTML text, with decorative blue paths drawn behind them. The three newspaper headlines use centered text and centered transform origins inside their own paper columns, independent of translation width. The centers were measured on the 1931 × 814 artwork master at (898,420), (1229,463) and (1620,444). The CSS horizontal centers are 46.5%, 63.65% and 83.9%, widths 13.8%, 15.6% and 18%, vertical centers 51.6%, 56.9% and 54.5%, and rotations 10°, 4.5° and −8.5°. Each uses `translate(-50%, -50%)` before rotation, centering both axes on the measured paper band. The folio-label type role applies to these headlines; the right headline uses the smaller localized role for English, German, French and Italian. Copy, translations and meaning are unchanged. This geometry is local to the approved folio, not a reusable global column system. The artwork and connector geometry explain attention, never establish economic truth. The hero remains a surface-specific signature rather than a mandatory template for every public page.

The confirmed real-app evidence is recorded in `.impeccable/review/final/hero-localization/{packet.md,captures.json,geometry.json}`: six languages across 320px, 390px, 1280px and 1650px, 24 geometry records and 11 hashed captures, including confirmed locale views, compact/mobile/menu and the full page with footer. The saved checks show no tested page overflow or header overlap, matched two-path/no-raster logos and measured headline centering. This is implementation evidence; final human visual acceptance remains PENDING and historical CLI remains OPEN. Latest release refinement evidence is separately recorded in `.impeccable/review/final/release/` with source manifests under `specs/077-public-landing-ecosystem/performance/`; it preserves the same visual system.

## Do's and Don'ts

### Do:
- Do preserve the canonical monocle logo, AXIGNAL blue and approved Observador artwork; public logos use the original inline SVG vectors without raster intermediates.
- Do pair Fraunces headings with Manrope reading and controls.
- Do preserve semantic links, native disclosures, visible keyboard focus and textual state cues.
- Do keep evidence types and limits visible in the family catalog.
- Do reflow annotations and reading columns for narrow screens and respect reduced motion.

### Don't:

- Don't apply these public composition tokens to the private app, Admin or AXENT.
- Don't turn artwork, surface output or a capability match into observed business truth.
- Don't infer pricing, access, customer results or source coverage from a design example.
- Don't fabricate testimonials, customer counts or outcomes; Landing Contract §13 requires real evidence.
- Don't turn a local layout, decorative annotation or existing kicker into a universal product rule.
