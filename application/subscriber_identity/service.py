"""Resolve trusted external identities to existing AXIGNAL Principals."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.xeed_access.reader import PrincipalReader
from domain.identity import PrincipalId
from domain.tenancy.model import Principal


class IdentityResolutionFailure(StrEnum):
    """Expected identity outcomes that cannot authorize an application actor."""

    INVALID_IDENTITY = "INVALID_IDENTITY"
    IDENTITY_NOT_BOUND = "IDENTITY_NOT_BOUND"
    DUPLICATE_BINDING = "DUPLICATE_BINDING"
    PRINCIPAL_NOT_FOUND = "PRINCIPAL_NOT_FOUND"
    INVALID_BINDING_RESULT = "INVALID_BINDING_RESULT"


class IdentityResolutionError(Exception):
    """A verified external identity cannot resolve to one existing Principal."""

    def __init__(self, failure: IdentityResolutionFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True, slots=True)
class VerifiedExternalIdentity:
    """Opaque issuer/subject supplied by a trusted authentication boundary.

    This value does not authenticate itself. Only a trusted outer adapter may
    construct or pass it after verifying the configured identity assurance.
    Values are kept exact: the mapper does not normalize either field.
    """

    issuer: str
    subject: str
    client_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, str) or not self.issuer.strip():
            raise ValueError("verified issuer is required")
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("verified subject is required")
        if self.client_id is not None and (
            not isinstance(self.client_id, str) or not self.client_id.strip()
        ):
            raise ValueError("verified client scope must be non-empty when provided")


class IdentityBindingReader(Protocol):
    """Find existing Principal bindings for one exact verified identity pair."""

    def find_principal_ids(self, identity: VerifiedExternalIdentity) -> tuple[PrincipalId, ...]: ...


class SubscriberPrincipalResolver:
    """Resolve exactly one verified identity binding to an existing Principal."""

    def __init__(
        self,
        bindings: IdentityBindingReader,
        principals: PrincipalReader,
    ) -> None:
        self._bindings = bindings
        self._principals = principals

    def resolve(self, identity: VerifiedExternalIdentity) -> Principal:
        """Return an existing Principal or raise a non-authorizing failure.

        Reader exceptions propagate so an unavailable or corrupt authority
        cannot be collapsed into the valid "identity not bound" outcome.
        """

        if not isinstance(identity, VerifiedExternalIdentity):
            raise IdentityResolutionError(IdentityResolutionFailure.INVALID_IDENTITY)

        matches = self._bindings.find_principal_ids(identity)
        if not isinstance(matches, tuple):
            raise TypeError("identity binding reader must return a tuple of PrincipalIds")
        if not matches:
            raise IdentityResolutionError(IdentityResolutionFailure.IDENTITY_NOT_BOUND)
        if len(matches) != 1:
            raise IdentityResolutionError(IdentityResolutionFailure.DUPLICATE_BINDING)

        principal_id = matches[0]
        if not isinstance(principal_id, str) or not principal_id.strip():
            raise IdentityResolutionError(IdentityResolutionFailure.INVALID_BINDING_RESULT)

        principal = self._principals.get_principal(principal_id)
        if principal is None:
            raise IdentityResolutionError(IdentityResolutionFailure.PRINCIPAL_NOT_FOUND)
        if not isinstance(principal, Principal) or principal.id != principal_id:
            raise IdentityResolutionError(IdentityResolutionFailure.INVALID_BINDING_RESULT)
        return principal
