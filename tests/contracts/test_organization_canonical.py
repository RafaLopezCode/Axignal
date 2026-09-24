"""Organization identity is canonical, never subscriber-scoped (MASTER §6, §7.3)."""

from __future__ import annotations

import dataclasses

from domain.organizations.model import Organization

FORBIDDEN_SCOPE_FIELDS = {
    "account_id",
    "subscriber_id",
    "tenant_id",
    "owner_id",
    "user_id",
    "claimed_by",
    "profile_owner",
    "xignal_id",
    "subscription_id",
}


def test_organization_has_no_subscriber_scope_fields() -> None:
    field_names = {field.name for field in dataclasses.fields(Organization)}
    assert field_names & FORBIDDEN_SCOPE_FIELDS == set()


def test_organization_identity_is_observer_independent() -> None:
    organization = Organization(id="org-acme", canonical_name="ACME")
    assert organization.identity_key == "org-acme"
