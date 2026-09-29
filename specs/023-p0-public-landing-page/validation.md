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
- Canonical image-generation briefs are present in `AXIGNAL_PUBLIC_LANDING_PAGE_CONTRACT.md` §16; the reviewer’s inability to confirm that source was not treated as a product defect.

## Current gate status

```text
COPY_DECK_EN=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
COPY_DECK_ES=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
CTO_SEMANTIC_REVIEW=PASS
COPY_FREEZE=PASS_2026-09-29
STORYBOARD=15/15 REVISED_AFTER_INDEPENDENT_REVIEW
STORYBOARD_READY_FOR_RENDERED_REVIEW=YES_AFTER_COPY_FREEZE
STORYBOARD_FREEZE=PENDING_RENDERED_HUMAN_REVIEW
PREVIEW_WEBP=0/15
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
- Graphify update/check: PASS — rebuilt 5,025 nodes / 7,870 edges / 438 communities. Graphify reported community labels need optional LLM refresh after community-set change; deterministic structural update/check still exited 0.
- `git diff --check`: PASS.

No runtime, image derivatives, browser surface or production state was changed by this preproduction slice.
