"""Canonical private-observer identities and Principal-Tenant membership."""

from __future__ import annotations

from dataclasses import dataclass

from domain.identity import PrincipalId, TenantId


class IdentityError(ValueError):
    """Raised when a canonical private identity is invalid."""


def _require_id(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise IdentityError(f"{name} is required")


@dataclass(frozen=True)
class Principal:
    """Canonical identity of an actor authenticated by an outer boundary."""

    id: PrincipalId

    def __post_init__(self) -> None:
        _require_id(self.id, "principal id")


@dataclass(frozen=True)
class Tenant:
    """Canonical private isolation and Xeed-ownership boundary."""

    id: TenantId

    def __post_init__(self) -> None:
        _require_id(self.id, "tenant id")


@dataclass(frozen=True)
class PrincipalTenantMembership:
    """Authoritative binding permitting a Principal to act in a Tenant."""

    principal_id: PrincipalId
    tenant_id: TenantId

    def __post_init__(self) -> None:
        _require_id(self.principal_id, "membership principal id")
        _require_id(self.tenant_id, "membership tenant id")
