from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_access import (
    AdminAccessService,
    AdminAuthenticationError,
    AdminAuthorizationError,
    AdminPrivilegeConflict,
    VerifiedAdminIdentity,
)
from domain.admin_access import (
    AdminApprovalEvidence,
    AdminAssurance,
    AdminPrincipalId,
    AdminRiskClass,
    AdminRole,
    AdminScope,
    PrivilegeChangeKind,
)
from pipeline.admin_access import SqliteAdminAccessStore


class FakeAdminAuthenticator:
    def __init__(self, identities: dict[str, VerifiedAdminIdentity]) -> None:
        self._identities = identities

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identities.get(credential)


def _identity(
    principal_id: str,
    now: datetime,
    assurance: AdminAssurance = AdminAssurance.STEP_UP,
) -> VerifiedAdminIdentity:
    return VerifiedAdminIdentity(
        principal_id=AdminPrincipalId(principal_id),
        authenticated_at=now,
        assurance=assurance,
        auth_source="test-admin-auth",
    )


def _service(
    tmp_path: Path,
    identities: dict[str, VerifiedAdminIdentity],
) -> tuple[AdminAccessService, SqliteAdminAccessStore]:
    store = SqliteAdminAccessStore(tmp_path / "admin-access.sqlite3")
    return AdminAccessService(store, FakeAdminAuthenticator(identities)), store


def test_bootstrap_founder_is_single_verified_and_auditable(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    service, store = _service(tmp_path, {"admin-credential": _identity(founder, now)})

    event = service.bootstrap_founder(
        "admin-credential",
        occurred_at=now,
        reason="initial production founder bootstrap",
    )

    assert event.target_principal_id == founder
    assert event.kind is PrivilegeChangeKind.BOOTSTRAP_FOUNDER
    assert store.roles_for_principal(founder) == frozenset({AdminRole.FOUNDER})
    assert store.privilege_events() == (event,)
    with pytest.raises(AdminPrivilegeConflict):
        service.bootstrap_founder(
            "admin-credential",
            occurred_at=now,
            reason="second bootstrap must fail",
        )


def test_subscriber_or_unknown_credential_cannot_bootstrap_or_issue_admin_session(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    service, _ = _service(tmp_path, {})

    with pytest.raises(AdminAuthenticationError):
        service.bootstrap_founder(
            "subscriber-session-token",
            occurred_at=now,
            reason="subscriber must not bootstrap admin",
        )
    with pytest.raises(AdminAuthenticationError):
        service.issue_session(
            "subscriber-session-token",
            authenticated_at=now,
        )


def test_role_scope_least_privilege_and_expiry(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    business = AdminPrincipalId("admin:business")
    identities = {
        "founder-stepup": _identity(founder, now),
        "business-primary": _identity(business, now + timedelta(minutes=2), AdminAssurance.PRIMARY),
    }
    service, store = _service(tmp_path, identities)
    service.bootstrap_founder(
        "founder-stepup",
        occurred_at=now,
        reason="bootstrap founder",
    )
    founder_credential = service.issue_session(
        "founder-stepup",
        authenticated_at=now,
    )
    service.change_role(
        founder_credential.token,
        target_principal_id=business,
        role=AdminRole.BUSINESS,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="business operator",
    )
    business_credential = service.issue_session(
        "business-primary",
        authenticated_at=now + timedelta(minutes=2),
        lifetime=timedelta(hours=1),
    )

    grant = service.authorize(
        business_credential.token,
        required_scope=AdminScope.CUSTOMERS_READ,
        risk=AdminRiskClass.READ,
        now=now + timedelta(minutes=3),
    )
    assert grant.principal_id == business
    assert AdminScope.CUSTOMERS_READ in grant.scopes
    assert AdminScope.FISCAL_WRITE not in grant.scopes

    with pytest.raises(AdminAuthorizationError):
        service.authorize(
            business_credential.token,
            required_scope=AdminScope.FISCAL_WRITE,
            risk=AdminRiskClass.WRITE,
            now=now + timedelta(minutes=3),
        )
    with pytest.raises(AdminAuthenticationError):
        service.authorize(
            business_credential.token,
            required_scope=AdminScope.CUSTOMERS_READ,
            risk=AdminRiskClass.READ,
            now=now + timedelta(hours=2),
        )
    assert store.roles_for_principal(business) == frozenset({AdminRole.BUSINESS})


def test_sensitive_privilege_change_requires_step_up(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    target = AdminPrincipalId("admin:support")
    identities = {
        "founder-stepup": _identity(founder, now),
        "founder-primary": _identity(founder, now, AdminAssurance.PRIMARY),
    }
    service, _ = _service(tmp_path, identities)
    service.bootstrap_founder(
        "founder-stepup",
        occurred_at=now,
        reason="bootstrap founder",
    )
    primary = service.issue_session(
        "founder-primary",
        authenticated_at=now,
    )

    with pytest.raises(AdminAuthorizationError, match="step-up"):
        service.change_role(
            primary.token,
            target_principal_id=target,
            role=AdminRole.SUPPORT,
            kind=PrivilegeChangeKind.GRANT_ROLE,
            occurred_at=now + timedelta(minutes=1),
            reason="support assignment",
        )


def test_founder_quorum_then_critical_changes_require_dual_approval(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    first = AdminPrincipalId("admin:founder-1")
    second = AdminPrincipalId("admin:founder-2")
    third = AdminPrincipalId("admin:founder-3")
    identities = {
        "first-stepup": _identity(first, now),
        "second-stepup": _identity(second, now + timedelta(minutes=2)),
    }
    service, store = _service(tmp_path, identities)
    service.bootstrap_founder(
        "first-stepup",
        occurred_at=now,
        reason="bootstrap founder",
    )
    first_credential = service.issue_session(
        "first-stepup",
        authenticated_at=now,
    )

    service.change_role(
        first_credential.token,
        target_principal_id=second,
        role=AdminRole.FOUNDER,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="establish founder quorum",
    )
    second_credential = service.issue_session(
        "second-stepup",
        authenticated_at=now + timedelta(minutes=2),
    )

    with pytest.raises(AdminAuthorizationError, match="dual approval"):
        service.change_role(
            first_credential.token,
            target_principal_id=third,
            role=AdminRole.FOUNDER,
            kind=PrivilegeChangeKind.GRANT_ROLE,
            occurred_at=now + timedelta(minutes=3),
            reason="third founder",
        )

    service.change_role(
        first_credential.token,
        target_principal_id=third,
        role=AdminRole.FOUNDER,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=3),
        reason="third founder",
        approval=AdminApprovalEvidence(
            approver_principal_id=second,
            approver_session_id=second_credential.session_id,
        ),
    )
    assert AdminRole.FOUNDER in store.roles_for_principal(third)


def test_last_founder_cannot_be_revoked(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    service, _ = _service(tmp_path, {"founder": _identity(founder, now)})
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    credential = service.issue_session("founder", authenticated_at=now)

    with pytest.raises(AdminPrivilegeConflict, match="last active founder"):
        service.change_role(
            credential.token,
            target_principal_id=founder,
            role=AdminRole.FOUNDER,
            kind=PrivilegeChangeKind.REVOKE_ROLE,
            occurred_at=now + timedelta(minutes=1),
            reason="must not remove last founder",
        )


def test_session_revocation_is_fail_closed_for_every_role(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    support = AdminPrincipalId("admin:support")
    identities = {
        "founder": _identity(founder, now),
        "support": _identity(support, now + timedelta(minutes=2), AdminAssurance.PRIMARY),
    }
    service, _ = _service(tmp_path, identities)
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    founder_credential = service.issue_session("founder", authenticated_at=now)
    service.change_role(
        founder_credential.token,
        target_principal_id=support,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="support operator",
    )
    credential = service.issue_session(
        "support",
        authenticated_at=now + timedelta(minutes=2),
    )
    service.revoke_own_session(
        credential.token,
        revoked_at=now + timedelta(minutes=3),
        reason="sign out",
    )

    with pytest.raises(AdminAuthenticationError, match="revoked"):
        service.authorize(
            credential.token,
            required_scope=AdminScope.SUPPORT_READ,
            risk=AdminRiskClass.READ,
            now=now + timedelta(minutes=4),
        )


def test_agent_safe_role_cannot_read_customer_or_financial_state(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    agent = AdminPrincipalId("admin:agent-safe")
    identities = {
        "founder": _identity(founder, now),
        "agent": _identity(agent, now + timedelta(minutes=2), AdminAssurance.PRIMARY),
    }
    service, _ = _service(tmp_path, identities)
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    founder_credential = service.issue_session("founder", authenticated_at=now)
    service.change_role(
        founder_credential.token,
        target_principal_id=agent,
        role=AdminRole.AGENT_SAFE_READER,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="agent-safe projection only",
    )
    credential = service.issue_session(
        "agent",
        authenticated_at=now + timedelta(minutes=2),
    )

    safe = service.authorize(
        credential.token,
        required_scope=AdminScope.AGENT_SAFE_READ,
        risk=AdminRiskClass.READ,
        now=now + timedelta(minutes=3),
    )
    assert safe.scopes == frozenset({AdminScope.AGENT_SAFE_READ})
    with pytest.raises(AdminAuthorizationError):
        service.authorize(
            credential.token,
            required_scope=AdminScope.CUSTOMERS_READ,
            risk=AdminRiskClass.READ,
            now=now + timedelta(minutes=3),
        )


def test_raw_admin_token_never_appears_in_secret_free_grant_or_repr(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    service, _ = _service(tmp_path, {"founder": _identity(founder, now)})
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    credential = service.issue_session("founder", authenticated_at=now)
    grant = service.authorize(
        credential.token,
        required_scope=AdminScope.EXECUTIVE_READ,
        risk=AdminRiskClass.READ,
        now=now + timedelta(minutes=1),
    )

    assert credential.token not in repr(credential)
    assert credential.token not in repr(grant)
    assert not hasattr(grant, "token")


def test_stale_step_up_cannot_perform_sensitive_action(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    target = AdminPrincipalId("admin:support")
    service, _ = _service(tmp_path, {"founder": _identity(founder, now)})
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    credential = service.issue_session("founder", authenticated_at=now)

    with pytest.raises(AdminAuthorizationError, match="fresh step-up"):
        service.change_role(
            credential.token,
            target_principal_id=target,
            role=AdminRole.SUPPORT,
            kind=PrivilegeChangeKind.GRANT_ROLE,
            occurred_at=now + timedelta(minutes=16),
            reason="stale step-up must not authorize privilege change",
        )


def test_role_revocation_applies_to_existing_session_immediately(tmp_path: Path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    first = AdminPrincipalId("admin:founder-1")
    second = AdminPrincipalId("admin:founder-2")
    business = AdminPrincipalId("admin:business")
    identities = {
        "first": _identity(first, now),
        "second": _identity(second, now + timedelta(minutes=2)),
        "business": _identity(business, now + timedelta(minutes=4), AdminAssurance.PRIMARY),
    }
    service, _ = _service(tmp_path, identities)
    service.bootstrap_founder("first", occurred_at=now, reason="bootstrap founder")
    first_session = service.issue_session("first", authenticated_at=now)
    service.change_role(
        first_session.token,
        target_principal_id=second,
        role=AdminRole.FOUNDER,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="establish founder quorum",
    )
    service.issue_session(
        "second",
        authenticated_at=now + timedelta(minutes=2),
    )
    service.change_role(
        first_session.token,
        target_principal_id=business,
        role=AdminRole.BUSINESS,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=3),
        reason="business role",
    )
    business_session = service.issue_session(
        "business",
        authenticated_at=now + timedelta(minutes=4),
    )
    service.authorize(
        business_session.token,
        required_scope=AdminScope.CUSTOMERS_READ,
        risk=AdminRiskClass.READ,
        now=now + timedelta(minutes=5),
    )

    service.change_role(
        first_session.token,
        target_principal_id=business,
        role=AdminRole.BUSINESS,
        kind=PrivilegeChangeKind.REVOKE_ROLE,
        occurred_at=now + timedelta(minutes=6),
        reason="remove business access",
    )

    with pytest.raises(AdminAuthorizationError, match="no active roles"):
        service.authorize(
            business_session.token,
            required_scope=AdminScope.CUSTOMERS_READ,
            risk=AdminRiskClass.READ,
            now=now + timedelta(minutes=7),
        )


def test_http_guard_accepts_only_admin_bearer_tokens(tmp_path: Path) -> None:
    from tools.runtime.admin_access import AdminHttpAccessGuard

    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    service, _ = _service(tmp_path, {"founder": _identity(founder, now)})
    service.bootstrap_founder("founder", occurred_at=now, reason="bootstrap founder")
    credential = service.issue_session("founder", authenticated_at=now)
    guard = AdminHttpAccessGuard(service)

    with pytest.raises(AdminAuthenticationError):
        guard.authorize_header(
            None,
            required_scope=AdminScope.EXECUTIVE_READ,
            risk=AdminRiskClass.READ,
            now=now,
        )
    with pytest.raises(AdminAuthenticationError):
        guard.authorize_header(
            "Bearer subscriber-session-token",
            required_scope=AdminScope.EXECUTIVE_READ,
            risk=AdminRiskClass.READ,
            now=now,
        )

    grant = guard.authorize_header(
        f"Bearer {credential.token}",
        required_scope=AdminScope.EXECUTIVE_READ,
        risk=AdminRiskClass.READ,
        now=now + timedelta(minutes=1),
    )
    assert grant.principal_id == founder
    assert not hasattr(grant, "token")


@pytest.mark.parametrize(
    ("role", "allowed", "denied"),
    [
        (AdminRole.BUSINESS, AdminScope.CUSTOMERS_WRITE, AdminScope.FINANCE_WRITE),
        (AdminRole.FINANCE_FISCAL, AdminScope.FISCAL_WRITE, AdminScope.CUSTOMERS_WRITE),
        (AdminRole.OPERATIONS, AdminScope.SYSTEM_OPERATE, AdminScope.BILLING_WRITE),
        (
            AdminRole.RESEARCH_INTELLIGENCE,
            AdminScope.RESEARCH_OPERATE,
            AdminScope.SYSTEM_OPERATE,
        ),
        (
            AdminRole.TECHNICAL_SYSTEM,
            AdminScope.INTEGRATIONS_MANAGE,
            AdminScope.CUSTOMERS_WRITE,
        ),
        (AdminRole.SUPPORT, AdminScope.SUPPORT_WRITE, AdminScope.FINANCE_READ),
        (
            AdminRole.AGENT_SAFE_READER,
            AdminScope.AGENT_SAFE_READ,
            AdminScope.CUSTOMERS_READ,
        ),
    ],
)
def test_non_founder_role_matrix_is_least_privilege(
    role: AdminRole,
    allowed: AdminScope,
    denied: AdminScope,
) -> None:
    from domain.admin_access import scopes_for_roles

    scopes = scopes_for_roles(frozenset({role}))
    assert allowed in scopes
    assert denied not in scopes
    assert AdminScope.PRIVILEGE_MANAGE not in scopes


def test_founder_role_has_all_declared_admin_scopes() -> None:
    from domain.admin_access import scopes_for_roles

    assert scopes_for_roles(frozenset({AdminRole.FOUNDER})) == frozenset(AdminScope)
