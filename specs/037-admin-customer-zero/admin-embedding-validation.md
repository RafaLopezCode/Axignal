# AO-24A / TASK 4 — Admin product embedding correction

Date: 2026-10-04. CURRENT_TASK = AO-24A. Main branch, local implementation.

## Problem and root cause

The shared subscriber renderer had been implemented, but selecting Customer Zero
left the Admin dashboard for a standalone product page. This misinterpreted the
human requirement: Admin must use and evaluate the actual client experience
within its own dashboard. This report supersedes that hosting interpretation in
`unification-validation.md`; the earlier runtime acquisition evidence remains
historical evidence, not visual acceptance of the rejected standalone hosting.

## Implementation

Both `/admin#customer-zero` and `/admin/customer-zero` retain the Admin shell.
Customer Zero embeds the same RuntimeExperience / RuntimeProductProjection used
by the subscriber. AXENT uses the same authorized endpoint and contextual UI.
No iframe, parallel economic renderer, new datastore, privileged truth writer or
private operational props are introduced. Staff controls remain a disclosure.

The product remains mounted while temporarily viewing operational domains,
preserving selected signal and contextual conversation. Hash and popstate
navigation restore domains without full-page relocation. Content anchors do not
select administrative domains. Exactly one skip-link target exists; the embedded
product has its own main identifier. Admin and product mobile drawers have
distinct names, focus trapping and Escape recovery. Container queries adapt the
product to the available dashboard width. The compact temporal footer applies
equally to the shared subscriber renderer.

## Executed validation

- uv sync --frozen: PASS (17 packages).
- uv run ruff format --check .: PASS (824 files).
- uv run ruff check .: PASS.
- uv run mypy with isolated cache: PASS (258 source files).
- uv run pytest with isolated basetemp: 1,035 PASS, 148.46 seconds.
- Frontend typecheck: PASS; tests: 30 PASS; i18n: PASS (976 entries).
- Frontend production build: PASS (34 routes). No frontend lint script exists.
- Architecture Guard: PASS (no violations); axignal-governance: PASS across all
  eight checks. No gate suppression or test weakening.
- Final Graphify AST update: PASS (11,162 nodes, 25,606 edges, 680 communities).

The new test verifies Admin hosting and absence of location relocation; the
shared economic SSR output is identical after normalizing only its main ID.
Existing tests retain runtime state, endpoint, target, fixture exclusion,
subscriber-safe provenance, persistence and private/product separation coverage.

## Browser QA against compiled preview and real FR-30 runtime

Local preview: 127.0.0.1:3810. Runtime: 127.0.0.1:8765, real mode, preserved
QA store `D:/AXIGNAL/.ao24a-unified-proof`. No new acquisition was needed for
this presentation correction; persisted economic observations were not edited.

Verified by interactions, not screenshots alone:

- Admin -> Customer Zero stays within the Admin shell; operational navigation
  remains available. Switching to Centro de atencion and returning preserves the
  selected signal and AXENT question/answer.
- Browser Back restores operations; Forward restores Customer Zero.
- Skip link focuses `main`, keeps Customer Zero visible and has a unique target.
- Narrow Admin and product drawers open independently; Escape restores the
  correct opener. Document width stays 320px with each drawer open.
- Direct `/admin/customer-zero` and reload recover the actual persisted Today
  projection with the same claim and observation time, 2026-10-04 12:49:17 Madrid.
- Signal reading exposes OBSERVED, CURRENT and explicit UNKNOWN limits.
- How AXIGNAL knows exposes runtime EvidenceNarrative, observation, OFFICIAL_WEB
  source https://axignal.com/, currentness and uncertainty. No private operations
  records appear in the product reading.
- AXENT 'Que sigue abierto' returns the runtime-authored uncertainty passage,
  covering only the authorized public homepage; other surfaces remain UNKNOWN.

Six measured sizes: 1440x1000, 1280x720, 1024x900, 768x900, 390x844, 320x900.
No horizontal document or main overflow; no Norte/Atlas/OPS-018/REV-027 leakage
in the canonical main. Desktop AXENT stays visible at 1440 and 1280; narrower
layouts retain its modal entry. Measurements and visual evidence:
`apps/web/experience/qa/037-customer-zero/admin-embedding-screenshots/`.

## Economic evidence and status

Persisted real signal: `xignal:737c35e849d6393e23cf067ce1141940`, observation
2026-10-04T10:49:17.137943+00:00. It establishes public homepage observability,
not commercial opportunity, reputation, search visibility or other surfaces.
The previous acquisition/reobservation and process restart proof is retained in
the historical unification report. This change does not manufacture additional
economic conclusions or claim autonomous AXENT research is available.

IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY +
HUMAN_VISUAL_ACCEPTANCE_PENDING. No push or production deployment.
