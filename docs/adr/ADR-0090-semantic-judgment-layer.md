# ADR-0090: Semantic judgment layer (Python, System One, reasoning)

- **Status:** Proposed for CTO decision
- **Date:** 2026-10-08
- **Authority:** MASTER §13–14 (models are replaceable and not authority), §8 (demand-materialized reuse), §27–29 (price per Focus, computational budget), §53 (typed questions, no universal score); Constitution; ADR-0006, ADR-0011, ADR-0047, ADR-0048, ADR-0089; spec 062.
- **Supersedes, if accepted:** the eligibility disposition in `docs/research/jev/EB05_JEV_ELIGIBILITY_REASSESSMENT_2026-10-05.md` for production use (not for distillation, which stays prohibited).

## Context

AXIGNAL had two cognitive extremes in production: deterministic cues (cheap, auditable, low recall, local vocabularies) and Luna (`gpt-6-luna`, grounded answers: capable, slower, priced per input and output token). TypeSafe's Jev answers narrow typed questions over supplied state in about 150 ms, charges only input tokens (USD 0.042 per million for `jev-1.13.0`) and reads the state once for many questions. It was unused: the only live run (P0-JEV-03) sent state without the claim or evidence, and EB-05 then failed closed on MCA §2.3(b).

Read in full, MCA §2.1–2.2 licenses integrating the API into the customer's own applications for its end users. §2.3(b) forbids using the Services or Output to distil the model, train a model that imitates it, or develop a similar or competing product or service, i.e. a competitor to TypeSafe. AXIGNAL is an economic-intelligence application that would use Jev as a component. This is an engineering reading for the CTO, not a legal opinion.

## Decision

1. **One provider-neutral layer** (`application/semantic_layer`): versioned questions (Choice, Score, Noul), world-level JSON state, typed answers that are never canonical truth, a cost ledger with versioned prices, per-run budgets, and an exact judgment memory keyed by state fingerprint, question version and evaluator model.
2. **A cascade, with Python at both ends.** Python compiles state and filters first. System One answers every question of a batch in one call. Questions declared escalable that stay uncertain go to the reasoning model, one call per batch, within a call budget. Python decides what any answer may change. Over budget means abstain (UNKNOWN); a provider failure is UNKNOWN for that batch only.
3. **Adapters stay replaceable.** `cognition/providers/typesafe_system_one.py` is the only place that imports the TypeSafe SDK. Luna serves a new `SEMANTIC_DECISION` job with a strict JSON schema whose values are the declared labels or `UNKNOWN`; quoted state is data, never instructions. An open-weight evaluator can implement the same port.
4. **Reuse is the economic engine.** State is world-level (public notice, capability class), never tenant-private, so a judgment made for one Focus serves every Focus that meets the same tender. Model or question changes are misses and are judged again.
5. **First consumer: the semantic demand screen** (spec 062). It may filter confidently unrelated demand (counted as `SEMANTIC_UNRELATED`, not deleted), supply the delivery mode the Economic Relevance Gate needs, and order surfaced demand by judged fit. It never creates candidates, widens reach or strengthens an epistemic state.
6. **Off by default.** Composition requires `AXIGNAL_SEMANTIC_LAYER_ENABLED=true`, a readable TypeSafe key file and a positive budget; escalation additionally needs a positive Luna call budget and reuses AXENT's Luna binding and operator prices.
7. **Never distil.** No Jev output is used to train, fine-tune or calibrate another model. Open-weight alternatives may be trained only on AXIGNAL's own human labels.

## Consequences

- Semantic depth per Focus becomes compatible with €4.95 per additional Focus: at USD 0.042 per million input tokens, two hundred judged batches a day cost cents a month before reuse.
- Thresholds are policy, not truth; they must be evaluated on AXIGNAL's labelled cases before being trusted (calibration is not assumed).
- Known Jev 1.13 weaknesses (counting, dates, arithmetic, indirection, large noisy state) stay in Python by construction; the cascade refuses state over the documented limits instead of truncating.
- Rate limits are adjusted dynamically by TypeSafe; the SDK's bounded backoff applies and failures degrade to UNKNOWN.
