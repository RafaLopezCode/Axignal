# Shared spacing and rendered contracts

Presentation-only refinement under DESIGN_DOCTRINE; CURRENT_TASK = AO-24A.
Mode PRESERVE. No epistemic, runtime or navigation semantics are changed.

`apps/web/experience/app/globals.css` defines a 4px spacing scale:
4, 8, 12, 16, 24 and 32px. Semantic roles currently include:

- `--space-status-title`: 16px between an epistemic badge and its heading.
- `--space-content-action`: 24px between explanatory content and the action.
- `--space-panel-inset`: 32px desktop, 24px mobile for the unknown-state panel.

The canonical runtime unknown-state uses explicit grid gaps and zeroes inherited
heading/paragraph/action margins. Its action retains a 44px minimum target.
Both Customer Zero and subscriber use that same surface. The status is a badge,
not a button; the panel heading remains h2 below the page h1.

This is the start of shared spacing governance, not a claim that every legacy
margin or application screen is already migrated or tested.

## Rendered regression check

`apps/web/experience/tools/spacing-contract.mjs` exports a read-only DOM probe
and a validator for geometric minimums. The host browser executes the probe on
the actual compiled UI, then passes its measurements to the validator. No new
browser dependency is installed. Unit tests verify that collapsed gaps, clipped
content, undersized targets, absent measurements and overflow are rejected.
They alone do not render CSS or replace the browser check.

After changes to these roles, rerun browser measurements at desktop, 768, 390 and
320px, including both runtime entry points. Open an unsupported dimension,
invoke `measureUnknownStateSpacing` through the host browser's read-only evaluate
API, and require `validateUnknownStateSpacing(sample)` to return no failures.
Save fresh measurements and screenshots; never substitute old evidence for a
new render. Verify the action opens AXENT and dismissal returns keyboard focus.

## 2026-10-04 evidence

Before: status/title gap 0px, action 36px; the contract rejected both.
After: status/title and title/body gaps 16px, body/action 24px, action 44px,
panel padding 32/24px, no document overflow. Border-box inset measurements include
the 1px border. Tested Capacidades, Mercados and Actividad; Admin widths
1280/1743/768/390/320; standalone subscriber at 1280. AXENT opening and Escape
focus return verified on mobile. Browser console errors/warnings: none captured.

Evidence: `apps/web/experience/qa/037-customer-zero/spacing/`.
Human acceptance remains pending. No changes to observations or economic truth.

Authority read: AXIGNAL Design Director, Constitution, DESIGN_DOCTRINE and the
existing AO-24A shared-reader specification. Delta is limited to the evidenced
unknown-state spacing regression and its reusable scale/QA contract.

Validation: frontend typecheck and 33 tests pass; final production build passes;
Ruff format/check, mypy (258 files), Architecture Guard and governance pass.
Graphify AST update and whitespace check pass. The initial build hit a local
EPERM cache-directory error; a rebuild with the preview stopped passed. The first
Python suite run was affected by sandbox socket permissions (WinError 10013),
so a separately authorized complete rerun is used for the final result:
**1035 passed in 133.46s**. No Python implementation or gate was changed.

## Cognitive reader rendered check (2026-10-06)

`measureCognitiveReadingLayout` and `validateCognitiveReadingLayout`, in the same
read-only browser QA module, additionally check the subscriber reading and AXENT
against TYPOGRAPHY_ROLES: body 14/400, control 13/500, metadata 11/400, section
label IBM Plex Mono 10/400, AXENT invitation Fraunces 24/400, heading hierarchy,
44px targets, evidence-panel inset and viewport overflow. Open an organization
reading with retained source provenance and expand AXENT before measuring.

Fresh browser measurements at 1280/768/390/320px rejected 36px targets,
12px/650 control type, editorial section labels and a 320px header overflow.
These regressions were repaired without changing epistemic meaning. The existing
unknown-state contract also rejected an 18px mobile inset; it is restored to
24px. Both contracts now return no failures at all four widths. Escape from the
mobile AXENT dialog restores focus to its invoking control.

Measurements and screenshots are retained outside the source checkout under
`D:\AXIGNAL\Worktrees\test-artifacts\cognitive-e2e-20261006`. This is automated
and rendered evidence, not human visual acceptance; that acceptance remains
pending. The subscriber browser scenario uses controlled identity/capacity and
a genuinely acquired public source, and does not verify production onboarding.
