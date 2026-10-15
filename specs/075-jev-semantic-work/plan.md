# Plan: Jev where it is most useful (spec 075)

## Constitution check

| Gate | Result |
|---|---|
| MASTER precedence | Pass. §56.13, §56.14 and §56.17 describe this use. No doctrine change. |
| Truth boundary | Pass. A judgment only labels, orders or sets aside. It never creates candidates, widens reach, strengthens an epistemic state or writes canonical truth. |
| UNKNOWN != FALSE | Pass. No judgment means the call is shown as today, and UNRELATED is never inferred. |
| Provider neutrality | Pass. The `application/semantic_layer` ports are used; only `cognition/providers` imports the SDK. |
| Input rights (ADR-0090) | Pass. Calls are public demand that may be displayed. Activity verification sends controlled vocabulary and page kind only. |
| No training on Jev output (ADR-0090) | Pass. Measurement uses AXIGNAL-owned truth labels only. |
| Deterministic CI | Pass. Tests use fake judges; no gate calls a provider. |

## Architecture review

**Slice 1 (US1, this PR): fit judgments for live demand.**

1. **Questions and state stay those of spec 062.** `semantic_screen.record_batch(record, capability_id)` builds the same world-level state from a `ProcurementRecord` (the candidate wrapper delegates to it), so a judgment made once serves every Focus and every subscriber.
2. **Off the read path.** A new job, `tools/runtime/demand_fit.py`:
   - takes each complete open-demand slice and its calls still open;
   - pairs them with the catalog capabilities that the organizations' stored readings carry, matched by code;
   - skips pairs already in memory and judges the rest, newest first, within a per-run token budget, through the existing cascade (ledger, budget, memory, one batch per call).
   - It runs after daily ingestion (`observation_daily`) and in `run_golden` (self-check and golden set), bounded and opt-in through the existing layer switch.
3. **Read from memory only.** `fit_recall(memory, judge, model)` returns, for (record, capability), the remembered FIT label, or None when the judgment is missing, from another model or question version, or uncertain under the cascade policy. `LiveDemandReader` takes it as an optional port. No provider call happens at read time.
4. **Composition (Python, deterministic, no score).**
   - A call's fit is its best fit across its matched capabilities. It is unknown if any capability's fit is unknown, because unknown never sets aside.
   - UNRELATED is set aside: removed from `candidates`, counted in `demand.setAsideByFit`, and listed in `demand.setAside` (title, link, capabilities, fit).
   - The order is CORE, unknown, PARTIAL, ADJACENT, then the buyer's ADDITIONAL classification, then new, then deadline.
5. **Presentation.** Each call carries `fit`, `fitBy` (evaluator, model, question version) and a label in the observatory and the first-observation copy, saying it is an evaluator's judgment.
6. **Measurement.** `run_golden` judges the observed organizations' pairs inline, so the self-check measures precision with fit applied. Promotion follows FR-008.

**Slice 2 (US2, next PR): activity verification.** A CHOICE question per lexicon activity, over controlled vocabulary, page kind and anonymous page ids, measured on the golden and truth sets before it can establish or reject an activity.

## Risks

- **Provider rate limits or outage.** Pairs stay unjudged and lists behave as today. The job is bounded and resumable through memory.
- **Wrong UNRELATED judgments hide real demand.** Set-aside calls stay inspectable, and the self-check and golden set measure false negatives before default enablement.
- **Cost.** About 400 input tokens per pair at $0.042 per million: under $0.05 for 1,000 new pairs. Budgets live in configuration and the ledger.
