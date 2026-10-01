"""Admin security authority, separate from subscriber tenancy."""

from domain.admin_access.model import (
    AdminAccessError,
    AdminApprovalEvidence,
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminPrivilegeEvent,
    AdminPrivilegeEventId,
    AdminRiskClass,
    AdminRole,
    AdminScope,
    AdminSession,
    AdminSessionId,
    AdminSessionRevocation,
    PrivilegeChangeKind,
    scopes_for_roles,
)

__all__ = [
    "AdminAccessError",
    "AdminApprovalEvidence",
    "AdminAssurance",
    "AdminAuthorizationGrant",
    "AdminPrincipalId",
    "AdminPrivilegeEvent",
    "AdminPrivilegeEventId",
    "AdminRiskClass",
    "AdminRole",
    "AdminScope",
    "AdminSession",
    "AdminSessionId",
    "AdminSessionRevocation",
    "PrivilegeChangeKind",
    "scopes_for_roles",
]
