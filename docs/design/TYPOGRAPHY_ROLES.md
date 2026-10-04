# Shared typography roles

Authority: DESIGN_DOCTRINE and the accepted AXIGNAL product grammar. This is
presentation guidance; it does not alter product or epistemic authority.

The application imports `apps/web/experience/app/typography.css` after its public
and product styles. New controls should use these semantic tokens or utilities
instead of introducing a local size/weight for the same role.

| Role | Family | Size | Weight | Purpose |
| --- | --- | --- | --- | --- |
| Reading | Manrope | 14px | 400 | Explanations and conversation |
| Control | Manrope | 13px | 500 | Navigation, questions, actions, inputs |
| Emphasis | Manrope | Inherited role | 600 | Active navigation and context name |
| Metadata | Manrope | 11px | 400 | Secondary context and dates |
| Section label | IBM Plex Mono | 10px | 400 | Short section and scope labels |
| Panel title | Fraunces | 24px | 400 | Editorial panel invitation |

Utilities: `type-body`, `type-control`, `type-meta`, `type-label`,
`type-panel-title`. Tokens also govern existing selectors in Admin, subscriber,
AXENT and public navigation/forms. Large page titles retain their existing
responsive editorial scale. Handwriting retains its narrative role.

Equivalent roles have the same family and weight across containers. A sidebar
is not a reason to make a question smaller than a navigation item. Responsive
layout may change spacing or wrapping, not the meaning of typography.
Maintain 44px control targets independently of font size.

This consolidates the shared roles rather than claiming every historical CSS
declaration has been removed. Future local overrides must justify a different
semantic role. Browser evidence compares computed styles, not only screenshots:
`apps/web/experience/qa/037-customer-zero/unified-admin-chrome/typography.json`.
