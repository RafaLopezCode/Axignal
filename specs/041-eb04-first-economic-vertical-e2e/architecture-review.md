# EB-04 architecture review

## Decision

EB-04 is a composition slice, not a new subsystem.

The implementation deliberately reuses:

- EB-01 execution budget/reservation controller;
- EB-02 identity binding, representation and exact spans;
- EB-03 source registry and reuse authority;
- existing semantic extraction contracts;
- existing first_vertical TypedJudgmentVector reasoning;
- existing EvidenceAdmission and FAXT creation boundary;
- existing EconomicHumanOutput compiler.

## New composition boundary

`first_vertical_e2e.py` is the reference composition root for this milestone. It does not own truth or provider policy.

`governed_dispatch.py` is a reusable execution-governance adapter layer for existing ports. It performs only reservation, elapsed-time measurement, cost/usage reconciliation and attempt recording.

## Authority boundaries

- Source Registry authorizes observation/reuse metadata, not truth.
- Semantic extractor proposes grounded candidates, not FAXT.
- Identity binding binds a mention to a canonical identity, but is not canonical truth.
- EvidenceAdmission alone authorizes the capability FAXT.
- Structured evaluator provides narrow semantic judgments, not policy/write authority.
- Python deterministic composition determines POTENTIAL/UNKNOWN attention state.
- Economic Human Output is presentation over the evaluated snapshot, not a second semantic authority.

## Composition-discovered EB-01 correction

A resource-specific limit at its exact maximum must not block work that consumes zero of that resource. Example: after 2/2 source acquisitions, semantic extraction with `sources=0` is allowed, while a third source is rejected before dispatch.

Global constraints remain global:

- elapsed deadline;
- exhausted monetary budget;
- configured fail-closed UNKNOWN cost;
- no-progress stop.

## Explicit non-authority

ECONOMIC_CANDIDATE != RELATIONSHIP  
POTENTIAL != OBSERVED  
WARRANTED_ATTENTION != SALE PROBABILITY  
HUMAN OUTPUT != CANONICAL WRITE  
REPLAYABLE != TRUE

## Deferred

Live JEV/Luna usage, provider economics benchmarking, continuous scheduling, shared monitoring and subscriber-visible product wiring remain later slices.
