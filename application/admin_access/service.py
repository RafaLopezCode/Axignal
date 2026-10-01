"""Admin authentication-session and RBAC application boundary."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol

from domain.admin_access import (
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


class AdminAuthenticationError(PermissionError):
    """Authentication or session validation failed closed."""


class AdminAuthorizationError(PermissionError):
    """Authenticated Admin lacks required authority."""


class AdminPrivilegeConflict(RuntimeError):
    """Privilege history would become ambiguous or invalid."""


@dataclass(frozen=True, slots=True)
class VerifiedAdminIdentity:
    """Provider-neutral proof returned only after Admin-plane authentication."""

    principal_id: AdminPrincipalId
    authenticated_at: datetime
    assurance: AdminAssurance
    auth_source: str


class AdminAuthenticationPort(Protocol):
    """Verifies Admin-plane credentials; subscriber credentials are invalid here."""

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None: ...


@dataclass(frozen=True, slots=True)
class AdminSessionCredential:
    """Opaque bearer credential returned only to the trusted outer auth adapter."""

    session_id: AdminSessionId
    token: str = field(repr=False)


class AdminAccessStore(Protocol):
    """Persistence port for server-side Admin sessions and immutable privilege history."""

    def has_privilege_history(self) -> bool: ...

    def append_privilege_event(self, event: AdminPrivilegeEvent) -> bool: ...

    def privilege_events(self) -> tuple[AdminPrivilegeEvent, ...]: ...

    def roles_for_principal(self, principal_id: AdminPrincipalId) -> frozenset[AdminRole]: ...

    def append_session(self, session: AdminSession) -> bool: ...

    def get_session_by_digest(self, token_digest: str) -> AdminSession | None: ...

    def get_session(self, session_id: AdminSessionId) -> AdminSession | None: ...

    def append_revocation(self, revocation: AdminSessionRevocation) -> bool: ...

    def is_revoked(self, session_id: AdminSessionId) -> bool: ...


def _digest_token(token: str) -> str:
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def _event_id() -> AdminPrivilegeEventId:
    return AdminPrivilegeEventId("admin-priv:" + uuid.uuid4().hex)


def _session_id() -> AdminSessionId:
    return AdminSessionId("admin-session:" + uuid.uuid4().hex)


class AdminAccessService:
    """Fail-closed Admin security boundary independent of subscriber tenancy."""

    def __init__(
        self,
        store: AdminAccessStore,
        authenticator: AdminAuthenticationPort,
        *,
        default_session_lifetime: timedelta = timedelta(hours=8),
        max_session_lifetime: timedelta = timedelta(hours=12),
        step_up_max_age: timedelta = timedelta(minutes=15),
    ) -> None:
        if default_session_lifetime <= timedelta(0):
            raise ValueError("default admin session lifetime must be positive")
        if max_session_lifetime < default_session_lifetime:
            raise ValueError("max admin session lifetime cannot be shorter than default")
        if step_up_max_age <= timedelta(0):
            raise ValueError("step-up max age must be positive")
        self._store = store
        self._authenticator = authenticator
        self._default_lifetime = default_session_lifetime
        self._max_lifetime = max_session_lifetime
        self._step_up_max_age = step_up_max_age

    def bootstrap_founder(
        self,
        credential: str,
        *,
        occurred_at: datetime,
        reason: str,
    ) -> AdminPrivilegeEvent:
        """Create the single initial founder grant from verified Admin-plane identity."""

        identity = self._authenticate_external(credential, occurred_at)
        if self._store.has_privilege_history():
            raise AdminPrivilegeConflict(
                "founder bootstrap is allowed only before privilege history exists"
            )
        event = AdminPrivilegeEvent(
            event_id=_event_id(),
            target_principal_id=identity.principal_id,
            role=AdminRole.FOUNDER,
            kind=PrivilegeChangeKind.BOOTSTRAP_FOUNDER,
            occurred_at=occurred_at,
            actor_principal_id=identity.principal_id,
            actor_session_id=None,
            reason=reason,
        )
        self._store.append_privilege_event(event)
        return event

    def issue_session(
        self,
        credential: str,
        *,
        authenticated_at: datetime,
        lifetime: timedelta | None = None,
    ) -> AdminSessionCredential:
        """Issue an opaque Admin-only bearer after Admin-plane authentication."""

        identity = self._authenticate_external(credential, authenticated_at)
        roles = self._store.roles_for_principal(identity.principal_id)
        if not roles:
            raise AdminAuthorizationError("authenticated identity has no Admin role")
        selected = self._default_lifetime if lifetime is None else lifetime
        if selected <= timedelta(0) or selected > self._max_lifetime:
            raise ValueError("admin session lifetime is outside allowed bounds")
        token = secrets.token_urlsafe(48)
        session = AdminSession(
            session_id=_session_id(),
            principal_id=identity.principal_id,
            token_digest=_digest_token(token),
            issued_at=identity.authenticated_at.astimezone(UTC),
            expires_at=(identity.authenticated_at + selected).astimezone(UTC),
            assurance=identity.assurance,
            auth_source=identity.auth_source,
        )
        self._store.append_session(session)
        return AdminSessionCredential(session_id=session.session_id, token=token)

    def authorize(
        self,
        token: str,
        *,
        required_scope: AdminScope,
        risk: AdminRiskClass,
        now: datetime,
        approval: AdminApprovalEvidence | None = None,
    ) -> AdminAuthorizationGrant:
        session = self._resolve_authenticated_session(token, now)
        roles = self._store.roles_for_principal(session.principal_id)
        scopes = scopes_for_roles(roles)
        if required_scope not in scopes:
            raise AdminAuthorizationError("required Admin scope denied")
        if risk in {AdminRiskClass.SENSITIVE, AdminRiskClass.CRITICAL}:
            if session.assurance is not AdminAssurance.STEP_UP:
                raise AdminAuthorizationError("step-up authentication required")
            if now.astimezone(UTC) - session.issued_at > self._step_up_max_age:
                raise AdminAuthorizationError("fresh step-up authentication required")
        if risk is AdminRiskClass.CRITICAL:
            self._validate_dual_approval(
                actor=session,
                required_scope=required_scope,
                approval=approval,
                now=now,
            )
        return AdminAuthorizationGrant(
            session_id=session.session_id,
            principal_id=session.principal_id,
            roles=roles,
            scopes=scopes,
            assurance=session.assurance,
        )

    def change_role(
        self,
        token: str,
        *,
        target_principal_id: AdminPrincipalId,
        role: AdminRole,
        kind: PrivilegeChangeKind,
        occurred_at: datetime,
        reason: str,
        approval: AdminApprovalEvidence | None = None,
    ) -> AdminPrivilegeEvent:
        if kind not in {PrivilegeChangeKind.GRANT_ROLE, PrivilegeChangeKind.REVOKE_ROLE}:
            raise ValueError("runtime role change must be grant or revoke")
        founder_count = self._active_founder_count()
        if (
            role is AdminRole.FOUNDER
            and kind is PrivilegeChangeKind.REVOKE_ROLE
            and founder_count <= 1
        ):
            raise AdminPrivilegeConflict("cannot revoke the last active founder")
        founder_quorum_bootstrap = (
            role is AdminRole.FOUNDER
            and kind is PrivilegeChangeKind.GRANT_ROLE
            and founder_count == 1
        )
        risk = (
            AdminRiskClass.CRITICAL
            if role is AdminRole.FOUNDER and not founder_quorum_bootstrap
            else AdminRiskClass.SENSITIVE
        )
        actor = self.authorize(
            token,
            required_scope=AdminScope.PRIVILEGE_MANAGE,
            risk=risk,
            now=occurred_at,
            approval=approval,
        )
        active_roles = self._store.roles_for_principal(target_principal_id)
        if kind is PrivilegeChangeKind.GRANT_ROLE and role in active_roles:
            raise AdminPrivilegeConflict("role is already granted")
        if kind is PrivilegeChangeKind.REVOKE_ROLE and role not in active_roles:
            raise AdminPrivilegeConflict("role is not currently granted")
        event = AdminPrivilegeEvent(
            event_id=_event_id(),
            target_principal_id=target_principal_id,
            role=role,
            kind=kind,
            occurred_at=occurred_at,
            actor_principal_id=actor.principal_id,
            actor_session_id=actor.session_id,
            reason=reason,
        )
        self._store.append_privilege_event(event)
        return event

    def revoke_own_session(
        self,
        token: str,
        *,
        revoked_at: datetime,
        reason: str,
    ) -> AdminSessionRevocation:
        session = self._resolve_authenticated_session(token, revoked_at)
        revocation = AdminSessionRevocation(
            session_id=session.session_id,
            revoked_at=revoked_at,
            actor_principal_id=session.principal_id,
            reason=reason,
        )
        self._store.append_revocation(revocation)
        return revocation

    def _authenticate_external(self, credential: str, now: datetime) -> VerifiedAdminIdentity:
        if not isinstance(credential, str) or not credential.strip():
            raise AdminAuthenticationError("missing Admin authentication credential")
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("authentication time must be timezone-aware")
        identity = self._authenticator.verify(credential, now=now)
        if identity is None:
            raise AdminAuthenticationError("Admin authentication failed")
        if (
            identity.authenticated_at.tzinfo is None
            or identity.authenticated_at.utcoffset() is None
        ):
            raise AdminAuthenticationError("Admin authenticator returned naive time")
        if identity.authenticated_at > now:
            raise AdminAuthenticationError("Admin authentication proof is from the future")
        if not identity.auth_source.strip():
            raise AdminAuthenticationError("Admin authentication source is required")
        return identity

    def _resolve_authenticated_session(self, token: str, now: datetime) -> AdminSession:
        if not isinstance(token, str) or not token.strip():
            raise AdminAuthenticationError("missing Admin session credential")
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("authorization time must be timezone-aware")
        session = self._store.get_session_by_digest(_digest_token(token))
        if session is None:
            raise AdminAuthenticationError("unknown Admin session")
        self._validate_live_session(session, now)
        if not self._store.roles_for_principal(session.principal_id):
            raise AdminAuthorizationError("Admin principal has no active roles")
        return session

    def _active_founder_count(self) -> int:
        principals = {event.target_principal_id for event in self._store.privilege_events()}
        return sum(
            AdminRole.FOUNDER in self._store.roles_for_principal(principal_id)
            for principal_id in principals
        )

    def _validate_live_session(self, session: AdminSession, now: datetime) -> None:
        current = now.astimezone(UTC)
        if current < session.issued_at:
            raise AdminAuthenticationError("Admin session is not valid yet")
        if current >= session.expires_at:
            raise AdminAuthenticationError("Admin session expired")
        if self._store.is_revoked(session.session_id):
            raise AdminAuthenticationError("Admin session revoked")

    def _validate_dual_approval(
        self,
        *,
        actor: AdminSession,
        required_scope: AdminScope,
        approval: AdminApprovalEvidence | None,
        now: datetime,
    ) -> None:
        if approval is None:
            raise AdminAuthorizationError("critical Admin action requires dual approval")
        if approval.approver_principal_id == actor.principal_id:
            raise AdminAuthorizationError("critical Admin action requires a distinct approver")
        approver = self._store.get_session(approval.approver_session_id)
        if approver is None or approver.principal_id != approval.approver_principal_id:
            raise AdminAuthorizationError("invalid Admin approval session")
        self._validate_live_session(approver, now)
        if approver.assurance is not AdminAssurance.STEP_UP:
            raise AdminAuthorizationError("critical Admin approval requires step-up assurance")
        if now.astimezone(UTC) - approver.issued_at > self._step_up_max_age:
            raise AdminAuthorizationError("critical Admin approval requires fresh step-up")
        approver_scopes = scopes_for_roles(self._store.roles_for_principal(approver.principal_id))
        if required_scope not in approver_scopes:
            raise AdminAuthorizationError("approver lacks required Admin scope")
