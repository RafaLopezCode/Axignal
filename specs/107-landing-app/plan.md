# Plan and architecture review
Mode: EXPLORE, explicitly authorized and isolated. Existing homepage remains the comparison baseline.

Reuse the current Next app, locale infrastructure, original brand assets, projection fixture, exampleInsights, commercial price book, existing access and acquisition contracts. Build an independent public composition. Economic data is FIXTURE_ONLY; selectors are PRESENTATION_STATE; unsupported conclusions remain UNKNOWN_UNSUPPORTED.
Extract the shared source/proof rendering into a leaf presentation component, preserving its subscriber markup and evidence policy. This avoids importing the subscriber workspace into the lab. No runtime changes.
GSAP is a separately loaded enhancement after exploration intent, essential fonts and initial paint; it owns no economic state. useGSAP context and matchMedia own cleanup; no pinning, scroll hijacking or invisible essential content.

Architecture review: PASS. App-only read-only presentation; evidence remains non-navigable for fixtures; no new endpoint, analytics kind, canonical write, provider or private scope. Graphify inspected Landing, example projection and Observatory relationships.
Validation: six-locale content, shared evidence/temporal contract tests, typecheck, i18n, SEO and build; actual browser interaction/console/viewport checks; Python deterministic gates; AST graph update. Human acceptance remains separate.

## Performance follow-up · CTO 2026-10-19

The CTO rejects the 4.64 s mobile laboratory LCP. Graphify and the current bundle show a full four-language translation catalog on every route, including Spanish/English. Preserve the synchronous catalog for pure projection/server consumers; load only the requested translated language in the React provider using cached module promises and React 19 use/startTransition. Generate the four delivery files from the existing canonical catalog and verify exact parity for every key. Keep all explicit-locale SSR content and client navigation functional. Remove the single catalog dependency from the shared date formatter using the exact existing six-language values. No truth, API, account, privacy or commercial authority changes.

Architecture review: app presentation delivery only; shared provider API retained. Verify frontend contracts, six-language rendered HTML and browser language changes (including failure/hydration logs), original/new desktop/mobile visual geometry, build, architecture and governance. Measure the resulting release serially with the same Lighthouse settings; preserve the rejected baseline and all diagnostics. No experimental global CSS flag or production deployment.

The profile schema validator is also deferred until an actual profile read/save response needs admission. Parsing, error handling and epoch/version guards remain in the same methods; no account request is added to public pages.
