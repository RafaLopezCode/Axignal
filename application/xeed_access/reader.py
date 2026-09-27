"""Membership-first application authority for reading a private Xeed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from domain.identity import PrincipalId, TenantId, XeedId
from domain.tenancy.model import Principal
from domain.xeed.model import Xeed


class ReadFailure(StrEnum):
    """Precise internal failures; external private adapters must conceal Xeed existence."""

    MISSING_AUTH_CONTEXT = "MISSING_AUTH_CONTEXT"
    UNKNOWN_PRINCIPAL = "UNKNOWN_PRINCIPAL"
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    INVALID_XEED_ID = "INVALID_XEED_ID"
    XEED_NOT_FOUND = "XEED_NOT_FOUND"
    XEED_ACCESS_DENIED = "XEED_ACCESS_DENIED"


class XeedReadError(Exception):
    """Internal authorized-read failure without private object metadata."""

    def __init__(self, failure: ReadFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True)
class TrustedRequestContext:
    """Principal and selected Tenant already established by a trusted boundary.

    This value does not authenticate the Principal. Callers must only construct
    it from an authenticated outer adapter; tenant_id alone grants no access.
    """

    principal_id: PrincipalId
    tenant_id: TenantId

    def __post_init__(self) -> None:
        if not isinstance(self.principal_id, str) or not self.principal_id.strip():
            raise ValueError("trusted request context requires a principal id")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("trusted request context requires a tenant id")


class PrincipalReader(Protocol):
    """Resolves a canonical Principal identity."""

    def get_principal(self, principal_id: PrincipalId) -> Principal | None: ...


class MembershipReader(Protocol):
    """Checks authoritative Principal-Tenant membership."""

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool: ...


class XeedReader(Protocol):
    """Resolves a Xeed after membership has been established."""

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None: ...


_AUTHORIZED_XEED_TOKEN = object()


@dataclass(frozen=True, init=False)
class AuthorizedXeed:
    """A Xeed result constructible only by the authorized-read boundary."""

    _value: Xeed

    def __init__(self, xeed: Xeed, *, _token: object | None = None) -> None:
        if _token is not _AUTHORIZED_XEED_TOKEN:
            raise TypeError("AuthorizedXeed can only be created by AuthorizedXeedReader")
        object.__setattr__(self, "_value", xeed)

    @property
    def xeed(self) -> Xeed:
        """The Xeed after successful authorization."""

        return self._value


class AuthorizedXeedReader:
    """Enforces Principal membership and Xeed ownership before release."""

    def __init__(
        self,
        principals: PrincipalReader,
        memberships: MembershipReader,
        xeeds: XeedReader,
    ) -> None:
        self._principals = principals
        self._memberships = memberships
        self._xeeds = xeeds

    def read(
        self,
        context: TrustedRequestContext | None,
        xeed_id: XeedId,
    ) -> AuthorizedXeed:
        """Return an authorized wrapper or fail closed with an internal outcome."""

        if context is None:
            raise XeedReadError(ReadFailure.MISSING_AUTH_CONTEXT)

        principal = self._principals.get_principal(context.principal_id)
        if principal is None:
            raise XeedReadError(ReadFailure.UNKNOWN_PRINCIPAL)

        if not self._memberships.has_membership(principal.id, context.tenant_id):
            raise XeedReadError(ReadFailure.TENANT_ACCESS_DENIED)

        if not isinstance(xeed_id, str) or not xeed_id.strip():
            raise XeedReadError(ReadFailure.INVALID_XEED_ID)

        xeed = self._xeeds.get_xeed(xeed_id)
        if xeed is None:
            raise XeedReadError(ReadFailure.XEED_NOT_FOUND)

        if xeed.tenant_id != context.tenant_id:
            raise XeedReadError(ReadFailure.XEED_ACCESS_DENIED)

        return AuthorizedXeed(xeed, _token=_AUTHORIZED_XEED_TOKEN)
