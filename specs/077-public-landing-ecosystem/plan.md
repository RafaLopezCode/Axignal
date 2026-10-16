# Implementation Plan: Public landing ecosystem

**Branch**: `codex/public-landing-ecosystem` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)
**Status**: Public ecosystem implemented and validated; authorized actual-app review complete; final human visual acceptance pending.

## Summary

Extend the existing public experience into a coherent home, data-family hub and six industry journeys, linked to the canonical example, actual access channels and existing pricing/trust pages. Establish professional visual depth using the approved brand and custom authored assets. Keep public explanation distinct from actual observations. Existing private product surfaces and backend remain outside the write boundary.

## Technical Context

- TypeScript 5.9, Next 16.3, React 19.3, existing Lucide icon system and local Fraunces/Manrope/Bic fonts. No runtime dependency is needed.
- Presentation-only catalog typed by existing `FamilyId`, with order from `FAMILY_ORDER`; localized content for es/en/fr/de/it/pt and static allowlisted industry slugs.
- Existing `PublicShell`, canonical metadata helpers, locale provider and governed price book are reused. New public styles use a dedicated namespace; do not alter Observatory/AXENT selectors or global typography.
- No new persistence or API. Existing `/demo`, auth/contact channels and AO-12 status gate remain their own authorities.
- Semantic HTML and real links form the reading/navigation fallback. Progressive enhancement may select a family/industry; keyboard/touch and reduced motion work without hover dependency.
- Target desktop, tablet and 320px+ mobile; preserve meaningful public server rendering, language metadata and 404 behavior. Avoid new large animation libraries, scroll interception and unbounded raster assets.

## Constitution Check — before research and after design

PASS for the planned boundary, subject to implementation checks:

1. No canonical write, new domain schema, provider dependency or research authority is introduced.
2. Public examples remain the existing labeled example; no fabricated operational values, client proof or coverage claims are authored.
3. UNKNOWN remains unknown; opportunities are potential; geography is capability-specific; search/generative/experience results are conditioned observations.
4. Observation is the commercial unit, not signals; current Design Partner access and fixed governed pricing remain truthful.
5. No CRM, SEO execution, profile editing, universal score or sponsored truth is introduced.
6. No subscriber/Admin data, authentication or private analytics is exposed; no new tracking activation.
7. Deterministic gates retain their strength. Skill binaries/LLM/image-generation work are development tools and never required CI dependencies.

## Architecture review

Graphify was consulted before source exploration. The current proposal needs no architectural migration: data flows remain static public presentation → existing public navigation. The family catalog references canonical IDs by type/order, not fixture organization arrays. Route additions join Next's existing localization, sitemap and metadata boundaries. `PublicShell` changes require particular checks on signup/login/contact/Knowledge navigation; they must not inherit marketing-only layout styles. No renderer or backend change is authorized. A new ADR is unnecessary for this presentation-only extension; any later need for new API/data exposure must be reviewed before implementation.

## Project Structure / intended write boundary

```text
specs/077-public-landing-ecosystem/        spec, research, plan, tasks, contracts, verification
apps/web/experience/lib/                 typed public catalog, locale/SEO helpers only as needed
apps/web/experience/components/          public marketing components and scoped CSS
apps/web/experience/app/                 public pages, published locale routes, sitemap
apps/web/experience/public/              new approved illustration derivatives + provenance
apps/web/experience/tests/               content, routes, semantics and public-contract checks
.impeccable/                             development-only composition/review records
```

Forbidden write targets: domain/application/pipeline/cognition; backend/BFF; Admin; Observatory and AXENT components, shared canvas and subscriber contracts; authentication behavior; production deployment configuration. Existing public UI components may be reused but never patched to alter private behavior.

## Delivery sequence

1. Lock one of the three presented HTML compositions (user input pending). Record the six-block direction contract and chosen seed/sketch.
2. Create the public copy/catalog, mapped to canonical families, with substantive six-industry questions and explicit limitations; localize without invented integrations.
3. Implement the selected home first viewport and its meaningful family/industry interaction, then the full home argument and connected pages. Produce necessary custom artwork from approved Observador references and retain prompt/origin provenance.
4. Integrate navigation, locale routes, canonical metadata, sitemap, pricing and the actual example/access exits. Preserve gated measurement/contacts.
5. Run meaningful content/route/render tests; browser-inspect desktop/mobile, batch material fixes and confirm. Do not add dashboard-specific changes.
6. Run the deterministic gates, Graphify AST update, one detector pass, independent finish reviewer and documenter. Record actual results and visual acceptance state. No merge or deploy without review/authorization for this feature.

## Validation strategy

- Catalog parity with ten canonical family IDs; every industry references existing families and has distinct real questions and evidence limits.
- Real paths: home → family/industry → canonical example or actual access channel. Unknown nested slugs/locales fail closed; localized SSR and metadata remain coherent.
- Existing AO-12 CTA names/gates, governed prices, auth/status, contact and private boundaries remain intact. Existing tests must pass without weakened assertions.
- Browser evidence at desktop and narrow mobile, keyboard focus/menu interaction, long translated text, reduced motion, overflow and actual CTA destinations. New generated assets are illustrations and never evidence.
- Full repository gates plus frontend typecheck/tests/i18n/build and relevant Admin HTTP contract checks before merge proposal. Fresh task-owned pytest basetemp on Windows.

## Complexity / unresolved decisions

No new service, package, storage or API complexity. Human composition selection is recorded: understanding, round 2, comp first. The separate production plan/asset review is pending under reference/component-review.md; its receipt has not been submitted. Human visual acceptance of the completed implementation is a later separate stage, not implied by sketch selection.

## Human checkpoint override — 2026-10-16

The user explicitly authorized direct review of the running Next.js application in place of the incompatible intermediate HTML-only Impeccable component checkpoint: “Continúa con la aplicación real”. The selected composition and actual asset approval remain binding. The CLI hero checkpoint is not recorded as passed; its earlier failed pixel attempts and HTML entry limitation are retained. Complete the ecosystem, run all deterministic gates, and inspect the actual desktop/mobile application. Final human visual acceptance remains pending. This does not authorize merge or production deployment.

## Annotated public refinement

Keep the same architecture: reuse MarketingShell for Knowledge with its exact existing locale routes and an opt-in reading layout class; no new shell. Reuse WeeklyBriefChannel through a marketing variant with explicit checking/paused/unavailable states, retries and existing AO-15 request/AO-16 separate consent. The backend remains unchanged and availability is never fabricated. Existing controller, notice versions, receipt and duplicate-submit protection remain authoritative. Shared sector artwork is replaced by a bounded WebP from the built-in image tool, with original/full prompt retained. Header and family separation remain scoped to marketing. HTTP regression checks cover localized Knowledge hub/article frame continuity and newsletter server rendering.

## Explicit release and performance authorization — 2026-10-16

The human subsequently requested «Cuando termines, Commit, deploy y Push despues de optimizar la carga de la pagina para el posicionamiento de GSC». This authorizes commit/push/integration and production deployment after checks. Earlier no-deployment notes are historical; the automatic Impeccable history is retained. Optimize delivery within the existing public architecture: complete identical WOFF2 faces, responsive art with hashed immutable assets, critical font hints and no speculative demo loads. Preserve all private/auth/billing boundaries and active production overlays. Report byte savings separately from real field Core Web Vitals; never invent ranking or CrUX results.
