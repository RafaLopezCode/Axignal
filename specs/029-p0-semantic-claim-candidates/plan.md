# Plan

1. Add an explicit DOCUMENT_SEMANTIC_EXTRACTION cognitive job kind.
2. Define versioned semantic extraction targets and candidate budgets.
3. Bind jobs to exact document and contract fingerprints.
4. Normalize StructuredResult into AXIGNAL-owned EconomicClaimCandidate identities.
5. Require exact grounding against visible text or structured data.
6. Reject ungrounded, duplicate, over-budget and out-of-contract proposals.
7. Exercise the existing ModelRouter with a provider fixture.
8. Run full deterministic validation and integrate only after CI success.