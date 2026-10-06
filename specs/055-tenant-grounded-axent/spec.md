# 055 — Tenant-grounded AXENT

**Status:** IMPLEMENTED behind configuration (off by default) · **Date:** 2026-10-07
**Doctrine:** MASTER §13 (replaceable providers), §14 (models are not truth),
§15.1 (CLAIM ≠ WRITE), §15.4 (UNKNOWN ≠ FALSE), §20 (currentness), §53.3
(derived opportunity stays POTENTIAL). Consumes 049–052 (subscriber runtime,
authorized read) and 054 (observation runtime coverage).

## Root problem

Subscriber AXENT answered with regexes and fixed sentences over the authorized
reading: no reasoning, no per-question retrieval, no memory, no abstention
beyond a template, no research request. The obvious way to add Luna (send the
whole reading and the transcript every turn) costs ~5k input tokens per turn,
grows with the conversation and lets the model answer from general knowledge
(measured: 4 ungrounded claims in 10 turns).

## Design

```
question → subscriber read (principal, membership, tenant, Xeed re-checked)
  → corpus of that reading only (+ runtime family coverage for that Xeed)
  → deterministic intent: kind × canonical families × geographies × named subjects
  → retrieval: family narrowing → geography → temporal cut → lexical rank → dedup
  → budgeted pack (items, per family, changes, gaps, evidence tokens)
  → route: abstain | deterministic (counts, unknowns, sources) | cache | Luna
  → Luna (gpt-6-luna, no tools, strict JSON, store=false) proposes claims citing pack refs
  → verification: unknown refs dropped; epistemic and currentness from cited evidence
  → answer composed from verified claims only; unknowns; ResearchRequest if needed
```

- **Tenant isolation** is the access boundary, not a filter: the only corpus is
  the reading returned by `SubscriberEconomicRuntime.read`, which re-checks the
  principal's membership, the tenant and the Xeed. There is no global index.
  Cache keys carry tenant, Xeed and the corpus fingerprint (evidence, epistemic
  state, currentness, provenance, day of cut). Research requests are stored per
  tenant and Xeed.
- **No second brain:** no vector store, no new taxonomy (the ten canonical
  `ObservationFamily` values), no new truth. Luna sits behind
  `CognitiveProvider` through `ModelRouter`; JEV is untouched.
- **Grounding:** a claim survives only if every cited ref is in this turn's
  pack; its label is the weakest of the cited evidence, so POTENTIAL is never
  promoted and STALE never looks current. A question naming a subject absent
  from the tenant's evidence (e.g. another organization) is declined without
  inference and without research on a third party.
- **Security:** evidence text is sanitized (control characters, prompt
  delimiters neutralized, length-bounded), quoted inside `<evidence>`, and
  flagged `untrusted_text=true` when it looks like instructions.
- **Memory:** the client returns the previous turn's compact memory (focus,
  family, geographies, cited ids). It is validated against the authorized focus
  and only continues elliptical follow-ups; every turn retrieves again from the
  reading. No transcript is sent to the model.
- **Model routing:** counts, unknowns and sources are answered by Python; no
  evidence → abstention; unchanged evidence → cache; only synthesis calls Luna.
- **Generative UI** stays deterministic (`composeFamily` + `validatePlan`);
  Luna writes only the prose.

## Configuration

- Runtime: `AXIGNAL_AXENT_LUNA_MODEL` (e.g. `gpt-6-luna`) plus `OPENAI_API_KEY`
  in the process enable Luna; without them AXENT stays deterministic/extractive.
- Experience: `AXIGNAL_AXENT_GROUNDED=true` routes `/api/subscriber/axent`
  through the grounded endpoint; otherwise the previous explanation is kept.
- Prices are arguments of the cost model (`CostRates`), never constants.

## Evidence

- `benchmark-live.json`: 10 fixed turns (SEO, reputation, opportunities,
  relationships, change, unknown, cross-tenant, why, follow-up, count) against
  `gpt-6-luna`, provider-reported usage. Naive full-reading-plus-transcript vs
  grounded: input tokens 49,553 → 2,611 (−94.7 %), output 2,051 → 554, model
  calls 10 → 4, total latency 26.2 s → 7.3 s; ungrounded claims shown 4 → 0
  (1 dropped by verification).
- `tests/axent/`: the 15 adversarial cases, verification, Luna call shape, cost.
- `tests/integration/test_axent_grounded_e2e.py`: two tenants on the same
  canonical organization through the real subscriber HTTP facade.

## Out of scope / UNKNOWN

- Luna list prices: the cost model needs configured rates; with the measured
  tokens, cost per turn = (2,611 × in + 554 × out) / 10 / 1e6.
- The observation runtime does not yet consume the research-request ledger
  (requests are recorded per tenant and Xeed; attention only).
- Production enablement and deployment.
