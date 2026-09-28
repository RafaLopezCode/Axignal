# ADR-0021: Authorized Xeed Read of Its Global Organization Context

- **Status:** Accepted and implemented as a domain/application contract; production persistence remains unimplemented
- **Date:** 2026-09-28
- **Authority:** CTO P0-CORE-04; MASTER §§3, 6.1, 7.3, 15.2, 36; Constitution I, IV, VI; ADR-0018–0020
- **Scope:** resolving the canonical Organization referenced by one authorized Xeed

## Context

`Xeed.organization_id` is an `OrganizationId` reference. `Organization` is a
global AXIGLAND entity with its own `OrganizationId` and `canonical_name`;
neither field is copied into private Xeed state. The existing authorized-Xeed
boundary proves private context access, but no application read contract
resolves the referenced global Organization for that context.

The MASTER describes FAXT with a generic `subject_id`; it does not establish
that every canonical FAXT subject is an Organization. The Python model also
keeps `FAXT.subject_id` as `str`. This decision deliberately does not type or
reinterpret that field.

## Decision

- An Organization read through a private Xeed requires an `AuthorizedXeed`.
  The reader obtains the OrganizationId only from that authorized value; a raw
  XeedId, OrganizationId, TenantId or caller-provided Organization cannot
  substitute for it.
- The reader resolves the referenced Organization through a canonical global
  Organization reader and returns the original object with its AuthorizedXeed
  context. It does not copy Organization truth into Xeed or create a
  tenant-owned Organization.
- A missing Organization, invalid canonical result or identity mismatch fails
  closed. No partial or substituted result is returned.
- Multiple authorized Xeeds, including Xeeds in different Tenants, may
  reference and resolve the same global Organization. This preserves one
  world identity and is not cross-Tenant private-data sharing.
- The contract is an application boundary backed by deterministic test/dev
  readers. It does not implement authentication, persistence or a production
  Organization repository.
- The domain contains canonical `ObservedRelationship` and
  `PotentialRelationship` concepts between Organizations. Observed creation
  requires EvidenceAdmission; potential remains distinct. This does not make
  `XeedFaxtReference` a Relationship, connect a FAXT subject to an Organization,
  or provide an AuthorizedXeed-scoped Relationship reader.
- Organization `capabilities` and `markets` are direct canonical fields.
  They do not classify FAXTs or establish the Golden Master's Signals or
  Activity cardinal fields. Those assignments remain unsupported.

## Alternatives considered

- **Accept a raw XeedId or OrganizationId:** rejected; identifiers alone do not
  prove the private context authorization established by ADR-0018.
- **Copy canonical name or Organization fields into Xeed:** rejected; Xeed
  references a global Organization and does not own its truth.
- **Cast every FAXT subject to OrganizationId:** rejected; neither MASTER nor
  current contract proves that all FAXT subjects are Organizations.
- **Treat contextual FAXT membership or visual adjacency as a relationship:**
  rejected; the reference expresses private context membership only.
- **Add production persistence or a relationship collection reader:**
  rejected; neither is needed to establish this contract and neither is
  authorized by this slice.

## Tradeoffs

The boundary permits a consumer with an already-authorized Xeed to resolve its
global Organization context, while leaving general FAXT subject identity
unresolved. Separate relationship access and FAXT-to-cardinal mapping are still
required before a populated Golden-Master graph can claim those semantics.

## Consequences

- `Organization.canonical_name` is available through the AuthorizedXeed-only
  application contract, with no production storage claim.
- `FAXT.subject_id` remains opaque `str`; `SUBJECT_KIND=UNKNOWN_UNSUPPORTED`.
- Global Organization relationships have canonical domain authority, but this
  reader does not expose them through Xeed membership.
- Golden Master cardinal-zone assignments for FAXTs remain
  `UNKNOWN_UNSUPPORTED`; `capabilities` and `markets` are only direct
  Organization fields.
- P0-HFX-01 readiness must be decided against these remaining boundaries, not
  inferred from this contract's tests or gates.
