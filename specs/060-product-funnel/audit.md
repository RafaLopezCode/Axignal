# 060 — Funnel audit, public example evaluation and implementation strategy

**Scope:** the public product UX, funnel, narrative, navigation and canonical example
(ownership confirmed by the CTO coordination update, 2026-10-08). Backend plumbing for
Contact, Privacy/GDPR and the newsletter belongs to Codex; the UX contract this surface
needs from it is in [spec.md](spec.md#ux-contract-for-contact-gdpr-and-newsletter-codex).
Audited against production `1775382` (`https://axignal.com`) on 2026-10-08.

## 1. Resources used

| Resource | Why |
| --- | --- |
| Project skill `axignal-design-director` | Governing design workflow (authority order, EXTEND mode, truth vs presentation) |
| Project skills `frontend-design`, `ui-ux-pro-max` | Craft reference only, under the MASTER |
| Plugin skill `design:ux-copy` | Copy review: outcome before mechanism, "so what?" |
| New project skill `axignal-funnel-audit` | Repeatable funnel evidence (this audit, and the re-audit after Codex) |
| Built-in browser + headless Chrome over CDP (`qa/060-product-funnel`) | Production reading, full-page captures at 1440/1024/768/390, visitor-like E2E |
| Read-only HTTP probes | Route status, titles, robots, sitemap, auth/brief/acquisition status |
| MASTER §1.1, §2.1A, §25–27, §33, §39, §41; ADR-0089; specs 033, 036, 037, 056, 057, 059 | Product truth |
| Isolated nginx container on the server (no network, `--rm`) | Proved the soft-404 fix (`nginx -t` + path behaviour); files removed afterwards |
| Draft PR #161 diff | To avoid touching legal/privacy copy owned by the trust work |

Not used: the claude.ai `deep-research` skill and subagents. The questions are about
this product's own truth, not external literature.

## 2. Comprehension audit (production)

**5 seconds — fails.** Hero: "El mundo cambia. Tu mirada también." / "Encuentra sentido
en lo que ocurre…". It answers neither *what is this*, *for whom* nor *what does it do
for me*. The right half is an abstract orbit with a fictional company and "Ejemplo
ilustrativo" in 8px. On a phone the header clips "Acceder" and the privacy notice
covers the only CTA.

**30 seconds — partial.** "Empieza por una organización", "Cada observación deja
contexto", "Una señal tiene un antes" carry the right ideas (observe, remember, time),
but as metaphors. Relevance (*what matters to this business*) and explanation (*why*)
never appear as outcomes.

**2 minutes — fails on proof and next step.** Price is visible and correct (€9.95 +
€4.95). Evidence, UNKNOWN and time exist only inside the example, which introduces
itself as a "Demo · datos ilustrativos" with a fake avatar and a fake subscription
panel. The next step is ambiguous: five CTAs open the same example under five names;
"Preparar mi acceso" leads to sign-up; the brief and the advisory "conversar" lead to
local drafts.

## 3. Funnel as it is

```text
ENTRY        /  (search, social)   ·  any unknown URL → retired static landing (200, index,follow)
NAV          Cómo funciona(#start) · Pricing(#subscription) · Knowledge · Contacto · Confianza · [Acceder]
PRIMARY      "Descubrir mi Panorama" → /panorama (an example, not "my" Panorama)
SECONDARY    "Acércate un poco" / "Hay más debajo" → #start
DEMO PATH    5 names → /panorama ("Descubrir mi Panorama", "Ver un ejemplo", "Abrir experiencia",
             "Entender esta señal", "Explorar la demo", "Entrar en el Panorama", "Explorar julio")
TRUST PATH   "Leer nuestros límites" → /policies ("datos pendientes de publicación")
PRICING      #subscription → "Preparar mi acceso" → /signup
ACCESS       /signup → flashes "esta versión no crea cuentas" → Google (available in prod)
FIRST FOCUS  /account → add organization → "La contratación todavía no está activa"
```

### Dead ends, loops and competing routes

| Finding | Where | Effect |
| --- | --- | --- |
| Soft 404 serves the retired static landing ("Observe the economic world from the outside", `index,follow`) for `/pricing`, `/demo`, `/dashboard`, `/trust`, `/admin`, `/design`, `/es`, `/en`… | edge nginx `try_files … /index.html` | A second, older message competes with `/` in search and for curious visitors |
| `/` missing from the sitemap | `app/sitemap.ts` | Home is the only page search engines must discover by links |
| Footer "Sistema visual" → `/design`, "Admin" → `/admin` | `MiniFooter` | Both fall into the soft 404 (loop to the old landing) |
| Example sidebar "Sistema AXIGNAL", settings "Accesibilidad y estados" → `/design` | `panorama.tsx` | Same loop, from inside the proof |
| Weekly brief section → local draft only; brief `enabled:false` | landing | Dead end and "pending" language |
| Advisory "Conversar sobre el alcance" → `/contact` (draft + download only) | landing | Dead end until the contact channel is published (#161 / Codex) |
| "Sobre esta experiencia" dialog: "versión local… organizaciones ficticias… revisión visual humana" + link to `/design` | landing footer | Explicit prototype statement on the production home |
| Example "Suscripción": "Esta demo no procesa pagos"; "Mi observación": "Estado del foco ilustrativo"; avatar "NR" | example | Mock account inside the proof |
| ChatGPT button "Próximamente" (disabled) | access | Disabled control = prototype feel |

### Concept load on the first visit

Panorama, foco de observación, familias (10), Axent, Knowledge, brief, Customer Zero
(in the privacy notice), AXIGLAND (example footnote), "lentes de atención", "señal
ilustrativa", "corte temporal". Only *organization*, *what changed*, *why it matters*,
*evidence* and *price* are needed to decide.

## 4. "AXIGNAL observing AXIGNAL" as the canonical public example

Destroyed first, as asked:

- **Trust timing:** the controller's legal identity is still being published (#161 /
  Codex). An example whose own identity reads UNKNOWN undermines trust exactly where it
  must be earned.
- **Too little economy to show:** a pre-launch SaaS has almost no procurement demand,
  reviews, relationships or exposure. It would prove UNKNOWN beautifully and
  opportunity, reach and exposure not at all.
- **Wrong question answered:** visitors ask "what would I see about *my* business?".
  A self-portrait answers "what does AXIGNAL think of itself" and reads as
  self-promotion (MASTER §39 neutrality is about appearance too).
- **Authority boundary:** Customer Zero is an admin-private record (MASTER §2.1A). A
  public projection needs a governed, redacted, read-only contract and live production
  data on a public page: a capability activation, not a UI change.

**Verdict: not now.** Keep one fictional, explicitly labeled example whose story covers
all three scopes and all three epistemic states, rendered with the product's own
components. **Revisit when:** legal identity is published, a public projection contract
with redaction is authorized, and AXIGNAL's own observed footprint can show reach,
expansion and exposure. Then "Así ve AXIGNAL a AXIGNAL" becomes a strong *second* proof
("we run it on ourselves"), linked from Trust, not the first example.

Alternatives rejected: a real third-party company (consent, neutrality, reputational
risk); real public events around a fictional company (mixes REAL and SYNTHETIC).

## 5. Desired funnel

```text
curiosity     5 s   "Sabe qué cambia alrededor de tu empresa. Y por qué te importa."
                     + who it is for + €9.95/month per organization
comprehension 30 s  you choose → AXIGNAL observes and remembers → you see what matters and why
relevance           four situations: run a business · sales/BD · consultancies & agencies · SEO
proof               one example, opened at the right depth from four proof cards:
                     where it plays (garden) · where each conclusion comes from (evidence)
                     · what it does not know (UNKNOWN) · when it learned each thing (time)
trust               "Lo que AXIGNAL no hará": invent · sell what it says · mix your account with the world
desire / action     pricing that answers what I pay / what I get / what one organization is
                     → "Empieza con tu organización" → sign-up says the three next steps
```

Header: Cómo funciona · Ejemplo · Precio · Knowledge — Acceder · **Empezar**. Contact,
trust and data rights move to the footer and menu. One dominant CTA per stage: before
proof "Ver un ejemplo"; after proof, pricing and closing "Empieza con tu organización".

## 6. Ideal IA for the canonical public example

The example must tell one story, top to bottom, reusing subscriber components (demo ≤
product):

1. **Frame (one line):** guided example · fictional organization · what it does ·
   "in your account, real organizations you choose" · exits (start / back).
2. **Its economic world (first-map moment):** where it works · where it could grow (own
   acts only) · what affects it from outside (paths, not circles) · what is still
   unknown. Each place with its source and date. Shared with the subscriber reading
   through the spec 059 garden.
3. **What changed:** the dated change log (evidence arrived, opportunity updated, new
   tender, source became stale). The example already has these facts
   (`lib/cognition/facts.ts` `change.events`); today they are buried in a family lens.
4. **What deserves attention:** three items, one per epistemic state (POTENTIAL,
   OBSERVED, UNKNOWN), each with *what happened · why it matters · which capability
   connects · why it is within reach · evidence · what remains uncertain*. No score.
5. **What AXIGNAL watches next:** the signals' `next` fields as a short list ("read the
   programme requirements", "look for more opinions").
6. **Time:** the global cut (July → September → now) re-renders all of the above
   without future knowledge.
7. **Ask:** AXENT as a secondary rail, after the reader has seen the context.
8. **Explore by topic:** the ten families, collapsed by default (progressive
   disclosure), still one click away for experts.

Empty state: "No hubo cambios materiales esta semana" is a valid first section; it is
never filled with invented activity.

## 7. Concepts to delay or remove from public pages

| Concept | Decision |
| --- | --- |
| Xeed, AXIGLAND, FAXT, INXIGHT, PATHX, Customer Zero | Remove from public copy (MASTER §1.1) |
| Foco de observación | Say "organización observada"; keep the term inside the account |
| Panorama | Product screen name only; not a CTA promise ("Descubrir mi Panorama") |
| Familias (10) | Inside the example, collapsed; not on the landing |
| AXENT | After the context exists (step 3 of "cómo funciona"), never as the headline |
| MCP | Pricing inclusion: "tu contexto también en Claude y otros asistentes compatibles con MCP" (spec 057, verified with real Claude) |
| Knowledge | Header link for SEO/method; not a landing section |
| Weekly brief | Only when wired and enabled; never as a local draft |
| Human advisory | Keep the separate offer (MASTER §27.5) once contact works |

## 8. Implementation (this branch)

Implemented as designed; see [spec.md](spec.md) for decisions and
[validation.md](validation.md) for results. Still open, outside this surface: the
legal identity and live Contact/GDPR/newsletter channels (CTO #161 and Codex), checkout
(contracting off), and the measurement switch (operator, with the privacy notice).

## 9. Evidence

Before (production, above the fold): `evidence/before-*.jpg`. After (this branch, local build): `evidence/after-*.jpg`. Full-page captures and per-page audits are
reproducible with `apps/web/experience/qa/060-product-funnel/capture.mjs`.
