# P0-CORE-01 Data Model

This is the minimum identity and authorization model. It adds no persistence.

## Identity values

- OrganizationId: global AXIGLAND world identity.
- TenantId: private isolation/ownership identity.
- PrincipalId: canonical identity of an actor authenticated by a future
  outer adapter.
- XeedId: private observation-context identity.

They use the repository's string representation through distinct static types.
Labels and organization names do not participate in identity.

## Records

    Principal(id: PrincipalId)
    Tenant(id: TenantId)
    PrincipalTenantMembership(principal_id: PrincipalId, tenant_id: TenantId)
    Xeed(id: XeedId, tenant_id: TenantId, organization_id: OrganizationId,
         label: optional presentation string)
    TrustedRequestContext(principal_id: PrincipalId, tenant_id: TenantId)
    AuthorizedXeed(xeed: Xeed)

## Invariants

1. One Xeed belongs to exactly one Tenant.
2. One Xeed references exactly one existing Organization identity; it does not
   copy Organization truth.
3. Multiple Xeeds owned by different Tenants may reference the same
   Organization.
4. `XeedGerminationState` is keyed by one Xeed and carries lifecycle/work state only; it does not replace Xeed identity or grant knowledge membership.
5. A TrustedRequestContext is accepted only from a future trusted outer
   authentication boundary. It does not authenticate its Principal.
6. The application reader verifies Principal identity and membership before
   Xeed resolution, then checks the Xeed's Tenant before returning
   AuthorizedXeed.
7. No knowledge object is read or bound to a Xeed in this slice.

## Result semantics

Internal failures distinguish missing context, unknown Principal, denied
Tenant membership, unknown Xeed and cross-Tenant Xeed access. A future private
external adapter maps unknown Xeed and cross-Tenant denial to the same
non-enumerating not-found response.
