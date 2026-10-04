# TASK 4 — runtime subscriber UX unification

CURRENT_TASK = AO-24A

## Specify / clarify

Sharing the FR-30 projection did not share the subscriber experience. The real
routes currently render a linear inspector; the spatial Panorama and AXENT use
fixtures. Human authorization: reconcile the full product UX without duplicating
truth or inventing unsupported capabilities. No production deployment requested.

Canonical public terminology follows MASTER: organization, observation focus,
signals and Panorama. Legacy Xeed/Xignal remain contract identifiers only.

## Audit and presentation authority

Reusable: product-shell/workspace/sidebar/topbar/timeline and AXENT visual grammar,
Brand, LocaleToggle, Badge, IconButton, Dialog, focus trap, typography and tokens.
Presentation state: reading/spatial mode, navigation back/forward/home, focus
trail, dimensions, disclosures and dialog state.
Fixture-only: projection.ts organizations/signals/families/snapshots, illustrative
AXENT explanations/composition refs and hero selection. Never adapt these into
runtime truth. Existing illustrative experience remains explicitly separate.
Runtime-direct: organization, focus, nodes, Today, narrative/sourceRefs,
epistemic/currentness/uncertainty and observation dates.
Unsupported in FR-30: economic dimension classification, relationships, multiple
focus enumeration, historical snapshots, autonomous AXENT research tools. Show
unavailable/UNKNOWN; prepare UI boundaries without simulating data.

## Plan / architecture review

1. Consolidate both real entries around one controller and canonical product
   presentation. Human feedback supersedes the previous standalone interpretation:
   Customer Zero hosts that product **inside** the Admin dashboard, retaining Admin
   navigation. The product stays mounted when switching operational sections so
   signal focus and contextual AXENT conversation survive returning. Staff utility
   disclosure is separate; no subscriber-view hop or private operational context
   passed into the product. The standalone subscriber consumes the same renderer.
2. Reuse existing shell classes/primitives and extract focus navigation for the
   existing illustrative Panorama and the runtime experience. No graph engine.
3. Real spatial signal canvas, Today, focused reader, evidence journey, temporal
   boundary, organization selector and explicit unsupported dimension states.
4. Extend existing AXENT endpoint with authorized runtime mode. Server retrieves
   current safe projection, never accepts browser economic facts. Deterministic
   reading of runtime-authored explanations; unavailable research is explicit.
   No provider/network/LLM dependency in gates and no extra acquisition backend.
5. Behavioral navigation/explanation/authorization tests; compiled-browser real
   E2E, all six widths, keyboard/mobile dialogs and persistence/process restart.

Constitution check: PASS. No canonical writer, new datastore, provider assumption
or customer-owned graph. Graphify confirms Panorama→project fixture coupling and
route impact. ADR-0031/32/33/51/76/81 and mobile ADR-0042 govern runtime semantics.
Design mode EXTEND of runtime / PRESERVE incumbent product grammar; no promotion
of human visual acceptance or of illustrative data into economic authority.

## Tasks

- [x] Shared product controller, shell and navigation
- [x] Runtime-focused canvas, Today, evidence and temporal boundaries
- [x] Authorized AXENT runtime explanation using existing endpoint
- [x] Behavior and fail-closed tests
- [x] Browser E2E and responsive/accessibility checks
- [x] Deterministic gates, commits and evidence-backed convergence

Convergence evidence: [unification-validation.md](unification-validation.md).
Dashboard hosting correction: [admin-embedding-validation.md](admin-embedding-validation.md).
Human visual acceptance remains PENDING; no production deployment or push.
