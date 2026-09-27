"""Canonical Xeed identity, ownership and first supported subject reference."""

from __future__ import annotations

from dataclasses import dataclass

from domain.identity import OrganizationId, TenantId, XeedId


class XeedError(ValueError):
    """Raised when a Xeed identity or ownership reference is invalid."""


@dataclass(frozen=True)
class Xeed:
    """A private observation context owned by one Tenant.

    The Organization reference identifies the observed world entity; it does
    not copy Organization truth or make the Organization private to the Tenant.
    """

    id: XeedId
    tenant_id: TenantId
    organization_id: OrganizationId
    label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise XeedError("Xeed id is required")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise XeedError("Xeed tenant id is required")
        if not isinstance(self.organization_id, str) or not self.organization_id.strip():
            raise XeedError("Xeed organization id is required")
        if self.label is not None and not self.label.strip():
            raise XeedError("Xeed label must be non-empty when provided")
