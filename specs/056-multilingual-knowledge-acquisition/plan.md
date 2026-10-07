# Plan: Multilingual Knowledge Acquisition Corpus

## Architecture

- Keep Knowledge inside the existing public experience and its visual system.
- Store acquisition documents as typed, reviewable JSON seeds partitioned by editorial cluster. Localized content is materialized before build.
- Expose static `/[locale]/knowledge` and `/[locale]/knowledge/[slug]` routes. Route identity comes from the locale-specific slug; `/{locale}` alternatives, canonical URLs, sitemap and page links are derived from the same document registry.
- Preserve `/knowledge` as the default-language entry point and preserve legacy article access while transitioning the existing notebook.
- Validate editorial graph, locale coverage, uniqueness, body similarity and publication thresholds deterministically before accepting the corpus.
- Emit visible article content and Article/BreadcrumbList JSON-LD from the same source. There is no runtime AI/content service.

## Boundaries and risks

- Product claims remain subordinate to MASTER and the pre-implementation status of DRI. Public absence is reported as an observed gap only under stated observation conditions; cause and recommendation stay conditional.
- Locale paths may describe the same concept, so duplication checks compare only within a locale and require authored language-specific intent and copy.
- Existing article URLs and unlocalized drafts must not create duplicate indexable documents. Redirect/canonical behavior is covered by tests and browser verification.

## Validation

Run focused acquisition tests, frontend tests/typecheck/i18n/build, repository deterministic gates and Graphify update. Verify generated routes and HTML metadata in a browser before opening a PR. Do not deploy.
