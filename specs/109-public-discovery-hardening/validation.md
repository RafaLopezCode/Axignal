# Validation — public discovery hardening

Date: 2026-10-21. Public evidence only; Search Console diagnostics and credentials are excluded from this record.

## Scope and result

An HTTP/HTML crawl without JavaScript inspected all 596 sitemap URLs and 12 additional boundary routes. Before the change, 60 localized home/catalog documents lost their social image through Next's nested metadata replacement. The candidate restores all 60, with no sitemap HTTP errors, unexpected `noindex`, malformed JSON-LD or incorrect localized HTML language. Root and `/en` intentionally share English wording; their distinct canonical URLs and reciprocal language alternatives are retained.

The declared official search favicon already returned 200. The added `/favicon.ico` alias uses the same approved artwork; it does not assert that the former alias caused Google's presentation. The production fallback and Next agree on the redirect. Structured data connects the actual organization, website, page and service, with monthly reference prices derived from the commercial price book and explicit invitation-only terms. No invented reviews, client counts or commercial availability are added.

## Deterministic checks

- Locked Python environment synchronized; formatting, Ruff, mypy, Architecture Guard and every governance gate pass.
- Python: 2,723 passed, seven environment-specific skips on Windows (below).
- Frontend: 427 passed, zero skipped; strict typecheck passes; six-language inventory passes (2,786 entries); SEO command passes 19 tests.
- Production Next build passes: 663 generated routes. The final price metadata uses the existing price book rather than duplicate literals.
- Graphify AST-only update completes without model/API calls.
- `git diff --check` passes. No briefing, reference images, generated graph, private analytics or scratch logs are staged.

## Seven Windows omissions

| Test | Reason and impact |
| --- | --- |
| `tests/contracts/test_ao184_step_up.py:210` | POSIX file modes; no authentication/session code changed. |
| `tests/integration/test_observation_materialization.py:466` | POSIX ownership; no storage or materialization code changed. |
| `tests/observation_runtime/test_scheduler_deployment.py:117` | POSIX deployment; no scheduler code changed. |
| `tests/observation_runtime/test_scheduler_deployment.py:130` | POSIX deployment; no scheduler code changed. |
| `tests/observation_runtime/test_scheduler_deployment.py:140` | POSIX deployment; no scheduler code changed. |
| `tests/observation_runtime/test_scheduler_deployment.py:164` | POSIX deployment; no scheduler code changed. |
| `tests/semantic_layer/test_providers.py:123` | Optional `typesafe_sdk` absent; no semantic provider or SDK changed. |

Required Ubuntu CI rechecks the POSIX-capable cases before merge; the filesystem ownership test additionally requires root and stays conditional on that authority. The optional SDK case also remains explicitly conditional. No related runtime code changed, no gate was weakened and no required dependency was added to eliminate a skip.

The first container CI build exposed a missing test input: the Nginx fallback configuration was not copied into the build stage. The Dockerfile now includes that exact public configuration, as it already includes the Traefik configuration for SEO checks. The final runtime image still copies only the Experience subtree; no configuration or secret exposure is added.

## Visual and interaction evidence

Presentation mode: PRESERVE. No page body, CSS, illustration, navigation, pricing behavior or animation changes. Candidate production server inspected in the browser at 1440×1000 and 390×844: [desktop](evidence/desktop.jpg), [mobile](evidence/mobile.jpg). Sources/observed dates expand correctly; footer return-to-top works; browser error/warning log is empty during those interactions. The demonstration continues to identify synthetic fixtures and potential opportunities explicitly.

## Performance method and limits

Lighthouse 13.5.0, Chrome headless, mobile simulated throttling, fresh profile, no concurrent build/test load. Actual public root before this release: performance 94, accessibility/best-practices/SEO 100; LCP 2,609 ms, CLS 0, TBT 87.5 ms; no run warnings. Candidate loopback root: performance 95, accessibility/SEO 100, best-practices 96; LCP 2,484 ms, CLS 0.0934, TBT 46.5 ms. Loopback is not a production result; its acquisition API is unavailable in this frontend-only local server. Final public measurements are required after cutover. No field INP measurement or field Core Web Vitals claim is made.

## Search and assistant boundaries

[Google AI features](https://developers.google.com/search/docs/appearance/ai-features) use the same crawlability and helpful-content foundations. The existing `llms.txt` is a supplementary, source-linked product directory, not a ranking or indexing mechanism. [Favicon eligibility](https://developers.google.com/search/docs/appearance/favicon-in-search) and indexing do not guarantee display. Sitemap acceptance, valid schema and live fetch availability are technical evidence, not a promise of rankings, citations or endorsement. The separate server-side Search Console credential renewal remains an operator authentication matter and is not solved by committing secrets.

## Release acceptance

The first release, `c7b2ae39d0508c31d6929ed3cac6163bf1a5483a` (PR #360), passed exact-head and main CI, the canonical deployment gate and all 596 sitemap documents. Post-deploy checks exposed a profile-specific gap: production bind-mounts `subscriber-edge-nginx.conf` over the base Nginx configuration, so the base favicon alias was not active. The corrective change adds the same exact alias to that active profile and extends the regression check to both configurations; neither forwarding rules nor private access are expanded. The official declared search icon remained 200 throughout. Final acceptance must test the public alias itself, not just the frontend or the base image.

The first public mobile run after #360 measured LCP 1,996 ms, TBT 65 ms and CLS 0.0975, with performance 96 and accessibility/best-practices/SEO 100. The CLS trace identifies the privacy notice: its urgent visibility update preceded the lower-priority language transition. Locale readiness and resolved language now commit together, and the notice waits for that actual readiness. No timer, artificial loading state, copy, consent choice, preference policy or layout change is introduced. Browser and final Lighthouse checks must verify the correction.

Merge only after exact-head CI succeeds. Deploy the immutable merged SHA through the canonical five-file Compose entrypoint, retain subscriber/AXENT/semantic/research configuration and verify public/private routes, image labels and health. Repeat the public crawl, Lighthouse mobile/desktop and Search Console live inspection after release. Record final public release results separately from private operator diagnostics.
