# Feature: Multilingual Knowledge Acquisition Corpus

**Status:** Implementation slice, scoped to public editorial surfaces.
**Authority:** MASTER §§2, 22, 40, 54–55; Constitution; ADR-0014–0017; spec 036.
**Objective:** Extend the existing AXIGNAL Knowledge notebook into a static, localized discovery corpus that explains the product and its epistemic boundaries without implying unimplemented sensors or SEO/GEO execution.

## User outcomes

1. A visitor can discover useful, distinct pages by problem, audience, product concept and method, then follow contextual links to related explanations.
2. A reader can open stable Spanish, English, French, German, Italian and Portuguese URLs that contain human-adapted copy, their own metadata and reciprocal language alternatives.
3. Search and generative discovery surfaces can resolve one canonical URL, an inspectable source of each editorial explanation, and a crawlable index of published pages.
4. Editors can reject a page when any language is missing, metadata or slugs collide, the document is thin, links are broken or untranslated copies are nearly identical.

## Requirements

- Content is authored and versioned offline. Request-time generation never calls an LLM or external content API.
- Every published page has a distinct intent, localized title/description/slug/body, direct answer, examples, limitations, contextual CTA, breadcrumbs and 3–6 related links where cluster size permits.
- `UNKNOWN != FALSE`, `OBSERVED != POTENTIAL`, `FAXT != INXIGHT`; source representation is not economic reality.
- Digital Representation Intelligence is observation, not SEO/GEO execution, reputation management or a claim of improved ranking. Measurement claims require instrument/version, conditions, time, sample and uncertainty.
- No claim implies unsupported source coverage, live generative search measurement, customer/lead conversion, rankings, review manipulation or measured savings.
- Canonicals, reciprocal `hreflang`, `x-default`, robots and sitemap derive from the same static corpus and route builder.
- JSON-LD is limited to visible Article and BreadcrumbList content. No invented publication dates, ratings, reviews, FAQs or commercial offers.
- The old `/knowledge` entry remains a route to the canonical Spanish hub. Existing public product routes remain untouched.

## Acceptance

- All published entries pass deterministic validation for six locales, unique localized slug/title/description, length, non-thin content, 3-gram similarity, related-ID integrity, inbound cluster links, valid CTA targets and sitemap/hreflang parity.
- Static build emits each indexable document and localized hub; unknown locale/slug returns 404.
- Frontend test, typecheck, i18n check, build, required Python/governance gates pass.
- Desktop and 390px mobile browser checks cover hub, commercial article, knowledge article, every locale, language links, CTA, metadata, sitemap, robots and 404.

## Out of scope

Runtime SEO/GEO optimization, SERP rank tracking, authenticated scraping, anti-bot bypass, search/generative measurement sensors, opportunity/lead generation, profile editing, new product integrations, runtime AI editorial generation, legal claims, production deployment and claims of traffic/conversion outcomes.
