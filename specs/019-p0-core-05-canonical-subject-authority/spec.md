# P0-CORE-05 Canonical Subject / Entity Authority

**Status:** Reconciled; subject identity remains unresolved
**Mode:** `CANONICAL_SUBJECT_ENTITY_RECONCILIATION`
**Base:** `2775d196d6942537f46c2a52a0e6ecb573d1f5ad`
**Authority:** MASTER §§4.5, 15.2–15.4, 16, 17, 36, 50; Constitution I, IV,
VI–VIII, X; ADR-0003, ADR-0005, ADR-0009, ADR-0018–0021

## Problem

The canonical FAXT contract exposes `subject_id: str`. Subscriber Projection
must not infer an Organization, graph node, relationship, or cardinal field
from this string, the Golden Master, or a predicate. This slice determines
what AXIGNAL can currently claim about that field and whether an additional
contract is justified.

## Evidence and reconciliation

| Authority | Evidence | Result |
|---|---|---|
| MASTER §§4.5 and 15.2 | FAXT is evidence-backed and has conceptual fields `subject_id`, `predicate`, and `object_or_value`; §4.5 gives an Organization-like example but no exhaustive subject-kind rule. | A subject is the referent of a FAXT claim, but its entity class and identity plane are unspecified. An example is not a closed ontology. |
| MASTER §§15.3, 16, 36, 50 | Predicate examples span products/capabilities, legal identity, certification, corporate structure and relationships. Organization and Relationship are conceptual domain objects; §50 places domain ontology closure in a later milestone. | These sections do not establish which classes may be FAXT subjects or that every subject is an Organization. |
| Constitution I, IV, VI–VIII, X | MASTER is semantic authority; user input cannot write truth; writes require admission; FAXT/INXIGHT/PATHX and observed/potential remain distinct; UNKNOWN is not false; deterministic code owns truth mechanics. | Missing subject-kind authority must remain unknown; model output, fixtures, labels, or convenience cannot fill it. |
| ADR-0003, ADR-0005, ADR-0009 | Epistemic neutrality and separation of FAXT, INXIGHT, Relationship, PATHX and graph projection. | No generic entity framework or graph edge follows from the FAXT field. |
| ADR-0018–0021 | Organization is global; Xeed is private context; Xeed references a global Organization; XeedFaxtReference is explicit membership; authorized readers resolve only governed Organization/FAXT references. ADR-0021 explicitly leaves FAXT subject kind untyped. | OrganizationId and XeedId remain distinct; private membership does not identify the FAXT subject or expose relationships. |
| `domain/faxt/model.py`, `domain/identity.py` | FAXT field/factory type is `str`; identity types currently include OrganizationId, FaxtId, PrincipalId, TenantId and XeedId, but no subject type. | Current canonical representation is an opaque string. No semantic cast or deterministic resolver exists. |
| `domain/relationships/model.py`, `domain/pathx/model.py`, `domain/inxight/model.py` | Observed/Potential relationship endpoints and PATHX organization endpoints are strings; INXIGHT has a string `subject_scope`. | Those strings do not establish a shared identity plane with FAXT.subject_id. |
| Deterministic contracts | `test_faxt_subject_semantics_remain_unresolved_and_are_not_cast_to_organization`; Xeed/Organization identity and authorization contracts; observed/potential separation tests. | Existing tests preserve unknown subject semantics, global Organization identity, authorized context and epistemic separation. No implementation contract supports cross-type resolution. |

## Decisions

### FAXT subject

`FAXT.subject_id` is the opaque identifier string of the subject about which a
canonical FAXT claim is made. The subject's kind and identity authority are not
defined by the current MASTER or contracts. No exhaustive subject classes are
proven, and it cannot be proven that every FAXT subject is an Organization.
The minimum truthful representation remains the existing `str`; do not add a
subject-kind field, enum, registry, generic Entity, or resolver.

```text
FAXT_SUBJECT_CURRENT_REPRESENTATION=str
SUBJECT_KIND=UNKNOWN_UNSUPPORTED
SUBJECT_IDENTITY_AUTHORITY=UNKNOWN_UNSUPPORTED
SUBJECT_RESOLUTION=UNKNOWN_UNSUPPORTED
```

Raw string equality is not semantic identity. In particular,
`faxt.subject_id == str(organization.id)` does not authorize an Organization
cast, lookup, or relationship. A future change that reinterprets stored
subject strings requires a separately governed identity and migration decision.

### Object/value ambiguity

`object_or_value: str` does not say whether a value is a literal or a reference
to another canonical object. Resolving object-side identity or deriving
FAXT-based entity/relationship edges is out of scope and blocked until a
separate canonical contract resolves this ambiguity.

### Relationship boundary

MASTER §§15.3, 16 and 36 permit relationship-related claims while defining
canonical Organization-Relationship objects as their own domain concept;
ADR-0021 confirms that those objects exist independently of Xeed–FAXT
membership. `ObservedRelationship` requires EvidenceAdmission;
`PotentialRelationship` remains a separate unobserved possibility. Their
Organization endpoint fields do not resolve a FAXT subject. No deterministic
mapping from FAXT subject/predicate/object to a canonical Relationship is
defined, and this slice does not expose Relationships through an AuthorizedXeed
reader.

```text
RELATIONSHIP_READ_IMPLEMENTATION=OUT_OF_SCOPE
XEED_FAXT_REFERENCE != RELATIONSHIP
```

### Golden Master fields

No Golden Master label, fixture, node, edge, zone, geometry, or navigation
state establishes ontology. Organization `capabilities` and `markets` remain
direct Organization fields; no FAXT-to-cardinal mapping is established.
Signals, Activity, and semantic graph edges remain
`UNKNOWN_UNSUPPORTED` as projection inputs.

## Implementation case

**CASE C — doctrine does not define FAXT subject kind.** No runtime/domain
contract or ADR is added. The existing opaque representation and deterministic
unknown-subject contract are preserved. This spec records the evidence and
updates the HFX integration matrix without upgrading any unknown projection
field.

## Scope and invariants

No FAXT semantic migration, subject resolver, generic ontology, relationship
reader, Subscriber Projection, UI, persistence, database, AXENT, model/JEV, or
Golden Master change is authorized. Preserve:

- Organization and FAXT as `GLOBAL_WORLD`; Xeed as
  `PRIVATE_COGNITIVE_CONTEXT`.
- `Xeed != Organization`; `OrganizationId != XeedId != FaxtId`.
- `FAXT != INXIGHT`; `Relationship != PATHX`; `OBSERVED != POTENTIAL`.
- `CLAIM != WRITE`; canonical writes require EvidenceAdmission.
- `XeedFaxtReference` is private membership only, not relationship,
  provenance, relevance, ranking, discovery, evidence rights, or ownership.
- `UNKNOWN != FALSE`; `evidence_refs != provenance authority`.
- Golden Master source inventory and digest remain unchanged.

## HFX-01 readiness

`HFX_01_READY=NO`. At minimum, FAXT subject kind/identity resolution remains
unsupported; object-side literal/reference semantics block FAXT-derived graph
edges; AuthorizedXeed-scoped relationship access is not established; and
cardinal assignments for FAXTs (including Signals and Activity) remain
unsupported. CORE-05 passing does not authorize HFX-01.
