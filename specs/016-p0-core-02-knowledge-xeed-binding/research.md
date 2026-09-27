# P0-CORE-02 Research and Reconciliation

## Canonical inputs

- CTO P0-CORE-02 decision: exact meaning and negative semantics of a reference;
  FAXT only; independent explicit reference per Xeed; AuthorizedXeed required;
  test/dev in-memory authority allowed; production writer/persistence absent.
- P0-CORE-01 / ADR-0018: global Organization, Tenant-owned Xeeds, membership
  before AuthorizedXeed, no knowledge binding in that slice.
- MASTER FAXT doctrine: global evidence-backed canonical knowledge with
  epistemic/currentness and evidence references.
- Existing code: FAXT has stable string identity and evidence refs; Xeed has
  typed identity, Tenant owner and Organization subject; no production
  repository or knowledge reader existed.

## Reconciled decision

The CTO decision resolves the previously ambiguous question only for FAXT.
The implementation uses a private contextual pair and does not generalize to
heterogeneous knowledge. A reader requires the capability from P0-CORE-01 and
tests the Xeed-specific pair before touching the global FAXT catalog.

## Evidence boundaries

The implementation proves deterministic domain/application behavior only.
It does not prove persistence, production writes, source rights, provenance,
binding time/history, or lifecycle behavior for changed/revoked source objects.
