# EB-08 — Human Product & Production Proof

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER → Constitution → Human-First ADRs → FIRST_MAP readiness → EB-04..EB-07 → Economic Brain Execution Roadmap
**Roadmap slice:** EB-08

## Purpose

Carry governed economic-brain output into the existing subscriber product contract,
prove continuity/isolation at 1/2/100 Organization contexts, and establish measured
load/backup/recovery evidence before production exposure.

## Reuse before creation

EB-08 reuses:
- EB-04 FirstEconomicVerticalE2EResult and EconomicHumanOutput;
- EB-07 opportunity semantics;
- existing RuntimeSignal / RuntimeProjection and Today/AXIGLAND rendering;
- FIRST_MAP readiness and FR-30 persisted read-model;
- FirstProofStore SQLite persistence.

No parallel frontend, read model, graph, tenant store or workflow/scheduler is created.

## Authorized behavior

1. Map EconomicHumanOutput into the existing subscriber RuntimeSignal contract:
   POTENTIAL/UNKNOWN remains explicit; evidence, time, uncertainty and source lineage survive.
2. Attach the economic Xignal to an existing subscriber projection only when the
   output subject matches the projection Organization.
3. Preserve the existing Xeed→Xignal membership and Today semantics.
4. Keep the complete EconomicHumanOutput as an internal read-model extension;
   the web parser may strip unknown operational extensions while rendering the
   normalized Xignal through the canonical RuntimeSignal contract.
5. Exercise FirstProofStore with isolated 1, 2 and 100 Organization/Xeed contexts.
6. Measure write/read/backup durations without declaring an SLA.
7. Create and verify a consistent SQLite backup using sqlite3 backup; reopening
   both the live store and backup must recover every expected context.

## Invariants

- Human wording never changes epistemic meaning.
- POTENTIAL != OBSERVED.
- UNKNOWN != FALSE.
- Economic output subject must equal the selected Organization context.
- Xeed attention never becomes Organization ownership/truth authority.
- Evidence Narrative remains navigable from the RuntimeSignal.
- Backup/load harness data is explicitly synthetic and cannot become economic truth.
- Performance measurements are observations from the test machine, not product claims.
- Production exposure is forbidden until browser E2E against the exact candidate SHA succeeds.

## Measured local evidence — 2026-10-05

| Organizations | Write total | Read total | DB bytes | Backup | Recovered live | Recovered backup | Isolated |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 11.515 ms | 1.123 ms | 20,480 | 13.209 ms | 1/1 | 1/1 | yes |
| 2 | 25.948 ms | 2.020 ms | 20,480 | 14.334 ms | 2/2 | 2/2 | yes |
| 100 | 1525.191 ms | 38.319 ms | 159,744 | 13.736 ms | 100/100 | 100/100 | yes |

These measurements are reproducible harness observations, not SLA commitments.

## Exit criteria

- Economic POTENTIAL/UNKNOWN output parses and renders through the existing runtime contract.
- Existing projection is not mutated in-place by composition.
- Cross-Organization attachment fails closed.
- 1/2/100 store contexts are isolated and recover after reopen and backup restore.
- Frontend unit/type/build and repository deterministic gates are green.
- Browser product E2E proves Today/AXIGLAND/evidence/continuity on the exact integrated SHA.
- Production deployment occurs only after that browser proof and must be verified externally.
