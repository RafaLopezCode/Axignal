"""Authorized reads of the global Organization referenced by one Xeed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.xeed_access.reader import AuthorizedXeed
from domain.identity import OrganizationId
from domain.organizations.model import Organization


class OrganizationReadFailure(StrEnum):
    """Internal outcomes for resolving a Xeed's global Organization context."""

    MISSING_AUTHORIZED_XEED = "MISSING_AUTHORIZED_XEED"
    INVALID_ORGANIZATION_REFERENCE = "INVALID_ORGANIZATION_REFERENCE"
    ORGANIZATION_NOT_FOUND = "ORGANIZATION_NOT_FOUND"
    INVALID_CANONICAL_RESULT = "INVALID_CANONICAL_RESULT"


class OrganizationReadError(Exception):
    """A referenced global Organization could not be safely released."""

    def __init__(self, failure: OrganizationReadFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


class CanonicalOrganizationReader(Protocol):
    """Resolves a canonical global Organization by its world identity."""

    def get_organization(self, organization_id: OrganizationId) -> Organization | None: ...


_AUTHORIZED_XEED_ORGANIZATION_TOKEN = object()


@dataclass(frozen=True, init=False)
class AuthorizedXeedOrganization:
    """Original global Organization read through an authorized private Xeed."""

    _authorized_xeed: AuthorizedXeed
    _organization: Organization

    def __init__(
        self,
        authorized_xeed: AuthorizedXeed,
        organization: Organization,
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _AUTHORIZED_XEED_ORGANIZATION_TOKEN:
            raise TypeError("AuthorizedXeedOrganization can only be created by its reader")
        object.__setattr__(self, "_authorized_xeed", authorized_xeed)
        object.__setattr__(self, "_organization", organization)

    @property
    def authorized_xeed(self) -> AuthorizedXeed:
        """The private context that authorized this contextual read."""

        return self._authorized_xeed

    @property
    def organization(self) -> Organization:
        """The original shared Organization; no Xeed-local copy is made."""

        return self._organization


class AuthorizedXeedOrganizationReader:
    """Resolve only the Organization reference carried by an AuthorizedXeed."""

    def __init__(self, organizations: CanonicalOrganizationReader) -> None:
        self._organizations = organizations

    def read(self, authorized_xeed: AuthorizedXeed) -> AuthorizedXeedOrganization:
        """Return the referenced global Organization or fail closed."""

        if not isinstance(authorized_xeed, AuthorizedXeed):
            raise OrganizationReadError(OrganizationReadFailure.MISSING_AUTHORIZED_XEED)

        organization_id = authorized_xeed.xeed.organization_id
        if not isinstance(organization_id, str) or not organization_id.strip():
            raise OrganizationReadError(OrganizationReadFailure.INVALID_ORGANIZATION_REFERENCE)

        organization = self._organizations.get_organization(organization_id)
        if organization is None:
            raise OrganizationReadError(OrganizationReadFailure.ORGANIZATION_NOT_FOUND)
        if not isinstance(organization, Organization) or organization.id != organization_id:
            raise OrganizationReadError(OrganizationReadFailure.INVALID_CANONICAL_RESULT)

        return AuthorizedXeedOrganization(
            authorized_xeed,
            organization,
            _token=_AUTHORIZED_XEED_ORGANIZATION_TOKEN,
        )
