# ADR-0072 — Proposition-Bound Evidence Admission

**Status:** ACCEPTED
**Date:** 2026-10-03
**Scope:** AUD-01; domain/evidence; domain/faxt; legacy semantic germination
**Derives from:** MASTER §15.1-15.3, §23, §56.2, §56.14; Engineering Constitution VI, VIII, X, XIV

## Context

The 2026-10-03 adversarial audit demonstrated that a valid admission decision could be reused with the same evidence identity after changing evidence content/authority and could then authorize a different subject/predicate/value. The same legacy path could turn an erroneous semantic SUPPORTED verdict into a canonical FAXT.

The defect was structural: admission authenticated an evidence ID and an internal token, but did not authenticate the exact evidence content and proposition being written.

## Decision

Canonical FAXT creation requires a proposition-bound AdmissionDecision produced from an immutable AdmissionRequest.

The request binds:
- the complete Evidence value through a deterministic SHA-256 digest;
- evidence identity;
- source authority;
- observed time;
- subject;
- predicate;
- object/value;
- exact extracted claim/proposition;
- deterministic predicate-authority policy.

FAXT.create reconstructs the expected request from its inputs and calls EvidenceAdmission.require_claim. A decision admitted for another evidence value, subject, predicate, object/value, claim or policy cannot be reused.

Evidence-only admission remains temporarily available for non-FAXT boundaries that are explicitly scheduled for AUD-02 hardening. An evidence-only decision cannot authorize FAXT.create.

## Source-authority policy

MASTER §15.3 establishes that source authority is predicate-specific. AXIGNAL therefore does not treat every canonical source class as valid for every predicate.

The initial deterministic policy supports only currently materialized families with explicit doctrinal mapping:
- official web -> declared product/capability predicates;
- registry -> legal identity predicates;
- certifier -> certification/standard predicates;
- corporate document -> structure/results predicates;
- counterparty -> supplier/customer/relationship predicates.

Unknown predicates fail closed. Specialist-source predicate policy remains unmaterialized until a specific predicate family is explicitly governed.

Attention-only USER/AGENCY/SUBSCRIBER signals never establish canonical truth.

## Exact claim posture

For this admission version, claim_proposition must exactly match the normalized Evidence.extracted_claim.

This intentionally rejects semantic paraphrase at the admission boundary. A model or judge may propose/interpret a paraphrase upstream, but canonical admission does not grant that paraphrase independent authority.

If future normalization requires a richer proposition representation, it must be a separately versioned deterministic contract rather than loosening this comparison.

## Temporal binding

A canonical FAXT cannot override observed_at with a different timestamp from the admitted Evidence.

Temporal reinterpretation belongs in currentness/validity layers; it must not mutate the observation time that was admitted.

## Anti-forgery posture

The internal canonical token is init=False. Hand-built AdmissionDecision values are non-canonical, and dataclasses.replace() of a canonical decision loses the private token automatically.

This is a language-level integrity guard for normal application code, not a claim that Python object internals form a hostile-process security boundary.

## Legacy semantic germination

The legacy isolated germination flow now:
1. obtains semantic judgment;
2. constructs an exact AdmissionRequest;
3. independently calls EvidenceAdmission.admit_claim;
4. writes FAXT only if proposition-bound admission succeeds.

A SUPPORTED model/judge result is not sufficient. If the extracted evidence claim contradicts/differs from the proposed claim, the evidence admission rejects it and no FAXT is written.

## Non-goals

AUD-01 does not claim to repair:
- direct construction/rehydration of canonical domain types;
- relationship admission binding;
- OBSERVED projection support policy;
- narrative semantic verification;
- tenant/private reuse;
- temporal currentness propagation.

Those remain AUD-02 and later remediation tasks.

## Consequences

- CLAIM != WRITE is enforced at the exact FAXT proposition boundary.
- Same evidence ID with changed content cannot reuse a prior decision.
- Subject/predicate/value mutation cannot reuse a prior decision.
- Unknown source authority and unknown predicate policy fail closed.
- Evidence-only admission cannot authorize FAXT.
- Model verdicts remain proposals, not truth authority.
- Valid exact replay remains deterministic.