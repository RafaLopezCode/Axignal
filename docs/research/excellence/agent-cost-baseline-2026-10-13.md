# What one organization would cost a subscriber's own agent each month

Estimate of 2026-10-13, model in `tools/evaluation/agent_cost.py` (`python -m tools.evaluation.agent_cost`).

- **Baseline prices:** GPT-6 Luna as configured in production: **$0.125 / M input tokens, $0.50 / M output tokens**. Exchange rate used: 0.92 EUR/USD, a stated assumption, not a live quote.
- **Comparison point:** **€4.95 / month** for each additional organization.

## What the agent would have to do

The work is what AXIGNAL delivers for one organization: the ten families, the crossings, and their evolution. It breaks down into **19 tasks** (website and audit, real-user speed, GEO questions, press, notoriety, reviews, activity and certifications, markets, technology and logo walls, 12-month public awards, open public calls, value chain, job board, registers, identifiers, sector headlines, regulation, crossings, monthly diff).

- **Cadence:** a full study each month, plus a **weekly refresh** of the volatile ones (demand, press, jobs, speed, headlines, regulation) so evolution can be seen.
- **Calls:** 235 tool calls a month per organization.
- **Calibration:** the 8-country golden pass of the same day, where the median organization has 6.5 families with findings, about 22 findings, and up to 99 distinct sources in relationships.

## Monthly cost per organization

| Scenario | Input tokens | Output tokens | Token cost | Agent time | Person's time supervising |
|---|---|---|---|---|---|
| Efficient (context amplification 1.5×) | 4.1 M | 0.14 M | **€0.53** | 31 min | 32 min |
| Central (4×) | 10.8 M | 0.27 M | **€1.37** | 59 min | 68 min |
| Heavy (10×) | 27.0 M | 0.41 M | **€3.30** | 98 min | 132 min |

**Context amplification** is the factor an agent loop re-reads its growing context with on every turn. Agent time is 8–25 s per call.

## Reading it honestly (MASTER §30.2)

- **On tokens alone, Luna is cheap.** In every scenario an agent's tokens cost less than €4.95, so the price argument cannot be "tokens".
- **The argument is time.** It takes **1–4 hours a month per organization** of agent plus a person's attention: launching the work, checking it, keeping notes and comparing month to month.
  - Central scenario: ~2 h (59 min of agent, 68 min of supervision).
  - At an illustrative €30/h, the person's time alone costs **~€34 per organization a month**.
- **And it is what an agent does not get by itself:**
  - **Not reproducible:** 12 months of public contract awards (more than 150,000 awards indexed) that reveal its clients, partners and competitors.
  - **Partially reproducible:**
    - Real-user speed (CrUX needs its own key).
    - GEO measured with a frozen instrument, comparable month to month.
    - Press, regulation and tenders in several countries and portals.
    - Value-chain tables.
    - **Evolution itself:** an agent remembers nothing between months unless someone keeps and compares its notes. AXIGNAL keeps every family in time, with dated changes.
  - **Governed states:** observed, declared, potential and unknown, with source, instrument and limitation. An agent mixes them unless instructed every time.
- **With AXIGNAL's MCP** (ADR-0095), the same agent reads the panorama, the evidence and the history in a few calls of compact JSON: a few tens of thousands of tokens instead of millions, minutes instead of hours.

## Next

Measure the MCP side for real: an agent writes the value report of each golden-set organization (a) with the MCP and (b) on its own. Record tokens, time, verifiable claims and epistemic errors (roadmap phase A, agent evaluation).
