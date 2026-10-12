# Public back-to-top control — 2026-10-12

Small EXTEND repair of the existing public frame, under the MASTER,
Constitution, Design Director and motion/input contract. BackToTop is owned
by PublicShell, so all long public pages share it. It appears after scrolling
beyond max(480px, 75% of viewport height). It uses the incumbent blue and Lucide
ArrowUp with six localized visible labels, a 48px target and visible focus.

Click/Enter focuses the existing main landmark without jumping focus to an
unrelated control, then returns to y=0. Reduced motion selects instant scrolling.
A chapter fragment is cleared while preserving path/query and synchronizing
the Next router through its documented native-history integration. Local Next
code confirms passing its internal state would bypass that integration; passing
null retains framework state through Next's wrapper. Reference:
[Next native history](https://nextjs.org/docs/app/getting-started/linking-and-navigating#native-history-api).

Browser QA: actual Chrome DOM widths 2844px and 433px. Initially no button at
the top; after navigation/scroll the button is visible. At narrow width its
rectangle is x=263, y=870, width=134, height=48 in a 433×937 viewport, with no
horizontal overflow. Enter and pointer click return to y=0, focus main and
remove the button. After returning from #how, the URL has no fragment, and
selecting the same chapter again scrolls to y=1716 and restores the button.
This second navigation was verified after correcting the Next router state.
Privacy's initial notice hides the control to protect its actions. The small
privacy preferences control remains on the opposite side.

Screenshot capture was unreliable in this browser session. A crop captured an
unrelated part of the page and was removed; no incorrect pixel evidence is
presented. Verification above comes from real browser interaction, rendered
bounds/styles and focus/URL state, not an invented screenshot. Reduced-motion
media emulation was unavailable; its instant branch was inspected in code.
The temporary viewport override is reset before delivery.

Frontend typecheck, 271 tests and production build passed. Frozen sync, Ruff
formatting/lint, mypy, Architecture Guard and governance passed. Full pytest:
2180 passed, 7 skipped, 2 warnings in 770.50 seconds. Design detector: no findings.
No domain truth, user data, provider, dependency or production service changed.
Human visual acceptance remains pending; no automatic visual acceptance claim.
