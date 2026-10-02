"""AO-12 first-party marketing and acquisition event domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

MarketingEventId = NewType("MarketingEventId", str)
AnonymousSessionRef = NewType("AnonymousSessionRef", str)

_ID = re.compile(r"^[a-z][a-z0-9:_-]{2,159}$")
_TOKEN = re.compile(r"^[A-Za-z0-9._~:-]{1,200}$")


class MarketingEventKind(StrEnum):
    LANDING_VIEWED = "LANDING_VIEWED"
    CHAPTER_VIEWED = "CHAPTER_VIEWED"
    CTA_ACTIVATED = "CTA_ACTIVATED"
    WEEKLY_BRIEF_OPENED = "WEEKLY_BRIEF_OPENED"
    WEEKLY_BRIEF_REQUESTED = "WEEKLY_BRIEF_REQUESTED"


class MarketingIdentityClass(StrEnum):
    ANONYMOUS_SESSION = "ANONYMOUS_SESSION"
    BRIEF_REQUEST = "BRIEF_REQUEST"


class AttributionModelVersion(StrEnum):
    OBSERVED_TOUCH_V1 = "OBSERVED_TOUCH_V1"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _bounded(value: str | None, name: str, maximum: int) -> None:
    if value is not None and len(value) > maximum:
        raise ValueError(f"{name} must be at most {maximum} characters")


def normalize_campaign_token(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if not _TOKEN.fullmatch(normalized):
        raise ValueError("campaign attribution token is invalid")
    return normalized


@dataclass(frozen=True, slots=True)
class MarketingEvent:
    event_id: MarketingEventId
    occurred_at: datetime
    received_at: datetime
    kind: MarketingEventKind
    identity_class: MarketingIdentityClass
    session_ref: AnonymousSessionRef
    surface: str
    locale: str
    path: str
    request_id: str | None = None
    chapter: int | None = None
    cta: str | None = None
    referrer_origin: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    attribution_model: AttributionModelVersion = AttributionModelVersion.OBSERVED_TOUCH_V1

    def __post_init__(self) -> None:
        if not _ID.fullmatch(str(self.event_id)):
            raise ValueError("event_id must use a bounded stable identifier")
        if not _ID.fullmatch(str(self.session_ref)):
            raise ValueError("session_ref must use a bounded opaque identifier")
        _aware(self.occurred_at, "occurred_at")
        _aware(self.received_at, "received_at")
        if self.occurred_at > self.received_at:
            raise ValueError("marketing event cannot occur after receipt")
        if self.received_at.timestamp() - self.occurred_at.timestamp() > 86_400:
            raise ValueError("marketing event is too old")
        if self.identity_class is MarketingIdentityClass.BRIEF_REQUEST and not self.request_id:
            raise ValueError("BRIEF_REQUEST event requires request_id")
        if self.identity_class is MarketingIdentityClass.ANONYMOUS_SESSION and self.request_id:
            raise ValueError("anonymous marketing event cannot carry request identity")
        if self.request_id is not None and not _ID.fullmatch(self.request_id):
            raise ValueError("request_id must use a bounded stable identifier")
        if self.chapter is not None and not 1 <= self.chapter <= 15:
            raise ValueError("chapter must be between 1 and 15")
        _bounded(self.surface, "surface", 80)
        _bounded(self.locale, "locale", 12)
        _bounded(self.path, "path", 300)
        _bounded(self.cta, "cta", 120)
        _bounded(self.referrer_origin, "referrer_origin", 240)
        for name in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
            normalize_campaign_token(getattr(self, name))


@dataclass(frozen=True, slots=True)
class MarketingAttributionSummary:
    model_version: AttributionModelVersion
    event_count: int
    anonymous_session_count: int
    linked_request_count: int
    source_counts: tuple[tuple[str, int], ...]
    campaign_counts: tuple[tuple[str, int], ...]
