# ADR-0064: Evidence-Backed Weekly Brief Pipeline

## Status

Accepted for AO-16.

## Context

AO-15 established a lawful request, coverage review and newsletter-consent boundary. It deliberately stopped before issue composition and delivery. AO-16 must now demonstrate AXIGNAL through a free weekly observation brief without turning acquisition content into a second truth system, a generic AI-content engine or a free Xeed entitlement.

The brief needs to survive three failure modes:

1. padding an issue to a marketing quota when evidence is weak;
2. allowing model wording to become the source of an observed development;
3. recording a send after consent, source currentness or provider readiness has ceased to be valid.

## Decision

- AO-16 is a private acquisition projection over governed Observation Memory. It does not write AXIGLAND and does not call EvidenceAdmission.
- A material item is eligible only when it references an existing observation for the AO-15 accepted subject, survives deterministic content deduplication and evaluates to CURRENT under a versioned temporal-currentness policy.
- An issue contains zero to three material items. Zero items is an explicit NO_MATERIAL_CHANGE issue; no filler is generated.
- Every material item preserves observation id, source reference, observation date, content fingerprint, currentness condition, deterministic observed-field summary, why_may_matter, and at least one explicit UNKNOWN statement.
- The observed-field summary is deterministic and model-independent. Optional model drafting may change only why_may_matter for an already-selected observation. The drafting contract has no field capable of changing source, date, observed fields, currentness or adding a new observation.
- Pilot delivery requires an AO-01 STEP_UP Admin with admin:acquisition:write to approve the exact immutable issue snapshot.
- Immediately before provider work, delivery replays AO-15 request state. Withdrawn consent, suppression, insufficient coverage or any other loss of delivery_eligible fails closed before the provider is called.
- External email work must pass AO-18 require_connection with the runtime environment, resolvable secret reference, fresh healthy integration state and email:send scope. No ungoverned provider bypass is permitted.
- Issue snapshots, approvals, deliveries and corrections are durable append-only records. Replaying the same identity with equal content is idempotent; reusing an identity with different content is a conflict.
- A correction appends explanation to delivery history and never rewrites the original sent issue.
- Production may deploy the pipeline while actual sending remains dormant. A real delivery is authorized only when AO-15 collection is legally activated and an AO-18 governed email integration/provider adapter is configured and healthy.

## Consequences

AXIGNAL can pilot a reconstructible weekly observation brief that shows real governed evidence without manufacturing activity. The free brief remains commercially useful but epistemically subordinate to Observation Memory and the canonical truth mechanisms.

The pipeline is provider-neutral. A future email adapter or drafting model can be replaced without changing issue evidence identity, eligibility, approval or correction semantics.

## Non-goals

AO-16 does not:

- create a free Xeed or AXENT entitlement;
- infer materiality automatically from provider confidence;
- turn marketing engagement into economic truth;
- admit observations as FAXTs;
- create a public send endpoint;
- authorize production collection before AO-15 legal/privacy activation;
- register or provision an email provider credential.
