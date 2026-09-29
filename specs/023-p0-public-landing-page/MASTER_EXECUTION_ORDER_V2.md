# AXIGNAL — MASTER EXECUTION ORDER V2
## P0 Public Paginated Landing — COPY → PREVIEW ASSETS → STORYBOARD → PRODUCTION ASSETS → IMPLEMENT → VERIFY → PR

**Status:** EXECUTION AUTHORITY FOR THIS SLICE  
**Base:** `10d6d130072c271357ce7db389301dc82ed31925`  
**Mode:** `EXTEND`  
**Runtime target:** public AXIGNAL landing only  
**Merge/deploy:** forbidden without explicit CTO authorization

## 1. Mission

Build the public AXIGNAL landing as a 15-chapter, viewport-scale narrative that makes the real product immediately understandable, credible and desirable.

The execution sequence is mandatory:

```text
AUTHORITY → COPY_FREEZE → PREVIEW_ASSETS → RENDERED_STORYBOARD_REVIEW
→ STORYBOARD_FREEZE → PRODUCTION_ASSET_PIPELINE → IMPLEMENT
→ BROWSER_QA → REPAIR → FULL_GATES → PR
```

Code is not allowed to substitute for unresolved copy or unresolved visual composition.
## 2. Authority

Apply this precedence without exception:

1. `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`
2. `.specify/memory/constitution.md`
3. accepted ADRs
4. `docs/product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md`
5. `docs/product/AXIGNAL_PUBLIC_LANDING_PAGE_CONTRACT.md`
6. canonical Design System / Golden Master / Brand authorities
7. this execution order and the other artifacts in `specs/023-p0-public-landing-page/`
8. implementation

If any lower artifact conflicts with a higher one, repair the lower artifact. Never weaken doctrine, tests, architecture or governance to make implementation pass.

The Landing is a projection of product truth, never a new truth authority.
## 3. Confirmed preconditions

At creation of this order:

- PR #31 Settings is merged.
- PR #32 Landing Product Contract is merged.
- canonical Landing contract requires 15 chapters, six launch locales, COPY_FREEZE and STORYBOARD_FREEZE.
- authoritative masters are exactly 15 human-approved PNG files at 1920×1080.
- the source masters are retained outside the repository root because each exceeds the repository 2 MiB hygiene gate.
- external governed source location is currently `D:\AXIGNAL\_source_assets\landing\masters-1920x1080\`.
- browser production assets do not yet exist.
- Landing runtime does not yet exist.
- production deployment is out of scope.

Do not infer LIVE product capabilities from Landing copy. Planned/non-live capabilities must be omitted or clearly qualified under the canonical Landing contract.
## 4. Product invariants

Never violate:

```text
ONE_CANONICAL_AXIGLAND=YES
XIGNAL_IS_PERSISTENT_OBSERVATION=YES
XIGNAL_IS_OWNERSHIP=NO
USER_DIRECTS_ATTENTION_NOT_CONCLUSIONS=YES
CLAIM_IS_WRITE=NO
OBSERVED_IS_POTENTIAL=NO
UNKNOWN_IS_FALSE=NO
FAXT_IS_INXIGHT=NO
RELATIONSHIP_IS_PATHX=NO
AXENT_IS_CANONICAL_TRUTH_AUTHORITY=NO
PAY_TO_INFLUENCE_CANONICAL_TRUTH=NO
DIRECT_PROFILE_EDITING=NO
CRM_OR_WORKFLOW_SUITE=NO
```

Marketing must never fabricate customers, ROI, testimonials, awards, coverage, scarcity, guarantees or model certainty.
## 5. Mandatory design stack

Before visual work, read and use:

- `/.agents/skills/axignal-design-director/SKILL.md` as primary router.
- `frontend-design` for art direction, hierarchy, typography and anti-generic composition.
- `ui-ux-pro-max` for responsive, navigation, ergonomics and accessibility.
- Impeccable/craft guidance for spacing, proportion, alignment, density and AI-slop detection.
- atuizz/product-cognition guidance where installed for journey, CTA and cognitive-load review.
- Vercel web-interface guidance for interaction, semantics, responsiveness and performance.
- browser/Playwright for rendered verification.

External skills are advisory. AXIGNAL authority always wins.

Do not build a SaaS template, card grid, dashboard, glassmorphism surface, crypto aesthetic, AI gradient or LLM interface.
## 6. GATE 0 — Repository and runtime preflight

Before implementation:

1. inspect branch, status, worktrees, stash, `origin/main` and open PRs touching `apps/web/**`;
2. inspect the actual public web runtime and build commands;
3. inspect current brand assets, route authority, locale foundations and auth/signup routes;
4. confirm `specs/023-p0-public-landing-page/` remains the feature area;
5. confirm no source master PNG exists inside the repository root;
6. verify the external master manifest: 15 files, 1920×1080, source bytes and SHA-256 hashes;
7. do not choose a framework before inspecting the existing runtime.

Prefer: reuse → repair → extend → create.

Do not touch `domain/**`, canonical `application/**`, `pipeline/**` or `cognition/**` unless a demonstrated root cause requires it and authority permits it.
## 7. GATE 1 — COPY_FREEZE

The file `COPY_DECK_EN_ES_V1.md` is the initial production-copy proposal.

For all 15 chapters it must define:

- human question / narrative purpose;
- eyebrow where used;
- production headline;
- body;
- value line where used;
- primary and secondary CTA copy where applicable;
- optional microcopy only when it removes ambiguity/friction;
- relation between copy and artwork;
- chapter-specific epistemic guardrails;
- mobile copy strategy.

English is source authority. Spanish is first-class reviewed locale.

Do not translate into fr/de/it/pt until EN semantics are accepted and ES has passed semantic review.

`COPY_FREEZE=PASS` requires CTO/human approval of EN 15/15 and ES 15/15. Before that pass, only disposable non-runtime exploration is permitted when needed to evaluate copy fit. It must remain outside product runtime, create no reusable implementation credit and never be presented as an implemented Landing.
## 8. Copy quality guardrails

Copy must:

- explain value before ontology;
- sound human, premium, restrained and specific;
- use the artwork to create meaning rather than narrating the picture;
- keep paragraphs short enough for full-viewport reading;
- avoid architecture vocabulary when plain language preserves truth;
- preserve POTENTIAL, UNKNOWN, evidence and temporal boundaries;
- avoid stronger epistemic claims in localization;
- make the next action obvious without fake urgency.

Each chapter should answer one human question and advance one narrative step.

Final copy must make a first-time visitor able to explain AXIGNAL, AXIGLAND, Xignal, AXENT, evidence, time, POTENTIAL, independence, price and next action.
## 9. GATE 2 — Preview assets and rendered storyboard review

The file `STORYBOARD_V1.md` defines the initial production storyboard, but STORYBOARD_FREEZE requires rendered evidence.

Before that freeze:

- verify all source hashes against `SOURCE_MASTER_MANIFEST_V1.md`;
- generate deterministic WebP **preview derivatives outside the repository/runtime tree** from the approved masters;
- use those preview derivatives in a disposable/static review harness or equivalent browser-renderable surface;
- do not integrate that harness into the product runtime;
- do not count preview work as implementation completion;
- preserve the exact source aspect ratio and record the preview conversion tool/version/settings.

AVIF evaluation is optional at this stage. Evaluate it only when a supported deterministic encoder is already available and the comparison can be made without introducing avoidable dependency or workflow cost.

The preview stage exists only to make storyboard decisions observable. It must not create fake routes, fake auth, fake billing or reusable runtime code.

## 10. GATE 3 — STORYBOARD_FREEZE

For each chapter the storyboard must specify:

- copy zone and information hierarchy;
- artwork focal intent;
- desktop/tablet/mobile focal treatment;
- chapter-specific copy-measure/fit guidance;
- CTA configuration;
- header readability/contrast treatment;
- right-side pagination behavior;
- entry/exit transition intent;
- reduced-motion equivalent;
- chapter-specific responsive risks.

Focal percentages and crop assumptions are hypotheses until the actual preview derivatives are rendered at the required breakpoints.

`STORYBOARD_FREEZE=PASS` requires a coherent 15/15 desktop/tablet/mobile composition reviewed against browser-rendered evidence. No chapter may invent a conflicting visual grammar.

## 11. GATE 4 — Governed production asset pipeline

Authoritative masters remain outside the repository.

Required mapping uses base names:

```text
landing-01-outside
landing-02-observe
landing-03-understand
landing-04-axigland
landing-05-xignal
landing-06-first-map
landing-07-evidence
landing-08-discover
landing-09-digital-representation
landing-10-time
landing-11-axent
landing-12-independence
landing-13-use-cases
landing-14-pricing
landing-15-start
```

For every source master:

- verify SHA-256 against `SOURCE_MASTER_MANIFEST_V1.md`;
- never overwrite or modify the master;
- preserve 1920×1080 aspect ratio;
- generate deterministic WebP fallback;
- record tool/version, dimensions, quality settings and bytes;
- inspect dark gradients, brush texture, fabric, skin and fine edges;
- reject banding, blocking, halos or focal damage.

AVIF is an evidence-gated optimization, not a completion requirement. Generate AVIF candidates only when the selected encoder/runtime/browser path is supported and the comparison is worth running. WebP-only satisfies the asset gate when AVIF is unavailable, unsupported or fails the quality/size comparison.

When both formats are accepted, use `<picture>` with AVIF first and WebP fallback. Never let formats use different semantic crops.

No production derivative may violate repository asset-size governance.
## 12. Loading and performance

There are 15 hero-class images. Do not create a 15-image initial burst.

Target:

- chapter 01 eager/high priority;
- chapter 02 warmed/preloaded only when justified by measured navigation behavior;
- distant chapters lazy/progressive;
- no white flash during ordinary forward navigation;
- no layout shift caused by image discovery;
- image dimensions/aspect ratio known before load.

Measure in browser/network tooling. Do not report performance improvements from file-size guesses alone.

Do not add a heavyweight image dependency for 15 files if an existing trustworthy tool or small deterministic script is sufficient.
## 13. GATE 5 — Implementation

Canonical chapter order is immutable:

```text
OUTSIDE → OBSERVE → UNDERSTAND → AXIGLAND → XIGNAL
→ FIRST_MAP → EVIDENCE → DISCOVER → DIGITAL_REPRESENTATION
→ TIME → AXENT → INDEPENDENCE → USE_CASES → PRICING → START
```

Build one locale-independent chapter model plus locale catalogs. Do not fork components by language.

Launch locales:

`en, es, fr, de, it, pt`

English is the canonical translation source and the unconditional fallback locale. Spanish is the first-class human-reviewed locale. French, German, Italian and Portuguese are required launch locales and MUST be localized from the frozen English meaning after COPY_FREEZE.

### Locale resolution and selector

The public Landing MUST adapt automatically to the visitor's supported browser language while always offering an explicit accessible language selector.

Resolution precedence:

1. an explicit locale encoded by an addressable locale route, when the final routing architecture supports locale-addressable URLs;
2. the visitor's explicit selector override persisted for that browser/session according to the chosen public-web persistence mechanism;
3. a future authenticated Principal-owned locale preference, only when that governed runtime actually exists;
4. the first supported language from `navigator.languages`, falling back to `navigator.language`;
5. `en`.

Normalize regional BCP-47 tags to the supported base locale where appropriate, for example `es-MX → es`, `fr-CA → fr`, `pt-BR → pt`. Unsupported languages MUST fall back to English without mutating canonical IDs, source language or product truth.

The selector MUST:
- expose all six launch locales: English, Español, Français, Deutsch, Italiano, Português;
- be keyboard accessible and usable on desktop/mobile;
- make the active locale obvious without relying on flag icons;
- override browser detection immediately;
- persist the explicit visitor choice without inventing account/profile persistence;
- update the document `lang` and locale-aware metadata/content;
- never translate protected product vocabulary inconsistently.

Architecture must remain ready for:

`zh, ja, ko`

Protected vocabulary: AXIGNAL, AXIGLAND, AXENT, Xignal, FAXT, INXIGHT, PATHX.
## 14. Header and navigation

Persistent semantic actions:

- canonical AXIGNAL wordmark/logo;
- What is AXIGNAL?;
- AXIGLAND;
- How it knows;
- Pricing;
- Log in;
- + Xignal.

Discover real route authority before wiring Log in or + Xignal. Never fabricate signup, billing or checkout behavior.

Pagination must support:

- direct chapter selection;
- wheel/trackpad;
- Down/PageDown and Up/PageUp;
- Home/End;
- touch where reliable;
- native scroll fallback;
- coherent Back/Forward when chapters are addressable.

Prefer native scroll-snap plus bounded state. No scroll trap, no double jump, no bespoke navigation engine without demonstrated need.
## 15. Visual system and motion

Art direction:

**Renaissance ways of seeing applied to the contemporary economic world.**

The artwork is dominant. Copy normally occupies the dark left/left-center field while focal subjects remain visible.

Use the canonical CSS contrast layer from the Landing contract. Adjust only per-image when accessibility requires it.

Motion is restrained:

- opacity;
- small transform;
- refined chapter-state transition;
- pagination transition.

No aggressive parallax, cinematic zoom, bounce, continuous ambient motion or decorative animation of every text block.

`prefers-reduced-motion` must preserve the full story with no comprehension loss.
## 16. Responsive and accessibility

Mandatory QA breakpoints:

- 1720×1080
- 1440×900
- 1280×720
- 1024×768
- 768×1024
- 390×844
- 360×800

Each chapter may own focal metadata. Never force one global `background-position`.

Target WCAG 2.2 AA where applicable:

- semantic landmarks;
- coherent headings;
- keyboard access;
- visible focus;
- adequate touch targets;
- sufficient contrast;
- reduced motion;
- correct `lang`;
- no color-only state;
- no horizontal overflow;
- accessible pagination.

Decorative background art does not need verbose alt copy when adjacent text carries the meaning.
## 17. SEO and truthful acquisition

Implement only correct public metadata:

- title;
- description;
- canonical URL where route authority exists;
- locale-aware metadata;
- Open Graph using real brand assets;
- crawlable copy.

No fake review/rating schema.

Pricing authority:

- EUR 9.95/month includes 1 Xignal.
- EUR 4.95/month per additional Xignal.

Do not invent annual plans, free trials, enterprise pricing, discounts, tax handling, cancellation promises or usage limits.

If real billing does not implement the pricing contract, expose no fake checkout path.
## 18. GATE 6 — Browser quality loop

Mandatory loop:

```text
RENDER → INSPECT → CRITIQUE → IDENTIFY ROOT CAUSES
→ REPAIR → RENDER AGAIN
```

Use Design Director + frontend-design + UI UX Pro Max + craft guidance + browser evidence.

Inspect:

- hierarchy;
- legibility;
- crop/focal subject;
- spacing;
- line length;
- CTA clarity;
- visual balance;
- pagination state;
- responsive behavior;
- cognitive load;
- consistency;
- console errors;
- network loading.

A third visual iteration must be motivated by observable defects, not perfectionism.
## 19. Browser QA matrix

Desktop: all 15 chapters at 1720×1080, 1440×900 and 1280×720.

Tablet/narrow: all 15 at 1024×768 and 768×1024.

Mobile: all 15 at 390×844 and 360×800.

For every locale visually inspect at minimum:

- chapter 01;
- longest-copy chapter;
- PRICING;
- START.

Then smoke all 15 chapters in all six locales for missing keys, clipping and overflow.

Functional QA covers initial load, next/previous, direct navigation, wheel/trackpad, keyboard, touch, history/deep link if applicable, locale fallback, real Login/+ Xignal/Pricing/How-it-knows routes, reduced motion, refresh, console and broken assets.

Every browser QA PASS must be evidence-backed. Maintain `BROWSER_QA_EVIDENCE_V1.md` with the exact tested HEAD SHA, viewport, locale, chapter/range, browser/tool, screenshot or recording reference, console result, network/loading result where relevant, defect/repair linkage and final verdict. Screenshots may live in CI/PR artifacts or a governed local review bundle rather than Git when binary size makes that safer, but the manifest must identify where the evidence can be inspected and record hashes when practical. Unsupported PASS values are invalid.
## 20. Tests and gates

Add only deterministic tests that cheaply protect:

- exactly 15 chapter IDs in canonical order;
- source/production image mapping;
- locale completeness;
- pricing authority;
- header/route actions;
- asset manifest consistency;
- architecture boundaries where relevant.

Never snapshot every paragraph merely for ceremony. Never weaken existing tests.

Before PR run:

```powershell
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run architecture-guard --root .
uv run axignal-governance
```

Also run discovered real web build/tests, browser QA and console checks.
## 21. Git and scope safety

Implementation branch after preproduction review:

`feature/p0-public-landing-page`

Do not implement on this preproduction branch unless the CTO explicitly promotes it.

Preserve unrelated worktrees and `stash@{0}`.

Do not reintroduce the former local `specs/022-p0-public-landing-page/`; 022 is canonical Identity authority.

Do not put prompts/specs inside asset directories.

Do not merge or deploy production without explicit CTO authorization.

Stop only for a real authority conflict, route collision, auth/billing requirement with no truthful path, missing/corrupt source assets, overlapping branch ownership or a change that would require weakening governance/architecture.
## 22. Required implementation ledger

Return:

```text
SLICE=P0-PUBLIC-LANDING
MODE=EXTEND
BASE_SHA=
BRANCH=
HEAD_SHA=
CONTRACT_AUTHORITY=
COPY_FREEZE=
STORYBOARD_FREEZE=
UX_SKILLS_USED=
DESIGN_DIRECTOR=
BROWSER_VERIFICATION_TOOL=
BROWSER_QA_EVIDENCE_MANIFEST=
SOURCE_IMAGES_FOUND=15/15
SOURCE_IMAGES_UNMODIFIED=
SOURCE_MANIFEST_VERIFIED=
WEBP_IMAGES_GENERATED=15/15
AVIF_IMAGES_GENERATED=
AVIF_ACCEPTED=
IMAGE_CONVERSION_TOOL=
IMAGE_TOTAL_SOURCE_BYTES=
IMAGE_TOTAL_WEBP_BYTES=
IMAGE_TOTAL_AVIF_BYTES=
```
```text
CHAPTERS_IMPLEMENTED=15/15
LOCALES_IMPLEMENTED=en,es,fr,de,it,pt
MISSING_TRANSLATION_KEYS=
PUBLIC_ROUTE=
PAGINATION=
HEADER=
CTA_ROUTING=
REDUCED_MOTION=
RESPONSIVE=
PERFORMANCE_LOADING=
DESKTOP_BROWSER_QA=
DESKTOP_BROWSER_QA_EVIDENCE=
TABLET_BROWSER_QA=
TABLET_BROWSER_QA_EVIDENCE=
MOBILE_BROWSER_QA=
MOBILE_BROWSER_QA_EVIDENCE=
LOCALE_VISUAL_QA=
LOCALE_VISUAL_QA_EVIDENCE=
CONSOLE_ERRORS=
CONSOLE_EVIDENCE=
NETWORK_LOADING_EVIDENCE=
DESIGN_CRITIQUE_PASS_1=
DESIGN_REPAIR_PASS_1=
DESIGN_CRITIQUE_PASS_2=
DESIGN_REPAIR_PASS_2=
WEB_BUILD=
FOCUSED_TESTS=
RUFF_FORMAT=
RUFF_CHECK=
MYPY=
PYTEST=
ARCHITECTURE_GUARD=
AXIGNAL_GOVERNANCE=
SECRET_SCAN=
CI=
CANONICAL_CLAIM_REVIEW=
HUMAN_VISUAL_ACCEPTANCE=PENDING
PR=
MERGED=NO
DEPLOYED=NO
PRODUCTION_E2E=NO
BLOCKERS=
```

Evidence vocabulary in the ledger: `CONFIRMED`, `INFERRED`, `UNKNOWN`.
## 23. Final acceptance question

Before requesting human review, verify that a first-time visitor can explain:

1. what AXIGNAL is;
2. what AXIGLAND is;
3. what a Xignal buys;
4. what AXENT does;
5. why independent observation is useful;
6. how an important conclusion can be inspected;
7. observed reality vs POTENTIAL relevance;
8. why time/currentness matter;
9. why a company cannot pay to edit the map;
10. current Xignal pricing;
11. the natural next action.

If this fails, the Landing is not ready even if CI is green.

**Truth first. Meaning before metrics. Conversion through clarity. One story. Fifteen chapters. One Xignal as the next action.**
