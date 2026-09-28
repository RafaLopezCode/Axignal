"""Authorized Xeed reads resolve, but never copy or own, global Organizations."""

from __future__ import annotations

from typing import cast, get_type_hints

import pytest

from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganization,
    AuthorizedXeedOrganizationReader,
    OrganizationReadError,
    OrganizationReadFailure,
)
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    ReadFailure,
    TrustedRequestContext,
    XeedReadError,
)
from domain.faxt.model import FAXT
from domain.identity import (
    OrganizationId,
    PrincipalId,
    TenantId,
    XeedId,
)
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from tests.support.xeed_authority import InMemoryXeedAuthority


class _OrganizationAuthority:
    """Small deterministic canonical reader fake for this contract suite."""

    def __init__(self) -> None:
        self.organizations: dict[OrganizationId, Organization | object] = {}
        self.calls: list[OrganizationId] = []

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        self.calls.append(organization_id)
        return cast(Organization | None, self.organizations.get(organization_id))


def _setup() -> tuple[
    InMemoryXeedAuthority,
    AuthorizedXeedReader,
    _OrganizationAuthority,
    AuthorizedXeedOrganizationReader,
]:
    identities = InMemoryXeedAuthority()
    for principal_id, tenant_id in (
        ("principal-a", "tenant-a"),
        ("principal-b", "tenant-b"),
    ):
        identities.add_principal(Principal(PrincipalId(principal_id)))
        identities.add_tenant(Tenant(TenantId(tenant_id)))
        identities.add_membership(
            PrincipalTenantMembership(PrincipalId(principal_id), TenantId(tenant_id))
        )
    identities.add_xeed(Xeed(XeedId("xeed-a"), TenantId("tenant-a"), OrganizationId("org-a")))
    identities.add_xeed(Xeed(XeedId("xeed-b"), TenantId("tenant-b"), OrganizationId("org-b")))
    organizations = _OrganizationAuthority()
    reader = AuthorizedXeedOrganizationReader(organizations)
    return (
        identities,
        AuthorizedXeedReader(identities, identities, identities),
        organizations,
        reader,
    )


def test_organization_is_resolved_only_from_authorized_xeed_and_original_is_returned() -> None:
    identities, xeed_reader, organizations, reader = _setup()
    organization = Organization(OrganizationId("org-a"), "ACME")
    organizations.organizations[organization.id] = organization
    authorized_xeed = xeed_reader.read(
        TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
        XeedId("xeed-a"),
    )

    result = reader.read(authorized_xeed)

    assert isinstance(result, AuthorizedXeedOrganization)
    assert result.authorized_xeed is authorized_xeed
    assert result.organization is organization
    assert result.organization.id == OrganizationId("org-a")
    assert not hasattr(result.organization, "tenant_id")
    assert organizations.calls == [OrganizationId("org-a")]
    assert identities.calls == ["principal", "membership", "xeed"]


@pytest.mark.parametrize("raw_context", [None, XeedId("xeed-a"), OrganizationId("org-a")])
def test_raw_ids_cannot_replace_authorized_xeed_for_organization_read(
    raw_context: object,
) -> None:
    _, _, organizations, reader = _setup()

    with pytest.raises(OrganizationReadError) as error:
        reader.read(raw_context)  # type: ignore[arg-type]

    assert error.value.failure is OrganizationReadFailure.MISSING_AUTHORIZED_XEED
    assert organizations.calls == []


def test_missing_global_organization_fails_closed() -> None:
    _, xeed_reader, organizations, reader = _setup()
    authorized_xeed = xeed_reader.read(
        TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
        XeedId("xeed-a"),
    )

    with pytest.raises(OrganizationReadError) as error:
        reader.read(authorized_xeed)

    assert error.value.failure is OrganizationReadFailure.ORGANIZATION_NOT_FOUND
    assert organizations.calls == [OrganizationId("org-a")]


@pytest.mark.parametrize(
    "canonical_result",
    [object(), Organization(OrganizationId("org-other"), "Other")],
)
def test_wrong_type_or_mismatched_global_identity_fails_closed(
    canonical_result: object,
) -> None:
    _, xeed_reader, organizations, reader = _setup()
    organizations.organizations[OrganizationId("org-a")] = canonical_result
    authorized_xeed = xeed_reader.read(
        TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
        XeedId("xeed-a"),
    )

    with pytest.raises(OrganizationReadError) as error:
        reader.read(authorized_xeed)

    assert error.value.failure is OrganizationReadFailure.INVALID_CANONICAL_RESULT


def test_tenant_cannot_resolve_another_tenants_xeed_then_read_its_organization() -> None:
    _, xeed_reader, organizations, _reader = _setup()
    organizations.organizations[OrganizationId("org-b")] = Organization(
        OrganizationId("org-b"), "BETA"
    )

    with pytest.raises(XeedReadError) as error:
        xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
            XeedId("xeed-b"),
        )

    assert error.value.failure is ReadFailure.XEED_ACCESS_DENIED
    assert organizations.calls == []


def test_shared_global_organization_remains_one_object_across_tenants() -> None:
    identities = InMemoryXeedAuthority()
    for principal_id, tenant_id, xeed_id in (
        ("principal-a", "tenant-a", "xeed-a"),
        ("principal-b", "tenant-b", "xeed-b"),
    ):
        identities.add_principal(Principal(PrincipalId(principal_id)))
        identities.add_tenant(Tenant(TenantId(tenant_id)))
        identities.add_membership(
            PrincipalTenantMembership(PrincipalId(principal_id), TenantId(tenant_id))
        )
        identities.add_xeed(
            Xeed(XeedId(xeed_id), TenantId(tenant_id), OrganizationId("org-shared"))
        )
    organization = Organization(OrganizationId("org-shared"), "Shared Global Org")
    organizations = _OrganizationAuthority()
    organizations.organizations[organization.id] = organization
    reader = AuthorizedXeedOrganizationReader(organizations)
    xeed_reader = AuthorizedXeedReader(identities, identities, identities)

    result_a = reader.read(
        xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-a"), TenantId("tenant-a")),
            XeedId("xeed-a"),
        )
    )
    result_b = reader.read(
        xeed_reader.read(
            TrustedRequestContext(PrincipalId("principal-b"), TenantId("tenant-b")),
            XeedId("xeed-b"),
        )
    )

    assert result_a.organization is result_b.organization is organization
    assert result_a.authorized_xeed is not result_b.authorized_xeed
    assert organizations.calls == [OrganizationId("org-shared"), OrganizationId("org-shared")]


def test_faxt_subject_semantics_remain_unresolved_and_are_not_cast_to_organization() -> None:
    assert get_type_hints(FAXT)["subject_id"] is str
    assert get_type_hints(FAXT.create)["subject_id"] is str


def test_xeed_references_global_organization_without_copying_its_truth() -> None:
    assert get_type_hints(Xeed)["organization_id"] is OrganizationId
    assert get_type_hints(Organization)["id"] is OrganizationId
    assert get_type_hints(Organization)["canonical_name"] is str
    assert "canonical_name" not in Xeed.__dataclass_fields__
    assert "tenant_id" not in Organization.__dataclass_fields__
