"""HTTP adapter for the Admin security boundary.

No Admin route is exposed here. Future Admin HTTP handlers must pass through this
adapter instead of parsing subscriber identity or provider roles themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from application.admin_access import (
    AdminAccessService,
    AdminAuthenticationError,
    VerifiedAdminIdentity,
)
from domain.admin_access import (
    AdminApprovalEvidence,
    AdminAuthorizationGrant,
    AdminRiskClass,
    AdminScope,
)
from pipeline.admin_access import SqliteAdminAccessStore


class RejectingAdminAuthenticator:
    """Validation-only runtime adapter; external credentials are never accepted here."""

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del credential, now
        return None


def build_validation_only_admin_access(data_dir: Path) -> AdminAccessService:
    """Compose durable AO-01 session validation without an issuance/login provider."""

    return AdminAccessService(
        SqliteAdminAccessStore(data_dir / "admin-access.sqlite3"),
        RejectingAdminAuthenticator(),
    )


@dataclass(slots=True)
class AdminHttpAccessGuard:
    service: AdminAccessService

    def authorize_header(
        self,
        authorization_header: str | None,
        *,
        required_scope: AdminScope,
        risk: AdminRiskClass,
        now: datetime,
        approval: AdminApprovalEvidence | None = None,
    ) -> AdminAuthorizationGrant:
        """Authorize one HTTP request from an Admin-only bearer credential."""

        if authorization_header is None:
            raise AdminAuthenticationError("missing Admin authorization header")
        scheme, separator, token = authorization_header.partition(" ")
        if separator != " " or scheme != "Bearer" or not token.strip():
            raise AdminAuthenticationError("invalid Admin authorization header")
        return self.service.authorize(
            token.strip(),
            required_scope=required_scope,
            risk=risk,
            now=now,
            approval=approval,
        )
