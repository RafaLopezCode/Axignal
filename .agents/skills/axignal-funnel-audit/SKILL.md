---
name: axignal-funnel-audit
description: Audit and verify AXIGNAL's public funnel (landing → example → pricing → access) for comprehension, one canonical example, no dead ends, no prototype copy, responsive layout and accessibility. Use before and after any change to public pages, header/footer, the public example or access pages.
---

# AXIGNAL Funnel Audit

Orchestrates repeatable evidence for the public journey. Subordinate to the MASTER,
the Constitution, `axignal-design-director` and spec 060
(`specs/060-product-funnel/spec.md`). It does not create product semantics.

## Questions it must answer

1. **5 seconds:** does the first screen say what AXIGNAL is, for whom and what for,
   without internal names (Xeed, AXIGLAND, FAXT, INXIGHT, PATHX)?
2. **30 seconds:** observe → remember → detect change → filter by relevance → explain.
3. **2 minutes:** evidence, time, UNKNOWN, reach, AXENT, price, next step.
4. **One example:** every "show me" lands on `EXAMPLE_HREF` (`/panorama`), deep-linked.
5. **Example ≠ your account:** stated once, at the top, with what the fictional
   organization does.
6. **No dead ends, no loops, no staff links** (`/design`, `/admin`) on public surfaces.
7. **No prototype feel:** no "demo", "versión local", "datos ilustrativos", disabled
   placeholder controls or fake avatars on public pages.
8. **Copy:** every claim passes "so what?" and every example sentence says what
   happened, whether it is real or an example, and why it matters.

## Tools (no browser package; system Chrome over CDP)

From `apps/web/experience` with the site running (`npm run dev` or a candidate):

```bash
npx tsx --test tests/funnel.test.ts
node qa/060-product-funnel/capture.mjs http://127.0.0.1:3810 <out-dir>
node qa/060-product-funnel/funnel_e2e.mjs http://127.0.0.1:3810 390
node qa/060-product-funnel/evidence.mjs https://axignal.com before qa/060-product-funnel/screens
```

- `tests/funnel.test.ts`: public links, one example, prototype phrases, sitemap,
  measurement bounds, garden epistemics (deterministic gate).
- `capture.mjs`: full-page screenshots at 1440/1024/768/390 plus an audit
  (overflow, one `h1`, unnamed controls, small targets).
- `funnel_e2e.mjs`: clicks the journey like a visitor and fails on the first broken step.
- `evidence.mjs`: above-the-fold before/after JPEGs for the PR.

## Rules

- Read production read-only; never sign in, submit forms or change settings.
- Compare before/after at the same widths; report findings with screenshots.
- New public copy goes through `t(es, en)` and `lib/translations.json` (de, pt, fr, it);
  `npm run check:i18n` must report no missing entries.
- Fix the code, never the gate. Human visual acceptance remains with the CTO.
