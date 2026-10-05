# Current-main integration architecture review

Date: 2026-10-05. Candidate: `a1c3519`; target: `b489156` on
`codex/economic-brain-integration`.

## Authority and disposition

Reviewed MASTER §§14–21, 46, 53, 55–56; Constitution; architecture Overview,
Terminology, logical Atlas and current-state gap ledger; ADR-0012/0013,
ADR-0047 and ADR-0072/0074/0075/0076/0077; candidate spec/plan/tasks; unified
Economic Brain execution roadmap. Constitution check: PASS for the internal
offline slice. No product or provider authority is added.

`a1c3519` and `b489156` share parent `441b4d0`. Their changed file sets do not
intersect. The semantic overlap is admission: the candidate's synthetic FAXT
fixture predates the required observation subject and GroundedClaim. Fix input
preparation and add rejection tests. EvidenceAdmission, execution budgets and
all existing gates/tests retain current-main implementation and expectations.

## Boundaries

- Application compiles normalized public inputs and independent dimensions.
  No acquisition, repository write or canonical factory occurs during reasoning.
- Only matching existing admitted FAXT supports OBSERVED/CORROBORATED input;
  declared material stays DECLARED. Final interpretation is POTENTIAL or UNKNOWN.
- Exact delivery/date/certification checks are deterministic. Three scoped
  semantic questions use StructuredEvaluatorPort and evaluate_structured;
  capability, request and replay validation remain provider-neutral.
- Confidence/distributions remain raw judgment metadata. Attention comes from
  a versioned multidimensional Python policy without a sale score or threshold.
- Basis retains evidence, identities, source/time, representations, uncertainty
  and material contradictions. Consumption at another time requires a new run.
- Human Output is an internal snapshot with no route or authorization grant.
  Its caller must supply previously normalized, rights-cleared public material.
  Rights-reference strings and fingerprints are not an independent verification
  or source-rights engine. Subscriber publication must use governed metadata-first
  authorization and exact narrative material resolution before payload access.
- No tenant-specific Organization, private truth store, provider SDK, dependency,
  renderer, UI or production configuration is introduced.

## Roadmap scope

This is useful offline EB-04 reference implementation; it does not bypass the
production critical path EB-01 → EB-02/03 → EB-04. It does not claim full
acquisition-to-product E2E, measured economics, durable incremental temporal
memory, or complete ontology/relationship typing. Those remain production work.

Graphify query was attempted: executable unavailable; no generated graph exists
in this worktree. Source/contract inspection replaces navigation only; blocking
Architecture Guard and governance still must pass. Attempt structural update
after changes and record the actual result in the integration review.

## Human Output review

Design Director scope: EXTEND, internal read-model semantics only. Human task:
inspect why a capability may warrant project attention. Meaning precedes data;
POTENTIAL/UNKNOWN, temporal state, independent dimensions and source excerpts
remain explicit. Missing commercial context stays unassessed; negative judgments
are retained. Data are fixture-only or existing admitted support, with derived
interpretation never promoted to canonical truth. No accepted visual surface
changes; Golden Master/browser/accessibility/visual acceptance are not applicable
to this backend slice. Future product consumption needs Human First validation.
