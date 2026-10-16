# Human typography, control and logo followup — 2026-10-16

Scope: localized newspaper headlines, outlined login, equal SVG logo dimensions and untruncated locale selector. Six languages unchanged; Fraunces and all product meanings preserved. Public CSS/MarketingFooter only; private interfaces, auth and backend untouched.

Newspaper band centers are measured on the1931×814hero master: (898,420), (1229,463), (1620,444). Percentage centers46.5/63.65/83.9 and51.6/56.9/54.5; translate(-50%,-50%) and10/4.5/-8.5degree rotations. Longer right headings use existing smaller localized display role, without clipping, truncation or substituted wording. The first preliminary approximation was superseded after the user's centering screenshot; only confirmed captures are published here.

Header/footer share the exact canonical vector component and dimensions147×43desktop,142pxmobile/124pxnarrowmobile with automatic height. Login148×49transparent with1px#354f98outline; locale select112px/native arrow/padding8px. Existing native interaction, routes and keyboard access remain.

24real-app DOM checks: six languages at320,390,1280,1650px; no tested page overflow/header overlap, equal logo geometry/two paths/no raster, centered label positions and no measured title overflow on both desktop sizes. At mobile the existing linked reading fallback remains. Portuguese mobile menu was opened and captured;112pxselect shows the entire name. Full-page capture includes the actual global footer. No backend mutation or newsletter request.

349frontend tests, production build, TypeScript,6real HTTP contracts, Architecture Guard and8Governance categories pass. Graphify AST22490nodes/66462edges. Full Python baseline2461passed remains unchanged; no backend change. No new detector run. Final human visual acceptance remains pending; historical CLI checkpoint OPEN under previously authorized real-app override. No merge or deployment.
