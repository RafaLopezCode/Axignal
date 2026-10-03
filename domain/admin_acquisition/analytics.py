"""AO-14/AO-17 privacy-minimized product analytics and growth events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

AnalyticsEventId = NewType("AnalyticsEventId", str)
ANALYTICS_DEFINITION_VERSION = "AO14_V1"


class AnalyticsEventKind(StrEnum):
    SIGNUP_COMPLETED = "SIGNUP_COMPLETED"
    FIRST_XEED_CREATED = "FIRST_XEED_CREATED"
    TODAY_VIEWED = "TODAY_VIEWED"
    EVIDENCE_VIEWED = "EVIDENCE_VIEWED"
    RETURN_VISIT = "RETURN_VISIT"
    BRIEF_ENGAGED = "BRIEF_ENGAGED"
    EVIDENCE_CLICKED = "EVIDENCE_CLICKED"
    REQUEST_ACCOUNT_LINKED = "REQUEST_ACCOUNT_LINKED"
    ADVISORY_INQUIRY = "ADVISORY_INQUIRY"
    ADVISORY_CLOSED = "ADVISORY_CLOSED"
    COMPLAINT_RECORDED = "COMPLAINT_RECORDED"
    DELIVERY_COST_RECORDED = "DELIVERY_COST_RECORDED"


class TrafficClassification(StrEnum):
    HUMAN = "HUMAN"
    BOT = "BOT"
    AMBIGUOUS = "AMBIGUOUS"
    INTERNAL = "INTERNAL"
    UNKNOWN = "UNKNOWN"


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("analytics event time must be timezone-aware")


def _bounded(value: str | None, name: str, maximum: int = 200) -> None:
    if value is not None and (not value.strip() or len(value) > maximum):
        raise ValueError(f"{name} must be non-empty bounded text")


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    event_id: AnalyticsEventId
    kind: AnalyticsEventKind
    occurred_at: datetime
    classification: TrafficClassification
    session_ref: str | None = None
    request_id: str | None = None
    issue_id: str | None = None
    account_id: str | None = None
    xeed_id: str | None = None
    evidence_ref: str | None = None
    advisory_ref: str | None = None
    amount_minor: int | None = None
    currency: str | None = None
    definition_version: str = ANALYTICS_DEFINITION_VERSION

    def __post_init__(self) -> None:
        _bounded(str(self.event_id), "event_id", 160)
        _aware(self.occurred_at)
        for name in (
            "session_ref",
            "request_id",
            "issue_id",
            "account_id",
            "xeed_id",
            "evidence_ref",
            "advisory_ref",
        ):
            _bounded(getattr(self, name), name)
        if self.definition_version != ANALYTICS_DEFINITION_VERSION:
            raise ValueError("unsupported analytics definition version")
        if self.kind is AnalyticsEventKind.REQUEST_ACCOUNT_LINKED and (
            not self.request_id or not self.account_id
        ):
            raise ValueError("request/account link requires request_id and account_id")
        if (
            self.kind
            in {
                AnalyticsEventKind.BRIEF_ENGAGED,
                AnalyticsEventKind.EVIDENCE_CLICKED,
            }
            and not self.issue_id
        ):
            raise ValueError("brief engagement requires issue_id")
        if self.kind is AnalyticsEventKind.EVIDENCE_CLICKED and not self.evidence_ref:
            raise ValueError("evidence click requires evidence_ref")
        if (
            self.kind
            in {
                AnalyticsEventKind.ADVISORY_INQUIRY,
                AnalyticsEventKind.ADVISORY_CLOSED,
            }
            and not self.advisory_ref
        ):
            raise ValueError("advisory event requires advisory_ref")
        if self.kind is AnalyticsEventKind.DELIVERY_COST_RECORDED:
            if self.amount_minor is None or self.amount_minor < 0:
                raise ValueError("delivery cost requires non-negative amount_minor")
            if self.currency is None or len(self.currency) != 3 or not self.currency.isalpha():
                raise ValueError("delivery cost requires three-letter currency")
            object.__setattr__(self, "currency", self.currency.upper())
        elif self.amount_minor is not None or self.currency is not None:
            raise ValueError("money fields are reserved for delivery cost events")
