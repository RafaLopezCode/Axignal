# P0-CORE-02 Data Model

## Implemented domain object

`XeedFaxtReference` is an immutable value with:

| Field | Type | Authority |
| --- | --- | --- |
| `xeed_id` | `XeedId` | Private context identity established by P0-CORE-01 |
| `faxt_id` | `FaxtId` | Global canonical FAXT identity |

The pair means only that the FAXT was explicitly admitted into the Xeed's
private cognitive context. It is not an owner, truth, provenance, relevance,
importance, discovery, derivation, rights grant, or epistemic-state object.

The reference copies no FAXT fields, evidence references, epistemic state,
currentness, source identity, original evidence content or timestamps.
Reference temporal semantics and lifecycle history are not established.

## Application read result

`AuthorizedXeedFaxt` wraps the P0-CORE-01 `AuthorizedXeed`, the explicit
reference and the original global `FAXT`. It is emitted only after checking
the reference, then resolving the FAXT. It is a contextual release wrapper,
not a second FAXT or a canonical truth owner.

## Test/dev-only authority

The in-memory fixture stores global FAXT values by `FaxtId` separately from
references by `(XeedId, FaxtId)`. It has no production adapter, writer policy,
database or persistence guarantee.

## Not represented

Evidence, Observation, Relationship, INXIGHT, PATHX and other types have no
direct reference model here. Client, Workspace, source-rights authorization,
provenance chains, temporal event history and revocation lifecycle are not
represented.
