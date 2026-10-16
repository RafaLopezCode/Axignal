# Bounded followup — 2026-10-16

The user requested more prominence for section#pricing > aside.marketing-advisory on the Spanish home (browser comment: «Quiero mas notoriedad en este procing»). The shared component now uses a canonical-blue panel, a white display heading, a large formatted 995 EUR monthly price and a white action button to discuss scope. Original amount, service scope, launch/tax conditions and /contact destination are preserved in all six locales. It remains a separate human service, not an access tier. This propagates to home and pricing.

The preceding continuation also closes an evidenced responsive defect: at820px, the absolutely positioned hero copy overlapped the family heading. Header/hero reflow now applies below1280px. Long French/Italian display copy uses4vw at desktop; compact Spanish uses4.9vw from1280 to1439. The selected desktop visual world remains.

Evidence: tablet-before.png (old bug); tablet-820-it-final.png; desktop-1280-es-final.png; desktop-1440-it-final.png; advisory-desktop-1650.png; advisory-mobile-390.png. The final matrix covers6locales ×9widths768,820,1024,1151,1279,1280,1440,1520,1650:54samples, zero document/title/panel overflow or copy/next-section collisions. Additional pricing320/390×6locales:12samples, zero document/panel/price overflow, correct /contact links. Both raw JSONs are included. Root inspected all five final captures; temporary resize/scroll captures were replaced, not submitted as evidence.

Latest validation:344frontend tests pass; TypeScript and i18n pass(2437entries, no missing); production build passes; all3HTTP journey contracts pass across60localized pages; Architecture Guard and all8Governance categories pass. The full Python suite previously passed2461/7skips; unaffected backend tests were not repeated for CSS/markup changes. No dependencies/backend/private app/AXENT changes. No detector rerun or fake CLI closure. Human visual acceptance remains pending. No commit/merge/deploy.

Review only these material changes for prominence, semantic fidelity and responsive fit. Preserve the prior verdict/history; write a separate followup verdict. This is not a new whole-product audit.
