# ADR-0071 — Governed Measurement Registry and Instrument Compatibility

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-03, AO-04, AO-05, AO-06, AO-24, AO-25  
**Builds on:** ADR-0015

## Context

AXIGNAL already has operational metrics and multiple measurement-producing surfaces, but premium advisory cannot treat a metric name, model-selected KPI, dashboard field or third-party score as measurement authority.

ADR-0015 establishes that measurements are instrument-bound, versioned, sample-aware and not naively comparable across instrument drift. AO-24 materializes that doctrine as an executable private Admin/Advisory registry.

## Decision

A KPI or measure has authority for advisory/reporting only when a versioned MeasurementDefinition is explicitly registered.

A definition must declare:

- the question and decision it serves;
- deterministic formula or coding rule;
- unit;
- source family;
- instrument identity and version;
- subject/scope;
- default observation window;
- freshness threshold;
- minimum informative sample;
- uncertainty policy;
- compatibility key;
- interpretation limits;
- evaluation cases;
- effective time.

Measurement observations reference an exact registered definition version and must preserve subject, instrument/version, compatibility key, time window, sample, informative sample, uncertainty and source references.

The registry recognizes three observation states:

- MEASURED
- NOT_MEASURED
- INSUFFICIENT

NOT_MEASURED and INSUFFICIENT cannot carry a numeric/string metric value. They are never converted to zero.

A MEASURED observation below the registered minimum informative sample is rejected; the producer must record it as INSUFFICIENT instead.

Historical comparison is allowed only when measure identity, compatibility key, subject and instrument identity/version match. Instrument/version drift is INCOMPATIBLE unless a future explicitly validated bridge is introduced.

Freshness is evaluated at projection time. A stale historical measurement retains its original value and provenance but becomes unusable for current advisory decisions.

## Authority boundary

- Registry definitions: private authority over what a KPI means for Admin/advisory.
- Measurement producers: supply observations, never redefine metric meaning.
- Models/AXENT/Frontier providers: may synthesize only from registered measures; they do not choose arbitrary KPI authority.
- Command Center: remains an operational consumer/projection and is not promoted to universal metric authority.
- AO-25 advisory workbench: consumes AO-24 definitions/readouts.
- AXIGLAND/EvidenceAdmission: AO-24 has no canonical economic truth-write authority.

## Empty-registry posture

The runtime starts with an empty AO-24 registry.

This is deliberate. AXIGNAL does not seed convenient KPIs merely because they are common or already visible elsewhere. A measure becomes advisory authority only through an explicit governed registration.

## Persistence and audit

Definitions are immutable and sequentially versioned per measure identity.

Observations are append-only/replay-safe by observation identity.

Definition registration and observation ingestion require admin:advisory:write with STEP_UP assurance and emit Admin governance audit records under the ADVISORY target.

## Consequences

- Premium reports cannot silently switch formulas or instruments.
- Measurement drift cannot masquerade as business change.
- Missing pillars remain NOT_MEASURED/INSUFFICIENT.
- Sample size and uncertainty survive into advisory surfaces.
- Stale results remain historical evidence instead of being overwritten.
- AO-25 can operate over a typed, inspectable measurement authority rather than model-selected metrics.
