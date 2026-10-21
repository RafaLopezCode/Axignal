# Navigation validation

2026-10-21. Mode: PRESERVE. Source base: deployed `8a6c8e93671db7485baf33ebaf0581b0754df825` plus this repair. This records browser evidence, not human visual acceptance.

## Authority and change

Read the AXIGNAL Design Director, design doctrine/governance, Constitution, ADR-0016, architecture/terminology and existing public presentation contracts. No economic meaning changes. Repair selector extraction so the original Dialog body/header survives the focused landing stylesheet; add the requested existing Blog · Knowledge and Contact destinations; keep locale homes, editorial indexes and article language switching distinct; restore the newsletter fragment destination and shared footer entry. Access choices and product/demo availability remain governed by their existing contracts.

Rendered baseline at 548×1244: dialog body padding **0**, header display **block**, title 43.3px. The optimized selector filter retained `.dialog` but dropped its body/header child selectors. [Before](evidence/before-menu-548.jpg).

## Browser verification

Browser: Chromium in Codex IAB, actual production build served at `127.0.0.1:3830`; actual CSS/DOM geometry and native interactions. The production baseline is captured from `https://axignal.com/` at the deployed base revision.

| Coverage | Result |
| --- | --- |
| Landing menu 548×1244 | 500px dialog, 23px horizontal content inset, 27px title, Blog and Contact present. [Capture](evidence/menu-548.jpg). |
| Landing menu 390×844 | 343px dialog inside 375px client area, 16px outer gutters, no clipped close/link. [Capture](evidence/menu-390.jpg). |
| Landing menu 320×568 | 273px dialog inside 305px client area; 543px height; native vertical scrolling for the complete menu. [Capture](evidence/menu-320.jpg). |
| Keyboard on all three menus | Shift+Tab from Close wraps to signup; Tab from signup wraps to Close; Escape closes; focus returns to the opener. |
| Landing header | Six languages × widths 1440, 1401, 1280 and 1024: 24 cases, no overlapping or out-of-bounds header groups. Expanded navigation collapses at 1400px. |
| Catalog/reading header | Six languages × widths 1440, 1519, 1520 and 1280: 24 final cases, no overlapping or out-of-bounds groups after both responsive grid declarations are repaired. |
| Generic public header | Six languages × widths 1440, 1280, 1101 and 1024: 24 cases, no overlapping or out-of-bounds groups; localized labels awaited before measuring. |
| Interior mobile routes | 15 actual routes at 390px: Knowledge index, English article, data, industries, construction, pricing, contact, policy index/privacy/terms/cookies, GDPR, login, signup and demo. No horizontal page overflow. All 14 PublicShell menus expose localized Blog, Contact and signup, and close with Escape. |
| Product demo | Keeps its distinct real product frame, explicit fictional-data notice, AXIGNAL home link and signup path; no commercial menu injected into subscriber navigation. |
| Real journey | Menu Blog → `/es/knowledge`; menu Contact → `/contact`; brand return → `/es`. |
| Language selector | Actual changes to it/en/de/fr/pt/es preserve `#discover` and arrive at the public locale home, never `/landing-lab`. |
| Article continuity | English article → French translation remains the equivalent article; Blog then reaches `/fr/knowledge`. |
| Newsletter | Shared and marketing footer links target the existing home language plus `#weekly-brief`; that section ID now exists. No email/request submitted and no channel activated. |

Additional evidence: [article mobile menu](evidence/article-menu-390.jpg), [contact mobile menu](evidence/contact-menu-390.jpg), [German catalog desktop](evidence/catalog-desktop-de.jpg). Runtime availability of local standalone API channels is separate from navigation; unavailable channels retain their truthful fallback.

## Complete published-header audit

Instrument `AXIGNAL-public-navigation-HTTP/1.0`: crawl actual sitemap locations from the built server, HTML without JavaScript, concurrency 4. **596 URLs**, all 200 with the expected localized editorial-index link, Contact and signup in the public header. Zero faults. This HTTP contract audit complements the rendered route-family matrix; it is not claimed as 596 separate visual reviews.

## Automated gates

- Frontend: **429 passed**, zero skipped; strict TypeScript, six-language inventory (2,786 entries), required SEO tests and production Next build pass.
- New regression coverage checks public language targets against the published sitemap and preserves isolated preview targets. Delivered CSS checks require actual dialog padding and flex header declarations, rather than only the substring `.dialog`.
- Locked Python sync, Ruff format/lint, mypy, **2,723 passed / seven Windows-dependent skips**, Architecture Guard and all governance gates pass. The unchanged skip reasons are documented in spec 109; Linux CI must run before integration.
- Layout detector reports no findings in the repaired landing sources. No suppressions or weakened gates.
- Graphify update is AST-only. Generated graph, scratch outputs, credentials, GSC data and briefing assets stay outside the commit.

## Delivery boundary

Keep previous exact style URLs during cutover/rollback; new styles and their hashes must be served through AXIGNAL's existing public routing file. No wildcard asset ingress, private API exposure or base-only Compose release. Verify the external CSS, mobile menu, public destinations and product acceptance after an authorized production cutover. Human visual acceptance remains pending until the user reviews the evidence.
