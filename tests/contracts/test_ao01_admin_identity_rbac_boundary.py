from dataclasses import fields
from pathlib import Path

from application.admin_access import (
    AdminAuthenticationPort,
    AdminSessionCredential,
    VerifiedAdminIdentity,
)
from domain.admin_access import AdminAuthorizationGrant, AdminRole, AdminScope, scopes_for_roles

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "adr" / "ADR-0056-admin-identity-rbac-session-boundary.md"
ADMIN_SPEC = ROOT / "docs" / "product" / "AXIGNAL_ADMIN_PRODUCT_SPEC.md"
ARCH = ROOT / "docs" / "architecture" / "AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md"
IDENTITY_SPEC = ROOT / "specs" / "022-p0-identity-account-authority" / "spec.md"
HTTP_GUARD = ROOT / "tools" / "runtime" / "admin_access.py"


def test_admin_security_plane_is_not_subscriber_tenancy_authority() -> None:
    for relative in (
        "domain/admin_access",
        "application/admin_access",
        "pipeline/admin_access",
    ):
        for path in (ROOT / relative).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "PrincipalTenantMembership" not in text
            assert "TrustedRequestContext" not in text
            assert "domain.tenancy" not in text
            assert "application.xeed_access" not in text

    assert AdminAuthenticationPort is not None
    assert VerifiedAdminIdentity is not None


def test_agent_safe_role_has_exactly_one_safe_scope() -> None:
    assert scopes_for_roles(frozenset({AdminRole.AGENT_SAFE_READER})) == frozenset(
        {AdminScope.AGENT_SAFE_READ}
    )


def test_secret_free_grant_cannot_carry_raw_session_token() -> None:
    grant_fields = {item.name for item in fields(AdminAuthorizationGrant)}
    credential_fields = {item.name for item in fields(AdminSessionCredential)}

    assert "token" not in grant_fields
    assert "token_digest" not in grant_fields
    assert "token" in credential_fields


def test_ao01_decisions_are_canonical_and_no_longer_open() -> None:
    adr = ADR.read_text(encoding="utf-8")
    spec = ADMIN_SPEC.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    identity_spec = IDENTITY_SPEC.read_text(encoding="utf-8")
    http_guard = HTTP_GUARD.read_text(encoding="utf-8")

    assert "**Status:** Accepted" in adr
    assert "AdminPrincipal + AdminRole/Scope + AdminSession" in adr
    assert "Subscriber/product credentials are never accepted as Admin credentials" in adr
    assert "15 minutes" in adr
    assert "The last active founder cannot be revoked" in adr

    assert "`AGENT_SAFE_READER`" in spec
    assert "`admin:agent-safe:read`" in spec
    assert "concrete external Admin authentication provider and browser/session transport" in spec
    assert "-   RBAC implementation;" not in spec
    assert "whether some operational actions require dual approval" not in spec

    assert "ADMIN_AUTHORITY != SUBSCRIBER_TENANCY_AUTHORITY" in architecture
    assert "RAW_ADMIN_TOKEN != ADMIN_PROJECTION" in architecture
    assert "Admin RBAC is a separate plane under ADR-0056" in identity_spec
    assert "AdminHttpAccessGuard" in http_guard
    assert "Bearer" in http_guard
