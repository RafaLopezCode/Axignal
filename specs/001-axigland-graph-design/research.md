# Research: AXIGLAND Graph Design Governance

## Decisions

1. **Accept the bakeoff architecture as ADR-0009.** CTO authorization selects
   HYBRID, no foundation framework, AXIGNAL semantic/cartographic ownership,
   and Sigma + Graphology as the initial replaceable renderer implementation.
2. **Keep the renderer mechanical and behind an AXIGNAL-owned contract.** The
   contract's runtime schema is not frozen in this slice.
3. **Publish graph-specific skill guidance.** Existing `frontend-design` and
   `ui-ux-pro-max` remain subordinate; neither owns AXIGLAND product semantics.
4. **Make evidence status explicit.** P0-GRAPH-01R removed the Cosmos adapter
   and repaired harness behavior after raw evidence was committed. Historical
   filter/temporal figures and Cosmos measurements must not be described as
   currently validated/reproducible; Sigma expansion's final medium-fixture
   call had 3,900 pending nodes, not 20,000.
5. **Do not claim empirical label/accessibility success.** The bakeoff did not
   establish AXIGNAL label policy, accessibility architecture, or product
   performance targets.

## Rejected Alternatives

- Treat Sigma/Graphology objects as canonical graph truth: violates one
  canonical AXIGLAND and replaceability.
- Freeze an illustrative projection schema: not required to establish the
  architecture boundary and creates premature compatibility obligations.
- Add runtime/UI or renderer dependencies in this documentation slice: outside
  authorized scope.
- Reopen renderer selection despite CTO acceptance: contrary to the accepted
  decision absent invalid/corrupted source evidence.

## Evidence

- Accepted architecture decision and benchmark: `docs/research/AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md` and `AXIGLAND_GRAPH_ENGINE_BAKEOFF.md`.
- P0-GRAPH-01R repair commit and merged PR #3 are the source for harness
  caveats; immutable raw results/screenshots remain unchanged.
- Product semantics derive from the MASTER, Engineering Constitution, and
  ADR-0001 through ADR-0008.
