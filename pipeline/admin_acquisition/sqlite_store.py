"""Append-only AO-15 acquisition event store."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_acquisition import (
    AnalyticsEvent,
    AnalyticsEventId,
    AnalyticsEventKind,
    AnonymousSessionRef,
    BriefRequestEvent,
    BriefRequestEventId,
    BriefRequestEventKind,
    BriefRequestId,
    MarketingEvent,
    MarketingEventId,
    MarketingEventKind,
    MarketingIdentityClass,
    TrafficClassification,
)


class AcquisitionStoreConflict(ValueError):
    pass


class SqliteAdminAcquisitionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS admin_acquisition_events ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "event_id TEXT NOT NULL UNIQUE,"
                "request_id TEXT NOT NULL,"
                "kind TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL,"
                "actor TEXT NOT NULL,"
                "fingerprint TEXT NOT NULL,"
                "payload_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_acquisition_request "
                "ON admin_acquisition_events(request_id, sequence)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS admin_marketing_events ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "event_id TEXT NOT NULL UNIQUE,"
                "session_ref TEXT NOT NULL,"
                "kind TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL,"
                "received_at TEXT NOT NULL,"
                "fingerprint TEXT NOT NULL,"
                "payload_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_marketing_session "
                "ON admin_marketing_events(session_ref, sequence)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS admin_analytics_events ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "event_id TEXT NOT NULL UNIQUE,"
                "kind TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL,"
                "fingerprint TEXT NOT NULL,"
                "payload_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_analytics_kind "
                "ON admin_analytics_events(kind, sequence)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(event: BriefRequestEvent) -> str:
        values = {
            "event_id": str(event.event_id),
            "request_id": str(event.request_id),
            "kind": event.kind.value,
            "occurred_at": event.occurred_at.isoformat(),
            "actor": event.actor,
            "payload": list(event.payload),
        }
        return json.dumps(values, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _fingerprint(payload: str) -> str:
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def append_event(self, event: BriefRequestEvent) -> bool:
        payload = self._payload(event)
        fingerprint = self._fingerprint(payload)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT fingerprint, payload_json FROM admin_acquisition_events WHERE event_id = ?",
                (str(event.event_id),),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["fingerprint"]) == fingerprint
                    and str(existing["payload_json"]) == payload
                ):
                    return False
                raise AcquisitionStoreConflict(
                    "brief request event id reused with different content"
                )
            connection.execute(
                "INSERT INTO admin_acquisition_events("
                "event_id, request_id, kind, occurred_at, actor, fingerprint, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    str(event.request_id),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.actor,
                    fingerprint,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _event(row: sqlite3.Row) -> BriefRequestEvent:
        payload = json.loads(str(row["payload_json"]))
        return BriefRequestEvent(
            event_id=BriefRequestEventId(payload["event_id"]),
            request_id=BriefRequestId(payload["request_id"]),
            kind=BriefRequestEventKind(payload["kind"]),
            occurred_at=datetime.fromisoformat(payload["occurred_at"]),
            actor=payload["actor"],
            payload=tuple((str(key), str(value)) for key, value in payload["payload"]),
        )

    def events_for_request(self, request_id: str) -> tuple[BriefRequestEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_acquisition_events WHERE request_id = ? ORDER BY sequence",
                (request_id,),
            ).fetchall()
        return tuple(self._event(row) for row in rows)

    def all_events(self) -> tuple[BriefRequestEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_acquisition_events ORDER BY sequence"
            ).fetchall()
        return tuple(self._event(row) for row in rows)

    @staticmethod
    def _marketing_payload(event: MarketingEvent) -> str:
        values = {
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
            "received_at": event.received_at.isoformat(),
            "kind": event.kind.value,
            "identity_class": event.identity_class.value,
            "session_ref": str(event.session_ref),
            "surface": event.surface,
            "locale": event.locale,
            "path": event.path,
            "request_id": event.request_id,
            "chapter": event.chapter,
            "cta": event.cta,
            "referrer_origin": event.referrer_origin,
            "utm_source": event.utm_source,
            "utm_medium": event.utm_medium,
            "utm_campaign": event.utm_campaign,
            "utm_content": event.utm_content,
            "utm_term": event.utm_term,
            "attribution_model": event.attribution_model.value,
        }
        return json.dumps(values, sort_keys=True, separators=(",", ":"))

    def append_marketing_event(self, event: MarketingEvent) -> bool:
        payload = self._marketing_payload(event)
        fingerprint_values = json.loads(payload)
        fingerprint_values.pop("received_at", None)
        fingerprint_payload = json.dumps(fingerprint_values, sort_keys=True, separators=(",", ":"))
        fingerprint = self._fingerprint(fingerprint_payload)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT fingerprint FROM admin_marketing_events WHERE event_id = ?",
                (str(event.event_id),),
            ).fetchone()
            if existing is not None:
                if str(existing["fingerprint"]) == fingerprint:
                    return False
                raise AcquisitionStoreConflict("marketing event id reused with different content")
            connection.execute(
                "INSERT INTO admin_marketing_events("
                "event_id, session_ref, kind, occurred_at, received_at, fingerprint, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    str(event.session_ref),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.received_at.isoformat(),
                    fingerprint,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _marketing_event(row: sqlite3.Row) -> MarketingEvent:
        from domain.admin_acquisition import AttributionModelVersion

        payload = json.loads(str(row["payload_json"]))
        return MarketingEvent(
            event_id=MarketingEventId(payload["event_id"]),
            occurred_at=datetime.fromisoformat(payload["occurred_at"]),
            received_at=datetime.fromisoformat(payload["received_at"]),
            kind=MarketingEventKind(payload["kind"]),
            identity_class=MarketingIdentityClass(payload["identity_class"]),
            session_ref=AnonymousSessionRef(payload["session_ref"]),
            surface=payload["surface"],
            locale=payload["locale"],
            path=payload["path"],
            request_id=payload.get("request_id"),
            chapter=payload.get("chapter"),
            cta=payload.get("cta"),
            referrer_origin=payload.get("referrer_origin"),
            utm_source=payload.get("utm_source"),
            utm_medium=payload.get("utm_medium"),
            utm_campaign=payload.get("utm_campaign"),
            utm_content=payload.get("utm_content"),
            utm_term=payload.get("utm_term"),
            attribution_model=AttributionModelVersion(payload["attribution_model"]),
        )

    def marketing_events(self) -> tuple[MarketingEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_marketing_events ORDER BY sequence"
            ).fetchall()
        return tuple(self._marketing_event(row) for row in rows)

    def marketing_events_for_session(self, session_ref: str) -> tuple[MarketingEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_marketing_events WHERE session_ref = ? ORDER BY sequence",
                (session_ref,),
            ).fetchall()
        return tuple(self._marketing_event(row) for row in rows)

    @staticmethod
    def _analytics_payload(event: AnalyticsEvent) -> str:
        values = {
            "event_id": str(event.event_id),
            "kind": event.kind.value,
            "occurred_at": event.occurred_at.isoformat(),
            "classification": event.classification.value,
            "session_ref": event.session_ref,
            "request_id": event.request_id,
            "issue_id": event.issue_id,
            "account_id": event.account_id,
            "xeed_id": event.xeed_id,
            "evidence_ref": event.evidence_ref,
            "advisory_ref": event.advisory_ref,
            "amount_minor": event.amount_minor,
            "currency": event.currency,
            "definition_version": event.definition_version,
        }
        return json.dumps(values, sort_keys=True, separators=(",", ":"))

    def append_analytics_event(self, event: AnalyticsEvent) -> bool:
        payload = self._analytics_payload(event)
        fingerprint = self._fingerprint(payload)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT fingerprint, payload_json FROM admin_analytics_events WHERE event_id = ?",
                (str(event.event_id),),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["fingerprint"]) == fingerprint
                    and str(existing["payload_json"]) == payload
                ):
                    return False
                raise AcquisitionStoreConflict("analytics event id reused with different content")
            connection.execute(
                "INSERT INTO admin_analytics_events("
                "event_id, kind, occurred_at, fingerprint, payload_json"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    fingerprint,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _analytics_event(row: sqlite3.Row) -> AnalyticsEvent:
        payload = json.loads(str(row["payload_json"]))
        return AnalyticsEvent(
            event_id=AnalyticsEventId(payload["event_id"]),
            kind=AnalyticsEventKind(payload["kind"]),
            occurred_at=datetime.fromisoformat(payload["occurred_at"]),
            classification=TrafficClassification(payload["classification"]),
            session_ref=payload.get("session_ref"),
            request_id=payload.get("request_id"),
            issue_id=payload.get("issue_id"),
            account_id=payload.get("account_id"),
            xeed_id=payload.get("xeed_id"),
            evidence_ref=payload.get("evidence_ref"),
            advisory_ref=payload.get("advisory_ref"),
            amount_minor=payload.get("amount_minor"),
            currency=payload.get("currency"),
            definition_version=payload["definition_version"],
        )

    def analytics_events(self) -> tuple[AnalyticsEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_analytics_events ORDER BY sequence"
            ).fetchall()
        return tuple(self._analytics_event(row) for row in rows)
