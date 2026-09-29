# P0 Identity Authority Model

**Base:** `7d30966a68168a372ce25ab48d757c6887883adf`
**Evidence class:** accepted doctrine and current domain/application contracts. Test/development readers are not production authority.

## Authority matrix

| Concept | Meaning / owner | Current contract and lifecycle | Production status |
|---|---|---|---|
| Principal | Internal AXIGNAL actor identity; owned by AXIGNAL | `PrincipalId`, `Principal(id)`. External mapping, provisioning, suspension, profile, and deletion lifecycle absent. | Domain value/model contract exists; no authenticated boundary or production store. |
| Authenticated identity | Provider-scoped credential identity (`issuer`, `subject`); authentication provider owns credential proof. AXIGNAL adapter maps it to PrincipalId. | Provider metadata is not canonical identity. Multiple identities may map to one Principal through verified linking; email equality alone is insufficient. | Logical boundary only; no provider or mapping store. |
| Tenant | Private isolation and Xeed-ownership boundary; owned by AXIGNAL | `TenantId`, `Tenant(id)`. Not a Workspace, payer, legal customer, or Organization. Creation, display identity, membership mutation, and deletion lifecycle absent. | Domain contract exists; no production store/writer. |
| PrincipalTenantMembership | Binary relation authorizing current Principal-in-Tenant access | Pair `(principal_id, tenant_id)`. No roles, invitations, timestamps, billing, or membership lifecycle contract. | Domain model and test/dev reader; no production store/writer. |
| TrustedRequestContext | Trusted Principal and selected Tenant supplied by a future outer boundary | Does not authenticate either ID; raw selected Tenant is not membership proof. | Application value contract only. |
| AuthorizedXeed | Application proof wrapper returned after Principal, membership, Xeed, and Tenant checks | Current read order: context → Principal → membership → Xeed → Tenant match → AuthorizedXeed. | Application contract and deterministic tests; no production auth/persistence. |
| Xeed | Tenant-owned private observation context | Has `XeedId`, `TenantId`, exactly one `OrganizationId`, optional presentation label. References canonical Organization; no private copy or edit right. | Domain model/read contract; no production persistence/writer. |
| Organization | Canonical global economic entity | Shared across observer contexts; no Principal/Tenant/payer/subscriber ownership fields. | AXIGLAND domain authority; no Settings edit path. |
| PrincipalPreferences | Minimal owner concept for durable user-level presentation preferences, when persistence is authorized | Owned by Principal, independent of Tenant. UI locale may be stored here; this is not a profile aggregate or company data. | Product ownership resolved; no model, schema, store, or writer. |
| Payer / subscriber identity | Commercial identity used for payment/entitlement ownership | Not equated with Principal, Tenant, Organization, or Xeed. | Not modeled; product decision required. |
| Entitlement | AXIGNAL interpretation of commercial state as capability/capacity for an authorized consumption scope | Future provider-independent port; Tenant may be the consumption scope, never thereby the payer. Unknown remains unknown and grants no new paid capacity. | Logical boundary only; no billing adapter or persistence. |

## Trust and access boundaries

Authentication provider → verified issuer-scoped identity → AXIGNAL mapping → PrincipalId. Authentication alone does not authorize access. A trusted application context is constructed only after verification; AXIGNAL then rechecks membership and the Xeed's Tenant ownership using its own contracts. Provider roles, organizations, email domains, and billing claims do not replace that check.

Canonical Organization truth stays observer-independent. Private deletion or account lifecycle cannot delete admitted AXIGLAND truth. XIGNAL remains an allocation of observation, not a claim or ownership right.

## Cardinality and lifecycle references

Product cardinality decisions and lifecycle gaps are recorded in `cardinality-model.v1.md`. They remain unknown unless a current contract or explicit product requirement resolves them.
