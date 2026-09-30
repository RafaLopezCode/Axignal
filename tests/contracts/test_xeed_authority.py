"""P0-CORE-01 identity, ownership and authorized-read invariants."""

from __future__ import annotations

from dataclasses import replace
from typing import get_type_hints

import pytest

from application.xeed_access.reader import (
    AuthorizedXeed,
    AuthorizedXeedReader,
    ReadFailure,
    TrustedRequestContext,
    XeedReadError,
)
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import (
    IdentityError,
    Principal,
    PrincipalTenantMembership,
    Tenant,
)
from domain.xeed.model import Xeed, XeedError
from tests.support.xeed_authority import InMemoryXeedAuthority


def _authority() -> tuple[InMemoryXeedAuthority, AuthorizedXeedReader]:
    authority = InMemoryXeedAuthority()
    authority.add_principal(Principal(PrincipalId("principal-a")))
    authority.add_principal(Principal(PrincipalId("principal-b")))
    authority.add_tenant(Tenant(TenantId("tenant-a")))
    authority.add_tenant(Tenant(TenantId("tenant-b")))
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal-a"), TenantId("tenant-a"))
    )
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal-b"), TenantId("tenant-b"))
    )
    reader = AuthorizedXeedReader(authority, authority, authority)
    return authority, reader


def _xeed(
    xeed_id: str,
    tenant_id: str,
    organization_id: str = "org-shared",
    label: str = "Shared label",
) -> Xeed:
    return Xeed(
        id=XeedId(xeed_id),
        tenant_id=TenantId(tenant_id),
        organization_id=OrganizationId(organization_id),
        label=label,
    )


def _context(
    principal_id: str = "principal-a", tenant_id: str = "tenant-a"
) -> TrustedRequestContext:
    return TrustedRequestContext(PrincipalId(principal_id), TenantId(tenant_id))


def test_identity_annotations_are_distinct_and_use_string_representation() -> None:
    identity_types = (PrincipalId, TenantId, XeedId, OrganizationId)
    assert len(set(identity_types)) == 4
    assert all(identity_type.__supertype__ is str for identity_type in identity_types)
    assert get_type_hints(Principal)["id"] is PrincipalId
    assert get_type_hints(Tenant)["id"] is TenantId
    assert get_type_hints(Xeed)["id"] is XeedId
    assert get_type_hints(Xeed)["organization_id"] is OrganizationId
    assert get_type_hints(Organization)["id"] is OrganizationId


def test_blank_canonical_ids_fail_validation() -> None:
    with pytest.raises(IdentityError):
        Principal(PrincipalId(" "))
    with pytest.raises(IdentityError):
        Tenant(TenantId(""))
    with pytest.raises(XeedError):
        _xeed(" ", "tenant-a")


def test_organization_is_world_identity_not_tenant_identity() -> None:
    organization = Organization(
        id=OrganizationId("org-acme"),
        canonical_name="ACME",
    )
    assert organization.identity_key == OrganizationId("org-acme")
    assert not hasattr(organization, "tenant_id")


def test_germination_state_is_scoped_by_xeed_id() -> None:
    from datetime import UTC, datetime
    from typing import get_type_hints as hints

    from domain.xeed.germination import XeedGerminationState

    assert hints(XeedGerminationState)["xeed_id"] is XeedId
    assert hints(Xeed)["id"] is XeedId
    state = XeedGerminationState(
        xeed_id=XeedId("xeed-a"),
        initiated_by="unverified-actor",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert state.xeed_id == XeedId("xeed-a")
    assert not hasattr(state, "organization_id")


def test_authorized_owner_can_read_xeed_after_membership_check() -> None:
    authority, reader = _authority()
    xeed = _xeed("xeed-a", "tenant-a")
    another_xeed = _xeed("xeed-a2", "tenant-a", "org-other")
    authority.add_xeed(xeed)
    authority.add_xeed(another_xeed)

    authorized = reader.read(_context(), xeed.id)
    another_authorized = reader.read(_context(), another_xeed.id)

    assert isinstance(authorized, AuthorizedXeed)
    assert authorized.xeed is xeed
    assert another_authorized.xeed is another_xeed
    assert authority.calls == [
        "principal",
        "membership",
        "xeed",
        "principal",
        "membership",
        "xeed",
    ]


def test_cross_tenant_known_xeed_is_denied_internally() -> None:
    authority, reader = _authority()
    authority.add_xeed(_xeed("xeed-b", "tenant-b"))

    with pytest.raises(XeedReadError) as error:
        reader.read(_context(), XeedId("xeed-b"))

    assert error.value.failure is ReadFailure.XEED_ACCESS_DENIED
    assert authority.calls == ["principal", "membership", "xeed"]


def test_spoofed_tenant_context_is_denied_before_xeed_lookup() -> None:
    authority, reader = _authority()
    authority.add_xeed(_xeed("xeed-b", "tenant-b"))

    with pytest.raises(XeedReadError) as error:
        reader.read(_context(tenant_id="tenant-b"), XeedId("xeed-b"))

    assert error.value.failure is ReadFailure.TENANT_ACCESS_DENIED
    assert authority.calls == ["principal", "membership"]


def test_missing_context_fails_closed_without_lookup() -> None:
    authority, reader = _authority()

    with pytest.raises(XeedReadError) as error:
        reader.read(None, XeedId("xeed-a"))

    assert error.value.failure is ReadFailure.MISSING_AUTH_CONTEXT
    assert authority.calls == []


def test_unknown_principal_fails_closed_before_membership_or_xeed_lookup() -> None:
    authority, reader = _authority()

    with pytest.raises(XeedReadError) as error:
        reader.read(_context(principal_id="unknown"), XeedId("xeed-a"))

    assert error.value.failure is ReadFailure.UNKNOWN_PRINCIPAL
    assert authority.calls == ["principal"]


def test_internal_not_found_and_cross_tenant_denial_remain_distinct() -> None:
    assert ReadFailure.XEED_NOT_FOUND is not ReadFailure.XEED_ACCESS_DENIED


def test_known_principal_without_membership_is_denied_before_xeed_lookup() -> None:
    authority, reader = _authority()

    with pytest.raises(XeedReadError) as error:
        reader.read(_context("principal-a", "tenant-b"), XeedId("xeed-b"))

    assert error.value.failure is ReadFailure.TENANT_ACCESS_DENIED
    assert authority.calls == ["principal", "membership"]


def test_unknown_xeed_fails_closed_after_membership_check() -> None:
    authority, reader = _authority()

    with pytest.raises(XeedReadError) as error:
        reader.read(_context(), XeedId("missing"))

    assert error.value.failure is ReadFailure.XEED_NOT_FOUND
    assert authority.calls == ["principal", "membership", "xeed"]


def test_invalid_xeed_id_fails_validation_without_xeed_lookup() -> None:
    authority, reader = _authority()

    with pytest.raises(XeedReadError) as error:
        reader.read(_context(), XeedId(" "))

    assert error.value.failure is ReadFailure.INVALID_XEED_ID
    assert authority.calls == ["principal", "membership"]


def test_two_tenants_can_observe_same_organization_with_distinct_xeeds() -> None:
    authority, reader = _authority()
    xeed_a = _xeed("xeed-a", "tenant-a")
    xeed_b = _xeed("xeed-b", "tenant-b")
    authority.add_xeed(xeed_a)
    authority.add_xeed(xeed_b)

    assert xeed_a.organization_id == xeed_b.organization_id
    assert xeed_a.id != xeed_b.id
    assert reader.read(_context(), xeed_a.id).xeed is xeed_a
    assert reader.read(_context("principal-b", "tenant-b"), xeed_b.id).xeed is xeed_b
    with pytest.raises(XeedReadError) as error:
        reader.read(_context(), xeed_b.id)
    assert error.value.failure is ReadFailure.XEED_ACCESS_DENIED


def test_label_collision_does_not_change_identity_or_authorization() -> None:
    authority, reader = _authority()
    xeed_a = _xeed("xeed-a", "tenant-a", label="Same label")
    xeed_b = _xeed("xeed-b", "tenant-b", label="Same label")
    authority.add_xeed(xeed_a)
    authority.add_xeed(xeed_b)

    assert xeed_a.label == xeed_b.label
    assert xeed_a.id != xeed_b.id
    with pytest.raises(XeedReadError) as error:
        reader.read(_context(), xeed_b.id)
    assert error.value.failure is ReadFailure.XEED_ACCESS_DENIED


def test_label_mutation_preserves_xeed_identity() -> None:
    original = _xeed("xeed-a", "tenant-a", label="Old label")
    renamed = replace(original, label="New label")
    assert renamed.id == original.id
    assert renamed.tenant_id == original.tenant_id
    assert renamed.label != original.label


def test_test_authority_rejects_duplicate_xeed_id() -> None:
    authority = InMemoryXeedAuthority()
    authority.add_xeed(_xeed("xeed-a", "tenant-a", label="First"))
    with pytest.raises(ValueError, match="duplicate Xeed identity"):
        authority.add_xeed(_xeed("xeed-a", "tenant-b", label="Second"))


def test_authorized_result_cannot_be_constructed_without_reader_authority() -> None:
    with pytest.raises(TypeError):
        AuthorizedXeed(_xeed("xeed-a", "tenant-a"))  # type: ignore[call-arg]
