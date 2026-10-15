# Tasks: Jev where it is most useful (spec 075)

## US1: fit judgments for live demand (this PR)

- [x] T001 `semantic_screen.record_batch`: world-level fit state from a `ProcurementRecord` (the candidate wrapper delegates).
- [x] T002 `semantic_screen.FitRecall`: memory-only recall by exact state, question version and model; uncertain answers are unknown.
- [x] T003 `world_demand.fit`: `open_pairs` (open calls × catalog capabilities, by code, newest first) and `judge_pairs` (cascade: memory first, then System One within budget).
- [x] T004 `semantic_layer.fit_cascade_factory_from_env`: own budget, `AXIGNAL_SEMANTIC_FIT_TOKEN_BUDGET` (default 500k, hard cap 2M input tokens per run).
- [x] T005 `tools/runtime/demand_fit` job, run after daily ingestion (`observation_daily`) and inline in `run_golden` (self-check and golden set).
- [x] T006 `LiveDemandReader(fit=…)`:
  - UNRELATED is set aside, counted and listed;
  - the order is CORE, unknown, PARTIAL, ADJACENT;
  - duplicates keep the more favourable judgment;
  - no provider call on read.
- [x] T007 Web:
  - fit label and proof row ("non-authoritative judgment by {model}");
  - set-aside tally and inspectable list;
  - contract fields `additional`, `setAsideByFit` and `setAside`;
  - six locales.
- [x] T008 Tests:
  - set aside, order, unknown;
  - no judgments behaves as before;
  - another model is never reused;
  - pairing, budget, layer off;
  - web copy and contract.
- [ ] T009 After deploy: the self-check measures the truth set with fit applied (FR-008), and the daily ledger reports spend (SC-005).

## US2: activity verification (this PR)

- [x] T010 CHOICE question `activity_offered` (OFFERED / MENTIONED / USED_INTERNALLY / UNCLEAR), with state from controlled vocabulary, page kind and anonymous page ids only.
- [x] T011 Only OFFERED (or no judgment) establishes a lexicon activity. MENTIONED and USED_INTERNALLY are kept as negative classifications.
- [x] T012 The rights test still proves that no site text leaves without rights (ADR-0090 amendment).
- [ ] T013 After deploy: measure on the golden and truth sets with `AXIGNAL_ACTIVITY_VERIFICATION_ENABLED=true` before enabling it by default (FR-008). Off by default until then; off keeps the lexicon result, marked UNVERIFIED.
