# 060 — Product funnel: understandable, navigable, trustworthy

**Status:** IMPLEMENTED (experience) · audit: [audit.md](audit.md) · **Date:** 2026-10-08 · **Authority:** MASTER §1.1
(human product language), §25–27, §33, §39, §41, §53.6, §54; Constitution; ADR-0089;
specs 036, 056, 059.

## Problem (diagnosis)

1. **The first screen did not say what AXIGNAL is.** "El mundo cambia. Tu mirada
   también." answered no 5-second question (what, for whom, for what).
2. **Concepts arrived before value.** Panorama, focus, Axent, families, Knowledge and
   the brief all competed on the first page; ten chapters and a side wayfinder.
3. **One example, five doors.** Hero, use cases, explore preview, trust proof, closing
   and the mobile menu all pointed to `/panorama` under different names ("Descubrir mi
   Panorama", "Ver un ejemplo", "Abrir experiencia", "Explorar la demo"…).
4. **The example read like a prototype.** "Demo · datos ilustrativos", a fake "NR"
   avatar, a fake subscription panel ("Esta demo no procesa pagos"), links to the
   internal design system, "datos ficticios para revisión".
5. **The landing said it was a prototype.** "Esta versión local… espera revisión visual
   humana", "Esta demo no realiza cobros", "Canal de envío pendiente… borrador local".
6. **Dead ends.** The weekly brief section opened a local-draft form (the brief is
   disabled in production); footer links to `/design` and `/admin` fell through to the
   retired static landing.
7. **Soft 404 with a competing message.** Any unknown path (`/pricing`, `/demo`,
   `/admin`, `/es`…) answered 200 with the old static landing, `index,follow`; `/` was
   not in the sitemap.
8. **Copy described the method, not the outcome,** and example signals were abstract
   ("La rehabilitación abre una nueva conversación").
9. **Mobile:** the header clipped "Acceder"; the privacy notice covered the hero CTA.
10. **Access flashed "esta versión no crea cuentas"** before the status check returned,
    although Google sign-in is available in production.

## Decisions

### Message (5 s / 30 s / 2 min)

- **5 s:** "Sabe qué cambia alrededor de tu empresa. Y por qué te importa." + one
  sentence: AXIGNAL observes the organizations you choose in public sources, remembers,
  detects change and separates what matters, always with source and date. For whom:
  people who run or grow a business, and the consultancies/agencies that support
  several. Price visible: €9.95/month per organization.
- **30 s:** three steps (you choose → AXIGNAL observes and remembers → you see what
  matters and why) and AXENT as "ask the accumulated context".
- **2 min:** four proofs, each opening the example at the right depth: where each
  business plays (garden), where each conclusion comes from (evidence), what it does
  not know (UNKNOWN), when it learned each thing (time); who it is for; what AXIGNAL
  will not do; pricing.

Internal names stay out of the first layer (MASTER §1.1): no Xeed, AXIGLAND, FAXT,
INXIGHT, PATHX on public pages. AXENT appears once the visitor knows what context
exists; MCP appears as a pricing inclusion ("your context in Claude and other
MCP-compatible assistants"), verified in production by spec 057.

### One canonical public example

`/panorama` is the only public example (`EXAMPLE_HREF`); every "show me" CTA converges
on it, deep-linking to the relevant depth (`?family=markets`, `?signal=…&depth=prove`,
`?asOf=2026-07-01`, `?signal=reputation-gap`). It states once, at the top, that it is a
guided example with a fictional organization and what that organization does, and that
"in your account AXIGNAL observes the real organizations you choose". Its exits are
"Empieza con tu organización" and "Volver a AXIGNAL".

**"AXIGNAL observing AXIGNAL" — evaluated and not adopted now.** Customer Zero already
observes AXIGNAL in the private Admin runtime, so the idea is real. It is not the public
example today because: (a) the controller's legal identity is still being published
(draft PR #161), and an example whose own identity reads "unknown" breaks trust at the
worst moment; (b) a pre-launch SaaS has almost no procurement demand, reviews or
relationships, so it can prove UNKNOWN but not opportunity, reach or exposure; (c) it
answers "what does AXIGNAL think of itself", not "what would I see about my business",
and self-observation reads as self-promotion; (d) it needs a new public read-only
projection of an admin-private record (MASTER §2.1A boundary) and live production data
in a public page — a capability activation outside this slice. Preconditions to revisit:
published legal identity, an authorized public projection contract with redaction, and
enough observed economic activity to show all three scopes.

**Demo ≤ product.** The example's new "economic world" view is the same component the
real subscriber reading now renders from the persisted spec 059 garden
(`components/economic-garden.tsx`, `lib/runtime-garden.ts`). Place names, source,
excerpt and observation time come from the server (`place_label`, garden summary); the
UI never decides or widens reach. A malformed garden degrades to "not shown".

### Data classification (public example)

| Datum | Class |
| --- | --- |
| Organization, sources, dates, signals, reach places | SYNTHETIC (fictional, labeled at the top, in the topbar and in the footnote) |
| Exposure channels (fuel/travel, rules where it works) | EDITORIAL EXPLANATION derived from the example's delivery mode with spec 059 rules |
| Method, epistemic states, time cuts | Same code paths as the product |
| Real observed / real historical | None in the public example (see decision above) |

**Readable anywhere.** AXIGNAL is global, so the example must read the same in San
Francisco and Tokyo: countries and capital cities (works in Spain, could grow in
Portugal through its own job posting in Lisbon, no evidence yet for France or Germany),
and the activity in plain words ("retrofits buildings so they use less energy:
insulation, windows and heating") instead of a local term or a region only Spaniards
know. Expansion rests on the organization's own act, never on demand somewhere
(ADR-0089).

### Navigation and routes

| Route | Purpose | Entry | Exit / primary CTA | Decision |
| --- | --- | --- | --- | --- |
| `/` | Understand, see proof, decide | search, links | "Ver un ejemplo" (hero), "Empieza con tu organización" (after proof, pricing, closing) | KEEP, rewritten |
| `/panorama` | The one public example | every "show me" | "Empieza con tu organización", "Volver a AXIGNAL" | KEEP (noindex) |
| `/signup`, `/login` | Access | header "Empezar"/"Acceder", pricing, closing | Google | KEEP, clarified |
| `/account` | Your private AXIGNAL | after sign-in | add organization | unchanged |
| `/knowledge/*` | SEO, education, method | search, header | home | KEEP in header, removed from landing body |
| `/policies`, `/gdpr`, `/contact` | Trust, rights, contact | footer, menu, trust section | — | DEMOTED from header to footer/menu |
| `/design`, `/admin` | Staff tools | — | — | REMOVED from public footer, example and menus |
| unknown paths | — | — | 404 page → home / example | 404 instead of the retired static landing |

Header: Cómo funciona · Ejemplo · Precio · Knowledge — Acceder · **Empezar**. On phones
the languages, sign-in, contact, trust and data rights live in the menu.

### Removed complexity

Ten-chapter side wayfinder and floating "Explorar página"; marquee of eight job titles;
the abstract orbit scene; "Qué acumula" and "Explora" chapters; landing Knowledge
preview; weekly brief section (disabled in production; returns when wired to its API);
"Sobre esta experiencia" dialog; example subscription/"Mi observación" utilities, avatar
and design-system links; five names for the same demo CTA.

### Measurement

Reuses AO-12 (`/api/acquisition/events`, `OBSERVED_TOUCH_V1`): `LANDING_VIEWED`
(landing_view), `CHAPTER_VIEWED` on surface `landing` (how 2, proof 3, audience 4, trust
5, pricing 6 = pricing_view) and on surface `example` (opened 1 = public_demo_open,
family 2, signal 3, evidence 4, history 5 = demo_depth), `CTA_ACTIVATED` with named CTAs
(`hero-example`, `header-start`, `pricing-start`, `example-start`, `signup-start`,
`login-start`…). No new event kind, no cookie, no identity. It sends nothing unless the
runtime reports the model enabled; production reports `enabled:false` and this slice
does not change that. Enabling it is an operator decision that must also update the
privacy notice (owned by PR #161).

## UX contract for Contact, GDPR and newsletter (Codex)

The public surface needs three things from the backend plumbing Codex owns. It does not
build them, and it never shows a form whose channel is not live.

1. **Status first, per channel.** `GET /api/contact/status`, `GET /api/gdpr/status`
   and the existing `GET /api/weekly-brief/status` (AO-15) answer
   `{ "enabled": boolean }` plus, for contact/GDPR, the published controller identity
   (`controller`, `country`, `publicEmail`) once #161 publishes it. When `enabled` is
   false, the UI shows the published e-mail (or nothing), never a local draft.
2. **One request, one receipt.** `POST` with the visitor's fields and the notice
   version they saw. Success answers `{ "status": "received", "requestId": "…" }`, the
   same shape `POST /api/weekly-brief/requests` already returns. The UI shows the
   reference and what happens next (who answers, and for GDPR, the statutory period
   stated by the controller). Rejections answer `{ "status": "rejected", "reason":
   CODE }` with stable codes, so the UI can say what to fix in plain language.
3. **No identity in measurement.** The funnel only sends AO-12 anonymous events; a
   request ID may link a brief request to its session as AO-12 already allows. Contact
   and GDPR requests are never linked to funnel events.

Today the advisory "Hablar del alcance" links to `/contact`, which shows the published
e-mail once #161 lands. When (1) reports enabled, the funnel adds a landing brief
invitation wired to AO-15 (never a local draft) and the in-page contact/GDPR receipts.
Until then the brief and request forms stay out of the main journey.

## Not changed

MASTER, prices (MASTER §27), legal and privacy texts (PR #161), checkout/contracting,
public launch, AXENT activation, scheduler, Brain semantics, the subscriber portfolio,
Admin, Knowledge content.

## Validation

See [validation.md](validation.md).
