"""HTTP adapter for the Admin security boundary.

No Admin route is exposed here. Future Admin HTTP handlers must pass through this
adapter instead of parsing subscriber identity or provider roles themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.admin_access import (
    AdminAccessService,
    AdminAuthenticationError,
)
from domain.admin_access import (
    AdminApprovalEvidence,
    AdminAuthorizationGrant,
    AdminRiskClass,
    AdminScope,
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
