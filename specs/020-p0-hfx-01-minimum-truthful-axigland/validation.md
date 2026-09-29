# P0-HFX-01 Validation Record

**Status:** Implementation and local proof complete; exact-head remote proof
pending. Human visual acceptance is still required before merge.

**CTO repair supersession:** Human Visual QA subsequently failed the previous
presentation and rejected the earlier `UNAUTHORIZED_VISUAL_DELTAS=0` assertion.
The pre-repair visual statements below are historical evidence only; they are
not accepted as fidelity closure. The repair record at the end of this file and
the paired screenshot evidence supersede them. Human acceptance remains
pending.

## Reentry and authority

- Repository: `RafaLopezCode/Axignal`; origin refresh succeeded.
- `main`, `origin/main`, and the feature branch base were all
  `26f298425d88c67551cd432ab35da99d975c6a7a` at reentry.
- The worktree was clean before the authorized feature branch changes.
- Work branch: `feature/p0-hfx-01-minimum-truthful-axigland`.
- Manifest V1 precheck and postcheck: PASS; 27 inputs;
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- GO: YES. The existing `AuthorizedXeed`, authorized Organization reader,
  and authorized FAXT collection reader support the minimum slice. Subject
  kind/resolution, object reference semantics, semantic relationships,
  cardinal assignment, epistemic strata, provenance, and historical graph
  remain `UNKNOWN_UNSUPPORTED` or unavailable.

## Implementation and browser evidence

- Subscriber Projection is in `application/subscriber_projection/axigland.py`.
  It requires one `AuthorizedXeedOrganization` and an immutable tuple of
  `AuthorizedXeedFaxt` from that exact authorized context. Canonical IDs are
  retained; UI keys include the identity kind so equal raw IDs cannot collide.
- The demo authority and loopback server are test/dev-only under
  `tests/support/`; the server binds only `127.0.0.1`, accepts no caller-chosen
  Xeed/Tenant IDs, and labels all returned content as synthetic in-memory data.
- The browser surface is `apps/web/subscriber/`. It renders only the returned
  projection. The context boundary is presentation containment; the browser
  draws no semantic Organization–FAXT edges. Serialized memberships retain
  the canonical `XeedId → FaxtId` pair.
- Browser E2E used the already-installed Playwright and Chrome, with outbound
  non-localhost requests blocked. No project dependency was added. Script:
  `C:\Users\usuario\.codex\visualizations\2026\09\26\01a0dc72-5baf-7563-a5ca-d4f57d9f6243\hfx01-e2e.mjs`.
- Results: authorized context, only referenced FAXTs, cross-Xeed isolation,
  selected identity / Bottom Context / AXENT synchronization, Back/Forward/
  Home/branching, no semantic edges, UNKNOWN-neutral state styling, unassigned
  epistemic axis, sidebar collapse/expand, camera, pan/zoom, minimap,
  empty/unavailable states, keyboard selection, reduced motion, narrow viewport
  without horizontal overflow, and zero console errors: PASS.
- Captures are outside the repository in the same evidence directory:
  `hfx01-golden-master-1280x720.png`, `hfx01-root-1280x720.png`,
  `hfx01-faxt-selected-1280x720.png`, `hfx01-back-restored-1280x720.png`,
  and `hfx01-narrow-640x900.png`.
- Visual deltas classified: `REQUIRED_BY_CANON`—no semantic edges, no
  unsupported Xeed-switch/write affordances, explicit unknown/unavailable
  states, and disabled historical view; `REAL_DATA`—synthetic direct-field
  content with permanent test/dev disclosure; `ACCESSIBILITY`—keyboard focus,
  reduced motion, narrow-layout root-label omission to prevent overlap, and
  sidebar collapse; `CTO_AUTHORIZED`—Golden Master LogoMark adapted inline.
  Desktop root/selected/back and narrow states were visually inspected; no
  unauthorized delta was identified in those captures. Human visual acceptance
  remains pending.

## Local gates

Final local results on the implementation worktree; pytest temporary files
and package build outputs are outside the repository.

- `uv sync --frozen`: PASS.
- `uv run --offline ruff format --check .`: PASS; 329 files already formatted.
- `uv run --offline ruff check .`: PASS; all checks passed.
- `uv run --offline mypy`: PASS.
- `uv run --offline pytest`: PASS; 266 passed.
- `uv run --offline architecture-guard --root .`: PASS.
- `uv run --offline axignal-governance`: PASS.
- `node --check apps/web/subscriber/app.js`: PASS.
- `git diff --check`: PASS.
- `uv build --offline --out-dir <external evidence directory>`: PASS; source
  distribution and wheel built successfully under `build-hfx01-final2`.
- Graphify update/check: PASS; 4,579 nodes and 7,537 edges. Diagnostics report
  zero unverified nodes, zero missing-endpoint edges, and no post-build error;
  six dangling-endpoint edges and three self-loops remain visible in the
  diagnostic output.
- Golden Master Manifest V1 verification: PASS before and after; exact digest
  above.
- Local changed-path credential-pattern scan: PASS. Gitleaks CLI is not
  installed locally; remote CI Gitleaks remains required. `.env`, environment
  values, keychain contents, and credentials were not read.
- Frontend typecheck/build/test scripts: not applicable; no canonical frontend
  package manifest, TypeScript config, or frontend test/build convention exists
  in this repository. JavaScript syntax and real-browser E2E were executed.
- Dependencies added: none.

The canonical Python gates were rerun after the final implementation changes.
The governance gate was rerun after this validation record was written.

## Scope and safety

Only the HFX-01 projection, browser demo, deterministic support/tests, feature
spec artifacts, and evidence-backed HFX integration-matrix rows are in scope.
No Golden Master input, manifest, package/dependency file, runtime provider,
production store/writer, other slice, or deployment target was modified.

`A01–A35=NO`: Golden Master unchanged; no redesign or fixture fallback; no
authorization bypass, raw-Xeed authority, cross-tenant/global FAXT leakage, ID
conflation, subject/object resolution, fake semantic edges/cardinal categories/
strata/provenance/history, UNKNOWN promotion, React domain interpretation,
AXENT transcript, label identity, dependency, production persistence/writer,
model call, secret access, deployment, unrelated VPS access, weakened gate,
skipped browser interaction, unsupported visual/production claim, or future
slice start.

## Lossless Golden Master fidelity repair

- Reentry resumed on the existing branch at `8d5c740db580e55b2566673a76525c8baa44fe0b`;
  the three in-progress browser files and the pre-change delta register were
  preserved and inspected before continuation.
- Canonical authorization, readers, Subscriber Projection, and domain contracts
  remain unchanged. The visual repair changed the browser surface and its
  evidence/tests; the later brand-source follow-up adds only allowlisted local
  asset serving, deterministic build-time generation, and asset provenance.
- The adapted stylesheet begins with the complete Golden Master `v2.css`
  source byte content after normalizing its CRLF/LF line-ending difference;
  presentation overrides follow it. The Golden Master itself remains
  read-only.
- CSP evidence: the browser served the subscriber app with `style-src 'self'`.
  Static inline style attributes were removed; the depth stops now render at
  their Golden Master positions. Browser console errors for the HFX runtime:
  zero.
- Real-browser E2E in Chrome used 1280×720 and 640×900, reduced motion, and a
  route that aborted all non-localhost requests. V01–V18 passed. AXENT
  structure, disabled capabilities, active canonical identity, empty
  transcript, unavailable composer/moves, history/camera behavior, unknown
  preservation, no semantic edges and empty/unavailable responses passed.
- At 640×900, document scroll width was 640 px; the composer remained inside
  the viewport. Reduced-motion focus caused zero `requestAnimationFrame`
  calls.
- Paired screenshots are stored outside the repository in the existing task
  evidence directory. They include Golden Master and HFX default, AXENT,
  selected-node and Bottom Context at 1280×720, plus HFX narrow at 640×900.
- Golden Master Manifest V1 postcheck: 27 files, digest
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`, PASS.
- Full local suite after the presentation test was added: 268 passed. Pytest
  temporary files were directed to the task evidence directory because the
  default Windows temp/cache locations are not writable in this sandbox.
- Ruff format, Ruff check, mypy, Architecture Guard and AXIGNAL governance:
  PASS. `uv sync --frozen`: PASS. `uv build --offline` built the sdist and
  wheel outside the repository. Graphify structural update/check passed;
  diagnostics report six dangling-endpoint edges and four self-loops, with no
  missing endpoints or post-build errors.
- Changed-path credential-pattern scan: no hits. Local Gitleaks executable is
  unavailable; exact-head remote Secret scanning remains required.
- Browser screenshots, scripts and build outputs remain outside the Git
  worktree. Human Visual QA is still `PENDING`; automated browser evidence does
  not close human acceptance.

## Authoritative brand assets

- Read-only source inventory: five SVGs in `D:\AXIGNAL\LOGOS`. SHA-256 values
  and visual classification are recorded in
  `docs/design/BRAND_ASSET_AUTHORITY_V1.md`; source files were re-hashed after
  generation and remain unchanged.
- The former inline approximation is replaced in the same Golden Master logo
  slots by the official horizontal light logo and official isotope. The
  official horizontal dark logo is included for dark-background readiness;
  no dark theme was introduced. Header/sidebar geometry is unchanged.
- Seven assets are copied/generated in `apps/web/subscriber/assets/brand/`.
  `brand-assets.v1.json` records source/output SHA-256, output dimensions and
  format and transformation. SVG derivatives normalize line endings and
  trailing horizontal whitespace only; vector paths, colors, viewBox, and
  artwork remain unchanged. The two PNGs were rasterized directly from the
  authoritative SVG by Chrome Canvas; ICO embeds the 32×32 PNG. No
  raster-to-raster resizing or image dependency was added.
- Browser favicon and all seven allowlisted asset URLs returned HTTP 200 with
  the expected media types. Chrome rendered the light and dark wordmarks,
  shared gold isotope, and 16×16/32×32 favicons without clipping or distortion;
  the subscriber header uses the light logo at the Golden Master slot ratio.
  Runtime console errors: zero; browser requests stayed on loopback.
- Final full validation after this update: `uv sync --frozen`, Ruff format,
  Ruff check, mypy, Architecture Guard, AXIGNAL governance, deterministic
  build, and Manifest V1 all PASS; pytest: 270 passed. Graphify: 4,634 nodes,
  7,613 raw edges, zero missing endpoints, six dangling endpoints, five
  self-loops, no post-build error. `git diff --check` PASS.
- No manifest/PWA, Apple touch icon, Open Graph image, public URL, social
  profile, SEO metadata, or structured data was added: the repository has no
  such consumer or canonical public routing to support those claims.

## Human-First presentation semantics repair

This section supersedes earlier copy-state descriptions and test counts above
for the final precommit worktree. It does not supersede the canonical authority
or Golden Master evidence.

- `apps/web/subscriber/presentation.js` is the single subscriber-copy
  authority. Canonical predicate/state identifiers map to semantic keys, then
  to localized messages. Static labels, accessible names, titles, placeholders,
  metadata and dynamic copy are bound to catalog keys; the UI does not derive
  labels by editing machine tokens.
- English is the only populated locale. Locale selection canonicalizes BCP-47
  tags and falls back to English without changing any canonical field. No i18n
  dependency was added.
- `MAINTAINS_STANDARD` remains unchanged in the projection and maps to
  `predicate.maintainsStandard` / “Maintains a standard”. Unrecognized
  predicates use a neutral “Information” label. Presentation labels do not
  determine identity.
- Currentness `UNKNOWN` is rendered as “How current this information hasn't
  been verified.” `subjectKind` and `subjectResolution` remain
  `UNKNOWN_UNSUPPORTED` in the serialized projection and are omitted from the
  primary UI because they are not actionable there. Neither state is collapsed
  into the other or into false/absence.
- Non-actionable empty Connections and missing fields are quiet. A load failure
  has plain user-facing copy. The demo indicator says “DEMO · EXAMPLE DATA”;
  test/dev and authorization-contract wording is not emitted to subscribers.
- `presentation-copy-leakage-register.v1.md` records the source value,
  previous render, surface, meaning, desired user copy, localization need and
  repair. The visual-delta register records this as a copy-only supersession.
- Dedicated Chrome regression: raw `UNKNOWN_UNSUPPORTED` visible NO; raw
  `UNKNOWN` enum visible NO; canonical `UNKNOWN` preserved YES;
  canonical `UNKNOWN_UNSUPPORTED` preserved YES; the raw
  `MAINTAINS_STANDARD` token remains internal. Currentness, empty and load
  failure copy pass. Browser errors: zero; requested hosts: loopback only.
- Chrome V01–V18 pass at 1280×720 and 640×900, with reduced motion and
  non-localhost requests blocked. The presentation-copy audit and paired
  screenshots remain external evidence. Human Visual QA remains PENDING.
- Final Python validation: `uv sync --frozen`, Ruff format check, Ruff check,
  mypy, 273 pytest tests, Architecture Guard, AXIGNAL governance, and
  deterministic source/wheel build all PASS. Build outputs are outside the
  worktree.
- Graphify update/check PASS: 4,650 nodes, 7,382 edges; zero unverified nodes,
  missing endpoints, dangling endpoints, or post-build errors; five self-loops.
  Semantic community labels were not refreshed because that step invokes an
  LLM and is not required for structural checks.
- Golden Master Manifest V1 PASS: 27 inputs; digest remains
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- Changed-path credential-pattern screen PASS with zero matches across 21
  intended paths; `.env` and credentials were not read. Gitleaks is not
  installed locally; exact-head remote Gitleaks remains a required gate.
- Brand generator was rerun against the authoritative local source with output
  directed outside the worktree; SHA-256 matched all seven assets and the
  derivative manifest exactly.

## Left sidebar editorial parity repair

The source comparison used the executable Golden Master sidebar in
`D:\AXIGNAL\UX DEEPSEEK\src\v2\Gov.tsx` and its stylesheet in
`D:\AXIGNAL\UX DEEPSEEK\src\styles\v2.css`. The subscriber stylesheet retains
the source values for the standard sidebar width (252px), the 220px compact
desktop breakpoint, 26px horizontal scroll padding, 22px/24px section rhythm,
9px tracked section captions, 11px row padding, and 1px separators. No Golden
Master input was changed.

The HFX sidebar now omits an unsupported workspace value and authenticated
account identity, shortens the visible scope value to “This view”, removes
false switcher/chevron affordances, and preserves the unavailable Memory and
Uncertainty rows as quiet empty values with screen-reader-only explanations.
Research remains the only available governance action. Capability categories
are presentation metadata and do not modify canonical state. The test/dev
disclosure remains separate from account presentation.

The collapsed rail reuses the Golden Master control order and styling where
authorized: Today, active Xeed identity, disabled create-context affordance,
separator, Governance, and flexible spacer. Today remains actionable, current
Xeed is a static accessible group, and Governance expands the sidebar and
focuses its section. At compact viewports, the rail is the default; expansion
opens the full sidebar without removing the field from the layout.

The Golden Master and HFX browser captures were made at the same 1280×720
viewport. Sidebar width is 252px in both; horizontal content padding is 26px;
the Xeed card dimensions and governance row heights/column alignment match the
source layout. The intentionally absent workspace value shortens its section;
the Xeed caption/divider sit about 8–10px higher, while Governance and its row
baselines remain within about 2–4px of the reference. The footer omits an
unauthenticated identity; only the discreet demo disclosure remains. No
pixel-perfect claim is made.

Browser interaction evidence: the Research row exhibited the brass hover
state; the collapse control changed its accessible name and expanded state;
Tab reached Today, Enter returned a selected detail to the Organization, Tab
skipped the disabled create-context control, and Space on Governance expanded
the sidebar and focused the Governance section. At a 640px viewport the rail
is the initial compact navigation; expanding it presents the full sidebar as
an overlay while leaving the field in place. Focus-visible styling and hover
rules were inspected in CSS. The active Xeed remains a static accessible group;
unsupported workspace/account controls were not fabricated.

Sidebar contract and server tests: focused set 11 passed; full `uv run pytest`:
274 passed (pytest emitted a Windows cache-directory permission warning; no
test failed). Canonical local gates after the repair: `uv sync --frozen` PASS;
Ruff format PASS (333 files); Ruff check PASS; mypy PASS (63 source files);
pytest PASS (274); Architecture Guard PASS; AXIGNAL governance PASS.

Graphify update and check PASS: 4,655 nodes, 7,391 edges; diagnostics report
zero unverified nodes, missing endpoints, dangling endpoints, duplicates, or
post-build errors; five self-loops remain. Deterministic offline source/wheel
build PASS, with outputs stored outside the repository. Golden Master Manifest
V1 PASS: 27 files, digest remains
`1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.

Changed-path secret-pattern scan: 8 files, zero hits. Gitleaks is not installed
in the local environment; exact-head remote Gitleaks remains required. The
brand-asset generator's repeat run ended with an unsettled top-level await
inside its local Chrome rasterization step. Generated output was directed
outside the repository, and no branded asset or manifest was changed. Existing
tracked brand asset provenance and prior verified hashes remain intact.

Source, keyboard, compact layout, same-viewport visual comparison, and local
gates are complete. Human Visual QA remains `PENDING`; exact-head remote CI and
Gitleaks remain pending for the documentation-and-sidebar commit. No
pixel-perfect, human-acceptance, or merge-readiness claim is made here.

The human-provided breadcrumb comparison exposed a focus-trail presentation
regression: history entries had no visible separators, and the trail competed
with the field's Signals label. The repair adds decorative `/` separators,
constrains the trail width, truncates long labels with their full text retained
in the title, and removes the session-only qualifier from the cramped compact
layout. Focused contract/server tests pass (13 tests); the complete local gate
set was repeated after this repair, while human visual acceptance remains
pending.

The follow-up field-controls comparison confirmed the V2 actions are zoom in,
zoom out, fit all, center the primary context anchor, and reset exploration.
The subscriber controls now use the V2 1.3 zoom step, the reset glyph, and a
deterministic reset to Organization focus, initial history, depth, and fitted
camera. The minimap SVG is sized to its container instead of the browser's
default intrinsic 300×150 canvas; its viewport outline is softened.

No semantic graph edges are available in the authorized subscriber payload.
It contains explicit `XeedFaxtReference` membership records only. The V2
reference `src/v2/data.ts` supplies a separate static `EDGES` fixture for its
illustration; those edges are not canonical relationship authority. The field
and minimap therefore continue to show only the three authorized nodes and no
connecting lines. Rendering membership as an economic relationship would be
false. The server contract now explicitly asserts that no relationships are
serialized. Human Visual QA remains pending.

After the focus-trail/menu/minimap changes, the focused presentation/server
set passes (13 tests), and the complete suite passes (276 tests). `uv sync
--frozen`, Ruff format (333 files), Ruff check, mypy (63 files), Architecture
Guard, AXIGNAL Governance, Graphify update/check/diagnostics, JavaScript syntax,
Golden Master Manifest V1, and `git diff --check` all pass. Graphify reports
4,658 nodes / 7,401 edges, with no unverified nodes, missing or dangling
endpoints, duplicates, or post-build errors. The changed-path secret-pattern
scan reports zero hits across nine paths; `.env` was not read. Gitleaks is
not installed locally. The deterministic build recheck was attempted but
cannot resolve `hatchling` from the accessible offline cache; the previous
successful build used unchanged Python package inputs. No browser visual
acceptance was performed for these newest screenshot-driven changes.

## Synthetic UX laboratory continuation

- Implemented four allowlisted scenarios on the existing loopback test/dev
  server. Each Organization/FAXT uses the existing test/domain/application
  contracts; edges, timeline marks, extra context labels and AXENT content are
  tagged presentation-only fixtures under `uxLab`. The default route continues
  to return the canonical test/dev projection without `uxLab`; an unknown
  scenario returns 404. No production path or provider was called.
- Focused tests: 22 passed. Full suite: 285 passed. `uv sync --frozen` PASS;
  Ruff format PASS (336 files); Ruff check PASS; mypy PASS (63 source files);
  Architecture Guard PASS; AXIGNAL governance PASS.
- Chrome browser smoke used the already-installed browser and aborted all
  non-loopback requests. Sparse/Nominal/Dense/Edge Cases each returned HTTP 200
  with scenario object counts 3/9/17/12. Field/minimap synthetic edge counts
  were 0/8/24/7. Selecting the edge-case FAXTs showed “Not established ·
  synthetic” and “Possible · synthetic”; raw `UNKNOWN` or
  `UNKNOWN_UNSUPPORTED` copy was not observed. Representative nominal move,
  canned composer reply, and local context-filter interactions worked. Default
  route lab controls remained hidden and composer disabled. At 390×844 there
  was no horizontal overflow; reduced-motion preference was honored.
- Dense scenario labels visibly collide in the existing fixed-slot renderer.
  At 1280×720, label overlap is also visible in Nominal and the lab toolbar
  overlays the breadcrumb/session header; Dense has materially greater label
  congestion. These are reported renderer/fixture-overlay limitations, not
  accepted UX quality. Automated scenario smoke is not human acceptance;
  normal-browser human review remains `PENDING`.
- JavaScript syntax checks PASS; `git diff --check` PASS. Golden Master
  Manifest V1 PASS: 27 inputs and digest
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- Graphify update and check-update completed; diagnostics: 4,692 nodes,
  7,755 raw links, 0 unverified nodes, 0 missing endpoints, 6 dangling
  references, 5 self-loops, and no post-build error. The six dangling links
  are references from existing docs to the excluded external HFX research
  source-pack document; Graphify remains structural understanding, not product
  authority.
- Changed-path credential-pattern scan: 14 paths, zero hits. Local Gitleaks
  is not installed. `uv build --offline` was attempted with output directed
  outside the repository, but the build could not resolve `hatchling` from the
  accessible offline cache. Dependencies were not installed; this build gate
  remains unverified. `.env` and credential stores were not read.
- The lab work remains uncommitted and unpushed. No PR or exact-head remote CI
  proof is claimed. Human review is required before treating UX coverage as
  accepted. No new slice, HFX-02, deployment, or live/model/provider call was
  started.
- Minimap comparison against the frozen V2 source found a second full-canvas
  border plus a duplicate, high-contrast viewport outline. The nested canvas
  rect was removed and the viewport stroke was removed while retaining the
  subtle viewport fill, click-to-center behavior, and the single outer card
  frame. The current loopback browser was reloaded and visibly shows one frame
  with no inner gold border. The Golden Master source was not modified.
- The minimap border regression assertion passes. After this correction,
  `uv sync --frozen`, Ruff format/check, mypy, all 285 pytest tests,
  Architecture Guard, AXIGNAL governance, JavaScript syntax, Graphify
  update/check, Manifest V1, changed-path secret-pattern scan, and
  `git diff --check` were rerun and passed. The offline package build remains
  unverified because `hatchling` is absent from the accessible cache; no
  dependency was installed.

## Remote proof

This is the precommit validation record. It intentionally does not embed the
final commit SHA or its exact-head CI result: changing this file after remote
validation would create a new, unvalidated HEAD. Record commit/branch SHA, PR
identity/state, exact-head CI, deterministic validation, Graphify CI checks,
and Gitleaks in the PR and final delivery ledger. The PR must remain open and
unmerged. Human visual acceptance is still required; HFX-02 is not authorized.

## Synthetic UX findings repair continuation

- Re-entry remained on `feature/p0-hfx-01-minimum-truthful-axigland` at
  `863b5db49c40b00c3854f8fb02d2e47670c6136a`. The existing 14 changed paths
  were inspected and preserved; no path outside the authorized HFX-01
  application, tests, and spec artifacts was entered. No commit, push, merge,
  branch switch, reset, stash operation, or remote mutation was performed.
- Removed the in-product scenario toolbar. Synthetic scenarios remain selected
  only through the loopback test/dev server query allowlist; the regular
  subscriber route remains synthetic-lab-free.
- Inspected executable V2 `Field.tsx` and `data.ts`: authored stable world
  coordinates and screen-space labels; placement via authored side thresholds;
  no general dense-graph collision solver, wrapping, or truncation; semantic
  zoom tiers at 0.78 and 1.2 with attention-aware label/edge treatment. V2's
  static edges remain illustration data, not canonical Relationship authority.
- Added a deterministic screen-space label candidate pass with priority order
  focus → Organization → synthetic focus-neighbors → ordinary context. It
  checks field bounds, fixed obstacles, occupied labels, node marks, and
  synthetic edge segments; it tries alternate sides and declutters lower
  priority labels when no legal candidate remains. At overview zoom ordinary
  labels reduce while all node marks stay present. A focus-priority label may
  tolerate an edge intersection when every otherwise valid side crosses an
  edge. World coordinates and topology are unchanged. No fixture IDs or
  scenario-specific positioning rules were added.
- Browser evidence is limited to the available 1872×1244 viewport: Nominal and
  Dense captures showed no obvious label-label or label-node collisions after
  repair; zoom-out capture reduced labels while preserving node marks. One
  selection synchronized protagonist, camera, Focus Trail, Bottom Context,
  and AXENT context. Exact collision counts and the required 1280×720 multi-zoom
  and full navigation/minimap sequence remain pending Human QA. No human visual
  acceptance is claimed.
- Focused UX-lab contract tests: 14 passed. Full local suite: 287 passed with
  pytest cache disabled. Ruff format check (336 files), Ruff check, mypy (63
  source files), Architecture Guard, AXIGNAL governance, and JavaScript syntax
  passed. `git diff --check` passed. `uv sync --frozen` and the deterministic
  build could not be re-established: the configured uv cache is access-denied,
  and an isolated offline cache has no `hatchling`; no package was installed
  and no dependency/configuration was changed. Build status remains blocked by
  local offline cache/environment, not recorded as PASS.
- The Golden Master was not modified. Manifest V1 digest remains the expected
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`;
  final Manifest V1 verification passed for all 27 inputs.
- Final structural Graphify run used `graphify update . --no-cluster` and
  `graphify check-update .` (PASS). Diagnostics: 4,703 nodes, 7,771 raw edges,
  zero unverified nodes, missing endpoints, or duplicate edges; six dangling
  endpoints, five self-loops, no post-build error. The dangling references
  match the previously documented references to excluded external research
  source-pack material. No semantic extraction or model call was run.
- Final changed-path credential-pattern scan covered the 14 in-scope changed
  paths and found zero matches. `.env` and credential stores were not read.
  Local Gitleaks is unavailable; no remote/CI secret-scan result is claimed.
- Gate status: Ruff format 336 files PASS; Ruff check PASS; mypy 63 source
  files PASS; pytest 287 PASS; Architecture Guard PASS; AXIGNAL governance
  PASS; `node --check` PASS; `git diff --check` PASS. Direct executables from
  the existing `.venv` were used because `uv sync --frozen` failed before
  syncing when its configured cache could not open
  `C:\Users\usuario\AppData\Local\uv\cache\sdists-v9\.git` (Windows
  access denied, OS error 5).
- Build diagnosis: `pyproject.toml` declares `[build-system]` with
  `requires = ["hatchling"]` and `build-backend = "hatchling.build"`; the
  declaration is syntactically correct. `uv build --offline` with a fresh
  isolated cache failed because `hatchling` was not cached and network access
  was disabled. Thus the configured command is not runnable in a clean empty
  offline cache; this run does not establish a repository defect or a
  successful deterministic build. No dependency/configuration change or
  package installation was made. `DETERMINISTIC_BUILD=BLOCKED_LOCAL_OFFLINE_CACHE`.
- Final scope audit found exactly the 14 expected HFX-01 app/spec/test paths,
  with no other changed paths. `git diff --check` passed. Work remains
  uncommitted and unpushed; no PR/remote proof exists. Human QA at 1280×720,
  all required zoom levels, complete navigation, minimap synchronization, and
  edge readability remains pending. No JEV/OpenAI/provider call, HFX-02,
  deployment, commit, push, or merge occurred.
- No JEV, OpenAI, or external provider calls were made. This continuation did
  not commit, push, merge, start HFX-02, or deploy.

## Human minimap-fit correction

- The screenshots showed a real minimap framing defect: fixed normalized
  bounds were wider/taller than the current graph's node extents, leaving
  excess blank space when the map was shown larger. Replaced those static
  extents with deterministic padded bounds derived from current world nodes.
  Nodes, synthetic edges, camera viewport, and click-to-center now share the
  same forward/inverse coordinate mapping; camera viewport coordinates are
  clipped to the map's padded content bounds. Main graph positions, topology,
  and camera fitting are unchanged.
- Reloaded the loopback `SYNTHETIC_NOMINAL` route and inspected the resulting
  minimap in the current browser. The node/edge drawing now uses the available
  map interior with an even inset. This visual inspection used the available
  browser viewport, not 1280×720; complete pan/zoom/resize synchronization and
  human acceptance remain pending.
- Added a deterministic contract regression for derived map bounds and shared
  node/edge/camera/click mapping. Focused UX-lab tests: 9 passed; full suite:
  288 passed. Ruff format (336 files), Ruff check, mypy (63 files), Architecture
  Guard, AXIGNAL governance, JavaScript syntax, and `git diff --check` passed.
- Graphify was refreshed with `--no-cluster`; `check-update` passed. Structural
  diagnostics: 4,708 nodes / 7,781 raw edges, zero unverified nodes, missing
  endpoints, duplicates, or post-build errors; six previously documented
  dangling external-source references and five self-loops remain. Manifest V1
  verification passed: 27 inputs and digest
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- Final scope audit remains exactly 14 expected HFX-01 paths; changed-path
  credential-pattern scan found zero matches. `.env` was not read. `uv sync
  --frozen` remains blocked by the local uv-cache access denial, and
  `uv build --offline` remains blocked because the isolated cache lacks
  `hatchling`. No dependency/configuration changes were made. The complete
  human 1280×720 pan/zoom/resize QA remains pending; the browser is left at
  `http://127.0.0.1:62331/?scenario=SYNTHETIC_NOMINAL`.

## Xeed sidebar scale and authority regression

- Reworked the active-Xeed control as a quiet dropdown with an Organization
  reference shown separately. “New Xeed” remains visually secondary and
  disabled because no creation writer exists.
- The Nominal UX fixture contains 101 labels, all explicitly marked synthetic.
  The list has a bounded scroll region and local name search. Only the Xeed
  already represented by the authorized projection is enabled; the other
  fixture labels are disabled with an explanation. Selecting fixture labels
  cannot rename the active Xeed or change the Organization/projection.
- In the loopback browser, opened the list, filtered for `098`, and verified
  the page stayed on the Asterion projection; Escape closed the menu and
  restored the active-Xeed button. Human visual QA at 1280×720 remains pending.
- Focused HFX presentation, server, and UX-lab contracts: 25 passed.
  `node --check` for `app.js` and `presentation.js`, and `git diff --check`
  passed. No commit, push, merge, HFX-02, deployment, or provider call occurred.
- The updated inspection URL is
  `http://127.0.0.1:63359/?scenario=SYNTHETIC_NOMINAL`; its loopback-only
  test/dev server remains running. The earlier server was left untouched.

## Minimap framing correction

- The submitted minimap image showed that the prior 8-unit SVG inset plus
  additional 3-unit/4% data padding left excessive whitespace on all edges.
  Removed the data padding and reduced the inset to 5 SVG units, leaving a
  small safety margin around the largest node marker while using the full
  observed node extents. The canonical node positions and camera mapping stay
  unchanged. Previous visual acceptance of the padding amount is superseded;
  human QA remains pending.

## Locale UX foundation check — 2026-09-28

- Before this change, the subscriber document fixed `lang="en"`; the actual
  presentation catalog had only English copy, no browser-locale negotiation,
  no user override, and no locale preference persistence. Hard-coded strings
  outside the presentation-copy keys also remained in the interface.
- The current implementation resolves the synthetic preview in this order:
  supported explicit lab selection, first supported `navigator.languages` /
  `navigator.language` preference, then English. Unsupported browser tags are
  skipped. The default browser session resolved Spanish from its browser
  preference. “Automatic” removes the lab override and returns to that browser
  preference.
- The selector is under the synthetic QA operator’s Account/Preferences area.
  It is absent outside the loopback scenario lab. Selection is stored only in
  that browser’s local storage for the synthetic preview; it is not an account
  preference and does not establish production locale authority.
- Manually switched the live synthetic Nominal scenario through English,
  Spanish, German, Japanese, Arabic, and Automatic. Accessibility state showed
  localized examples across the sidebar, AXIGLAND zone/depth labels, Focus
  Trail, Bottom Context, AXENT headings/composer, timeline, and field-control
  labels. A German override remained selected after reload; choosing Automatic
  and reloading returned to the browser's Spanish preference. Arabic visibly
  changed the interface direction to RTL. The selector was left on Automatic.
- These are intentionally partial stress profiles, not translations. Some
  controls and status copy remain English (including some “current view” /
  helper text); the AXENT fixture transcript and question text remain in their
  source language. German text expansion is represented by longer labels.
  Japanese CJK and Arabic RTL exercise scripts and direction, but do not prove
  complete glyph, typography, accessibility, or narrow-viewport quality.
- Source-language FAXT values, Organization display identity, synthetic
  transcript text, and canonical identifiers remain unchanged when locale
  changes. Locale changes affect presentation copy and document direction
  only. No i18n dependency was added and no external model/provider was called.
- Focused presentation, web-server, and UX-lab contracts: **26 passed**.
  `node --check` passed for `app.js` and `presentation.js`; `git diff --check`
  passed. This check does not claim full localization or complete human visual
  acceptance at 1280×720; that QA remains pending.

## Q2 — reconcile with canonical Design Director / iconography authority

- Re-entry confirmed branch `feature/p0-hfx-01-minimum-truthful-axigland`,
  historical PR head `863b5db49c40b00c3854f8fb02d2e47670c6136a`, and canonical
  `origin/main` `b7837dcd347e6a14267b709fa40340f9028e35b6`. Merged canonical main
  with a normal merge commit (`a3d381e7b15bdcc3c49c5b694aa88bab90442691`);
  no history rewrite or force push occurred. The pre-existing HFX dirty work
  remained present throughout reconciliation.
- Removed the dirty HFX `DESIGN_SYSTEM.md` iconography override and the
  untracked duplicate `ICONOGRAPHY_AUTHORITY_V1.md`. ADR-0022 and the canonical
  Design System on main remain the only reusable iconography authority. The
  HFX sprite consumes the vendored Lucide subset at 1.5-unit stroke; the
  upstream ISC and MIT license notices are retained. No icon package or runtime
  dependency was added; Golden Master icon glyphs were not normalized.
- Exact 1280×720 browser inspection found that the long synthetic Edge Cases
  focus trail compressed labels and overlapped the session marker. The trail
  now keeps Today and the current stop, summarizes hidden stops with a
  locale-formatted count, and leaves sequential history available through
  Back/Forward. The marker yields when that compact form is active. This is a
  presentation-only correction; focus state and navigation history are intact.
- Browser scenarios inspected at an actual CSS viewport of 1280×720:
  Nominal, Dense, and Edge Cases. The document remained 1280×720 without
  horizontal or vertical document overflow. Edge Cases exposed no raw
  `UNKNOWN`/`UNKNOWN_UNSUPPORTED` subscriber copy. Back then Forward moved to
  the expected adjacent history entries while retaining the compact trail.
  The minimap and all five graph controls were present in Dense. An attempted
  1240×720 override produced an actual 1280×720 browser viewport, so exact
  1240×720 behavior is not claimed. English, Spanish, German, Japanese, Arabic
  and Automatic locale profiles were selected in the loopback Settings preview;
  Arabic set RTL and each profile retained 1280×720 document bounds. This is
  layout-stress evidence only, not full localization.
- Final deterministic gates on the reconciled candidate: `uv sync --frozen`
  passed; Ruff format (342 files), Ruff check, mypy (63 source files),
  `pytest` (**292 passed**), Architecture Guard, AXIGNAL governance (all eight
  checks), and JavaScript syntax checks passed. The first pytest attempt used a
  protected shared Temp root; the successful full run used a fresh external
  `--basetemp`. `git diff --check` passed. Graphify refreshed to 4,773 nodes,
  7,589 edges, 421 communities. Golden Master Manifest V1 verification passed
  with 27 inputs and unchanged digest
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- `gitleaks` is not installed locally. The GitHub exact-head CI result is still
  required after publishing the candidate. Product/domain, production, and
  Golden Master source bytes were not changed. Human visual acceptance remains
  pending for the exact rendered candidate; no merge is authorized until that
  acceptance is explicitly recorded.

### Q2 follow-up — minimap navigation and epistemic color alignment

- Reproduced the reported issue in `SYNTHETIC_DENSE` at 1280×720. Click-to-
  center already moved the camera, but the camera window was invisible and the
  minimap offered no continuous drag navigation. The camera window now has one
  restrained inset outline/fill, and pointer dragging continuously recenters
  the view. Click-to-center and Enter/Space centering remain available.
- Node colors in the minimap now use the same epistemic-state tokens as field
  nodes. Synthetic UX-lab edges now carry an explicit synthetic epistemic state;
  line color and dash pattern follow the V2 epistemic palette. Relation type
  no longer drives epistemic color or pattern. Missing/invalid states resolve
  to neutral UNKNOWN. None of these fixtures enter canonical relationships or
  product truth.
- Browser verification: Dense field rendered at 1280×720; zooming changed the
  minimap camera window, dragging inside it moved the graph, and Reset restored
  the complete fitted view. Screenshot inspection showed epistemic colors on
  field and minimap nodes/edges. This does not constitute human visual
  acceptance.
- Full local gates on these bytes: frozen sync, Ruff format/check, mypy,
  `pytest` (**292 passed**), Architecture Guard, AXIGNAL governance (all eight
  checks), JavaScript syntax, and `git diff --check` passed. Graphify update,
  `check-update`, and multigraph diagnostics passed: 4,777 nodes, 7,596 edges,
  zero unverified/missing/dangling/duplicate edges, five self-loops.
- Golden Master Manifest V1 verification passed: 27 inputs and unchanged
  digest `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
  Local Gitleaks remains unavailable; exact-head remote CI must be rerun after
  push. Human Visual QA remains pending.
