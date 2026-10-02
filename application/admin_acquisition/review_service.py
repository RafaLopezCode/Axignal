"""Privileged AO-15 coverage review operations."""

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
from domain.admin_acquisition import BriefRequestEventKind, BriefRequestSnapshot, BriefReviewState


class AdminBriefReviewService:
    def __init__(self, store: AcquisitionStore) -> None:
        self._store = store

    def accept(
        self,
        *,
        grant: AdminAuthorizationGrant,
        request_id: str,
        subject_reference: str,
        reason: str,
        now: datetime,
    ) -> BriefRequestSnapshot:
        _require_write_scope(grant)
        current = _snapshot(self._store, request_id)
        if current.review_state not in {
            BriefReviewState.REQUESTED,
            BriefReviewState.CLARIFICATION_REQUIRED,
        }:
            raise ValueError("only open requests can be accepted")
        if not subject_reference.strip() or not reason.strip():
            raise ValueError("subject reference and reason are required")
        _append(
            self._store,
            event_id=f"{request_id}:accepted:{int(now.timestamp())}",
            request_id=request_id,
            kind=BriefRequestEventKind.COVERAGE_ACCEPTED,
            occurred_at=now,
            actor=str(grant.principal_id),
            payload=_payload(subject_reference=subject_reference.strip(), reason=reason.strip()),
        )
        return _snapshot(self._store, request_id)

    def decline(
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
            raise ValueError("only open requests can be declined")
        if not reason.strip():
            raise ValueError("reason is required")
        _append(
            self._store,
            event_id=f"{request_id}:declined:{int(now.timestamp())}",
            request_id=request_id,
            kind=BriefRequestEventKind.COVERAGE_DECLINED,
            occurred_at=now,
            actor=str(grant.principal_id),
            payload=_payload(reason=reason.strip()),
        )
        return _snapshot(self._store, request_id)
