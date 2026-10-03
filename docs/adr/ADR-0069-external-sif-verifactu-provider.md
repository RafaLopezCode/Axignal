# ADR-0069 — External SIF / VERI*FACTU Provider Architecture

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-18, AO-20, AO-21, AO-22

## Context

AXIGNAL must operate invoices and fiscal evidence in Spain without silently becoming regulated invoicing software. The current official SIF/VERI*FACTU framework is governed principally by Real Decreto 1007/2023 and its technical development, including Orden HAC/1177/2024, as subsequently modified. The currently published adaptation deadlines are 2027-01-01 for article 3.1.a) taxpayers and 2027-07-01 for the remaining article 3.1 taxpayers.

Building an AXIGNAL-owned SIF would materially expand product scope and regulatory obligations: version-specific producer declaration, record generation, integrity/traceability/inalterability controls, XML/chain/hash mechanics, QR, AEAT remittance/authentication, event/retention requirements where applicable and continuing compliance maintenance.

## Decision

AXIGNAL selects **EXTERNAL_SIF_PROVIDER** as the only architecture authorized by AO-22.

AXIGNAL-owned SIF implementation is **not authorized**. Any future reversal requires a separate ADR and dedicated compliance project against the then-current official rules.

The fiscal provider is integrated through AO-18 and remains replaceable. AO-21 accounting-provider status does not imply SIF/VERI*FACTU status; the fiscal adapter must have its own integration definition and evidence.

No production invoice path may claim or imply VERI*FACTU/SIF compliance merely because a provider is configured.

## Mandatory evidence gate

Production live enablement and compliance wording require a same-version evidence set containing:

- provider responsible declaration;
- provider technical/adapter contract evidence;
- non-production integration/compliance test;
- explicit human approval under fiscal write authority.

Provider-version drift invalidates the complete evidence state until the new version is re-evidenced.

## Authority boundary

- External provider: regulated SIF mechanics for its declared product/version.
- AXIGNAL: private adapter metadata, provider/version evidence, operational status and references to AO-20/AO-21.
- Taxpayer: remains responsible for applicable tax obligations.
- AXENT/LLMs: no legal/tax authority.
- AXIGLAND: no fiscal compliance authority; Admin fiscal state cannot be admitted merely because it exists.

## Consequences

- AXIGNAL avoids becoming a proprietary regulated SIF under AO-22.
- Fiscal integration can be replaced without rewriting AO-20/AO-21.
- Missing evidence produces NO_PROVIDER or EVIDENCE_INCOMPLETE, never a positive compliance claim.
- Live fiscal enablement is fail-closed.
- Official rules/deadlines are versioned and must be revalidated before production enablement.
