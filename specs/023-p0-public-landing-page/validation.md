# Validation — P0 Public Landing Preproduction

**Base:** `10d6d130072c271357ce7db389301dc82ed31925`
**Scope:** preproduction governance/copy/storyboard/source-manifest only.

## Confirmed evidence

- PR #31 Settings merged before Landing preproduction.
- PR #32 Landing Product Contract merged as `10d6d130072c271357ce7db389301dc82ed31925`.
- 15/15 human source masters verified at 1920×1080.
- Total source size: 45,988,828 bytes.
- Each master SHA-256 is recorded in `SOURCE_MASTER_MANIFEST_V1.md`.
- Source masters are preserved outside repository root.
- Former local duplicate Landing contract and old 022 prompts were preserved outside the repository before cleanup.
- `022-p0-identity-account-authority` remains canonical Identity; Landing uses 023.
- Independent Codex review of PR #37 HEAD `3bf8320067ea205079aac310ad34f078d2331598` returned `REQUIRES_CHANGES`; all substantive findings were dispositioned in `REVIEW_DISPOSITION_PR37_V1.md`.
- Source-master contact-sheet inspection independently confirmed the spatial corrections required for chapters 08, 09, 12 and 15.
- A second independent Codex rendered-storyboard review at PR #37 HEAD `a2ed7f679e5afad0f6fc86e84710a93b8bb30000` found no visual/narrative/copy-fit/epistemic defects, but correctly blocked freeze on stale screenshot hashes and two undocumented Chapter 12 responsive review derivatives. Both evidence-governance findings were repaired and recorded in `REVIEW_DISPOSITION_PR37_V1.md`.
- Current screenshot evidence recomputation verifies 90/90 manifest hashes against the exact files with mismatch count 0.
- Canonical image-generation briefs are present in `AXIGNAL_PUBLIC_LANDING_PAGE_CONTRACT.md` §16; the reviewer’s inability to confirm that source was not treated as a product defect.

## Current gate status

```text
COPY_DECK_EN=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
COPY_DECK_ES=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
CTO_SEMANTIC_REVIEW=PASS
COPY_FREEZE=PASS_2026-09-29
STORYBOARD=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
STORYBOARD_READY_FOR_RENDERED_REVIEW=YES
CTO_RENDERED_STORYBOARD_REVIEW=PASS_BASE_90_EN_ES
RENDERED_LAYOUT_OR_CONSOLE_FAILURES=0/90
RENDERED_SCREENSHOT_HASH_MATCH=90/90
RESPONSIVE_RENDER_BUNDLE_HASH_MATCH=2/2
STORYBOARD_FREEZE=PENDING_HUMAN_ACCEPTANCE
PREVIEW_WEBP_CANONICAL_BASE=15/15
PREVIEW_WEBP_RESPONSIVE_REVIEW_DERIVATIVES=2
PREVIEW_WEBP_EXTERNAL_DIRECTORY_COUNT=17
PREVIEW_WEBP_CANONICAL_BASE_BYTES=5,418,926
PREVIEW_WEBP_EXTERNAL_DIRECTORY_BYTES=5,632,284
PREVIEW_WEBP_SSIM_MIN=0.98252
PREVIEW_WEBP_SSIM_AVG=0.984754
PRODUCTION_WEBP=0/15
AVIF_EVALUATION=NOT_RUN_OPTIONAL
LANDING_RUNTIME=NOT_STARTED
DEPLOYMENT=NOT_STARTED
```

## Automated validation

- `uv sync --frozen`: PASS.
- `uv run ruff format --check .`: PASS — 367 files.
- `uv run ruff check .`: PASS.
- `uv run mypy`: PASS — 63 source files.
- `uv run pytest -q -p no:cacheprovider`: PASS — 293 tests.
- `uv run architecture-guard --root .`: PASS.
- `uv run axignal-governance`: PASS — architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology.
- Graphify update/check: PASS — rebuilt 5,032 nodes / 7,876 edges / 422 communities. Graphify reported community labels need optional LLM refresh after community-set change; deterministic structural update/check still exited 0.
- `git diff --check`: PASS.

No runtime, image derivatives, browser surface or production state was changed by this preproduction slice.

## Runtime implementation evidence — 2026-09-29

This section supersedes the preproduction-only runtime/deployment lines above for branch
`feature/p0-public-landing-runtime`, based on Xeed/Xignal semantic authority
`a9b3a2f`.

```text
STORYBOARD_GOLDEN_MASTER=ACCEPTED_FOR_RUNTIME_TRANSFER
LANDING_RUNTIME=IMPLEMENTED
PRODUCTION_WEBP=15/15
RESPONSIVE_WEBP=2
LOCALES=en/es/fr/de/it/pt
BROWSER_RENDER_MATRIX=270/270 PASS
BROWSER_OVERFLOW_FAILURES=0/270
DESKTOP_VISUAL_QA=PASS
TABLET_VISUAL_QA=PASS
MOBILE_VISUAL_QA=PASS
PRICING_NAVIGATION=PASS
PRICING_PRIMARY_TO_START=PASS
WHEEL_ONE_GESTURE_ONE_CHAPTER=PASS
DEPLOYMENT=NOT_STARTED
PRODUCTION_E2E=NOT_STARTED
```

Runtime verification used real headless Chrome at 1620×1080, 900×1100 and
390×844 for all 15 chapters and all six locales. Additional visual inspection
covered Spanish Pricing on desktop, German Use Cases on tablet and French
Pricing on mobile.

Automated validation after runtime transfer:

- public landing contract tests: 7 passed;
- full repository suite: 300 passed using an external pytest temp root;
- `uv run ruff format --check .`: PASS;
- `uv run ruff check .`: PASS;
- `uv run mypy`: PASS — 63 source files;
- `uv run architecture-guard --root .`: PASS;
- `uv run axignal-governance`: PASS;
- `git diff --check`: PASS.

The runtime is therefore implemented and locally/browser verified, but it is
not yet integrated into the canonical branch, deployed, or production-E2E
verified.
