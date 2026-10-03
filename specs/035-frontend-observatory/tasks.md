# Tasks: Living economic observatory
Input: spec.md, plan.md, research.md, data-model.md, contracts/presentation.md; architecture review PASS.
## Phase 1: Setup
- [x] T001 Initialize exact-pinned isolated frontend in apps/web/experience/package.json and tsconfig.json.
- [x] T002 Copy verified official brand and fonts with provenance into apps/web/experience/public.
## Phase 2: Foundation
- [x] T003 Define distinct fixture organizations, focus, signals, evidence and snapshots in apps/web/experience/lib/projection.ts.
- [x] T004 Write failing scope/plan/epistemic tests in apps/web/experience/tests/contracts.test.ts before implementing governed plan.
- [x] T005 Implement strict version 1, 1..3 items, unique refs, registered keys and matching revision in apps/web/experience/lib/governance.ts.
- [x] T006 Implement shared brand, semantic badges, focus/dialog primitives and state recovery in apps/web/experience/components/ui.tsx and app/globals.css.
## Phase 3: US1 — Discover
Independent test: landing narrative, lens/demo, reduced-motion equivalent, enter Panorama.
- [x] T007 [US1] Build seven-chapter illustrated landing and interactive lens in apps/web/experience/components/landing.tsx.
- [x] T008 [US1] Wire metadata, exact brand and entry route in apps/web/experience/app/layout.tsx and app/page.tsx.
## Phase 4: US2 — Understand
Independent test: family → signal → reasoning → evidence → date → back → organization.
- [x] T009 [US2] Implement scoped projection API in apps/web/experience/app/api/projection/route.ts.
- [x] T010 [US2] Build Today, family constellation/reading alternative, direct depth and navigation in apps/web/experience/components/panorama.tsx.
- [x] T011 [US2] Implement source/evidence inspector and local illustrative source route in apps/web/experience/components/evidence.tsx and app/sources/[id]/page.tsx.
- [x] T012 [US2] Implement global temporal reprojection and readable mobile stack in apps/web/experience/components/panorama.tsx.
## Phase 5: US3 — Investigate
Independent test: contextual question → controlled component; reset scope; retry/stop.
- [x] T013 [US3] Implement AI SDK UI demonstration stream, strict scope validation and body limits in apps/web/experience/app/api/axent/route.ts.
- [x] T014 [US3] Implement SDK useChat, typed registered output, abort/context isolation and recovery in apps/web/experience/components/axent.tsx.
## Phase 6: US4 — Inspect privileged operations
Independent test: domain → record → authority/impact preview; server denial.
- [x] T015 [US4] Build private Admin domains, filters, details and contextual operational support in apps/web/experience/components/admin.tsx.
- [x] T016 [US4] Deny unauthorized operations at apps/web/experience/app/api/admin/action/route.ts and verify rejection in tests/contracts.test.ts.
## Phase 7: US5 — One system
Independent test: /design states, ES/EN, keyboard, mobile, reduced motion.
- [x] T017 [US5] Build design/state gallery and shared locale control in apps/web/experience/components/design.tsx and lib/locale.tsx.
- [x] T018 [US5] Complete responsive, focus, motion and non-color epistemic treatment in apps/web/experience/app/globals.css.
## Phase 8: Validation and convergence
- [x] T019 Run contract/type/build checks and record real results in specs/035-frontend-observatory/validation.md.
- [x] T020 Run actual browser desktop/mobile, evidence, AXENT, time, Admin, state/reduced-motion QA and capture provenance in specs/035-frontend-observatory/validation.md.
- [x] T021 Run deterministic repository gates and AST-only Graphify attempt, recording results in specs/035-frontend-observatory/validation.md.
- [x] T022 Run Spec Kit convergence against current implementation and document scope/human acceptance boundary in apps/web/experience/README.md.
## Dependencies and execution
Setup → Foundation → US1/US2 → US3; US4 and US5 reuse foundation; Validation after all. Independent files permit later parallel manual work (landing vs Admin vs design gallery), no agent delegation needed. Deliver complete journeys incrementally, inspect real browser before final report. Commercial/privileged/provider integration is explicitly unavailable rather than fabricated.

## Phase 9: Convergence
Finding: US4/AC3 and FR-010 partial. The review identified the illustrative read projection but did not separately show owning authority, the selected-record scope and the zero-write impact of the local authority check.
- [x] T023 [US4] Add explicit owning-authority, record-scope and demo-impact fields to action previews in apps/web/experience/components/admin.tsx, distinct from illustrative read-model names; confirm denial remains server enforced and document the integration boundary.
- [x] T024 [US5] Repair the non-destructive Observer viewport mask in apps/web/experience/components/ui.tsx after actual browser inspection found a clipped beret crest; preserve source pixels and confirm the complete supplied silhouette (FR-002, US5/AC1).
- [x] T025 [US3] Share one SDK Chat and draft across desktop/mobile AXENT surfaces in apps/web/experience/components/panorama.tsx and axent.tsx; preserve conversation on drawer close/resize, abort and clear on context revision change (FR-009, US2/AC4).
