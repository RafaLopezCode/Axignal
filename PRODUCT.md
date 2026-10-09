# Product

<!-- impeccable:product-schema 1 -->

> **Subordinate record.** This file exists so design tooling can load AXIGNAL product context.
> It restates nothing new and never overrides its authorities, in this order:
> `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` → `.specify/memory/constitution.md`
> → accepted ADRs (`docs/adr/`) → `docs/product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md` and specs.
> Where this file and an authority differ, the authority wins and this file is wrong.
> Every line below comes from those documents (sections cited); nothing here is a user interview.

## Platform

web

## Users

- **Direct subscriber**: someone who wants to understand their own organization, its economic environment and what could improve, without being an analyst (MASTER §7.1, HFX).
- **Agency or consultancy** (SEO, GEO, marketing, communication): observes a portfolio of client organizations and must explain differences, gaps, changes and useful results to each client (MASTER §27.2, HFX "Three context authorities").
- **Customer Zero / Staff**: uses the same subscriber experience, with operational controls kept separate.

## Product Purpose

AXIGNAL is an economic brain, not an economic index. It keeps persistent observation on chosen organizations and turns persistent machine intelligence into persistent human understanding (HFX north star). Success: a person knows what is happening, what matters, what changed, what could improve, why AXIGNAL says so and where to look next, without learning the engine or writing a prompt.

## Positioning

The subscription buys observation, not influence: users direct attention, never conclusions (MASTER §5). The mechanism is one canonical AXIGLAND with evidence admission, so every statement can be traced from meaning to source, instrument and date (HFX "Evidence on demand").

## Operating Context

Authenticated subscriber workspace (`/account`) over a portfolio of observed organizations (Observation Focus). It includes First Observation (spec 063), public offer understanding (spec 064), the economic reading, opportunities, temporal change, evidence and contextual AXENT. Six UI locales: es, en, fr, de, it, pt.

## Capabilities and Constraints

- Product vocabulary: Organization, Observation Focus, Signal, Panorama, Evidence, Relationship, Change, Opportunity (MASTER §1.1). Never reintroduce `Xeed`/`Xignal` in copy.
- Epistemic states must stay exact: `UNKNOWN ≠ FALSE`, `POTENTIAL ≠ OBSERVED`, `HISTORICAL ≠ CURRENT` (HFX "Independent output dimensions"). Attention is a projection, not truth.
- Semantic depth GLANCE → UNDERSTAND → REASON → PROVE is navigable, never a wizard (HFX).
- AXENT is a contextual navigator, never the only interface. It does not write canonical truth (MASTER §4.3, HFX).
- No CRM, task manager or sponsored functionality. No "edit company profile" (AGENTS.md, MASTER §2.1).
- No fake loading: progress shown must be semantically true (MASTER §9.4).
- Tenant, client context and Organization isolation are absolute.

## Brand Commitments

- Isotipo: the observation monocle; AXIGNAL blue `#354F98`; Fraunces wordmark (MASTER §4.8, `docs/design/BRAND_ASSET_AUTHORITY_V2.md`).
- Icons: Lucide only (ADR-0022).

## Evidence on Hand

Real runtime contracts in `apps/web/experience/lib/*-contracts.ts` and `lib/runtime-projection.ts`. No AXIGNAL user-study results exist: usability claims stay hypotheses until tested with the HFX research protocol (`docs/research/HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md`). Never fabricate customers, results or sources.

## Product Principles

Taken from HFX "Hard interaction principles":

1. Meaning before metrics.
2. No mental joins.
3. Evidence on demand.
4. Same truth, different density.
5. Return is a task, not a page list.

## Accessibility & Inclusion

WCAG 2.2 AA target plus cognitive accessibility (COGA-informed). Color is never the only carrier of state (HFX "Epistemic and visual grammar").
