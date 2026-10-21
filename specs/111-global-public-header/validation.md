# Global public header — verification

2026-10-21. Base `b123c244dd6eff82ad31705f3260b035612293eb`. MODE: EXTEND. This is implementation/technical evidence, not rendered or human visual acceptance.

## Change and authority

The owner explicitly requested one global public header and an authored desktop hamburger menu when links crowd the bar. Governing authority: Constitution, architecture/terminology, ADR-0016, design doctrine/governance, incumbent brand/type assets and Design Director; no product-semantic change. The previous presentations are documented in spec110. LandingLab and PublicShell now render the same PublicHeader outside their page skins. The catalog variant and old landing navigation/observer are removed. MarketingShell, articles, trust/contact and access retain their actual body/footer and locale-route contracts. Product/demo navigation is unchanged.

The bar contains brand, outlined sign-in, start CTA and explicit Menu control, with access actions moving inside at narrow widths. A native non-modal details/summary panel groups landing chapters, deeper public pages, trust/newsletter links, language and conversion. Desktop uses two columns, mobile one scrollable column; the summary remains outside that scroll region. No new animation library, modal focus trap, body scroll lock, endpoint or credential. Escape/outside/focus dismissal and language-focus return are implemented, but their rendered behavior remains unverified until browser access is restored.

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

## Required browser evidence — blocked

The browser security policy rejected acquisition of the owner's existing localhost3822 tab, stating that authority to observe its content was not granted. No alternate browser surface, raw browser protocol or external automation was used to bypass that refusal. A request to restore browser control is pending. HTTP tests used the separately built local server and are not substituted for browser QA.

Still required: desktop and320/390px mobile screenshots, closed/open panel; representative home/catalog/article/contact navigation; real language changes preserving article equivalents and preview/public boundaries; native keyboard activation, Escape/focus, narrow-menu scrolling, reduced-motion, console and performance verification. Do not claim these passed. No accepted Golden Master is updated, and no new visual acceptance is inferred.

STATUS: IMPLEMENTED + AUTOMATED_EVIDENCE_READY + BROWSER_QA_BLOCKED + HUMAN_VISUAL_ACCEPTANCE_PENDING. Production remains on the previous release. Reviewable local preview: `http://127.0.0.1:3830/de/landing-lab` and published-route equivalents in this build. Human visual acceptance remains pending.
