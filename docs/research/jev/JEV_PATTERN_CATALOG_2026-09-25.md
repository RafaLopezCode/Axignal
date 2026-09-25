# Jev pattern catalog — 2026-09-25

This catalog reports patterns, not product authorization. Official patterns are tagged by source-ledger ID; independent community observations remain separate.

| Pattern | Shape | Evidence class | Reliable boundary | Failure / caveat |
|---|---|---|---|---|
| Structured judgment | relevant state + typed question → typed answer | OFFICIAL_DOC O2–O6 | Typed answer space constrains interface | Does not establish semantic correctness or truth |
| Named structured state | JSON object with fields referenced from instructions | OFFICIAL_DOC O2; OFFICIAL_SKILL | Exposes relationships and reduces ambiguity | Irrelevant/noisy fields may distract; sufficiency is task-dependent |
| Parallel fan-out | one state, multiple independent questions in one request | OFFICIAL_DOC O7 | Questions may be decided together; answers do not condition on peers | Cannot use an earlier answer to construct a later candidate set |
| Sequential evidence acquisition | code retrieves or transforms using earlier output, then sends a new state/question | OFFICIAL_DOC O9; cookbook O12 | Use when second step depends on fetched evidence or first result | Extra calls/cost/latency and provenance joins must be managed |
| Choice over bounded candidates | define fixed outcomes, including `none`/review where needed | OFFICIAL_DOC O3; O12 | Selects among supplied labels | Cannot select omitted candidate or create a novel one |
| Multi-label predicates | one Noul per independently applicable condition | OFFICIAL_DOC O5; community E1 | Avoids forcing mutually nonexclusive labels into one Choice | Multiple Nouls may be correlated; no single confidence field |
| Graded ordered dimension | Score with concrete ordered levels | OFFICIAL_DOC O4; O13 | Same dimension can be compared within an evaluated use | Score is not an interval-scale measurement absent validation |
| Evidence-grounded citation check | deterministic quote/search first; judge claim against exact section plus claim | OFFICIAL_COOKBOOK O12 | Provides the semantic content to assess | Example results are versioned author reports, not a general benchmark |
| Entity alignment | compare two entity records; separate identity from field matches; route related cases to review | OFFICIAL_COOKBOOK O13 | Candidate pair information is supplied | False merges can be asymmetric/high cost; validate task-specific review policy |
| Pick among extracted values | deterministic parser creates candidates; Jev selects from candidates + `none` | OFFICIAL_DOC O11; community E1 | Code retains exact source value and validates shape | Jev is not an exact copying/parser authority |
| Composite score | ask independent dimensions, compose with explicit code weights | OFFICIAL_DOC O8 | Weights/policy remain inspectable and editable | Weighted compensation is unsafe for veto conditions unless represented separately |
| Select-and-route | Choice/Score/Noul judgment then explicit code policy routes auto/review/abstain | OFFICIAL_DOC O6/O9; E1/E2 | Low-confidence/unknown can go to review | Threshold must be justified by domain error costs and measured outcomes |
| Feature discovery | Jev-generated labels/features evaluated by external classical model and held-out target | OFFICIAL_COOKBOOK O14 | Objective, dataset split and scores are owned outside Jev | Author cookbook result is not an AXIGNAL forecast |
| Tool/action proposal | ask bounded Choice over legal code-provided actions, execute only after policy validation | community E2; AXIGNAL_DERIVATION | Candidate legality and execution remain deterministic | A typed tool choice is not permission or canonical authority |

## Decomposition rules

- Split a complex question when its components have independent downstream use, distinct evidence requirements, or distinct error costs. Preserve relationship context when decomposition would remove necessary meaning.
- Batch independent questions sharing the same evidence state. Ask sequentially when an answer determines what evidence to fetch, how to construct the next state, or which alternatives exist.
- Compose scores, thresholds, vetoes, missing answers and actions in application code or domain policy. Do not ask Jev to silently encode opaque policy.
- Preserve raw judgments so a policy change can be replayed against the same judgments when question semantics and evidence are unchanged. Re-evaluate Jev when state, model, or question meaning changes.

Sources: [JEV_SOURCE_LEDGER_2026-09-25.md](JEV_SOURCE_LEDGER_2026-09-25.md).
