# EB-05 implementation plan

1. Reuse the Decision Lab vNext compiler, DecisionContracts, FR-22 artifact
   conventions and the EB-04 StructuredEvaluatorPort/TypedJudgmentVector
   semantics; do not introduce a second domain contract.
2. Add offline fixture mechanics for single and batch execution over identical
   answerable compiled inputs, with labels excluded from adapter-visible state.
3. Measure per-contract dimension coverage/risk, severe errors, schema/failure
   counts, latency and usage. Keep unavailable monetary cost explicit.
4. Preserve exact request identity independently from measured latency, and
   keep failed batch calls visible without implicit fallback.
5. Publish deterministic preflight evidence for current eligibility. Jev stays
   blocked by ADR-0048; Luna/OpenAI remain unavailable without governed binding.
6. Repair and test malformed provider distribution rejection.
7. Run focused tests, deterministic repository gates, Graphify update and diff
   checks. Commit the slice without merge or push.
