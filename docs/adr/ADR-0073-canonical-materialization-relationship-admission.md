# ADR-0073 — Canonical Materialization and Relationship Admission Boundary

**Status:** ACCEPTED
**Date:** 2026-10-03
**Scope:** AUD-02; FAXT; Organization economic profile; ObservedRelationship; subscriber OBSERVED projection
**Derives from:** MASTER §15.1-15.4, §16, §23, §56.2; Engineering Constitution VI, VIII, X, XIV; ADR-0072

## Context

After AUD-01, EvidenceAdmission decisions were proposition-bound, but canonical domain objects could still be constructed or rehydrated outside the verified factory path. ObservedRelationship accepted evidence IDs unrelated to the decision, and subscriber projection could promote an INFERRED canonical FAXT to an OBSERVED business signal.

Organization also mixed identity with business profile fields that could be supplied directly without canonical evidence.

## Decision

Canonical materialization is now enforced at the effective object boundary.

### FAXT

FAXT uses an init-disabled dataclass with a constructor that always rejects direct materialization. FAXT.create is the only supported materialization path and calls EvidenceAdmission.require_claim before a private materializer constructs the frozen value.

dataclasses.replace on an existing FAXT therefore cannot manufacture a new canonical value with altered epistemic state, ID, provenance, currentness or other fields.

### ObservedRelationship

ObservedRelationship likewise has no effective public constructor.

ObservedRelationship.create requires:
- non-empty relationship identity, source, target and type;
- distinct endpoints;
- a valid observed interval;
- Evidence whose observed_at falls inside that interval;
- proposition-bound AdmissionDecision for source_org + relationship_type + target_org + exact claim.

Evidence refs are derived from the admitted Evidence object rather than accepted as caller-supplied authority.

Verified deserialization/replay requires both exact Evidence and AdmissionDecision. Persisted evidence_refs must exactly equal the admitted evidence identity. Empty or unrelated references fail closed.

PotentialRelationship remains directly constructible because it is explicitly non-observed hypothesis state and does not claim canonical observed truth.

### Organization

Organization identity remains directly constructible: stable ID, canonical name, aliases, locations and discovery metadata do not by themselves create a business-truth assertion.

Economic profile fields — markets, capabilities, products, corporate links and their evidence refs — cannot be supplied through the ordinary constructor.

Organization.from_admitted_faxts is the governed profile materializer. It accepts only canonical FAXT values for the same Organization subject and only OBSERVED/CORROBORATED state. INFERRED or UNKNOWN state cannot be promoted into an observed Organization profile.

### Subscriber OBSERVED projection

When a canonical FAXT is used as OBSERVED business support, its epistemic_state must itself be OBSERVED or CORROBORATED. INFERRED/DECLARED/STALE epistemic classifications cannot be silently upgraded to OBSERVED by presentation.

This does not close the alternative observation_support_refs path. Claim-kind governance for direct observations is AUD-03.

## Replay

Accredited exact relationship replay remains supported through deserialize_relationship with exact Evidence + exact AdmissionDecision + matching persisted evidence_refs.

## Non-goals

AUD-02 does not define which observation kinds may independently support OBSERVED subscriber signals. It does not resolve narrative semantics, tenant reuse, currentness propagation or fiscal evidence. Those remain AUD-03 and later.

## Consequences

- Canonical factory rules are now effective rather than advisory.
- Direct construction and dataclasses.replace cannot create altered FAXT truth.
- Observed relationships cannot borrow an unrelated admission decision.
- Empty evidence references cannot materialize an observed relationship.
- Organization business profile cannot be injected without admitted canonical FAXTs.
- INFERRED FAXT cannot present as OBSERVED business truth.
- Existing valid exact replay remains deterministic.