# AXIGNAL Design System Foundations

P0-DS-01 extracts the warm-paper visual foundation measured from the approved
DeepSeek V2 Golden Master. The canonical implementation is in
`apps/web/design-system/`; it defines shared presentation language and generic
controls only. It does not define Subscriber data, AXIGLAND topology, Focus
Trail meaning, evidence admission, provenance, AXENT reasoning, or Timeline
semantics.

## Ownership and layers

- `tokens.css` owns measured, semantic values: paper, ink, brass, semantic
  presentation colors, typography roles, repeated spacing, geometry, attention,
  and motion.
- `global.css` owns the low-level reset, inherited document typography, focus,
  selection, reading defaults, and reduced-motion behavior. CSS cascade layers
  make ownership explicit; global selectors do not encode page layout.
- `primitives.ts` and the primitive layer own a deliberately small set of
  reusable controls: Button, Input, Pill, and Status. Display/body/metadata
  roles are utilities. Tooltips, popovers, sidebars, graph nodes, and cognitive
  interactions remain feature-level until a shared contract is demonstrated.
- `apps/web/reference/p0-ds-01/` is an isolated `TEST_FIXTURE` specimen. Its
  synthetic labels are not canonical observations, evidence, provenance,
  Xeed data, or production Timeline/AXENT state.

The frontend boundary currently has no runtime or component framework. These
assets add no runtime dependency and do not select a rendering framework.
TypeScript is strict and dependency-free for the primitive API. Font files are
not copied from the prototype; the measured font names and safe fallbacks are
preserved, so exact rendering depends on the environment's font availability.

## Token semantics

The paper, ink, and brass values match the active V2 stylesheet. Spacing values
are the repeated V2 intervals (4, 8, 12, 16, 24, 32, 40 px), not a claim that
every V2 measurement is a global token. Component-specific widths and AXIGLAND
geography remain local. The source's 440 ms focus duration and cubic easing are
retained. Microtype stays 9–10 px, with 15 px body type.

Attention is explicit: baseline is normal; muted and de-emphasized use separate
opacity levels; selected uses the source brass wash/stroke; active uses brass
ink; and disabled uses reduced opacity plus native disabled semantics. Faint
ink is reserved for supporting metadata. Contrast remains dependent on the
Golden Master palette and must be reviewed for each future use at its actual
text size and background.

`--ax-epistemic-*` names presentation colors for states AXIGNAL recognizes.
Corroborated and contradicted remain explicitly `reference` colors because
their use in the specimen does not add canonical state contracts. Color is
never the only state cue: Status uses visible text and a shape marker.

## Global-first language support

Shared controls use logical sizing, padding, block borders, and start/end text
flow. Pills can grow and wrap; no fixed English label width is required. Body
line heights remain open for CJK glyphs, metadata tracking is limited to the
mono role, and uppercase is not required for hierarchy. Native text direction
can be supplied by the consuming document or a localized subtree. UI locale,
knowledge presentation language, and source language remain separate concerns;
no control uses visible text as an identity.

RTL applies to UI chrome through document direction and logical properties.
AXIGLAND semantic geography, graph coordinates, and epistemic topology must not
be mirrored as a side effect of RTL.

## Accessibility and behavior

Controls use native elements, preserve browser focus indicators, expose the
disabled state, and inherit readable typography. Under `prefers-reduced-motion`,
shared transition durations collapse to 0.001 ms. This accessibility-required
delta affects only motion duration; it does not change interaction or layout.
The Golden Master feature choreography is not generalized by this foundation.

Accessibility deltas are required but remain pending human visual confirmation:
status text uses higher-contrast ink, epistemic color is carried by a marker
with an adjacent visible label, metadata uses muted ink instead of the Golden
Master's faint tint, and reduced-motion preferences shorten shared transitions.
The measured faint palette remains available for non-text/decorative
attenuation. These changes are classified
`REQUIRED_BY_ACCESSIBILITY_PENDING_HUMAN_VISUAL_CONFIRMATION`; ratios for the
extracted text foregrounds against paper are checked against WCAG AA in the
tests.

## Canonical iconography

The single canonical library for common interface icons is **Lucide**, consumed
as `lucide-react` by a future React/TypeScript product surface. The source
selection is recorded in [ADR-0022](../adr/ADR-0022-canonical-iconography.md).
The current repository has no product web runtime or React package manifest, so
the package is intentionally not installed as an unused dependency. When a
real consumer is introduced, pin its exact published package version and lock
it with that consumer. Import named icons from the package entry points so
production bundlers can tree-shake unused icons. Do not mix Lucide with
Phosphor or another icon set.

The icon grammar follows the existing AXIGNAL design tokens:

- Use `1em` for an icon embedded in a text run, `16px` for ordinary controls,
  and `20px` only for a prominent control with a dedicated slot. These values
  are semantic roles, not per-screen sizing choices; add tokens when a real
  consumer needs them.
- Use outline icons with a normalized 1.5px stroke as the default. Avoid filled,
  duotone, or mixed-weight variants for common controls. A filled treatment is
  permitted only when the product contract assigns a persistent selected state
  and a reviewed icon pair exists; color alone never communicates that state.
- Active and inactive states retain the same icon shape and use the existing
  semantic state tokens plus text or control state. Do not invent per-icon
  colors.
- Put icon and label on the same alignment axis with the existing
  `--ax-space-2` gap. Center control icons in their hit area. Inline icons align
  to the text line; any optical correction belongs in a shared consumer
  primitive, not a screen-specific offset.
- Choose the action or concept before searching for a symbol. When no Lucide
  icon expresses it clearly, use a text label or omit the icon. Do not use
  Unicode glyphs as product iconography.
- An icon-only control needs a programmatic accessible name on the control.
  Hide its icon from assistive technology when that name is on the control.
  A tooltip may supplement the name and must appear on pointer hover and keyboard
  focus; it cannot be the only accessible name. A labeled icon is decorative to
  assistive technology unless the icon conveys additional meaning not in the
  label.
- Preserve the AXIGNAL isotipo and wordmark as governed brand assets; they are
  not replaceable by a library mark.

No `AxignalIcon` wrapper is added while there is no React consumer. At the first
consumer, add only a thin wrapper if it is needed to enforce the source, the
three semantic sizes, stroke, and accessible decorative/meaningful behavior.
It must not become a general icon registry or accept arbitrary icon sources.

### Golden Master iconography debt

The accepted V2 Golden Master contains common-action Unicode glyphs. They are
classified as `IMPROVISED_ICON` and held as
`GOLDEN_MASTER_ICONOGRAPHY_DEBT`; this decision does not authorize changing the
accepted reference:

| Golden Master source | Existing glyph use | Classification | Treatment |
| --- | --- | --- | --- |
| `src/v2/FocusTrail.tsx` | Back/forward/home controls (`←`, `→`, `⌂`) | `IMPROVISED_ICON` | Preserve pending explicit visual authorization. |
| `src/v2/Gov.tsx` | Home and sidebar direction glyphs (`⌂`, `«`, `»`) | `IMPROVISED_ICON` | Preserve pending explicit visual authorization. |
| `src/v2/Field.tsx` | Viewport controls (`+`, `−`, `↻`, `⤢`, `◎`) | `IMPROVISED_ICON` | Preserve pending explicit visual authorization. |
| `src/v2/Meridian.tsx` | Direction glyph (`→`) | `IMPROVISED_ICON` | Preserve pending explicit visual authorization. |
| `src/v2/Reader.tsx` | Action-copy direction glyph (`→`) | `IMPROVISED_ICON` | Preserve pending explicit visual authorization. |
| `src/v2/Logo.tsx` | AXIGNAL isotipo | `AXIGNAL_BRAND_ASSET` | Preserve; governed by brand authority. |
| `src/v2/marks.tsx` | Epistemic state marks | `LEGITIMATE_CUSTOM_SEMANTIC_ICON` candidate | Preserve in the reference; govern before reuse outside it. |
| `src/v2/Field.tsx`, `Evidence.tsx`, `Join.tsx` | Graph wires, minimap, evidence and trend diagrams | Not an interface icon | Preserve as data visualization. |

The listed Golden Master paths are external to this repository and are not
modified by the icon-library selection. Any future migration requires a
separately authorized visual change and human review against the accepted
reference.

## Golden Master validation

The executable reference is `D:\AXIGNAL\UX DEEPSEEK`, active V2 at
`http://localhost:5178/?v=20`. Baseline source evidence is an external SHA-256
manifest over `index.html`, package/build manifests, all `src/v2` source, and
`src/styles/v2.css`; `.env`, generated bundles, and dependencies are excluded
by explicit allowlist. The manifest script and before/after results are stored
outside both repository trees. At 1280 × 720 CSS pixels, the measured V2 shell
is 1280 × 720, left sidebar 252 px, Epistemic rail 88 px (source-exact), AXENT
rail 256 px (20%), central field 772 px, and resting Bottom Context 201.6 px
(28 vh). The active V2 uses paper `#f2eee4`,
ink `#201e19`, body 15 px, and the `0.22, 1, 0.36, 1` easing curve.

The required P0-DS-01 comparison is the same executable reference UI and
viewport before and after applying the extracted global layer. The baseline
states and source manifest are recorded in an external evidence record.
Browser font rasterization may be treated as non-material only where layout,
hierarchy, color, opacity, stroke, radius, density, and transition behavior
remain unchanged. No after-state comparison or visual-equivalence claim is
recorded by this implementation attempt; the acceptance gate remains open.

P0-HFX-00 adds a new, versioned byte-identity recipe for the currently accepted
executable source: [DeepSeek V2 Golden Master Source Manifest v1](GOLDEN_MASTER_SOURCE_MANIFEST_V1.md).
This source identity does not close the visual acceptance gate or replace the
external P0-DS-01 before/after evidence. The unrecovered historical digest is
retained as historical evidence in the v1 record and is not treated as a
reproducible gate.

## Explicitly deferred

No Subscriber production data, real AXENT/provider, real provenance, Timeline
reconstruction, Admin, Landing, localization catalog, or design-system theme
engine is implemented here. Font asset licensing and availability, full CJK/RTL
visual QA across the product, and feature-level accessibility belong to a
subsequent authorized slice.
