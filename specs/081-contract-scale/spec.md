# Feature Specification: Contract scale observed, lead activity first

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17, on biocultor.com: its secondary garden-care service "está en la web y Jev está haciendo bien su trabajo"; "continúa con el resto de puntos" (contract scale vs organization size; the lead activity first).

## Measured problem
- **Calls of every size were shown with no indication of size.** A small shop received 97 calls, among them one-year municipal green-area maintenance contracts worth more than a million euros. The source publishes value, lots and duration, but AXIGNAL did not read them.
- **The lead activity and secondary ones were mixed together.** Fertiliser supply (lead) and garden care (secondary) were interleaved.

## What changes
1. **`ContractScale`** holds what the source publishes: estimated value, currency, lots, smallest lot and duration in whole months. Every field is `None` when the source says nothing (unknown, never zero).
   - **TED:** `estimated-value-proc/lot`, `estimated-value-cur-*`, `duration-period-*-lot`.
   - **PLACSP (CODICE):** `BudgetAmount` (valor estimado, or else the budget before tax) for the project and each lot, and `PlannedPeriod/DurationMeasure`.
   - Both stores persist it. Records stored earlier read as unknown.
2. **Live demand** carries `scale` on each call and lists the **lead activity first**: the order in which the site's reading names its activities. Within each activity the existing order stays (fit, buyer's classification, novelty, deadline). Nothing is hidden or removed.
3. **Web:** each call's evidence shows "Published estimated value", "Lots; the smallest" and "Published duration" in 6 languages, as observed facts.

## Doctrine
Scale is **not** a filter, a score or a verdict on reach. Whether a call is within reach is a judgment the person makes. A later, inspectable reach dimension (for example a solvency ratio) needs the organization's observed turnover and is not inferred here (MASTER: no opaque universal score; UNKNOWN ≠ FALSE).

## Tests
- `tests/world_demand/test_contract_scale.py`: durations, TED total/lots/smallest/duration, PLACSP fixture, storage round-trip, lead-first ordering with nothing hidden.
- `apps/web/experience/tests/first-observation.test.ts`: the facts are shown, and nothing published shows nothing.
