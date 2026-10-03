# Validation — Frontend observatory

Date: 2026-10-03. Mode: EXPLORE. Branch: codex/frontend-observatory.
Status: implemented and locally tested; canonical integration and production deployment are not claimed.

## Authority and semantic review

Read the MASTER (all 3630 lines), Constitution, HFX doctrine, Design Doctrine, Brand Asset Authority V2, frontend master brief, reconciliation record, complete frontend-brief pack, architecture overview/terminology, logical atlas/gap ledger and relevant ADRs. The pack has an index/manifest and empty asset folders; its illustrative authority is the supplied user references. The official repository design-director and frontend-design references governed the design workflow.

Organization, attention focus/Xeed, Signal/Xignal, AXIGLAND, Panorama and AXENT remain distinct. No canonical term was globally replaced. Observed requires admitted evidence in the real system; this app uses labeled fixtures, not admission claims. Potential, unknown, derivation and evidence limits stay visible. Publication, event, detection and observation are distinguished. No opportunity score, customer inference, CRM functionality or canonical write was added.

## Actual automated results

| Check | Result |
| --- | --- |
| npm install exact lock | PASS, 57 packages, scripts disabled |
| npm run test | PASS, 9 tests |
| npm run typecheck | PASS |
| npm run build | PASS, 9 routes including three presentation API routes |
| uv sync --frozen | PASS |
| uv run ruff format --check . | PASS, 731 files |
| uv run ruff check . | PASS |
| uv run mypy | PASS, 216 source files |
| uv run pytest --basetemp=D:/AXIGNAL/.validation/frontend-035-pytest-3 --tb=short -q --maxfail=1 | PASS, 891 tests |
| uv run architecture-guard --root . | PASS, no violations |
| uv run axignal-governance | PASS, all eight gates |
| uvx --from graphifyy graphify update . --no-cluster | PASS, AST-only extraction, no LLM |
| uvx --from graphifyy graphify diagnose multigraph --json | PASS exit status; diagnostic reports 6 dangling references and 11 self loops in the existing aggregate graph, no post-build error |

The default pytest temporary directory failed with Windows access errors. A temp directory inside the repository ran 887 tests successfully but correctly failed four Decision Lab isolation tests. An existing directory outside the repository resolved the environment issue: all 891 passed. Test expectations were unchanged. Generated Next devtools and mypy caches were moved into dependency cache directories; hygiene gates were retained without exclusions or suppressions.

## Real browser journeys

Browser: Codex In-app Browser, actual runtime via CUA. Desktop 1440×900 and mobile 390×844. No synthetic screenshots. Read-only DOM inspection and real clicks/keyboard used.

- Landing: first meaningful entry, interactive observing/connecting/understanding lens, seven chapters, illustrated source identity, actual entry into Panorama.
- Panorama: all ten semantic families, potential dominant signal, direct Understand → Reason → Prove, preserved derivation and limitations, source inspector and fictitious source document.
- Time: July removes September/October information across Today and AXENT; actual historical view exposes only the known capability. Back navigation restores context. Event 28 Aug and detection/observation 1 Sep stay distinct.
- Organization: switching Norte → Atlas clears AXENT conversation. Empty selection has an actionable first-observation state.
- AXENT: actual HTTP 200 SDK UI stream; grounded explanation, a registered potential signal and registered source card. Request failure showed a retry without losing context. The origin defect (Next normalizes Request.url to localhost while public Host is 127.0.0.1) was diagnosed and repaired without allowing external origins, with regression coverage.
- Admin: twelve domains, quality detail, critical requirement, concrete action review, actual HTTP 403 authority check and visible denial. No data changed.
- Recovery: empty, unknown, loading, error and unavailable gallery; product error → return recovers the same contextual view.
- Localization: ES → EN changes document language and human copy.
- Mobile: readable stack, document width <=390px, navigation sheet and AXENT native dialog. Shift+Tab wraps within navigation, Escape closes and returns focus to its opener.
- Reduced motion: real preference control sets reduced mode; computed animated element count in main was zero. System preference is additionally respected by CSS media query. Essential actions have static equivalents.
- Console: development Fast Refresh reload warnings during source edits; no uncaught application errors observed. Final production console is recorded with captured evidence.

## Render → inspect → repair

First inspection found undersized product copy, surrounding reference annotations and an insufficiently spatial family presentation. A bounded repair enlarged reading text, improved contrast and hierarchy, and made the family atlas spatial with a linear alternative. Position is explicitly attention, not economic relations. Mobile remains a stack.

A subsequent observed asset defect clipped the Observer's beret crest. The mask was corrected against the actual source pixels. Admin's review also needed read projection / owning authority / record scope / impact separation. Both repairs are traced in convergence tasks T023–T024; no accepted Golden Master was replaced.

## Accessibility evidence and limits

Semantic navigation/main/aside, named controls, text epistemic labels, visible keyboard focus, native dialog focus/inert behavior, Escape/return focus, mobile navigation focus trap, alternative linear reading, local fonts and reduced motion. Desktop/mobile tested at the stated sizes. This is focused browser QA, not a claim of third-party WCAG certification or testing every assistive technology.

## Human review gate

AXIGNAL Design Director requires: “Automation may report defects, deltas and evidence. It MUST NOT declare a material AXIGNAL visual change accepted.”

IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING.
Retention, admiration and improved comprehension are design aims; no user research or post-launch measurements are fabricated.
## Final repair confirmation and visual evidence

T023: actual critical action dialog now separates illustrative read projection, owning authority (connection pending), record EVD-018 scope and the zero-write authority-check impact. Actual HTTP 403 and visible denial reconfirmed.
T024: actual rendered Observer now preserves the complete supplied beret, monocle, tablet and silhouette. Exact source pixels remain unchanged. Lens layer counter follows the active layer (03 / 03 when understanding).
T025: actual desktop explanation and an unsent draft remained in mobile AXENT after resizing. Mobile and desktop share one SDK Chat; closing the drawer preserves it. Context changes still replace the Chat and abort the previous stream. DOM inspection reported zero duplicate IDs; each input has its own accessible label association.

Final production console after SDK explanation and Admin denial: no warnings/errors captured. Production build passed after all three repairs, with nine routes. Local production server remains at http://127.0.0.1:3810, loopback only.

Actual JPEG evidence is in apps/web/experience/qa, with SHA-256, capture timestamp, byte length and browser in provenance.json:
- axignal-landing-desktop.jpg — 1440×900, comprehension lens and complete Observer.
- axignal-panorama-desktop.jpg — 1440×900, meaning-first attention entry.
- axignal-panorama-atlas.jpg — 1440×900, organization-centred family atlas and SDK cards.
- axignal-signal-axent.jpg — 1440×900, stored reasoning and registered composition.
- axignal-panorama-mobile.jpg — 390×844, readable subscriber stack.
- axignal-axent-mobile.jpg — 390×844, preserved contextual SDK response.
- axignal-admin-authority.jpg — 1440×900, explicit private authority/impact review and server denial.

The captures show actual local browser states; they are evidence supporting the running software, not the deliverable itself. Temporary viewport override was reset, and the final landing tab was marked as a deliverable and shown in Codex.

## Completion report

MODE: EXPLORE.
AUTHORITY_READ: sources above, canonical precedence maintained.
CHANGE: one isolated coherent frontend, complete local interaction journeys.
BROWSER_QA: desktop/mobile, SDK stream, time, evidence, recovery and private denial actually exercised.
GOLDEN_MASTER_DELTA: accepted source/Golden Master untouched; separate exploration only.
ACCESSIBILITY: named controls, text epistemology, keyboard focus/trap/return, native dialogs, reading alternative, local fonts and reduced motion; no certification claim.
EPISTEMIC_INVARIANTS: retained; all sample data explicitly fictitious.
AUTOMATED_GATES: pass as recorded above.
HUMAN_VISUAL_ACCEPTANCE: pending; no accepted visual authority was inferred.
STATUS: IMPLEMENTED + PROBADO locally. Live backend/provider integration and production deployment are not claimed.
## Final Spec Kit convergence

Outcome: converged for the explicitly specified local EXPLORE scope. Assessed current implementation against 14 functional requirements, 7 buildable success criteria, 5 user journeys and 25 tasks. No further actionable build gap remained after T023–T025. tasks.md SHA-256 was unchanged during the final convergence assessment; all 25 implementation tasks are checked. No extension hook manifest exists. Human visual acceptance and future live owning-service/provider integration remain outside this local implementation acceptance claim.

Final AST refresh: 9799 nodes / 22649 edges. Freshness check, Architecture Guard and all eight governance gates passed after the last source and evidence additions. The primary checkout at D:/AXIGNAL/Axignal remained clean.