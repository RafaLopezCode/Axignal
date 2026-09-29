# P0-HFX-01 Lossless Golden Master Visual Delta Register

Status: initial forensic register, captured before presentation repair.

Reference: executable DeepSeek V2 at `D:\AXIGNAL\UX DEEPSEEK`, active entry
`src/main.tsx` → `src/v2/V2App.tsx`, and the canonical runtime at
`http://127.0.0.1:8765/`. Desktop comparison is Chrome at 1280×720 with the
same reduced-motion preference; narrow comparison is 640×900. Baseline images
are retained outside the repository in the task evidence directory. Golden
Master source and its Manifest V1 remain read-only.

Classification is limited to `REAL_DATA`, `REQUIRED_BY_CANON`,
`ACCESSIBILITY`, `LOCALIZATION`, and `UNAUTHORIZED`.

## Material deltas established before repair

| ID | Golden Master behavior | Current HFX behavior | Classification | Justified? | Repair action |
|---|---|---|---|---|---|
| D01 | Persistent right AXENT column sized for moves, transcript, context and composer. | Inspector-like right surface with materially less cognitive-navigation space. | UNAUTHORIZED | No. | Restore the Golden Master column geometry and internal hierarchy. |
| D02 | AXENT is a persistent cognitive navigator. | AXENT is presented as an authorization/debug inspector. | UNAUTHORIZED | No. | Restore product-facing role; keep guarantees in contracts and tests. |
| D03 | Persistent “Ask about this node” composer and Ask action. | Composer is absent. | UNAUTHORIZED | No. | Restore an honest disabled/unavailable composer with no fabricated response. |
| D04 | Selected node appears in a semantic active-context pill. | Selected identity appears as diagnostic text. | UNAUTHORIZED | No. | Restore pill bound to canonical kind + ID, with a safe display label. |
| D05 | Contextual move pills remain visible. | Move system is absent. | UNAUTHORIZED | No. | Restore the move structure; mark unsupported execution unavailable. |
| D06 | Persistent conversation/transcript area. | Area is replaced by implementation notes. | UNAUTHORIZED | No. | Restore empty transcript structure; only explicit human and real AXENT turns may enter it. |
| D07 | Engineering authorization copy is not primary UX. | Authorized scope, reference mechanics, no-model and implementation-limit copy dominates AXENT. | UNAUTHORIZED | No. | Remove engineering diagnostics from the subscriber surface. |
| D08 | Open cartographic field without an enclosing context circle. | Large boundary circle encloses the nodes. | UNAUTHORIZED | No. | Remove the circle; keep membership only in the read contract and application state. |
| D09 | Protagonist/root is expressed through the inherited node grammar. | Organization is rendered as a large `ORG` badge/circle. | UNAUTHORIZED | No. | Remove the badge and preserve canonical identity in state and accessible naming. |
| D10 | Small marks, editorial labels and substantial negative space. | FAXT labels and metadata dominate the field. | UNAUTHORIZED | No. | Reuse Golden Master node mark, label, focus, attenuation and camera grammar. |
| D11 | Operational left navigation: Today, Workspace, Xeed, Governance and account footer. | Left column is an authorization/global-organization inspector. | UNAUTHORIZED | No. | Restore the operational hierarchy with unavailable states where actions lack authority. |
| D12 | Bottom Context is an editorial reader integrated below the field. | Bottom area is a property-grid inspector. | UNAUTHORIZED | No. | Restore Reader composition and hierarchy; populate only projection-authorized values. |
| D13 | Open cognitive cartography with spatial hierarchy, field labels, focus and minimap. | Centered three-object technical diagram with a dominant boundary. | UNAUTHORIZED | No. | Adapt the actual Field geometry and behavior to sparse canonical nodes. |
| D14 | Golden Master contains a dense fixture world and semantic relationships. | Canonical authorized projection contains one Organization and two referenced FAXTs, with no semantic edges. | REAL_DATA | Yes. | Preserve the sparse world and render zero semantic relationships; do not add fixture nodes. |
| D15 | Golden Master displays timeline marks backed by prototype history. | Canonical history reconstruction is unsupported. | REQUIRED_BY_CANON | Yes, for content only. | Keep timeline grammar; show a quiet unavailable state without markers or dates. |

## Active source component mapping

| Concern | Golden Master source | Disposition |
|---|---|---|
| App shell and responsive composition | `src/v2/V2App.tsx`, `.app2`, `.center`, `.stage2` in `src/styles/v2.css` | COPY_NEAR_LITERAL; replace only data-boundary composition. |
| Left sidebar | `src/v2/Gov.tsx`, `src/v2/XeedSwitcher.tsx`, `.gov`/`.gv-*`/`.xs-*` rules | COPY_NEAR_LITERAL; unavailable actions remain non-mutating. |
| Field, marks, camera, zoom, pan and minimap | `src/v2/Field.tsx`, `src/v2/marks.tsx`, `.field`/`.anch`/`.wires`/`.minimap` rules | ADAPT_DATA_BOUNDARY; do not copy `data.ts`, `EDGES`, fixture labels, zones as domain, or history. |
| Depth and epistemic rail | `src/v2/Lens.tsx`, `.lens-*` rules | COPY_NEAR_LITERAL; value stays presentation-only and no canonical assignment is introduced. |
| Focus navigation | `src/v2/FocusTrail.tsx`, `.trail-*` rules | KEEP_CANONICAL_EXISTING; preserve session focus history and adopt the presentation grammar. |
| Bottom Context / Reader | `src/v2/Reader.tsx`, `.reader`, `.focusview`, `.today`, `.idea*` rules | ADAPT_DATA_BOUNDARY; fixture narrative and assertions are excluded. |
| AXENT | `src/v2/Axent.tsx`, `.ax-*` rules | ADAPT_DATA_BOUNDARY; retain structure, use canonical identity for the pill, empty transcript, unavailable actions. |
| Timeline | `src/v2/Meridian.tsx`, `.meridian`/`.mer-*` rules | ADAPT_DATA_BOUNDARY; no fixture events, dates, or historical reconstruction. |
| Connections | `src/v2/Connections.tsx`, `.conn-*` rules | DO_NOT_COPY_FIXTURE; structure may remain only as a truthful unavailable/empty state, with zero semantic edges. |
| Prototype data/content/state | `src/v2/data.ts`, `src/v2/content.ts`, `src/v2/store.tsx` | DO_NOT_COPY_FIXTURE; presentation source only, never canonical truth or runtime state authority. |

## Required-state baseline assessment

| State | Golden Master reference | Pre-repair HFX | Initial classification | Acceptable before repair? | Reason |
|---|---|---|---|---|---|
| V01 DEFAULT_ROOT | `V2App` + `Gov` + `Field` + `Reader` + `Axent` | `index.html` / `app.js` | UNAUTHORIZED | No | Inspector hierarchy and enclosing circle replace the reference composition. |
| V02 FAXT_SELECTED | `Field` + `FocusTrail` + `Reader` | `app.js` | UNAUTHORIZED | No | Data selection works, but node and reader grammar differ. |
| V03 AXENT_ACTIVE_CONTEXT | `Axent` | `app.js` | UNAUTHORIZED | No | Pill is absent; raw diagnostic identity is shown instead. |
| V04 AXENT_COMPOSER | `Axent` | `index.html` / `app.js` | UNAUTHORIZED | No | Persistent composer affordance is absent. |
| V05 AXENT_MOVES | `Axent` | `app.js` | UNAUTHORIZED | No | Golden Master move system is absent. |
| V06 BOTTOM_CONTEXT | `Reader` | `index.html` / `app.js` | UNAUTHORIZED | No | Property grid replaces editorial Reader structure. |
| V07 BACK_RESTORED | `FocusTrail` + `store.tsx` | `app.js` | UNAUTHORIZED | No | Canonical history behavior passes, but inherited trail treatment differs. |
| V08 FORWARD_RESTORED | `FocusTrail` + `store.tsx` | `app.js` | UNAUTHORIZED | No | Same presentation delta as V07. |
| V09 HOME_RESTORED | `FocusTrail` + `Gov` | `app.js` | UNAUTHORIZED | No | Home returns to canonical Organization but uses different treatment. |
| V10 MANUAL_PAN | `Field` | `app.js` | UNAUTHORIZED | No | Pan functions, while field proportions/spatial grammar differ. |
| V11 MANUAL_ZOOM | `Field` + `.canvas-tools` | `app.js` | UNAUTHORIZED | No | Zoom works, while controls and node scale differ. |
| V12 MINIMAP | `Field` + `.minimap` | `app.js` | UNAUTHORIZED | No | Functional mini-view uses different placement, style, and boundary. |
| V13 DEPTH_CONTROL | `Lens` | `index.html` / `app.js` | UNAUTHORIZED | No | Control is a different button row instead of the reference rail. |
| V14 EPISTEMIC_AXIS | `Lens` | `index.html` / `app.js` | UNAUTHORIZED | No | Stops are presented as assigned strata instead of inherited unassigned grammar. |
| V15 TIMELINE_UNAVAILABLE | `Meridian` | `index.html` / `app.js` | UNAUTHORIZED | No | Timeline affordance is replaced by a disabled strip rather than adapted grammar. |
| V16 LEFT_SIDEBAR | `Gov` + `XeedSwitcher` | `index.html` | UNAUTHORIZED | No | Operational hierarchy is replaced by authority diagnostics. |
| V17 NARROW_VIEWPORT | V2 responsive rules in `src/styles/v2.css` | `subscriber.css` | UNAUTHORIZED | No | Existing layout fits but does not preserve reference component hierarchy. |
| V18 REDUCED_MOTION | V2 motion rules in `src/styles/v2.css` | `subscriber.css` | REQUIRED_BY_CANON | Yes | Reduced motion is respected; preserve that behavior during visual adaptation. |

Evidence collected from live local browser states and source inspection before
repair. These findings are a presentation audit; they do not alter domain
authority. Human Visual QA remains pending after automated repair.

## Repair implementation and evidence

The repair reuses the active V2 shell and stylesheet from the read-only
Golden Master and changes only the subscriber presentation boundary. The
canonical request context, authorized readers, projection payload, membership
meaning and server contracts were not modified. The normalized field positions
are presentation-only layout slots; they are not persisted, inferred from IDs,
or exposed as domain/cardinal assignments.

| Delta | Post-repair disposition | Evidence / remaining limit |
|---|---|---|
| D01–D02 | AXENT is a persistent 256 px cognitive navigator at 1280 px viewport width, with a separate empty transcript and full-height panel. | Browser geometry and screenshot comparison pass. Human visual acceptance remains pending. |
| D03–D06 | Composer and six move pills are present and explicitly unavailable; the transcript starts empty and remains empty after selection, camera, history, depth and disabled-action events. | AXENT contract tests and browser interaction checks pass; no response or action is fabricated. |
| D07 | Subscriber-facing authorization/debug report copy is removed. A discreet TEST / DEV · IN-MEMORY indicator remains in the left footer. | Static contract test and visible-copy browser check pass. |
| D08–D09 | No enclosing context circle, semantic connector or oversized Organization badge is rendered. The Organization remains a small field mark with its canonical label and identity in application state. | DOM asserts zero field edges; screenshot comparison pass. |
| D10 | Field nodes reuse the Golden Master `.anch`, `.dot`, `.halo` and `.anch-lbl` grammar; sparse labels remain editorial and subordinate. | Browser selected-node state passes. Differences in canonical wording are REAL_DATA. |
| D11 | Operational sidebar hierarchy is restored. Unsupported workspace, Xeed, governance and account operations remain visibly unavailable/disabled. | Browser collapse/expand and structure checks pass. |
| D12 | Bottom Context uses the V2 Reader hierarchy. It renders only Organization/FAXT projection fields and a neutral unavailable Connections state. | Root and selected-FAXT browser screenshots pass; no evidence or provenance is rendered. |
| D13 | Open field, normalized camera, pan/zoom/focus, minimap, cardinal labels and focus trail use the V2 spatial grammar. Display slots are neutral presentation state and create no edges or semantic/cardinal assignments. | Pan, zoom, focus, minimap and history checks pass. Sparse placement remains a presentation adaptation for human review. |
| D14 | Three canonical nodes (one Organization and two explicitly referenced FAXTs), with zero semantic edges. | REAL_DATA; no fixture nodes or edges copied. |
| D15 | Meridian timeline grammar remains visible, with history unavailable and no markers or dates. | REQUIRED_BY_CANON; disabled state checked in browser. |

### Visual state re-audit

| State | Browser result | Notes |
|---|---|---|
| V01 DEFAULT_ROOT | PASS | HFX and V2 reference captured at 1280×720. |
| V02 FAXT_SELECTED | PASS | Canonical FAXT focus and Bottom Context update; no inferred subject kind. |
| V03 AXENT_ACTIVE_CONTEXT | PASS | Pill follows canonical kind and ID while displaying a safe label. |
| V04 AXENT_COMPOSER | PASS | Persistent input and Ask affordance are disabled; submission adds no transcript. |
| V05 AXENT_MOVES | PASS | Six move affordances remain present and disabled. |
| V06 BOTTOM_CONTEXT | PASS | Root and selected-node Reader states captured. |
| V07 BACK_RESTORED | PASS | Prior focus and pill identity restored. |
| V08 FORWARD_RESTORED | PASS | Forward focus and pill identity restored. |
| V09 HOME_RESTORED | PASS | Home restores Organization focus; Xeed anchor remains Organization. |
| V10 MANUAL_PAN | PASS | Field camera moves without adding transcript or domain state. |
| V11 MANUAL_ZOOM | PASS | Camera zoom changes; canonical identities remain unchanged. |
| V12 MINIMAP | PASS | Map marks and viewport window render and reposition the camera. |
| V13 DEPTH_CONTROL | PASS | Depth control remains presentation-only. |
| V14 EPISTEMIC_AXIS | PASS | Four source labels remain unassigned to canonical FAXTs. |
| V15 TIMELINE_UNAVAILABLE | PASS | Meridian remains disabled; no historical data is fabricated. |
| V16 LEFT_SIDEBAR | PASS | Operational hierarchy and collapse/expand behavior work. |
| V17 NARROW_VIEWPORT | PASS | At 640×900, document width is 640 px and composer remains accessible. |
| V18 REDUCED_MOTION | PASS | `prefers-reduced-motion: reduce`; focusing a node requests no animation frame. |

Automated comparison did not establish Human Visual QA. Some differences from
the fixture world are required by canonical sparse data and unavailable
capabilities. No claim of human acceptance or zero remaining visual deltas is
made; a human must review the paired screenshots and close this gate.

### Screenshot evidence

Stored outside the repository at:

`C:\Users\usuario\.codex\visualizations\2026\09\26\01a0dc72-5baf-7563-a5ca-d4f57d9f6243\`

The directory contains paired 1280×720 Golden Master/HFX default, AXENT,
selected-node and Bottom Context captures, plus the HFX 640×900 narrow capture.
The browser blocked every non-localhost request. No provider/model call was made.

### Authoritative brand source correction

The later CTO branding authority designates `D:\AXIGNAL\LOGOS` as the artwork
source of truth. The adapted inline LogoMark has been replaced in its existing
Golden Master positions with the official horizontal light logo and isotope;
the official dark wordmark is prepared as an unused dark-context asset. This is
an expressly authorized brand-artwork delta only. Placement, shell geometry,
spacing, hierarchy, and all non-brand presentation remain unchanged. Source
inventory and output provenance are recorded in
`docs/design/BRAND_ASSET_AUTHORITY_V1.md` and
`apps/web/subscriber/assets/brand/brand-assets.v1.json`. The updated subscriber
and light/dark/small-icon asset preview are captured as
`hfx01-brand-applied-1280x720.png` and
`axignal-brand-assets-light-dark-and-small-icons.png` in the external evidence
directory above. Human Visual QA remains pending.

### Presentation semantics copy re-audit

The subsequent subscriber-copy audit supersedes the earlier wording where it
mentioned implementation or capability states:

| Surface | Previous wording/state | Current presentation decision | Semantic state |
|---|---|---|---|
| Predicate labels and accessible names | Raw predicate tokens such as `MAINTAINS_STANDARD` | Map canonical predicates through presentation keys to concise locale copy; unknown predicates use a neutral label | Canonical predicate is unchanged |
| Bottom Context currentness | Raw `UNKNOWN` | Show a localized explanation that freshness has not been verified | Canonical `UNKNOWN` is unchanged |
| Bottom Context subject kind/resolution | `UNKNOWN_UNSUPPORTED` fields | Omit both fields because neither is actionable in this surface | Canonical `UNKNOWN_UNSUPPORTED` values remain in the projection |
| Sidebar and AXENT scope | Xeed/authorization contract vocabulary | Use neutral context language | Authorization and private-context boundary are unchanged |
| Empty Connections and missing fields | “Unavailable” implementation explanation | Quietly omit non-actionable empty state and fields | Empty/unsupported capability is not converted into a domain conclusion |
| Demo disclosure | Test/development implementation label | “DEMO · EXAMPLE DATA” | Synthetic reality-level remains internal and explicit |

All subscriber static copy, accessible names, titles, and dynamic labels now
resolve through the locale presentation catalog. English is the only populated
locale; locale tags use BCP-47 parsing and copy selection does not modify
canonical identity. The copy-leakage register and deterministic browser audit
record the field-by-field decisions. Layout, interaction, geometry, and
Golden Master inputs remain unchanged. Human Visual QA remains pending.
