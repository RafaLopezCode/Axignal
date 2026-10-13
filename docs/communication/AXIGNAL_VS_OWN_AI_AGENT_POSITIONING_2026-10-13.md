# AXIGNAL vs "I'll do it with my own AI agent": positioning appendix

**Status:** Working strategy, an appendix to `AXIGNAL_COMMUNICATION_STRATEGY.md` (Gate 4 Differentiation; Q4 "Why should I believe what AXIGNAL shows me?"; Q7 "Why is persistent observation better than a one-off analysis?").
**Date:** 2026-10-13
**Authority:** MASTER §30 (moat: what is not defence), §30.2 (cost advantage ≠ customer moat), §43.9 (wrapper test), §10/§20 (LIVE, temporality), §15.4 (states), §21 (observability); ADR-0095 (subscriber MCP).
**Evidence:** `docs/research/excellence/agent-cost-baseline-2026-10-13.md` (cost model), `docs/research/excellence/golden-2026-10-13-de3b34a.json` (30 organizations, 8 countries).

## 1. The objection

> "ChatGPT/Claude can research a company for me. Why pay AXIGNAL?"

It is the most important objection for 2026–2027 buyers, and it gets stronger as models improve. The answer cannot be price, and it cannot be "AI can't do this".

## 2. What we must NOT say (honesty rules)

- **Not "it's cheaper in tokens".** It is false. With GPT-6 Luna an agent's tokens cost about €0.5–3.3 per organization per month, below €4.95 (cost model). Saying otherwise would be refuted by any technical buyer.
- **Not "AI agents can't find this".** Many findings are public and an agent can find some of them.
- **Not "AXIGNAL is 100 % deterministic".** GEO answers vary and sources change. What we claim is that our variation is **bounded, measured and labelled**.
- **Not that AXIGNAL knows the truth** (communication strategy Q6). It observes with evidence and says what it does not know.

## 3. The five pillars (in persuasion order)

### Pillar 1: The same question gets the same answer (determinism and objectivity)

**Claim:**
- An agent gives a different report each time you run it: sampling, search results that change daily, different browsing paths.
- AXIGNAL applies the same sources, rules, thresholds and versioned instruments every time.
- The model is used only for bounded judgments, with a frozen instrument and a memory of past judgments.
- Crossings (INXIGHTs) are rules, not opinions.

**Why it matters:** an analysis you cannot reproduce is an opinion, not a measurement.

**Proof to build (measurement plan, phase A):**
- Run an agent alone 3 times on the same company and AXIGNAL 3 times.
- Publish the % of findings that change between runs.

### Pillar 2: Evolution you can trust (history)

**Claim:**
- If an agent says 12 public clients this month and 8 last month, you cannot know whether the company changed or what the agent found changed.
- AXIGNAL compares readings by the same instrument, so a change means the company changed.
- Every family is kept in time: what appeared, what disappeared, when.

**Why it matters:** an agent remembers nothing between months unless someone keeps and compares its notes. AXIGNAL's value grows every week it observes. **The history cannot be bought or reproduced later.**

**Proof:**
- Timeline per family: dated changes, evolution and regression.
- `get_organization_history` in the MCP, with "since your last report".

### Pillar 3: Time back (hours, not tokens)

**Claim:**
- Reproducing AXIGNAL for one organization means about 235 tool calls a month.
- That is 31–98 minutes of agent time plus 32–132 minutes of a person launching, checking, keeping notes and comparing.
- Central scenario: about **2 hours a month per organization**.
- With AXIGNAL it is minutes: open the panorama, or let your agent read it through the MCP in a few calls.

**Why it matters:** the scarce resource of a CEO, a consultant or an agency is attention, not tokens. At an illustrative €30/h, the person's time alone is about €34 per organization a month.

**Proof:** the cost model (assumptions published). Then, measured: agent with MCP vs agent alone.

### Pillar 4: Evidence with its state (no mixed truths)

**Claim:**
- Every AXIGNAL finding says whether it is **observed**, **declared** by the organization itself, **potential** or **unknown**, with its source, instrument and limitation.
- An agent mixes them: it turns a company's claims into facts and plausibility into statements, and sometimes invents figures or sources with full confidence.
- It also inherits the bias of whatever search ranking or SEO pushes. AXIGNAL is an **independent observer**, not configured by the company it observes (MASTER §22).

**Why it matters:** you can defend a conclusion in front of a client, a board or a buyer only if you can show where it comes from and how sure it is.

**Proof:** "Show me how AXIGNAL knows" on every finding; observability per family (strong, partial, limited, unknown) instead of a magic score.

### Pillar 5: What an agent does not get by itself

**Claim:** some of what AXIGNAL shows is not available to a general agent, or only with effort and keys:
- **12 months of public contract awards** (more than 150,000 indexed), which reveal clients, partners and competitors.
- **Tenders and official journals** across countries and portals, screened continuously.
- **Real-user speed** (CrUX, its own key).
- **AI visibility** measured with a frozen instrument, comparable month to month.
- **Notoriety and hiring signals**, kept as series.

**Why it matters:** this is the difference between searching and observing.

**Proof:** the golden-set coverage per family and per country, published with its limits.

## 4. The synthesis line

> **Tu agente busca. AXIGNAL observa.**
> *Your agent searches. AXIGNAL observes.*

The same answer every time; the evolution with dates; each piece of evidence with its source and its state. And your agent can read it all from AXIGNAL in minutes.

Supporting lines (ES base; translate with care):
- «La misma pregunta, la misma respuesta. Lo que cambia es la empresa, no el instrumento.»
- «Tu agente no recuerda el mes pasado. AXIGNAL sí.»
- «Dos horas al mes por organización, o un minuto.»
- «Observado, declarado, potencial o desconocido: nunca mezclado.»
- «No compitas con tu agente: conéctalo. AXIGNAL por MCP le da el panorama, la evidencia y el historial.»

## 5. Where it is used

| Surface | Pillar(s) | Note |
|---|---|---|
| Landing, differentiation section | 1, 2, 4 | Never lead with price (COMMUNICATION ≠ PRICING). |
| Pricing page, FAQ "Why not my own agent?" | 3, 5 | Here time can be quantified with the published model. |
| Marketing pool letters (agencies, consultancies) | 2, 3, 4 | Agencies: "measure what changed independently of your work" (MASTER §22). |
| MCP connection page | 3, + "connect, don't compete" | The agent becomes AXIGNAL's reader, not its rival (MASTER §44). |
| Sales/demo | All, with the live panorama and its history | Show the same organization twice: identical reading. |

## 6. Proof backlog (we claim only what we can show)

1. **Consistency test:** an agent alone run 3 times vs AXIGNAL; % of findings that differ.
2. **MCP test:** a value report with the MCP vs without it; tokens, time, verifiable claims, epistemic errors.
3. **History demo:** an organization with ≥30 days of timeline and dated changes.
4. **Golden-set coverage:** keep publishing per family and per country, including what is still weak.

Until a proof exists, the related claim is phrased as a design principle ("AXIGNAL compares readings by the same instrument"), never as a measured result.
