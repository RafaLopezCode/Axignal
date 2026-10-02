"""AO-16 evidence-backed weekly brief domain objects."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from domain.evidence.epistemics import Currentness


class WeeklyBriefIssueKind(StrEnum):
    MATERIAL_CHANGES = "MATERIAL_CHANGES"
    NO_MATERIAL_CHANGE = "NO_MATERIAL_CHANGE"


@dataclass(frozen=True, slots=True)
class WeeklyBriefItem:
    observation_id: str
    source_ref: str
    observed_at: datetime
    content_fingerprint: str
    condition: Currentness
    observation_summary: str
    why_may_matter: str
    unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        values = (
            self.observation_id,
            self.source_ref,
            self.content_fingerprint,
            self.observation_summary,
            self.why_may_matter,
        )
        if any(not value.strip() for value in values):
            raise ValueError("weekly brief item fields must be non-empty")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("weekly brief observation time must be timezone-aware")
        if self.condition is not Currentness.CURRENT:
            raise ValueError("weekly brief material items must be CURRENT")
        if not self.unknowns or any(not value.strip() for value in self.unknowns):
            raise ValueError("weekly brief item requires explicit UNKNOWN statements")


@dataclass(frozen=True, slots=True)
class WeeklyBriefIssue:
    issue_id: str
    request_id: str
    subject_reference: str
    issue_version: str
    composition_policy_id: str
    composition_policy_version: str
    created_at: datetime
    kind: WeeklyBriefIssueKind
    items: tuple[WeeklyBriefItem, ...]
    evidence_fingerprint: str

    def __post_init__(self) -> None:
        values = (
            self.issue_id,
            self.request_id,
            self.subject_reference,
            self.issue_version,
            self.composition_policy_id,
            self.composition_policy_version,
            self.evidence_fingerprint,
        )
        if any(not value.strip() for value in values):
            raise ValueError("weekly brief issue identity/version fields must be non-empty")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("weekly brief issue time must be timezone-aware")
        if len(self.items) > 3:
            raise ValueError("weekly brief issue may contain at most three material items")
        expected_kind = (
            WeeklyBriefIssueKind.NO_MATERIAL_CHANGE
            if not self.items
            else WeeklyBriefIssueKind.MATERIAL_CHANGES
        )
        if self.kind is not expected_kind:
            raise ValueError("weekly brief kind must match item presence")


@dataclass(frozen=True, slots=True)
class WeeklyBriefApproval:
    issue_id: str
    reviewer_principal_id: str
    approved_at: datetime

    def __post_init__(self) -> None:
        if not self.issue_id.strip() or not self.reviewer_principal_id.strip():
            raise ValueError("weekly brief approval identity is required")
        if self.approved_at.tzinfo is None or self.approved_at.utcoffset() is None:
            raise ValueError("weekly brief approval time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class WeeklyBriefDelivery:
    delivery_id: str
    issue_id: str
    delivered_at: datetime
    integration_id: str
    provider_message_ref: str

    def __post_init__(self) -> None:
        values = (self.delivery_id, self.issue_id, self.integration_id, self.provider_message_ref)
        if any(not value.strip() for value in values):
            raise ValueError("weekly brief delivery fields must be non-empty")
        if self.delivered_at.tzinfo is None or self.delivered_at.utcoffset() is None:
            raise ValueError("weekly brief delivery time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class WeeklyBriefCorrection:
    correction_id: str
    issue_id: str
    occurred_at: datetime
    actor_principal_id: str
    reason: str
    note: str

    def __post_init__(self) -> None:
        values = (
            self.correction_id,
            self.issue_id,
            self.actor_principal_id,
            self.reason,
            self.note,
        )
        if any(not value.strip() for value in values):
            raise ValueError("weekly brief correction fields must be non-empty")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("weekly brief correction time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class WeeklyBriefReconstruction:
    issue: WeeklyBriefIssue
    approval: WeeklyBriefApproval | None
    deliveries: tuple[WeeklyBriefDelivery, ...]
    corrections: tuple[WeeklyBriefCorrection, ...]


def evidence_fingerprint(items: tuple[WeeklyBriefItem, ...]) -> str:
    payload = [
        {
            "observation_id": item.observation_id,
            "source_ref": item.source_ref,
            "observed_at": item.observed_at.astimezone(UTC).isoformat(),
            "content_fingerprint": item.content_fingerprint,
            "condition": item.condition.value,
            "observation_summary": item.observation_summary,
        }
        for item in items
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
