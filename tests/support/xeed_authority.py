"""In-memory Xeed authority used by tests only; never production persistence."""

from __future__ import annotations

from application.xeed_access.reader import (
    MembershipReader,
    PrincipalReader,
    XeedReader,
)
from domain.identity import PrincipalId, TenantId, XeedId
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed


class InMemoryXeedAuthority(PrincipalReader, MembershipReader, XeedReader):
    """A deterministic test/dev authority with duplicate-ID protection."""

    def __init__(self) -> None:
        self.principals: dict[PrincipalId, Principal] = {}
        self.tenants: dict[TenantId, Tenant] = {}
        self.memberships: set[PrincipalTenantMembership] = set()
        self.xeeds: dict[XeedId, Xeed] = {}
        self.calls: list[str] = []

    def add_principal(self, principal: Principal) -> None:
        self.principals[principal.id] = principal

    def add_tenant(self, tenant: Tenant) -> None:
        self.tenants[tenant.id] = tenant

    def add_membership(self, membership: PrincipalTenantMembership) -> None:
        self.memberships.add(membership)

    def add_xeed(self, xeed: Xeed) -> None:
        if xeed.id in self.xeeds:
            raise ValueError("duplicate Xeed identity")
        self.xeeds[xeed.id] = xeed

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        self.calls.append("principal")
        return self.principals.get(principal_id)

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        self.calls.append("membership")
        return (
            tenant_id in self.tenants
            and PrincipalTenantMembership(principal_id, tenant_id) in self.memberships
        )

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None:
        self.calls.append("xeed")
        return self.xeeds.get(xeed_id)
