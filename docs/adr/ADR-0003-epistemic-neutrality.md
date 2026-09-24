# ADR-0003: Epistemic Neutrality

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §5, §6, §23, §39, §46.4, §46.6, §46.7, §46.8, §46.12

## Context

Subscribers, targets, competitors and agencies all have incentives to influence
what AXIGNAL concludes. If their input can reach canonical state directly, the
map becomes purchasable and poisonable.

## Decision

`Users may direct AXIGNAL's attention, but never its conclusions.` Input defines
what AXIGNAL investigates, never what AXIGNAL believes. Subscription buys
observation, not influence. There is no `Edit company profile`. Corrections
enter only as reevaluation requests and are re-investigated independently.

## Consequences

- User/agency/subscriber signals are attention-only and never canonical.
- Hostile attention increases observation and improves the map instead of
  poisoning it.
- The map cannot be bought; observation can.

## Enforcement

- `EvidenceAdmission` rejects attention-only `SourceAuthority` values.
- `tests/contracts/test_evidence_admission.py` asserts this.
- Architecture Guard forbids sponsored/pay-to-rank ranking mutations.
