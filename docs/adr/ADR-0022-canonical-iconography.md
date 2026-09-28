# ADR-0022: Canonical Interface Iconography

- **Status:** Accepted; package adoption deferred until a product React consumer exists
- **Date:** 2026-09-28
- **Authority:** AXIGNAL Design System; CTO direction in canonical iconography addendum
- **Scope:** Common interface iconography on AXIGNAL product surfaces

## Context

The repository had no accepted icon library. The current product web boundary
has no React runtime or package manifest, and its shared primitives do not
provide icon authority. The accepted external V2 Golden Master includes common
action glyphs alongside AXIGNAL-specific state marks, brand artwork, and graph
visualizations. Those categories need distinct treatment; a library decision
does not grant authority to rewrite the accepted reference.

The candidates were Phosphor Icons and Lucide. Both support React and tree
shaking. Phosphor offers six weights and a larger semantic set, while its
official React guidance warns that barrel imports can increase development
transpilation work unless consumers use recommended import optimization.
Lucide offers a coherent outline family, typed React components, and
side-effect-free ESM package metadata suited to named imports. Exact product
bundle impact is not measurable before there is a consumer.

| Criterion | Lucide | Phosphor | AXIGNAL assessment |
| --- | --- | --- | --- |
| Visual grammar | Consistent outline icons with adjustable stroke | One icon family with six weights | Lucide fits the restrained technical controls and current V2 line language; the single default style limits arbitrary variation. |
| Semantic variety | Broad common interface action set | 9,000+ modules per official React guidance | Phosphor has greater breadth; current AXIGNAL controls do not justify the extra weight choices. Missing concepts fall back to text or no icon. |
| React / TypeScript | First-party `lucide-react`, typed props | First-party `@phosphor-icons/react`, typed React package | Both fit a future React/TypeScript consumer. |
| Tree shaking | ESM and `sideEffects: false`; named imports | Officially supports tree shaking | Both support production tree shaking; Phosphor documents extra development import optimization for its large barrel. |
| Accessibility | Consumer supplies meaning and accessible naming | Consumer supplies meaning and accessible naming | Neither library decides AXIGNAL's action labels, tooltip behavior, or decorative treatment; the Design System contract governs these. |
| Bundle impact | Unused named imports can be removed; product bundle not measured | Tree-shakable, but product bundle not measured | No size comparison is claimed before an actual consumer and build exist. |
| Maintenance | Active upstream; version pin deferred to real consumer | Active upstream | Keep one source, pin the consumer's package version, and review upstream before upgrades. |
| License | ISC package license plus MIT terms for Feather-derived icons in the bundled notice | MIT | Lucide is acceptable when all upstream notices ship with the consumer. |

## Decision

- Select **Lucide** as the one canonical library for common interface icons;
  future React consumers use `lucide-react`.
- Do not install the package in the current Python-first repository because it
  has no product React consumer. At adoption, pin the exact published package
  version in that consumer's package manifest and lockfile, and preserve all
  upstream license notices. The current upstream icon-set release reviewed is
  1.48.0; this is not a substitute for pinning the eventual package version.
- Use named imports so production bundlers can remove unused icons. Do not mix
  Lucide with Phosphor or another common-icon library.
- AXIGNAL's default is a 1.5px outline stroke, with semantic sizes of `1em`,
  `16px`, and `20px`. Filled or duotone styles are not used for common controls
  unless a separately reviewed product contract establishes a selected-state
  pair. Active/inactive meaning must not depend on icon color alone.
- Icon-only controls have an accessible name on the control; their icon is
  hidden from the accessibility tree. Tooltips supplement that name and support
  pointer hover and keyboard focus. Alignment, label spacing, accessible
  treatment, and the full grammar are specified in
  [`DESIGN_SYSTEM.md`](../design/DESIGN_SYSTEM.md#canonical-iconography).
- Do not add a wrapper until a real React consumer exists. Then add a thin
  `AxignalIcon` only if needed to enforce this source and grammar; it is not a
  registry or an ontology.
- The AXIGNAL isotipo and wordmark remain brand assets. Custom icons are
  reserved for AXIGNAL-specific semantics the library cannot express, require
  Design System governance, and are a last resort after semantic search.
- Common Unicode action glyphs already embedded in the accepted Golden Master
  are recorded as `GOLDEN_MASTER_ICONOGRAPHY_DEBT`. They remain unchanged until
  explicit visual authorization. Its epistemic marks remain candidates for
  legitimate custom semantic icons; diagrams and graph edges are visualizations,
  not interface icons.

## Alternatives rejected

- **Phosphor Icons:** rejected as the canonical source. Its broader weight
  range adds style choices AXIGNAL does not need for its current visual grammar,
  and its documented barrel-import development cost is an unnecessary concern
  for a minimal interface set. Its MIT license is simpler, but does not offset
  those tradeoffs for this selection.
- **Keep no canonical library or draw icons individually:** rejected because
  it perpetuates inconsistent sources and improvised common-action symbols.
- **Install `lucide-react` now:** rejected because there is no product React
  consumer; an unused dependency would add maintenance without providing
  product capability.
- **Migrate the accepted Golden Master now:** rejected because this decision
  does not authorize a visual change to that source.

## Tradeoffs

Lucide's outline family provides a deliberately narrow, consistent grammar but
may not contain a semantically suitable symbol for every future AXIGNAL concept.
The fallback is text or no icon; custom semantics need review. The exact bundle
impact remains unmeasured until an actual consumer is built. The package's
composite license notices must be retained with the installed package rather
than summarized as a single upstream license.

## Consequences

The Design System now owns common icon source, stroke, semantic sizes, filled
state constraint, active/inactive treatment, accessibility, tooltips, and
alignment. The Design Director forbids improvised common icons. Existing
Golden Master glyphs are named debt rather than silently changed. No runtime
code, package dependency, or visual output changes in this decision.

## Authority

AXIGNAL product and engineering doctrine remain superior to design guidance.
The selection is informed by the official
[Lucide repository](https://github.com/lucide-icons/lucide),
[Lucide React package](https://github.com/lucide-icons/lucide/tree/main/packages/lucide-react),
[Lucide license](https://github.com/lucide-icons/lucide/blob/main/LICENSE),
[Phosphor React documentation](https://github.com/phosphor-icons/react), and
the explicit CTO iconography addendum. The Golden Master is evidence of accepted
visual output and migration debt, not icon ontology or permission to edit.

## Scope

This ADR establishes the library and usage grammar only. It does not install
packages, implement product controls, change Golden Master assets, define
AXIGNAL epistemic semantics, or close human visual acceptance.
