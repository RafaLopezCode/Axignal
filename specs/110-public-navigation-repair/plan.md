# Plan and architecture review

Graphify identifies LandingLab, PublicHeader, Dialog, acquisition/marketing shells, shared brand/footer and stylesheet delivery as the existing boundaries. No architecture change or new ADR is necessary.

The visitor chooses a commercial chapter or leaves for editorial content/contact; inside a page they can recover to the locale home and switch language without reaching an isolated route. Preserve the existing type, brand, CTAs, official illustrations and product semantics. Group chapter links before destinations and account actions. Restore the incumbent dialog inset and header; retain native modal focus/scroll behavior. Collapse header navigation before long localized labels collide with access actions.

Implementation: retain dialog child selectors in deterministic CSS extraction, add existing destinations to current headers/menus, use current locale path helpers and separate preview/public language targets. Add a footer anchor and regression contracts for delivered dialog styles and published language destinations. Keep exact immutable style ingress aligned with generated assets; production activation must explicitly update AXIGNAL's edge allowlist without widening paths or affecting other projects.

Validation: baseline user screenshot and computed production styles establish the defect (padding 0, header block). Inspect the repair across public route families and devices, verify keyboard/links/current state, run deterministic gates and record actual results. Do not equate the prior 596-URL HTTP SEO crawl with complete rendered navigation QA.

The first rendered pass additionally exposes a 500px modal escaping a 390px viewport: `.lab-menu` overrides the shared dialog maximum. Bound its actual width to the viewport with existing 16px outer gutters, and restore the shared 27px dialog heading rather than inheriting the landing's section-heading ramp. Confirm both in the final pass.

The six-language desktop matrix finds header controls beyond the viewport at 1280px (French right edge 1404.5px; German 1355.1px). Page overflow clipping hid this from a scroll-width-only check. Collapse the expanded six-link header at 1400px and use the existing 16px spacing rhythm between links. This additional confirmation is driven by measured clipped controls, not subjective polish.

The independent interior-header matrix finds a separate grid constraint: equal side tracks let the fixed 444px access group overlap longer navigation at 1440px. Preserve the physical logo/action footprints using content-sized side tracks and center navigation in the remaining space. Existing marketing breakpoints stay intact. Confirm child rectangles as well as page overflow.
