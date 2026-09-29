# ADR-0023: XEED Is the Planted Observation Seed; XIGNAL Is an Emergent Economic Signal

- **Status:** Accepted
- **Date:** 2026-09-29
- **Authority:** MASTER §§4.4/4.4A, 7, 26, 27, 33; CTO product decision
- **Supersedes:** ADR-0004 terminology and its `ObservationSeed = XIGNAL` mapping
- **Scope:** customer activation semantics, Brain germination, Xignal meaning, pricing unit and Landing language

## Context

AXIGNAL had accumulated two incompatible vocabularies.

Older MASTER sections and ADR-0004 used `XIGNAL` as the customer's persistent
observation allocation. Newer Brain, subscriber and communication architecture
used the seed/germination model: the customer plants a `Xeed`, the Brain
germinates it, and a Living Xeed persists as the customer's observation context.

The product decision resolves the conflict in favor of the seed/germination
model.

## Decision

- **XEED** is the seed planted by the customer. It is the persistent customer
  observation objective/context around one canonical Organization.
- Planting a Xeed authorizes AXIGNAL's Brain to observe, investigate, verify,
  revisit and cultivate that organization's observable economic environment.
- A Xeed does not create or own the canonical Organization and does not grant
  canonical write authority.
- **XIGNAL** is an economic signal that emerges from Brain observation and
  research during germination/evolution of one or more Xeeds.
- One Xeed may produce many Xignals.
- Xignals may indicate activity, change, representation, relationships,
  contradictions, anomalies, demand, supply or other observable economic
  phenomena worth investigating.
- `XIGNAL != XEED`.
- `XIGNAL != FAXT`, `XIGNAL != INXIGHT`, `XIGNAL != RELATIONSHIP`,
  and `XIGNAL != PATHX`.
- `XIGNAL != CANONICAL WRITE`. A Xignal can direct attention or propose
  investigation, but canonical AXIGLAND mutation still requires governed
  evidence admission and the existing truth mechanisms.
- Public, reusable knowledge learned while germinating one Xeed may benefit
  other Xeeds subject to authorization, provenance and public/private
  boundaries.

## Commercial decision

Current pricing hypothesis is:

- EUR 9.95/month including one Xeed.
- EUR 4.95/month per additional Xeed.

Xignals are not individually billable. Organizations discovered around a Xeed
are not automatically billable Xeeds.

For agencies, a client/competitor/target that merits persistent observation may
have its own Xeed. Each Xeed may yield many Xignals.

## Agency / DRI consequence

SEO, GEO, AEO and AIO agencies are a first-class use case. AXIGNAL independently
observes how search engines, assistants, generative systems and public surfaces
represent a client and how that representation changes over time.

This does not authorize AXIGNAL to execute SEO/GEO/AEO/AIO work or to infer
causation from a simple before/after comparison.

## Consequences

- Landing CTA language uses **Plant a Xeed / Planta tu Xeed**.
- Product navigation may expose the active/living Xeed as the persistent user
  context.
- The legacy `domain.xignal.ObservationSeed` implementation is removed. Xeed
  lifecycle/work state now lives as `domain.xeed.XeedGerminationState`; the
  concrete Xignal payload remains intentionally deferred until its evidence and
  provenance contract is specified.
- Existing Xeed authorization/tenant isolation remains valid and is not weakened
  by this terminology correction.
- AXIGLAND remains one canonical world.
- EvidenceAdmission remains the canonical write gate.

## Migration guardrails

The implementation migration MUST NOT:

- rename symbols mechanically while preserving the old semantics;
- make Xignals tenant-owned canonical truth;
- equate a Xignal with a FAXT or other admitted knowledge object;
- make the customer able to author canonical Xignals directly;
- weaken Xeed authorization or public/private separation;
- change tests merely to force green without repairing the underlying semantic
  contract.

Historical research artifacts may retain the old term only when explicitly
marked as historical/superseded evidence. Current product, architecture and
implementation surfaces MUST use the reconciled semantics.
