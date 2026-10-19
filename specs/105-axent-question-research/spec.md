# Spec 105 — AXENT researches a question on the web, now (step 3)

## Why
When grounded AXENT cannot answer from the authorized reading it abstains and records a
research request, consumed only by the daily loop, which is off in production. The
subscriber got "no evidence" and nothing else.

## What
- Runtime: `POST /subscriber/organizations/{focus}/research {question}` behind the same
  session authorization as AXENT, on the subscriber's own organization only.
- `WebResearchRunner.ask`: **one search** — the brand as the press writes it ("Huel", not
  "Huel Limited"), the question, `-site:` its own domain — then at most **three pages read by
  AXIGNAL** within 15 s; a page is returned only if its own text names the organization.
  10 questions per tenant and UTC day, inside the global search cap; the same question is
  not paid twice (30-day shared cache).
- Web: under an answer that does not settle the question (abstention or a free question),
  "Investigar en la web" (subscriber only, never in the illustrative demo). The pages appear
  in the conversation with title, outlet, date and the page's words, as POTENTIAL: nothing
  becomes a finding; what the subscriber asks directs attention only (MASTER).

## Measured live (isolated copy, real key)
- Goiko, "¿Qué opinan sus clientes de la calidad?" → Economía Digital "los usuarios se quejan
  de la calidad", Sluurpy reviews (2.3 s).
- Holded, "¿Ha recibido inversión o financiación?" → "la ronda… en la que ha captado $1,6M" (3.6 s).
- Huel, "Is it planning an IPO?" → "Danone is acquiring Huel… in a €1B deal" (1.6 s); with the
  legal name in quotes it found nothing, hence the brand.
