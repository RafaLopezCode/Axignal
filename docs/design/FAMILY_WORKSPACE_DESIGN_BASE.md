# Family workspace: design base

> Subordinate to the MASTER, `DESIGN_DOCTRINE.md`, `DESIGN_SYSTEM.md` and the Human First doctrine (ADR-0016). This base fixes the direction. Where it conflicts with them, they win. This document adds no runtime code.

**Accepted by the CTO** on 2026-10-17 as the design base for the subscriber workspace. The instruction was: "se debe adaptar perfectamente a la UX más perfecta para Axignal".

**Reference comp:** a private canvas, "AXIGNAL Dashboard Motion" (version "Base de diseño v1"), owned by the CTO. It shows the Visibilidad family with the GEO measurements of 17-10-2026 for four public SEO/communication agencies.

## Why
SEO/GEO agencies and consultancies follow 10 to 20 clients each. Every family has to read as richly as a specialist tool, not as a lane of cards in a summary ("extremadamente potentes en cada familia"). Each family therefore gets a full-canvas page, with charts, trends, thumbnails and cards, inside one workspace.

## Layout (three regions)
1. **Left menu**, top to bottom:
   - the isotipo and wordmark;
   - the **organization selector**, a native `<select>` with a visible label, listing the subscriber's observed organizations;
   - the **"Añadir organización"** primary action;
   - a divider;
   - the **ten families**, each with its own dot, and Visibilidad's SEO, GEO / IA and Web channels.
2. **Family canvas** (centre):
   - **Header:** family eyebrow, organization name, one-line scope, actions.
   - **Measures:** 3 to 5 measures, each with its value and its basis line.
   - **Charts:** two rows of analytic panels, each with a title and a conditions line (sample, instrument, date).
   - **Evolution:** compared only under the same instrument.
   - **Pending measurement:** shown explicitly, never as zero.
3. **Axent panel** (right):
   - collapsible, opened and closed from the header;
   - an opening message that summarizes what was measured for this organization;
   - suggested questions about the current family and organization;
   - a free composer.

## Motion (keep, with these rules)
- **Kinds of motion:**
  - staggered rise of cards on first view;
  - bars that grow;
  - a share-of-voice ring that fills;
  - numbers that count to their value;
  - future measurement points that pulse;
  - the Axent panel slides in, messages rise, and a three-dot "typing" indicator shows while it answers.
- **Timing:** durations and easing come from `--ax-motion-*`. Focus motion is 440 ms with `cubic-bezier(0.22, 1, 0.36, 1)`. A count-up lasts 800 ms at most.
- **When it plays:** on first view and on a change of organization or family only, never on every re-render or poll.
- **`prefers-reduced-motion`:** final values at once and no pulse.
- **Screen readers:** never announce intermediate values. The final value lives in the accessible name, and live regions are only for Axent's replies.
- Motion never carries meaning that the static page lacks.

## Adaptations required before it ships (the base comp does not yet meet them)
1. **Epistemic state on every value.**
   - Each measure, chart and Axent statement carries its state (OBSERVED, POTENTIAL, UNKNOWN, STALE or HISTORICAL) as a marker plus a visible word, never color alone.
   - Never imply UNKNOWN = FALSE, POTENTIAL = OBSERVED or inference = fact.
   - "Pendiente de activar" is UNKNOWN, not zero.
2. **Every element links to its proof** (GLANCE → UNDERSTAND → REASON → PROVE). Each measure and chart opens "Cómo lo sabe AXIGNAL", with its instrument, conditions, date, sample, uncertainty and source links. These are the existing `basisRows`.
3. **No universal score and no counts without data.**
   - Family dots carry no number until a real count exists (`family-nav` rule).
   - Charts show only stored measurements, and missing ones are labelled.
4. **Reuse what exists; do not fork it.**
   - `family-nav.tsx` keeps owning family and channel selection, which travels in the URL together with the organization and the view.
   - The Summary, Evolution and Evidence views stay as views of the family canvas.
   - Axent reuses `axent.tsx` and `axent-composer.tsx`.
   - Copy goes through `t()` in 6 languages, with locale-formatted numbers.
5. **Axent never carries comprehension** (DESIGN_DOCTRINE).
   - The canvas is complete with the panel closed.
   - Answers restate stored findings with their evidence links and never invent causes.
   - Free questions go to governed research or to an explicit abstention.
   - Suggested questions derive from the current family's findings, never from canned copy.
6. **Organization actions.**
   - The selector lists the subscriber's portfolio.
   - "Añadir organización" opens the existing add-Focus flow with its entitlements and checkout.
   - There is never an "edit company profile" action: reevaluation, not editing.
7. **Family colors.**
   - One hue per family at equal perceived lightness and chroma: `oklch(0.58 0.13 h)`, hues 36° apart. This gives at least 3:1 against white for non-text contrast.
   - The name always sits beside the dot.
   - Promote the colors to `--ax-family-*` tokens; do not hard-code them.
8. **Responsive.**
   - Under 1024 px the Axent panel becomes a bottom sheet.
   - Under 768 px the left menu becomes a top drawer, with the organization selector first.
   - Targets are at least 44 px. Wide tables scroll in their own box.
9. **Palette.** The subscriber workspace's blue (`#354F98`, the isotipo blue) over white cards stays the operational palette. The warm-paper Golden Master remains the brand and AXIGLAND layer, and the two must not be mixed inside one panel.

## Per-family canvas (to design next, same base)
Every chart states its conditions and every value its state. Families:
- **Visibilidad:**
  - AI share of voice;
  - who is named instead;
  - search positions per query, with a link to see the search on Google;
  - web audit by section;
  - Core Web Vitals.
- **Reputación:** press over time, by outlet, with the attribution path; review profiles.
- **Valor:** offer map with its declared evidence; credentials.
- **Mercados:** map of premises and reach; countries of its group.
- **Relaciones:** clients, partners and competitors as a graph that keeps OBSERVED, DECLARED and POTENTIAL apart.
- **Demanda:** best fit versus other possible, deadlines on a timeline, scale.
- **Actividad:** changes over time; publications and hiring.
- **Economía:** stated figures with their source and year; unknowns explicit.
- **Organización:** identity anchors and their agreement.
- **Contexto:** regulation and sector headlines with dates.
