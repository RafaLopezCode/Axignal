# EB-07 — Opportunity & Continuous Observation

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER → Constitution → ADR-0012/0013 → EB-04/EB-06 contracts → Economic Brain Execution Roadmap
**Roadmap slice:** EB-07

## Purpose

Turn EB-04 economic reasoning into an investigable, explainable opportunity projection
and persist ResearchValue-authorized observation work so identical work is shared
rather than executed once per Observation Focus.

## Authorized behavior

- Derive an `EconomicOpportunity` from an EB-04 `EconomicReasoningResult`.
- Preserve POTENTIAL/UNKNOWN, exact state fingerprint, temporal evaluation time,
  Explainable Basis, reason codes and explicit missing commercial context.
- Never promote an opportunity to OBSERVED, FAXT, Relationship, customer or lead.
- Do not materialize a domain `INXIGHT` unless its existing canonical-support
  contract is satisfied; this slice keeps non-canonical opportunity reasoning in application.
- Convert only Prime work already authorized as `ADAPTIVE_RESEARCH` by
  ResearchValue into durable shared observation intents.
- Deduplicate identical governed intents across requesters using a deterministic
  work key that includes subject, state fingerprint, dimension, missing information
  and research-policy provenance.
- Persist requester provenance separately so shared compute never becomes shared authority.
- Use a durable lease with expiry and fencing. One live intent can have at most one
  valid execution lease; expired leases can be reclaimed and stale tokens cannot complete work.
- A changed state fingerprint creates a new work identity while prior work/history remains.

## Invariants

- OPPORTUNITY = POTENTIAL or UNKNOWN, never OBSERVED.
- OPPORTUNITY != FAXT.
- OPPORTUNITY != CUSTOMER / LEAD / RELATIONSHIP.
- REQUESTER ATTENTION != TRUTH AUTHORITY.
- SHARED WORK != DOUBLE COUNTED WORK.
- RESEARCH VALUE GATE precedes durable work.
- STATE CHANGE may create new work; it never overwrites previous work history.
- No generic workflow/scheduler framework is introduced.

## Exit criteria

- One aligned EB-04 result becomes an explainable POTENTIAL opportunity with explicit missing context.
- UNKNOWN reasoning remains UNKNOWN.
- Only ADAPTIVE_RESEARCH Prime items become durable observation work.
- Two requesters of the same governed intent share one work row.
- Durable lease/fencing prevents concurrent double execution and stale completion.
- Changed state produces a new work identity while preserving the old one.
- Focused and repository-wide deterministic gates are green.
