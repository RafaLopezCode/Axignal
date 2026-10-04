# AO-24A — execution and convergence evidence

CURRENT_TASK = AO-24A

Code commit: `1ae70d0e0a89e9af69ed53d5dbbaf1de8bd86b0b` on main.
Previous local narrator work preserved separately in `9aa8cc2`; the concurrently
landed backend restart test and roadmap evidence in `1b3b656` were preserved.

## Problem and root cause

The existing experience Admin presented illustrative operational reviews and its
subscriber link led to the illustrative Panorama. FR-30 already acquired public
evidence and persisted subscriber-safe projections, but had no integrated Admin
product entry, authorized browser transport or human evidence reading surface.

## Changes

EXTEND the existing Admin: distinct Use AXIGNAL / Customer Zero, durable
`/admin/customer-zero` route and reversible navigation. Private operational
records and the illustrative Axent guide are absent from this product path.
`/panorama/live` and Customer Zero share exactly `RuntimeProductProjection`.
The Customer Zero subscriber link also uses that real route. The adjacent
illustrative routes remain available outside Customer Zero.

Both use GET `/api/subscriber-context`; Plant/Reobserve uses POST `/api/xeeds`
with only the canonical attention command `https://axignal.com/`. The Next server
adapter forwards an existing AO-01 session, validates runtime authority per
request and strips unknown fields from the safe read contract. No shared server
credential, alternate backend, datastore, Brain, organization fixture, frontend
signal construction or canonical writer was added. No first_proof implementation
was changed. Organization name/id are read from the runtime.

The composed Admin runtime requires XEEDS_READ to read and RESEARCH_OPERATE to
observe. Standalone FR-30 compatibility is preserved. The existing opaque session
uses an HttpOnly, SameSite=Strict cookie; exact approved Origin/Host checks protect
writes. Staff cookie use is disclosed in the privacy inventory. QA identity
composition is explicitly local-only, outside production authentication.

Loading, planting, NO_XEED, governed rejection, insufficient evidence, runtime
failure and success have separate states. Today focuses the real signal without
changing Admin route state. Native disclosures show exact EvidenceNarrative,
sourceRefs, currentness, uncertainty and optional technical lineage. Existing
Fraunces/Manrope/IBM Plex Mono, color and responsive shell are reused. UI copy is
available in ES/EN/DE/PT/FR/IT; runtime-authored evidence text is not fabricated or
translated into a new economic assertion.

## Executed technical checks

- `uv sync --frozen`: PASS, 17 packages.
- `uv run ruff format --check .`: PASS, 820 files.
- `uv run ruff check .`: PASS.
- `uv run mypy --cache-dir D:/AXIGNAL/.ao24a-validation/mypy-cache`: PASS,
  258 source files. An initial grant-variable collision was corrected.
- `uv run pytest` with a fresh `--basetemp` directory under D:/AXIGNAL:
  full suite PASS, **1,035 tests**, 144.31 seconds. Windows default temporary
  storage was inaccessible; an external fresh temporary directory resolved it
  without code/test/gate weakening. Final FR-30/AO-24A contracts: **15 passed**,
  13.37 seconds, using `--basetemp D:/AXIGNAL/.ao24a-final-tests`.
- `uv run architecture-guard --root .`: PASS, no violations.
- `uv run axignal-governance`: PASS, all eight checks.
- Experience `npm run typecheck`: PASS.
- Experience `npm test`: PASS, **25 tests**.
- Experience `npm run check:i18n`: PASS, 961 entries, missing [].
- Experience `npm run build`: PASS, all 33 routes, including real Admin and
  shared Panorama. No lint script exists in this package; no frontend lint run
  or pass is claimed.
- `git diff --check`: PASS. AST-only `graphify update .`: PASS, 11,105 nodes,
  25,482 edges. Graph community labeling advisory did not require LLM execution.

Tests cover AO-01 scope enforcement, NO_XEED, invalid target rejection, safe
projection parsing, private-field stripping, canonical attention only, endpoint
use, no fixture/model construction in the product path, source links, cross-site
writes, and persisted HTTP reload after rebuilding the runtime. Controlled test
projections exist only in tests and never supply the Customer Zero runtime.

## Browser QA and first real observation

Real compiled Next UI and existing FR-30 HTTP runtime, isolated development
storage at `D:/AXIGNAL/.ao24a-real-proof`, no production deployment. Browser
interactions were performed through CUA, not screenshot-only inspection.

Executed: Admin → Customer Zero → authorized GET → visible NO_XEED → Plant
AXIGNAL → visible planting → POST /api/xeeds 201 → actual HttpSourceSensor
retrieval of `https://axignal.com/` → persisted projection → Today → narrative
and source disclosures → browser reload. No successful payload was mocked.

First real observation:
- Organization: payload `org:axignal`, `AXIGNAL`.
- Context: `xeed:production-first-proof:1`.
- Signal: `xignal:21691e27372ce304be7d864c7c34557e`.
- Observed at: `2026-10-04T01:47:04.639201+00:00`.
- Epistemic/currentness: OBSERVED / CURRENT; Today READY.
- Source: `https://axignal.com/`.
- Claim: public homepage was observable from outside with visible text.
- Search, generative, social and reputation surfaces remain UNKNOWN. Homepage
  reachability establishes no commercial capability, reputation or opportunity.

EvidenceNarrative was opened and inspected in Customer Zero and the shared
Panorama: XIGNAL → OBSERVATION → SOURCE → UNKNOWN, with verified artifacts for
observation/source and the runtime uncertainty wording. FR-30's admitted basis
is reused unchanged; this UI does not invent extra basis steps.

Desktop 1440×1000; mobile 390×844; narrow 320×900. Inspected sidebar/mobile
navigation, keyboard disclosure, Today focus, sources, recovery and shared
Panorama/back. No horizontal overflow at 390 or 320. No Norte/Atlas or private
account/financial records in the product main. Compiled final console warnings
and errors: empty. A stale tab during server restart was recovered using a fresh
tab in the same browser; normal authorized navigation then passed.

Controlled equivalent failures exercised the actual UI against the same FR-30
composition: insufficient 422 (`CONTROLLED_QA_SOURCE_NOT_EVALUABLE`), runtime
502 (`FIRST_PROOF_FAILED:RuntimeError`), governed rejection 400
(`CONTROLLED_QA_GOVERNED_REJECTION`). The QA launcher only raises failures;
it never manufactures observations or successful projections. Each recovered
the original persisted real projection via GET. Runtime restored to real mode.

## Reobserve, history and reload

Real public reobservation through the compiled browser, pinned to code commit
`1ae70d0e0a89e9af69ed53d5dbbaf1de8bd86b0b`, returned POST 201:
- Context: `xeed:production-first-proof:2`.
- Signal: `xignal:0a938c6f77e90932e01b52debd0e8087`.
- Observed at: `2026-10-04T02:19:19.943586+00:00`.
- Same source, constrained assertion and explicit unknowns, OBSERVED/CURRENT.

SQLite retains two distinct immutable session projections, not an overwritten
first record. Canonical stored payload SHA256 values:
- First: `f6bd4c59baf35379e00436cae973f0981273cd3de090a993ec87020f7ad5a709`.
- Second: `5a4a77ca3bd4ef3cf5febb8e70a6db78c3b80e09ce332bc3bf3915020d7b672d`.

Browser reload and a complete HTTP runtime process restart followed by browser
reload recover the exact second signal ID, observation timestamp and organization.
The persisted read-model continuity marker remains PERSISTED_RUNTIME_READ_MODEL.
Private Admin inputs were never submitted as evidence.

## Evidence and final state

`apps/web/experience/qa/037-customer-zero/browser-evidence.json` records the
observed DOM identity, timestamps, signal IDs, common renderer proof, process
restart/reload and responsive dimensions without credentials. Screenshots in
the sibling directory include NO_XEED, controlled failures, real narrative and
final desktop/mobile. `real-narrative-desktop.png` is earlier iteration evidence;
`final-desktop.png` supersedes it for the final reading.

IMPLEMENTED + RUNTIME_CONNECTED + AUTOMATED_QA_PASS + REAL_E2E_PASS +
VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING.
No production deployment or push performed. Human visual acceptance is required
by `.agents/skills/axignal-design-director/SKILL.md`; no accepted Golden Master
or human sign-off is invented. Current task stays AO-24A pending that acceptance.

The local QA credential/data are external to Git. The QA launcher is a test
composition of existing services, not a production authentication provider.
General subscriber account provisioning is outside this operator FR-30 harness.
