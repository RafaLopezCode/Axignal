# ADR-0074 — Claim-Kind Governed OBSERVED Projection

**Status:** ACCEPTED
**Date:** 2026-10-03
**Scope:** AUD-03; subscriber projection; direct observation support
**Derives from:** MASTER §15, §54, §56.19; Engineering Constitution VI, VIII, X, XIV; ADR-0031; ADR-0072; ADR-0073

## Context

After AUD-01 and AUD-02, canonical FAXT materialization was governed, but subscriber projection still allowed any observation_support_ref present in a supporting BasisDatum to authorize an OBSERVED Xignal.

This could turn an observation of a public page or search surface into an apparently observed business truth such as supply, capability or relationship.

## Decision

Direct observations are governed by phenomenon kind, not provider identity and not by bare observation ID membership in an ExplainableBasis.

project_explainable_xignal accepts direct observation support only through a GovernedObservationSupportResolver. The resolver returns an ObservationSupport contract containing:

- observation identity;
- subject identity;
- observed phenomenon kind;
- instrument reference and version;
- bounded scope reference;
- provenance reference;
- source reference;
- observed time;
- currentness.

## Initial policy

The initial policy is intentionally narrow:

- XignalKind.REPRESENTATION may be OBSERVED from ObservationPhenomenon.PUBLIC_REPRESENTATION.
- Economic business kinds such as SUPPLY, DEMAND and RELATIONSHIP require canonical support; direct public-surface observation is not authoritative for those truths.

New direct-observation phenomena require an explicit policy addition. Provider brands are never sufficient authority.

## Validation

For direct observation support, projection requires:

- governed resolver present;
- every requested observation ID resolves;
- phenomenon permitted for the requested XignalKind;
- exact subject match;
- CURRENT support;
- source_ref equal to the supporting BasisDatum;
- observed_at equal to the supporting BasisDatum.

Instrument/version, scope and provenance are mandatory fields of the support contract even when they are not rendered directly.

## Runtime integration

FR-30 first proof now builds ObservationSupport from the actual governed SourceObservation: sensor instrument_ref, instrument version, observation slot/scope, raw observation provenance, final source URI, retrieval time and currentness.

The valid condition-bound public homepage REPRESENTATION remains OBSERVED. It remains non-canonical truth.

## Non-goals

AUD-03 does not verify narrative text against stored extraction content, resolve relationship/PATHX references, or apply tenant/private reuse authority. Those are AUD-04 and later.

## Consequences

- A supporting observation ID alone cannot authorize OBSERVED output.
- Public representation observation cannot silently become supply/capability/relationship truth.
- Direct representation observations remain usable without forcing them into FAXT.
- Missing, stale, cross-subject or unresolved direct support fails closed.
- The policy is semantic and instrument/scope aware, not provider-whitelist based.