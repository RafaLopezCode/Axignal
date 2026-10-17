# Feature Specification: What fits best first, the rest apart with its reason

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17, on what would make AXIGNAL sellable at 9.95 €: "Mejor 5 oportunidades buenas que 95 mezcladas". Biocultor was shown 94 calls mixed together.

## What changes
1. **Each live call says whether it fits best.**
   - A call is `focus: BEST` when all of these hold:
     - it is for the organization's **lead activity**;
     - its own **main object** is the activity, not an additional code;
     - an evaluator did not judge it only PARTIAL or ADJACENT.
   - Otherwise it is `OTHER`, with inspectable `otherReasons`: SECONDARY_ACTIVITY, ADDITIONAL_CODE, PARTIAL_FIT or ADJACENT_FIT.
   - Nothing is hidden or scored, and `best` is counted beside `total`.
2. **The fit of open demand is judged once per UTC day by the runtime** (`judge_demand_fit`), bounded by `AXIGNAL_SEMANTIC_FIT_TOKEN_BUDGET` and shared through judgment memory, at about $0.02/day for all clients. Before, only the daily loop and the self-check judged it, so production reads were mostly unjudged.
3. **The web shows two groups.**
   - "What matters" lists only the calls that fit best.
   - "Other possible ones" is collapsed. Each card says why it is not above.
   - The tally reads "N open tenders that fit best · M other possible ones, with their reason".
   - All copy is in 6 languages.

## Doctrine
Multidimensional and inspectable: each reason stands alone and there is no universal score (AGENTS). Opportunity stays POTENTIAL. An evaluator's fit is non-authoritative and shown as such. UNKNOWN fit never demotes a call.

## Tests
- `tests/world_demand/test_contract_scale.py`: BEST and OTHER with reasons; a single activity is never "secondary"; each reason is checked on its own.
- `tests/first_observation/test_daily_demand_fit.py`: once per UTC day.
- `apps/web/experience/tests/demand-focus.test.ts`: the grouping, the reasons and the tally.
