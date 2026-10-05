# EB-02 implementation plan

## Constitution check

PASS: stdlib deterministic Python; domain depends inward only; identity has no
subscriber/model authority; UNKNOWN and ambiguity retained; no canonical writer
outside admission; currentness/time preserved rather than inferred; no new
infrastructure or dependencies. MASTER and gates remain unchanged.

## Architecture review

Extend the existing resolver and document/extraction contracts. Domain owns
Unicode identity mechanics, immutable text/span contracts and scoped governed
binding receipts. Application bridges document representations and resolved
Organizations to these contracts; pipeline owns static HTML parsing. Admission
independently checks source authority, exact tuple, spans and binding receipts.
Name history is immutable input to resolution, not a new truth store or topology
rewrite. Existing append-only merge/split/reversal governance is unchanged.

Graphify graph.json and executable are absent in this worktree. Architecture
inspection uses accepted ADR-0049/0072/0079, Overview, terminology and the logical
atlas/current-state gap ledger. Attempt structural update after implementation;
record unavailable tooling as non-semantic limitation, never skip hard gates.

## Implementation and verification

1. Add domain text spans and governed name/binding contracts, extend exact
   resolver with Unicode-safe keys and temporally governed history.
2. Repair static HTML visibility, integrity and artifact lineage. Extend
   DocumentRepresentation with surface projection and verifiable offsets.
3. Validate supplied extraction offsets; derive only unique exact offsets for
   older provider payloads. Retain spans in candidates and rich-state inputs.
4. Require representation-grounded canonical claims and authentic scoped
   bindings for non-literal entities; migrate synthetic fixtures explicitly.
5. Run focused adversarial suites, then format/lint/type/full tests/architecture/
   governance/diff gates. Converge against FR/SC, document evidence and commit.
