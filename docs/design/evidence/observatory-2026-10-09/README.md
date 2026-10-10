# Observatorio vivo — browser evidence (SYNTHETIC data)

Captured 2026-10-09 in the Claude in-app browser against this branch's Next frontend (`/account`). A QA-only mock served subscriber outputs that the **real Python subscriber composition** produced over the controlled test world (`tests/first_observation` harness; RFC 2606 `example.com` organizations and synthetic sources).

- Names, quotes and tenders are synthetic test data. The buyer "Ayuntamiento de Getafe" comes from the existing backend fixture; it is not a real tender or relationship.
- No real JEV, Google, customer or production data appears.
- A QA-only time switch reproduced "a week later" (first reading, then reobservation).

| Capture | What it shows |
| --- | --- |
| [00 Before](00-before-account-desktop.jpg) | The previous `/account`: a public marketing header and a 7,790 px dossier. The selected organization's reading started below the portfolio, pricing and connector panels (45 buttons, 14 disclosures). |
| [01 Desk](01-desk-return-desktop.jpg) | Portfolio desk on return. Lamp count on "Toda la cartera"; "2 hallazgos nuevos desde tu última visita"; one structured-data gap grouped across 4 organizations; per-organization lane counts in words. |
| [02 Briefing](02-organization-briefing-desktop.jpg) | Organization view: identity state and observation time; a hedged briefing sentence (Fraunces); a tally; a lamp line; three lanes (what matters / how it is understood / what is unknown). |
| [03 Lit until seen](03-lit-until-seen-desktop.jpg) | Changed findings carry "Nuevo", a brass ring and "Antes: Oportunidad de aclaración", taken from the runtime's comparable reading. |
| [04 Depth](04-depth-lamp-dimmed-desktop.jpg) | The depth panel beside the finding: meaning, reasoning, proof (quote, source, date, instrument). The opened finding's lamp dims and the rail drops from 2 to 1. |
| [04b AXENT](04b-depth-axent-desktop.jpg) | Contextual AXENT in the depth panel: quick questions in context, no prompt-writing. AXENT reads the runtime's recorded Today items, which differ from the per-device "since your last visit" lamps (see the PR follow-ups). |
| [05 Evolution](05-evolution-desktop.jpg) | Timeline of observations and offer readings. A change of interpretation is not shown as business proof. |
| [06 Evidence](06-evidence-desktop.jpg) | Authorized sources, web representation, and the complete First Observation and offer-understanding reports. Nothing is lost from the old dossier. |
| [07 First run](07-first-run-desktop.jpg) | Empty portfolio: one question, one field, three truthful steps. |
| [08](08-desk-mobile-390.jpg) · [09](09-portfolio-sheet-mobile-390.jpg) · [10](10-organization-mobile-390.jpg) · [11](11-depth-mobile-390.jpg) | 390×844: desk, portfolio sheet (focus-trapped), organization view, full-screen depth. Scroll width is 390 and the first lane starts inside the first viewport. |

## Acceptance tasks — status

Task-based acceptance criteria from the frontier challenge brief. Each can be measured in a moderated session using `docs/research/HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md`. **Human usability has not been tested and remains pending validation.** The "Verified here" column is automation and fixture evidence only.

| Task | Verified here (E2E with SYNTHETIC fixtures) | Measure with real users |
| --- | --- | --- |
| A. First visit | First-run screen; truthful observing stages; no fake progress (test). | Time to the first added organization; unaided explanation of what AXIGNAL does. |
| B. Return after a week | Lamps agree across rail, desk and briefing; "Antes:" delta; dimming on open (browser). | Time to name what changed and why it matters; errors. |
| C. Important finding | Opportunity depth: potential (not a customer), scoreless checked dimensions, reasoning, proof (browser and test). | Correct statement of scope and uncertainty. |
| D. Self-critique | Strength, gap, unresolved and instrument-limit states are separated. Proposal is shown as conditional; "not a demonstrated cause" (test). | Can tell a suggested improvement from a proven causal effect. |
| E. Evidence | Meaning to quote, source URL, date and instrument in one panel; back restores focus (browser). | Time from finding to source; context loss. |
| F. Switching organization | URL-addressed organization, view and item; rail always visible; history back and forward (browser). | Cross-client confusion incidents. |
| G. Mobile | 390 px: no overflow; all actions reachable; full-screen depth with back (browser). | Task completion on a phone. |
| H. Volume | Desk groups identical findings; rail search above 6 organizations; empty and no-signal copy (browser and test). | Comprehension with 0, 7 and 40 organizations (40 not yet measured). |
| I. Adverse states | UNKNOWN lane; robots-blocked and unobservable sites; withdrawn and failed instrument shown as not a company defect (test). | Misreading rate of UNKNOWN as negative. |
| J. Accessibility | Tabs (arrow keys), focus restore, focus-trapped sheets, Escape, shape-plus-text marks, reduced motion, contrast checked (6.9:1 badge). | Screen-reader walkthrough (NVDA or VoiceOver) still to be done manually. |
