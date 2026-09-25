# P0-JEV-02 Pre-Merge Repair Record

**Status:** REPAIRED; awaiting CTO re-review
**Evidence class:** Experimental tooling and deterministic contract validation
**Live Jev calls:** None
**Canonical authority changes:** None

## Scientific contract

Experiment plans now identify an implemented experiment type, one independent
variable, controlled dimensions, a policy version, and predeclared evaluation
criteria. Validation rejects confounds for question wording, state ablation,
atomic decomposition, model comparison, and repeatability. Experiment types
that the runner cannot execute are rejected.

The claim wording variants hold state constant. Atomic relationship variants
hold the state, model, cases, repetition count, policy and execution budget
constant while changing the question strategy. State variants are selected
through a versioned registry; unknown identifiers fail closed. Per-record
variant ID, variant version and state fingerprint make the applied transform
inspectable.

## Usage and pricing boundary

Preflight records measured encoded request bytes. Token count and monetary
cost are UNKNOWN before provider usage is returned. A dated, versioned
TypeSafe Jev 1.13 policy prices provider-reported input tokens only.
INVOICE_COST remains UNKNOWN because the public price page is not billing
evidence.

## Outcome and composition boundary

Outcome evaluation uses criteria persisted in the experiment definition before
execution. Operational failures, critical regressions, incompatible output
semantics, insufficient answered cases, or absent effect thresholds produce
INCONCLUSIVE with reasons. SUPPORTED and NOT_SUPPORTED require a predeclared
minimum effect and sufficient metrics.

Atomic relationship decomposition retains raw REL.PRESENCE, REL.TYPE, REL.TIME
and REL.CONTRADICTION judgments. A versioned deterministic experimental
composer maps them to a compound-comparable result while preserving unresolved
and contradictory states. It has no canonical admission or AXIGLAND write
path.

## Immutable evidence

Result artifacts are create-only and content-digested. The reproducibility
manifest records the source revision, experiment version and digest, corpus and
grammar versions, exact question versions, state contract/compiler and variant
versions, state fingerprints, policy and adapter/SDK versions, requested and
provider-resolved model where available, cases, repetitions, and execution
mode. Predeclared criteria and their digest are retained with the immutable
result. Replay re-composes recorded judgments without calling a provider.

All changes are limited to the P0-JEV-02 experimental lab, its deterministic
tests, feature documentation, and subordinate research notes. No live
experiment, production runtime, dependency, migration, canonical write,
grammar promotion, or follow-on slice is authorized by this repair record.
