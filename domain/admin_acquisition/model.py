"""AO-15 first-party free weekly brief request and consent domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

BriefRequestId = NewType("BriefRequestId", str)
BriefRequestEventId = NewType("BriefRequestEventId", str)

_ID = re.compile(r"^[a-z][a-z0-9:_-]{2,127}$")
_DOMAIN = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class BriefReviewState(StrEnum):
    REQUESTED = "REQUESTED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"


class CoverageState(StrEnum):
    UNKNOWN = "UNKNOWN"
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"


class NewsletterConsentState(StrEnum):
    NOT_GRANTED = "NOT_GRANTED"
    GRANTED = "GRANTED"
    WITHDRAWN = "WITHDRAWN"
    SUPPRESSED = "SUPPRESSED"


class BriefRequestEventKind(StrEnum):
    REQUEST_SUBMITTED = "REQUEST_SUBMITTED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    COVERAGE_ACCEPTED = "COVERAGE_ACCEPTED"
    COVERAGE_DECLINED = "COVERAGE_DECLINED"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"
    SUPPRESSED = "SUPPRESSED"
    WITHDRAWN = "WITHDRAWN"


def _text(value: str, name: str, maximum: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} is required and must be at most {maximum} characters")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def normalize_domain(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.startswith(("http://", "https://")):
        raise ValueError("company_domain must be a hostname, not a URL")
    if not _DOMAIN.fullmatch(normalized):
        raise ValueError("company_domain must be a valid hostname")
    return normalized


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 320 or not _EMAIL.fullmatch(normalized):
        raise ValueError("professional_email must be valid")
    return normalized


@dataclass(frozen=True, slots=True)
class BriefRequestEvent:
    event_id: BriefRequestEventId
    request_id: BriefRequestId
    kind: BriefRequestEventKind
    occurred_at: datetime
    actor: str
    payload: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not _ID.fullmatch(str(self.event_id)):
            raise ValueError("event_id must use a bounded stable identifier")
        if not _ID.fullmatch(str(self.request_id)):
            raise ValueError("request_id must use a bounded stable identifier")
        _aware(self.occurred_at, "occurred_at")
        _text(self.actor, "actor", 200)
        keys = [key for key, _ in self.payload]
        if len(keys) != len(set(keys)):
            raise ValueError("brief event payload keys must be unique")
        for key, value in self.payload:
            _text(key, "payload key", 80)
            if not isinstance(value, str) or len(value) > 2000:
                raise ValueError("payload value must be bounded text")


@dataclass(frozen=True, slots=True)
class BriefRequestSnapshot:
    request_id: BriefRequestId
    company_name: str
    company_domain: str
    professional_email: str
    purpose: str
    request_notice_version: str
    requested_at: datetime
    updated_at: datetime
    review_state: BriefReviewState
    coverage_state: CoverageState
    consent_state: NewsletterConsentState
    newsletter_notice_version: str | None = None
    consented_at: datetime | None = None
    subject_reference: str | None = None
    review_reason: str | None = None

    @property
    def delivery_eligible(self) -> bool:
        return (
            self.review_state is BriefReviewState.ACCEPTED
            and self.coverage_state is CoverageState.SUFFICIENT
            and self.consent_state is NewsletterConsentState.GRANTED
        )
