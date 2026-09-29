# Identity Cardinality and Lifecycle Matrix

Status values: **SUPPORTED** means an existing contract or explicit product requirement supports the statement; **DEFERRED** means a product decision is still required; **UNKNOWN** is not false.

| Relationship / event | Current evidence-backed authority | Status and boundary |
|---|---|---|
| Principal ↔ external identities | Provider-scoped issuer + subject maps through an AXIGNAL adapter. Verified provider-supported linking may attach multiple methods to one Principal. | Multiple identities per Principal are permitted only after verified control; storage and provider cardinality remain unimplemented. Email-string equality never merges Principals. |
| Principal ↔ Tenant | `PrincipalTenantMembership` is a pair checked before a Xeed read. | Membership is required for the pair; product-wide maximum/guaranteed cardinality is DEFERRED. |
| Tenant → Xeed | Every Xeed has one Tenant owner; a Tenant may own multiple Xeeds. | SUPPORTED by ADR-0018 and the Xeed domain model. |
| Xeed → Organization | Each Xeed references one `OrganizationId`; different Tenants may reference the same global Organization through separate Xeeds. | SUPPORTED by ADR-0018/0021; reference is not ownership or cross-Tenant data sharing. |
| Principal → preferences | MASTER places preferences conceptually with User, separate from Organization. A durable human-level preference is Principal-owned, independent of Tenant. | Ownership for explicit UI-locale preference is resolved; persistence and additional fields remain deferred. |
| Principal → profile | No Principal profile schema/store exists. | No broad profile aggregate or editable business profile is authorized. Display name/avatar policy is deferred. |
| Tenant ↔ payer/subscriber | No canonical payer/subscriber object or mapping exists. | DEFERRED. Tenant is not presumed to be payer or legal customer. |
| Tenant → entitlement consumption | A governed consumption scope can be checked by a provider-independent AXIGNAL entitlement boundary. | Tenant may be that scope; this does not define payer identity, billing cardinality, or subscription lifecycle. |
| Payer → Tenant / Xeed / Principal | No approved mapping exists. | DEFERRED; do not infer one-to-one relationships. |
| Xeed capacity → Tenant / Principal / payer | MASTER pricing is per persistent Xeed. Xignals are emergent observation signals and are not billable capacity. | Consumption/payer cardinality remains DEFERRED pending commercial authority. |
| Multiple observers → Organization | MASTER §§6.2/7.3 and ADR-0001 keep one canonical Organization observed by many. | SUPPORTED; no per-subscriber Organization copies, ownership, or edit rights. |
| Principal leaves Tenant | The current membership check denies subsequent reads after authoritative membership change. | Immediate access boundary SUPPORTED; writer, last-member, Xeed transfer, history, and retention behavior deferred. |
| Principal/Tenant/Xeed/subscription deletion | Private lifecycle is distinct from canonical knowledge lifecycle. | Deletion policies deferred; private deletion must not erase independently admitted AXIGLAND knowledge. |
| Entitlement is unknown | UNKNOWN must not become FALSE. | Unknown status remains explicit and cannot grant additional paid capacity; do not present it as a confirmed cancellation. |

## Explicit non-aggregates

`Account`, `Subscriber`, and `Workspace` are not created by naming convention. Add one only after a product decision establishes a distinct identity, lifecycle, cardinality, and authority that cannot be represented by the existing boundaries.
