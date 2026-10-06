# Mercados and reading preferences — rendered repair evidence

Mode: PRESERVE. Authority: AXIGNAL Design Director, design doctrine/governance,
incumbent global `.badge` and `.button.secondary` styles. Golden Master manifest
is source identity only; this repair does not claim a new visual acceptance.

## User-reported defects and repairs

- Currentness indicators had a separate 999px radius. They now reuse the global
  badge geometry (5px radius). Currentness labels and UNKNOWN dashed outlines
  remain explicit; OBSERVED/POTENTIAL/UNKNOWN are unchanged.
- Territory cards distributed their rows according to differently sized detail
  content. Four shared subgrid rows now align state, name, currentness and detail.
  A detail wrapper preserves those rows for both glance and expanded composition.
- Preferences changed hidden component state while a signal was selected. Choosing
  a reading mode now opens the corresponding general Panorama composition. The
  selected mode is URL presentation state; reload/back restore it. Organization
  and time parameters are retained. Public navigation stays on `/panorama`;
  laboratory navigation stays on `/design/panorama`.
- The settings language selector now has the same border/radius/height as adjacent
  controls. Header selectors retain their existing presentation. The user chose
  to keep Accessibility and states linked to `/design`; its destination is unchanged.

## Browser evidence

Codex in-app browser, local optimized build, illustrative demo data only.
Desktop: 1743x1244; mobile: 390x844. Browser viewport override reset afterward.

With Navarra and País Vasco details open, the four currentness indicators
originally started at y=491.796875, 503.328125, 543.328125, 543.328125px. After
repair they all start at y=491.796875px, have height 22.5px and radius 5px.
Mobile stacks cards without document overflow. Currentness/epistemic states
remain CURRENT/OBSERVED, CURRENT/POTENTIAL, UNKNOWN/UNKNOWN, UNKNOWN/UNKNOWN.

Preferences language selector and adjacent unselected button both measure
`1px solid rgb(204, 211, 223)`, radius 9px, height 50.1875px. Mobile dialog width
is 370px in the 390px viewport, without overflow. Reading mode displays ten
linear rows; spatial mode restores distinct positions. Reload and browser back
restore reading mode. Spatial selection also works through mobile preferences.
Escape closes the dialog and returns focus to Preferences. Both browser warning/
error logs were empty.

Artifacts outside Git:
`D:\AXIGNAL\Worktrees\test-artifacts\cognitive-e2e-20261006`:
`markets-alignment-before.json`, `markets-borders-after.json`,
`markets-borders-desktop.jpg`, `markets-borders-mobile.jpg`,
`preferences-after.json`, `preferences-borders-desktop.jpg`,
`preferences-borders-mobile.jpg`, `preferences-spatial-desktop.jpg`.

## Validation and delivery status

Frontend TypeScript, 94 tests, translation inventory (1326 entries, none missing),
optimized build, Ruff format/check, mypy, Architecture Guard and all eight
governance checks passed. Graphify was refreshed with AST extraction only.
The first build encountered a Windows cache write denial; the preview was stopped
and the final build completed successfully. No gate or threshold was changed.

Implemented and browser-tested locally. Human visual acceptance pending.
No remote integration or production deployment. Unrelated working-tree changes
are preserved.
