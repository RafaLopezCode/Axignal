"""AO-15 privileged acquisition lifecycle operations."""

from __future__ import annotations

from datetime import datetime

from application.admin_acquisition.service import (
    AcquisitionStore,
    _append,
    _payload,
    _require_write_scope,
    _snapshot,
)
from domain.admin_access import AdminAuthorizationGrant
from domain.admin_acquisition import (
    BriefRequestEventKind,
    BriefRequestSnapshot,
    BriefReviewState,
)


class AdminBriefLifecycleService:
    def __init__(self, store: AcquisitionStore) -> None:
        self._store = store

    def require_clarification(
        self,
        *,
        grant: AdminAuthorizationGrant,
        request_id: str,
        reason: str,
        now: datetime,
    ) -> BriefRequestSnapshot:
        _require_write_scope(grant)
        current = _snapshot(self._store, request_id)
        if current.review_state not in {
            BriefReviewState.REQUESTED,
            BriefReviewState.CLARIFICATION_REQUIRED,
        }:
            raise ValueError("only open requests can require clarification")
        if not reason.strip():
            raise ValueError("reason is required")
        _append(
            self._store,
            event_id=f"{request_id}:clarify:{int(now.timestamp())}",
            request_id=request_id,
            kind=BriefRequestEventKind.CLARIFICATION_REQUIRED,
            occurred_at=now,
            actor=str(grant.principal_id),
            payload=_payload(reason=reason.strip()),
        )
        return _snapshot(self._store, request_id)

    def block_delivery(
        self,
        *,
        grant: AdminAuthorizationGrant,
        request_id: str,
        reason: str,
        now: datetime,
    ) -> BriefRequestSnapshot:
        _require_write_scope(grant)
        _snapshot(self._store, request_id)
        if not reason.strip():
            raise ValueError("reason is required")
        _append(
            self._store,
            event_id=f"{request_id}:blocked:{int(now.timestamp())}",
            request_id=request_id,
            kind=BriefRequestEventKind.SUPPRESSED,
            occurred_at=now,
            actor=str(grant.principal_id),
            payload=_payload(reason=reason.strip()),
        )
        return _snapshot(self._store, request_id)
