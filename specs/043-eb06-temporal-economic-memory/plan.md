# EB-06 implementation plan

1. Extend existing Observation Memory field/state contracts minimally with explicit temporal state.
2. Add optional timezone-aware `as_of` filtering to deterministic state compilation.
3. Derive typed field changes while retaining existing StateChange dependency invalidation.
4. Persist field temporal state in the existing SQLite adapter, including migration default for older databases.
5. Prove replay/incremental equivalence, temporal-state semantics, history retention and selective invalidation with focused tests.
6. Run repository gates and commit without merge or push.
