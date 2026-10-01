"""Provider-neutral Admin identity, role, scope and session authority."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Final, NewType

AdminPrincipalId = NewType("AdminPrincipalId", str)
AdminSessionId = NewType("AdminSessionId", str)
AdminPrivilegeEventId = NewType("AdminPrivilegeEventId", str)


class AdminAccessError(ValueError):
    """Raised when Admin authority data is invalid."""


class AdminRole(StrEnum):
    FOUNDER = "FOUNDER"
    BUSINESS = "BUSINESS"
    FINANCE_FISCAL = "FINANCE_FISCAL"
    OPERATIONS = "OPERATIONS"
    RESEARCH_INTELLIGENCE = "RESEARCH_INTELLIGENCE"
    TECHNICAL_SYSTEM = "TECHNICAL_SYSTEM"
    SUPPORT = "SUPPORT"
    AGENT_SAFE_READER = "AGENT_SAFE_READER"


class AdminScope(StrEnum):
    EXECUTIVE_READ = "admin:executive:read"
    CUSTOMERS_READ = "admin:customers:read"
    CUSTOMERS_WRITE = "admin:customers:write"
    COMMERCIAL_READ = "admin:commercial:read"
    COMMERCIAL_WRITE = "admin:commercial:write"
    ACQUISITION_READ = "admin:acquisition:read"
    ACQUISITION_WRITE = "admin:acquisition:write"
    REVENUE_READ = "admin:revenue:read"
    BILLING_READ = "admin:billing:read"
    BILLING_WRITE = "admin:billing:write"
    FINANCE_READ = "admin:finance:read"
    FINANCE_WRITE = "admin:finance:write"
    FISCAL_READ = "admin:fiscal:read"
    FISCAL_WRITE = "admin:fiscal:write"
    XEEDS_READ = "admin:xeeds:read"
    QUALITY_READ = "admin:quality:read"
    RESEARCH_READ = "admin:research:read"
    RESEARCH_OPERATE = "admin:research:operate"
    ADVISORY_READ = "admin:advisory:read"
    ADVISORY_WRITE = "admin:advisory:write"
    GOVERNANCE_READ = "admin:governance:read"
    GOVERNANCE_MANAGE = "admin:governance:manage"
    INTEGRATIONS_READ = "admin:integrations:read"
    INTEGRATIONS_MANAGE = "admin:integrations:manage"
    SYSTEM_READ = "admin:system:read"
    SYSTEM_OPERATE = "admin:system:operate"
    SUPPORT_READ = "admin:support:read"
    SUPPORT_WRITE = "admin:support:write"
    AUDIT_READ = "admin:audit:read"
    PRIVILEGE_MANAGE = "admin:privilege:manage"
    AGENT_SAFE_READ = "admin:agent-safe:read"


class AdminAssurance(StrEnum):
    PRIMARY = "PRIMARY"
    STEP_UP = "STEP_UP"


class AdminRiskClass(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class PrivilegeChangeKind(StrEnum):
    BOOTSTRAP_FOUNDER = "BOOTSTRAP_FOUNDER"
    GRANT_ROLE = "GRANT_ROLE"
    REVOKE_ROLE = "REVOKE_ROLE"


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdminAccessError(f"{name} is required")


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AdminAccessError(f"{name} must be timezone-aware")


_ALL_SCOPES: Final[frozenset[AdminScope]] = frozenset(AdminScope)

_ROLE_SCOPES: Final[Mapping[AdminRole, frozenset[AdminScope]]] = MappingProxyType(
    {
        AdminRole.FOUNDER: _ALL_SCOPES,
        AdminRole.BUSINESS: frozenset(
            {
                AdminScope.EXECUTIVE_READ,
                AdminScope.CUSTOMERS_READ,
                AdminScope.CUSTOMERS_WRITE,
                AdminScope.COMMERCIAL_READ,
                AdminScope.COMMERCIAL_WRITE,
                AdminScope.ACQUISITION_READ,
                AdminScope.ACQUISITION_WRITE,
                AdminScope.REVENUE_READ,
                AdminScope.BILLING_READ,
                AdminScope.SUPPORT_READ,
                AdminScope.AUDIT_READ,
            }
        ),
        AdminRole.FINANCE_FISCAL: frozenset(
            {
                AdminScope.EXECUTIVE_READ,
                AdminScope.REVENUE_READ,
                AdminScope.BILLING_READ,
                AdminScope.BILLING_WRITE,
                AdminScope.FINANCE_READ,
                AdminScope.FINANCE_WRITE,
                AdminScope.FISCAL_READ,
                AdminScope.FISCAL_WRITE,
                AdminScope.AUDIT_READ,
            }
        ),
        AdminRole.OPERATIONS: frozenset(
            {
                AdminScope.EXECUTIVE_READ,
                AdminScope.XEEDS_READ,
                AdminScope.QUALITY_READ,
                AdminScope.RESEARCH_READ,
                AdminScope.INTEGRATIONS_READ,
                AdminScope.SYSTEM_READ,
                AdminScope.SYSTEM_OPERATE,
                AdminScope.SUPPORT_READ,
                AdminScope.AUDIT_READ,
            }
        ),
        AdminRole.RESEARCH_INTELLIGENCE: frozenset(
            {
                AdminScope.XEEDS_READ,
                AdminScope.QUALITY_READ,
                AdminScope.RESEARCH_READ,
                AdminScope.RESEARCH_OPERATE,
                AdminScope.ADVISORY_READ,
                AdminScope.ADVISORY_WRITE,
                AdminScope.AUDIT_READ,
            }
        ),
        AdminRole.TECHNICAL_SYSTEM: frozenset(
            {
                AdminScope.XEEDS_READ,
                AdminScope.QUALITY_READ,
                AdminScope.GOVERNANCE_READ,
                AdminScope.INTEGRATIONS_READ,
                AdminScope.INTEGRATIONS_MANAGE,
                AdminScope.SYSTEM_READ,
                AdminScope.SYSTEM_OPERATE,
                AdminScope.AUDIT_READ,
            }
        ),
        AdminRole.SUPPORT: frozenset(
            {
                AdminScope.CUSTOMERS_READ,
                AdminScope.XEEDS_READ,
                AdminScope.SUPPORT_READ,
                AdminScope.SUPPORT_WRITE,
            }
        ),
        AdminRole.AGENT_SAFE_READER: frozenset({AdminScope.AGENT_SAFE_READ}),
    }
)


def scopes_for_roles(roles: frozenset[AdminRole]) -> frozenset[AdminScope]:
    scopes: set[AdminScope] = set()
    for role in roles:
        scopes.update(_ROLE_SCOPES[role])
    return frozenset(scopes)


@dataclass(frozen=True, slots=True)
class AdminSession:
    """Server-side Admin session record. Raw bearer credentials are never stored here."""

    session_id: AdminSessionId
    principal_id: AdminPrincipalId
    token_digest: str
    issued_at: datetime
    expires_at: datetime
    assurance: AdminAssurance
    auth_source: str

    def __post_init__(self) -> None:
        _require_text(self.session_id, "session id")
        _require_text(self.principal_id, "admin principal id")
        _require_text(self.token_digest, "token digest")
        _require_text(self.auth_source, "auth source")
        _require_aware(self.issued_at, "issued_at")
        _require_aware(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise AdminAccessError("admin session must expire after issuance")


@dataclass(frozen=True, slots=True)
class AdminSessionRevocation:
    session_id: AdminSessionId
    revoked_at: datetime
    actor_principal_id: AdminPrincipalId
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.session_id, "session id")
        _require_text(self.actor_principal_id, "actor principal id")
        _require_text(self.reason, "revocation reason")
        _require_aware(self.revoked_at, "revoked_at")


@dataclass(frozen=True, slots=True)
class AdminPrivilegeEvent:
    event_id: AdminPrivilegeEventId
    target_principal_id: AdminPrincipalId
    role: AdminRole
    kind: PrivilegeChangeKind
    occurred_at: datetime
    actor_principal_id: AdminPrincipalId
    actor_session_id: AdminSessionId | None
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.event_id, "privilege event id")
        _require_text(self.target_principal_id, "target principal id")
        _require_text(self.actor_principal_id, "actor principal id")
        _require_text(self.reason, "privilege change reason")
        _require_aware(self.occurred_at, "occurred_at")
        if (
            self.kind is PrivilegeChangeKind.BOOTSTRAP_FOUNDER
            and self.role is not AdminRole.FOUNDER
        ):
            raise AdminAccessError("bootstrap event may grant FOUNDER only")
        if self.kind is not PrivilegeChangeKind.BOOTSTRAP_FOUNDER and self.actor_session_id is None:
            raise AdminAccessError("non-bootstrap privilege changes require actor session")


@dataclass(frozen=True, slots=True)
class AdminApprovalEvidence:
    """Approval by a separately authenticated, step-up Admin session."""

    approver_principal_id: AdminPrincipalId
    approver_session_id: AdminSessionId

    def __post_init__(self) -> None:
        _require_text(self.approver_principal_id, "approver principal id")
        _require_text(self.approver_session_id, "approver session id")


@dataclass(frozen=True, slots=True)
class AdminAuthorizationGrant:
    """Secret-free context safe for downstream Admin application services."""

    session_id: AdminSessionId
    principal_id: AdminPrincipalId
    roles: frozenset[AdminRole]
    scopes: frozenset[AdminScope]
    assurance: AdminAssurance
