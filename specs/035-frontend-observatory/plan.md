# Implementation Plan: AXIGNAL living economic observatory
**Branch**: `codex/frontend-observatory` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
## Summary
A separate EXPLORE frontend at apps/web/experience, running locally, uses exact official assets and an editorial spatial language. A lens-based landing teaches the same attention/evidence model that Panorama, AXENT, timeline and private Admin use. Fixture data is labeled throughout. Canonical Python/backend and accepted surfaces remain unchanged.
## Technical Context
**Language/Version**: TypeScript 5.9.3, Node 24.14.1.
**Primary Dependencies**: Next 16.3.8, React/React DOM 19.3.0, ai 7.0.127, @ai-sdk/react 4.0.130, Zod 4.6.5, lucide-react 1.51.0. Exact npm lock.
**Storage**: Read-only illustrative dataset; presentation preferences in browser only. No canonical writes, API keys or external models.
**Testing**: Node deterministic contract tests via tsx; tsc; Next production build; actual browser QA; existing Python deterministic gates.
**Target Platform**: modern desktop/mobile browsers, local loopback server.
**Project Type**: frontend plus presentation-only server routes.
**Performance Goals**: transform/opacity motion, no perpetual product animation, no stock video/3D; no remote font request after build.
**Constraints**: strict plan allowlist, no generated HTML/JSX, invalidation by context revision, reduced motion, explicit demo, existing Admin authorization required before any real mutation.
**Scale/Scope**: landing; ten families; three snapshots; illustrative organizations; evidence/projection registry; AXENT; twelve Admin domains; state/design gallery; ES/EN.
## Constitution Check
PASS before research and after design: MASTER precedes all visual choices. No domain modification, admission bypass, provider hardwiring, private truth mutation, sponsor/CRM product function or opaque opportunity score. Admin is private first-party operations per Master 2.1A, not a subscriber CRM. No runtime Python dependencies or weakening gates. Canonical terms remain internal. Organization, focus, signal, AXIGLAND, Panorama and AXENT retain distinct meanings.
## Project Structure
Documentation: specs/035-frontend-observatory/{spec,plan,research,data-model,architecture-review,quickstart,tasks}.md and contracts/presentation.md.
Source:
- apps/web/experience/app: routes, global styles, presentation-only API.
- apps/web/experience/components: shared primitives, landing, panorama, AXENT, Admin, design gallery.
- apps/web/experience/lib: fixtures, governed plan/context, dictionaries.
- apps/web/experience/tests: rejected-reference/stale-context/security contract checks.
- apps/web/experience/public: exact official SVG derivatives, locally hosted fonts, approved observer reference.
Accepted apps/web/landing and subscriber source is read-only.
## Design decisions
Token plan: paper #f7f8fa, white #fff, charcoal #3c3c3c, blue #354F98, faded blue #e7edf8, sage #dfe8df, lavender #e5e0ee, sand #eee8dc; muted tones do not encode epistemology alone. Radius 8/14/22px; editorial headings Fraunces, body Manrope, metadata IBM Plex Mono. Maximum normal line length 68ch. Bic notes short, subsidiary.
Spatial hierarchy: stable left navigation; central asymmetric editorial constellation; right contextual AXENT; bottom global time. Family focus changes hierarchy without inventing graph relations. Mobile uses readable stack. Direct depth and evidence side panel preserve selected object; back/forward restores URL state.
Motion: landing lens reveals teaching layers; scene entry establishes continuity. Product only animates transitions between scoped views; reduced motion removes movement. No simulated knowledge activity.
State model: READY, EMPTY, UNKNOWN, LOADING, ERROR, UNAVAILABLE; recovery links and retry return to verified demo state.
## Phases
Foundation/contract and asset provenance; landing narrative; subscriber/evidence/time/navigation; SDK UI AXENT; private Admin; design/state gallery; actual browser inspection; deterministic gates; Spec Kit convergence.
## Complexity Tracking
No constitution violation. The separate app avoids premature replacement of accepted visual authority. No speculative graph runtime or generic component framework.
