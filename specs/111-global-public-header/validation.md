# Global public header — verification

2026-10-21. Base `b123c244dd6eff82ad31705f3260b035612293eb`. MODE: EXTEND. Browser evidence below covers application revision `dc5514ab019baee8a9f5bc494e61f07d77fe6a84`; human visual acceptance remains pending.

## Change and authority

The owner explicitly requested one global public header and an authored desktop hamburger menu when links crowd the bar. Governing authority: Constitution, architecture/terminology, ADR-0016, design doctrine/governance, incumbent brand/type assets and Design Director; no product-semantic change. The previous presentations are documented in spec110. LandingLab and PublicShell now render the same PublicHeader outside their page skins. The catalog variant and old landing navigation/observer are removed. MarketingShell, articles, trust/contact and access retain their actual body/footer and locale-route contracts. Product/demo navigation is unchanged.

The bar contains brand, outlined sign-in, start CTA and explicit Menu control, with access actions moving inside at narrow widths. A native non-modal details/summary panel groups landing chapters, deeper public pages, trust/newsletter links, language and conversion. Desktop uses two columns, mobile one scrollable column; the summary remains outside that scroll region. No new animation library, modal focus trap, body scroll lock, endpoint or credential. Escape/outside/focus dismissal and language-focus return were exercised in the real browser as recorded below.

## Automated evidence

- Node22.23.3 application checks: **431 frontend tests**, zero skipped; strict TypeScript; language inventory2780 with no missing entries; **19 SEO tests**; production Next build; **28 admin transport HTTP tests**, all passed. After the last focus/contract changes, targeted funnel/navigation14 tests, types and production build repeated successfully.
- One scoped header stylesheet is included in existing deterministic base/legacy/lab assets. No additional blocking stylesheet request. Landing wire CSS **13,999 bytes gzip** using Node22, against the unchanged strict14,000-byte budget. Prior production CSS was13,937 bytes. No budget or test weakened.
- Existing funnel safety tests now scan the extracted header and its destination model. New checks require actual published/noindex routes, real section IDs, six languages, preview isolation, one shared component outside page skins and delivery of native-menu CSS in every surface asset.
- Locked Python sync, Ruff format/lint, mypy, Architecture Guard and governance passed. Full Python run:2722 passed, seven unchanged platform/optional skips, one repository-boundary failure caused by deliberately invalid test fixtures left under this checkout by an earlier sandbox probe. Those owned temporary fixtures were moved outside the repository; all three boundary tests and standalone Architecture Guard/governance then passed. This is reported transparently, not presented as an initially clean full-suite run. Clean full CI is required before integration.
- The seven existing Windows skips: POSIX file-mode contract; POSIX production ownership; four POSIX scheduler deployment tests; optional TypeSafe SDK. No skips added and no suppression introduced.
- Graphify AST update completed. Layout detector on the new header TSX/CSS returned `[]`; this cannot prove rendered hierarchy or responsiveness.

## Built HTTP integration

Instrument `AXIGNAL-global-header-HTTP/1.0`: actual final production build, Node22 local server, HTML without JavaScript, concurrency4. **604 routes**:596 sitemap URLs plus contact, policy index/privacy/terms/cookies, GDPR, login and signup. Every response200, exactly one global header, required native details/summary and public destinations. After removing route-specific current-location attributes and React-generated IDs, complete header HTML has **one identical signature per language across all route families**. Zero faults and zero divergent language groups. This establishes shared server output, not604 visual reviews.

Raw operational outputs are ignored under `.tmp-nav-20261021/`: frontend22 log, final build, targeted tests, Python run and boundary recheck, architecture/governance, Graphify, design scan and604-route HTTP JSON. They contain no briefing images or private Search Console data.

## Rendered browser evidence — access restored

Browser access was initially refused by policy. A subsequent auto-review rejection identified missing explicit permission to access the local origin. The owner then explicitly authorized browser access to `http://127.0.0.1:3830`. The same in-app browser acquired that origin successfully; no alternate browser, raw protocol or security bypass was used.

Instrument: Codex in-app browser, real local Next production build, CUA native/Playwright UI actions and read-only DOM inspection. Viewports: desktop1365×1244, tablet768×1024, mobile390×844 and320×740 CSS pixels. Viewport overrides were reset and the original movement preference restored afterwards. The browser screenshot API returned images with dimensions different from the CSS viewport; both are recorded in the manifest. No images were resized, retouched or generated. [Evidence index](evidence/README.md) records exact routes/states and checksums.

- Visually inspected closed/open desktop, two-column tablet, narrow single-column menu and its scrolled access/language area. Mobile panel has24px internal horizontal padding. No horizontal document overflow or clipped menu links at320px in any of the six languages; these six-language geometry checks are not six complete visual page reviews.
- Actual journeys: Spanish preview → blog → article → equivalent German article → data catalog → contact; contact language change → Spanish public home; public pricing anchor → Italian equivalent preserving `#pricing`; Newsletter anchor; access route; browser Back/Forward. The same header geometry remains on these representative page families. Header count stays one and menus close after navigation.
- Enter and Space activate the native disclosure; Tab enters the first chapter and proceeds through language/sign-in/start to page content; focus leaving closes the panel without a trap. Escape closes and returns focus to summary. Pointer outside closes it. At390px, scrolling the panel moved its scrollTop to205 while page scroll remained0 and summary top stayed12px.
- The pricing anchor settles below the sticky header (section top115.19px, header73px on390px viewport). Article translation stays an article; all six preview language changes stay within `/[locale]/landing-lab`. The app's movement-reduction control was enabled during menu interaction: header elements had no animations or transitions; the preference was restored. OS-level media emulation was not performed.
- Browser console inspection reported no captured warnings/errors for the inspected journeys. Contact showed its existing unavailable-channel fallback because this local frontend has no active contact backend; no form was submitted or channel activated. This verifies navigation and fallback rendering, not contact delivery or authentication.
- Actual landing DOM serves the existing single `/styles/lab.954551f31da3.css` stylesheet. Combined with the unchanged strict wire-size budget, this bounds stylesheet overhead. **No new Lighthouse run, LCP/TBT comparison or real INP was measured for this header revision**; no quantitative performance non-regression claim is made. Prior landing reports remain historical evidence only.

No additional header defect was established in this bounded review, so no subjective source changes were added. CI's four mandatory checks (frontend, deterministic validation, Graphify structural and secret scan) passed on application revision `dc5514a`. No accepted Golden Master is updated and automation does not grant visual acceptance.

STATUS: IMPLEMENTED + AUTOMATED_QA_PASS + BROWSER_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING. [Draft PR363](https://github.com/RafaLopezCode/Axignal/pull/363). Production remains on the previous release; no merge or deployment was performed. Reviewable local preview: `http://127.0.0.1:3830/es/landing-lab`.
