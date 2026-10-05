# EB-07 implementation plan

1. Reuse EB-04 EconomicReasoningResult and ExplainableBasis to project opportunity without new truth authority.
2. Reuse Prime + ResearchValue decisions as the only input allowed to create continuous-observation work.
3. Add a small application contract for shared work and a SQLite adapter with requester dedupe and lease fencing.
4. Prove shared work, persistence, lease reclaim, stale-token rejection and state-change identity in focused tests.
5. Run full deterministic gates; commit without production deployment.
