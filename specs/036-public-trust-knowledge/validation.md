# Validation — 036 Public Trust, Knowledge and Access

Date: 2026-10-03. Isolated branch: `codex/frontend-observatory`.

## Completion report

- **MODE:** EXTEND for public pages; human-authorized refinement of the exploratory Landing/Panorama from feature 035. No replacement or promotion of an accepted Golden Master.
- **AUTHORITY_READ:** MASTER Product Model V2; Engineering Constitution; HFX; Design Doctrine; Brand Asset Authority V2; Frontend Brand/Generative Experience Master Brief; reconciliation record and frontend-brief folder; relevant identity, public brief and graph ADRs/contracts; architecture overview, terminology and current-state ledger. Design Director and routed frontend design references are subordinate to those authorities.
- **CHANGE:** Source-backed Knowledge index and six full articles; two local doctrine-source permalinks; policy hub and privacy/terms/cookies drafts; Contact and GDPR local request drafting; Login/Signup with prepared Google/OpenAI identity boundary; six-language public/product presentation; official provider assets served locally. Landing adds reference pricing, separate human advisory, moving case ribbon with a focal aperture, inspectable trust, real article previews, newsletter draft preparation, chapter navigation and back-to-top. Shared footer links LinkedIn. Panorama organization centre, reading controls, composer and timeline geometry repaired. Shared Axent identity uses Fraunces, initial capital and #333333. Approved original Observer poses are reused via SVG viewports/masks; source PNG and brand originals are unchanged.
- **BROWSER_QA:** Actual optimized Next.js app in Codex in-app browser at `http://127.0.0.1:3810`. Desktop 1743×1188; mobile 390×844; narrow 320px German access check. Primary navigation, six languages, search/filter/empty recovery, full article and source access, local draft validation/preview/download/edit, prepared-provider unavailability/retry, conditional GDPR rights, privacy notice/reopening, responsive Panorama, historical reading, reduced motion, case pause/selection and nested-dialog Escape were exercised. Final console warning/error query was empty. Details below.
- **GOLDEN_MASTER_DELTA:** Changes are confined to the isolated 035/036 experience and requested shared presentation. No canonical brand source art or accepted legacy Golden Master changed. This is evidence for human review, not a new Golden Master acceptance.
- **ACCESSIBILITY:** Native language select and native modal dialogs; unique accessible dialog headings; nested Escape closes only the top dialog and restores focus without losing the parent draft; linked label/error messages; meaningful unknown/unavailable recovery; roving keyboard tabs; readable narrow layouts; ≥44px primary controls; paused/reduced case motion; epistemic meaning also represented in text.
- **EPISTEMIC_INVARIANTS:** Organization is an economic subject; observation focus allocates attention around it. Signal is emergent output, not certainty. Panorama projects one AXIGLAND, never owns or replaces it. AXENT investigates/explains without evidence-admission authority. Historical source visibility and explicit UNKNOWN/POTENTIAL are preserved. No canonical writes, synthetic dates, invented clients, universal opportunity score, account privileges or CRM workflows were added. Demo economic content remains fixture-only. Public terminology does not rename canonical code identifiers.
- **AUTOMATED_GATES:** Frontend tests 20/20; typecheck PASS; optimized build PASS (28 generated pages); translation AST inventory 912 entries with zero missing DE/PT/FR/IT values. Repository gates listed below all passed. No suppressions or weaker gates.
- **HUMAN_VISUAL_ACCEPTANCE:** PENDING. Only explicit human acceptance can close the visual gate.
- **STATUS:** IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING. Running locally; not merged, deployed or verified against production identity/email/rights services.

## Rendered findings and corrections

1. Organization-centre content now fits within a calm 206px circle; separate logo, title and contextual text stay inside. Mobile uses the corresponding smaller geometry.
2. Composer uses separate grid space for the 44px send action; the native textarea resize affordance no longer occupies its button space.
3. Axent uses Fraunces and #333333 in the contextual panel, Admin and Landing chapter 06. Final computed demo centres are both 727.125px, with `rgb(51, 51, 51)` and `Fraunces, serif`. A more-specific legacy preview span color was corrected after rendered QA detected the blue override. Canonical AXENT identifiers are preserved.
4. Reading-mode buttons have 6px internal padding, an 8px gap and 44px hit areas.
5. Panorama timeline fills the workspace (1463px controls at the desktop QA viewport) with flex children; the three existing dated snapshots are the only available dates. Further dates come from the snapshot collection, not presentation invention.
6. Six languages: ES, EN, DE, PT, FR, IT. Native names and document language were checked, including localized Knowledge headings and bounded demo Axent responses. The completeness gate checks actual authored source strings; it does not certify editorial translation quality or human approval.
7. The human-supplied action sheet is byte-identical to `public/observer/actions.png`. Guiding, accompanying and pointing views were inspected after masking source-sheet annotations; notebook/graphic/companion poses retain the source art and the single canonical monocle. Closing walking pose was inspected with the final footer.
8. Google uses the official gradient G, local Google Sans and approved spacing. OpenAI's current website sign-in documentation calls the action **Continue with ChatGPT**. Both providers remain unavailable/prepared without registered clients or an owning AuthenticationPort. Sign-in never grants model usage, subscriber membership or Admin privileges.
9. Reference pricing uses integer cents and the MASTER economics; 100 observation allocations compute €500/month. Human advisory has its separate scope, price and applicable-VAT qualifier. The trust section offers source/temporal inspection; authorized customer testimonials/logos remain unavailable. Newsletter prepares a local draft; request, coverage acceptance and delivery consent stay distinct.
10. First-visit privacy information is compact and nonmodal; a persistent Privacy button reopens details. Only locale and notice-dismissal preferences persist in the browser. Notice dismissal expires after 180 days; drafts never enter localStorage. No optional trackers, remote-font calls or fake compliance/consent claims were introduced.
11. Mobile chapter dialog links to the requested hash and closes; `Explora` reaches `/#explore`. Back-to-top reaches `/#what`. The rendered mobile document fits within 390px. Reduced-motion preference stops the case animation, and a pause control is independently available.
12. Shared footer LinkedIn resolves to `https://www.linkedin.com/company/axignal/`, with `_blank` and `noopener noreferrer`; the final footer screenshot records the visible link.

## Other recovery and continuity evidence

- Empty Knowledge search has visible zero-result explanation and reset; evidence topic filtering yields the expected authored articles.
- Article basis links resolve to local provenance-bearing doctrine excerpts rather than an unpublished GitHub commit URL. Unknown article/source slugs return the branded 404.
- Contact validation focuses the first invalid field. Multiline preview and downloaded TXT match exactly; the browser-created local draft was checked on disk. No transmission or lodged-request receipt is claimed.
- Nested newsletter preview: Escape reduces open native dialogs from two to one, keeps the complete message and restores Review Draft focus. Closing the parent then returns focus to Prepare Request. Unique title IDs prevent ambiguous accessible names.
- Prepared Google and ChatGPT starts show truthful unavailable states and recovery. Contract tests cover strict fields, origin/Host matching, malformed/oversized payloads and wrong content type. Responses create no cookie, session or redirect.
- Historical July view does not expose later illustrative evidence/signals. Currentness and provenance remain visible.
- In-app reduced motion was selected through reading preferences and preserved during navigation to Landing; the case strip's computed animation was `none`. System reduced motion is also governed by CSS media queries.

## Deterministic repository verification

| Gate | Result |
| --- | --- |
| `uv sync --frozen` | PASS, 17 dependencies |
| `uv run ruff format --check .` | PASS, 741 files |
| `uv run ruff check .` | PASS |
| `uv run mypy` | PASS, 216 source files |
| `uv run pytest` | PASS, 891 tests |
| `uv run architecture-guard --root .` | PASS, no violations |
| `uv run axignal-governance` | PASS: architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology |
| `git diff --check` | PASS |

Python gates ran during this feature's validation; subsequent changes were frontend presentation only. Architecture Guard and all eight governance sub-gates were reconfirmed after the final frontend repair. Mypy cache lives outside the worktree in `D:/AXIGNAL/.validation/frontend-036-mypy-cache`: the generated cache exceeded the repository hygiene size threshold, so its location was repaired without weakening that gate. Graphify AST-only update completed with 9962 nodes and 23028 edges; no semantic extraction or LLM/network CI dependency.

## Convergence

Spec Kit prerequisites resolved feature 036 with spec/plan/tasks and all supporting documents. No extension hooks were registered. Assessment covered eight FR requirements, five user stories, the success criteria, final plan decisions and all 21 tasks under applicable Constitution constraints. No remaining buildable implementation gaps or contradictions found. During the convergence assessment tasks.md SHA256 stayed `3D418C6ECF17B369A209D9E0817EA2B945C649AC252D5A0B79405CCE06FAACFA`; no empty convergence phase or remediation tasks were written. Task closure and the local commit belong to the subsequent delivery phase.

## Explicit dependencies and limits

Legal responsible entity, jurisdiction and public contact mailbox remain pending publication, as requested. Policies are publication drafts. OAuth clients/service adapters, actual account/session creation, contact/rights delivery and public-brief dispatch are not connected; no simulated success. Authorized customer proof was not supplied. Canonical backend and production services were untouched. The local generative surface composes registered governed fixture components; this work does not claim live AI research, production admission or complete OAuth end-to-end verification.

## Evidence

Unedited original browser PNGs are under `apps/web/experience/qa/036-public-trust-knowledge/screenshots/`; viewport, route/state, capture time and SHA256 are in `evidence-manifest.json`. Provider/Observer asset provenance is in `asset-provenance.json`. Human visual acceptance remains pending.