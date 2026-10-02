"""AO-12 first-party marketing event ingestion and attribution summaries."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit

from domain.admin_acquisition import (
    AnonymousSessionRef,
    AttributionModelVersion,
    MarketingAttributionSummary,
    MarketingEvent,
    MarketingEventId,
    MarketingEventKind,
    MarketingIdentityClass,
    normalize_campaign_token,
)


class MarketingEventStore(Protocol):
    def append_marketing_event(self, event: MarketingEvent) -> bool: ...
    def marketing_events(self) -> tuple[MarketingEvent, ...]: ...
    def marketing_events_for_session(self, session_ref: str) -> tuple[MarketingEvent, ...]: ...


def _origin_only(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname.lower()}{port}"


def _path_only(value: str) -> str:
    parsed = urlsplit(value)
    path = parsed.path or "/"
    if not path.startswith("/") or len(path) > 300:
        raise ValueError("marketing path is invalid")
    return path


class PublicMarketingEventService:
    def __init__(self, store: MarketingEventStore) -> None:
        self._store = store

    def ingest(
        self,
        *,
        event_id: str,
        session_ref: str,
        kind: MarketingEventKind,
        occurred_at: datetime,
        received_at: datetime,
        surface: str,
        locale: str,
        path: str,
        chapter: int | None = None,
        cta: str | None = None,
        referrer: str | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        utm_content: str | None = None,
        utm_term: str | None = None,
    ) -> bool:
        event = MarketingEvent(
            event_id=MarketingEventId(event_id),
            occurred_at=occurred_at,
            received_at=received_at,
            kind=kind,
            identity_class=MarketingIdentityClass.ANONYMOUS_SESSION,
            session_ref=AnonymousSessionRef(session_ref),
            surface=surface.strip(),
            locale=locale.strip().lower(),
            path=_path_only(path),
            chapter=chapter,
            cta=cta.strip() if cta and cta.strip() else None,
            referrer_origin=_origin_only(referrer),
            utm_source=normalize_campaign_token(utm_source),
            utm_medium=normalize_campaign_token(utm_medium),
            utm_campaign=normalize_campaign_token(utm_campaign),
            utm_content=normalize_campaign_token(utm_content),
            utm_term=normalize_campaign_token(utm_term),
        )
        return self._store.append_marketing_event(event)

    def link_brief_request(
        self,
        *,
        event_id: str,
        session_ref: str,
        request_id: str,
        occurred_at: datetime,
        received_at: datetime,
        surface: str,
        locale: str,
        path: str,
    ) -> bool:
        event = MarketingEvent(
            event_id=MarketingEventId(event_id),
            occurred_at=occurred_at,
            received_at=received_at,
            kind=MarketingEventKind.WEEKLY_BRIEF_REQUESTED,
            identity_class=MarketingIdentityClass.BRIEF_REQUEST,
            session_ref=AnonymousSessionRef(session_ref),
            request_id=request_id,
            surface=surface.strip(),
            locale=locale.strip().lower(),
            path=_path_only(path),
        )
        return self._store.append_marketing_event(event)


def summarize_marketing(events: tuple[MarketingEvent, ...]) -> MarketingAttributionSummary:
    sources = Counter(event.utm_source or "UNATTRIBUTED" for event in events)
    campaigns = Counter(event.utm_campaign or "UNATTRIBUTED" for event in events)
    return MarketingAttributionSummary(
        model_version=AttributionModelVersion.OBSERVED_TOUCH_V1,
        event_count=len(events),
        anonymous_session_count=len({str(event.session_ref) for event in events}),
        linked_request_count=len(
            {
                event.request_id
                for event in events
                if event.request_id is not None
                and event.kind is MarketingEventKind.WEEKLY_BRIEF_REQUESTED
            }
        ),
        source_counts=tuple(sorted(sources.items())),
        campaign_counts=tuple(sorted(campaigns.items())),
    )
