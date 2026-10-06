"""Offline identity mapping and existing subscriber authority contracts."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from application.subscriber_identity import (
    IdentityResolutionError,
    IdentityResolutionFailure,
    SubscriberPrincipalResolver,
    VerifiedExternalIdentity,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    ReadFailure,
    TrustedRequestContext,
    XeedReadError,
)
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from tests.support.xeed_authority import InMemoryXeedAuthority


class InMemoryIdentityBindings:
    """Test-only exact-key binding reader with duplicate rows preserved."""

    def __init__(self, rows: Mapping[tuple[str, str], tuple[PrincipalId, ...]]) -> None:
        self._rows = dict(rows)
        self.calls: list[tuple[str, str]] = []

    def find_principal_ids(self, identity: VerifiedExternalIdentity) -> tuple[PrincipalId, ...]:
        key = (identity.issuer, identity.subject)
        self.calls.append(key)
        return self._rows.get(key, ())


class FailingIdentityBindings:
    """Authority failure must propagate rather than become not-bound."""

    def find_principal_ids(self, identity: VerifiedExternalIdentity) -> tuple[PrincipalId, ...]:
        raise RuntimeError("identity authority unavailable")


class InMemoryOrganizations:
    """Test-only global Organization lookup for the existing authorized reader."""

    def __init__(self, organizations: Mapping[OrganizationId, Organization]) -> None:
        self._organizations = dict(organizations)

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self._organizations.get(organization_id)


def _resolver(
    rows: Mapping[tuple[str, str], tuple[PrincipalId, ...]],
    authority: InMemoryXeedAuthority | None = None,
) -> tuple[SubscriberPrincipalResolver, InMemoryIdentityBindings]:
    binding_reader = InMemoryIdentityBindings(rows)
    principal_reader = authority or InMemoryXeedAuthority()
    return SubscriberPrincipalResolver(binding_reader, principal_reader), binding_reader


def test_exact_issuer_and_subject_resolve_an_existing_principal() -> None:
    authority = InMemoryXeedAuthority()
    principal = Principal(PrincipalId("principal-a"))
    authority.add_principal(principal)
    resolver, bindings = _resolver(
        {("https://issuer.example/tenant", "Subject-01"): (principal.id,)},
        authority,
    )

    resolved = resolver.resolve(
        VerifiedExternalIdentity("https://issuer.example/tenant", "Subject-01")
    )

    assert resolved is principal
    assert bindings.calls == [("https://issuer.example/tenant", "Subject-01")]


@pytest.mark.parametrize(
    ("rows", "identity", "failure"),
    [
        (
            {},
            VerifiedExternalIdentity("https://issuer.example", "subject"),
            IdentityResolutionFailure.IDENTITY_NOT_BOUND,
        ),
        (
            {("https://issuer.example", "subject"): (PrincipalId("principal-a"),)},
            VerifiedExternalIdentity("https://other.example", "subject"),
            IdentityResolutionFailure.IDENTITY_NOT_BOUND,
        ),
        (
            {("https://issuer.example", "subject"): (PrincipalId("principal-a"),)},
            VerifiedExternalIdentity("https://issuer.example", "Subject"),
            IdentityResolutionFailure.IDENTITY_NOT_BOUND,
        ),
    ],
)
def test_unbound_or_confused_exact_key_never_resolves(
    rows: Mapping[tuple[str, str], tuple[PrincipalId, ...]],
    identity: VerifiedExternalIdentity,
    failure: IdentityResolutionFailure,
) -> None:
    resolver, _ = _resolver(rows)

    with pytest.raises(IdentityResolutionError) as error:
        resolver.resolve(identity)

    assert error.value.failure is failure


@pytest.mark.parametrize(
    "principal_ids",
    [
        (PrincipalId("principal-a"), PrincipalId("principal-b")),
        (PrincipalId("principal-a"), PrincipalId("principal-a")),
    ],
)
def test_any_duplicate_binding_is_an_integrity_failure(
    principal_ids: tuple[PrincipalId, ...],
) -> None:
    identity = VerifiedExternalIdentity("https://issuer.example", "subject")
    resolver, _ = _resolver({(identity.issuer, identity.subject): principal_ids})

    with pytest.raises(IdentityResolutionError) as error:
        resolver.resolve(identity)

    assert error.value.failure is IdentityResolutionFailure.DUPLICATE_BINDING


def test_binding_to_missing_principal_is_non_authorizing() -> None:
    identity = VerifiedExternalIdentity("https://issuer.example", "subject")
    resolver, _ = _resolver(
        {(identity.issuer, identity.subject): (PrincipalId("missing-principal"),)}
    )

    with pytest.raises(IdentityResolutionError) as error:
        resolver.resolve(identity)

    assert error.value.failure is IdentityResolutionFailure.PRINCIPAL_NOT_FOUND


def test_binding_authority_error_propagates_and_is_not_converted_to_not_bound() -> None:
    resolver = SubscriberPrincipalResolver(
        FailingIdentityBindings(),  # type: ignore[arg-type]
        InMemoryXeedAuthority(),
    )

    with pytest.raises(RuntimeError, match="identity authority unavailable"):
        resolver.resolve(VerifiedExternalIdentity("https://issuer.example", "subject"))


def test_none_from_binding_reader_is_a_contract_error_not_an_unbound_identity() -> None:
    class InvalidReader:
        def find_principal_ids(self, identity: VerifiedExternalIdentity) -> tuple[PrincipalId, ...]:
            return None  # type: ignore[return-value]

    resolver = SubscriberPrincipalResolver(InvalidReader(), InMemoryXeedAuthority())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must return a tuple"):
        resolver.resolve(VerifiedExternalIdentity("https://issuer.example", "subject"))


@pytest.mark.parametrize(
    ("issuer", "subject"),
    [("", "subject"), ("issuer", "  ")],
)
def test_verified_identity_rejects_blank_key_parts(issuer: str, subject: str) -> None:
    with pytest.raises(ValueError):
        VerifiedExternalIdentity(issuer, subject)


def test_resolved_principals_reuse_existing_membership_first_readers() -> None:
    authority = InMemoryXeedAuthority()
    principal_a = Principal(PrincipalId("principal-a"))
    principal_b = Principal(PrincipalId("principal-b"))
    tenant_a = Tenant(TenantId("tenant-a"))
    tenant_b = Tenant(TenantId("tenant-b"))
    organization = Organization(OrganizationId("org-shared"), "Shared Organization")
    authority.add_principal(principal_a)
    authority.add_principal(principal_b)
    authority.add_tenant(tenant_a)
    authority.add_tenant(tenant_b)
    authority.add_membership(PrincipalTenantMembership(principal_a.id, tenant_a.id))
    authority.add_membership(PrincipalTenantMembership(principal_b.id, tenant_b.id))
    focus_a = Xeed(XeedId("focus-a"), tenant_a.id, organization.id)
    focus_b = Xeed(XeedId("focus-b"), tenant_b.id, organization.id)
    authority.add_xeed(focus_a)
    authority.add_xeed(focus_b)

    identity_a = VerifiedExternalIdentity("https://issuer.example", "subject-a")
    identity_b = VerifiedExternalIdentity("https://issuer.example", "subject-b")
    resolver, _ = _resolver(
        {
            (identity_a.issuer, identity_a.subject): (principal_a.id,),
            (identity_b.issuer, identity_b.subject): (principal_b.id,),
        },
        authority,
    )
    resolved_a = resolver.resolve(identity_a)
    resolved_b = resolver.resolve(identity_b)
    reader = AuthorizedXeedReader(authority, authority, authority)
    # Tenant selection is a separate request-context concern, not an identity claim.
    authorized_a = reader.read(TrustedRequestContext(resolved_a.id, tenant_a.id), focus_a.id)
    authorized_b = reader.read(TrustedRequestContext(resolved_b.id, tenant_b.id), focus_b.id)
    organization_reader = AuthorizedXeedOrganizationReader(
        InMemoryOrganizations({organization.id: organization})
    )

    projected_a = organization_reader.read(authorized_a)
    projected_b = organization_reader.read(authorized_b)

    assert authorized_a.xeed is focus_a
    assert authorized_b.xeed is focus_b
    assert authorized_a is not authorized_b
    assert projected_a.organization is projected_b.organization is organization
    assert projected_a.authorized_xeed is authorized_a
    assert projected_b.authorized_xeed is authorized_b
    assert not hasattr(projected_a.organization, "tenant_id")

    with pytest.raises(XeedReadError) as cross_tenant:
        reader.read(TrustedRequestContext(resolved_a.id, tenant_a.id), focus_b.id)
    assert cross_tenant.value.failure is ReadFailure.XEED_ACCESS_DENIED

    authority.memberships.remove(PrincipalTenantMembership(principal_a.id, tenant_a.id))
    with pytest.raises(XeedReadError) as revoked:
        reader.read(TrustedRequestContext(resolved_a.id, tenant_a.id), focus_a.id)
    assert revoked.value.failure is ReadFailure.TENANT_ACCESS_DENIED
