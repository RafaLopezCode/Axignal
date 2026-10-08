"""Bounded contact/privacy requests and truthful delivery receipts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, Protocol

RequestKind = Literal["CONTACT", "PRIVACY_RIGHTS"]
DeliveryStatus = Literal["UNAVAILABLE", "PENDING", "DELIVERED", "FAILED"]
PRIVACY_CATEGORIES = frozenset(
    {"access", "rectification", "erasure", "restriction", "objection", "portability", "other"}
)


@dataclass(frozen=True)
class PublicRequest:
    request_ref: str
    kind: RequestKind
    category: str
    name: str
    email: str
    subject: str
    message: str
    locale: str
    notice_version: str

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def validate_request(payload: object, *, kind: RequestKind) -> PublicRequest:
    if not isinstance(payload, dict) or set(payload) != {
        "requestRef",
        "category",
        "name",
        "email",
        "subject",
        "message",
        "locale",
        "noticeVersion",
    }:
        raise ValueError("INVALID_REQUEST")
    limits = {
        "requestRef": 64,
        "category": 32,
        "name": 100,
        "email": 254,
        "subject": 120,
        "message": 3000,
        "locale": 2,
        "noticeVersion": 64,
    }
    values: dict[str, str] = {}
    for field, limit in limits.items():
        value = payload[field]
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
            raise ValueError("INVALID_REQUEST")
        if any(ord(char) < 32 and (field != "message" or char not in "\n\t") for char in value):
            raise ValueError("INVALID_REQUEST")
        values[field] = value.strip()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{16,64}", values["requestRef"]):
        raise ValueError("INVALID_REQUEST")
    if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+", values["email"]):
        raise ValueError("INVALID_EMAIL")
    if values["locale"] not in {"es", "en", "fr", "de", "it", "pt"}:
        raise ValueError("INVALID_LOCALE")
    if len(values["message"]) < 15:
        raise ValueError("INVALID_MESSAGE")
    if kind == "PRIVACY_RIGHTS" and values["category"] not in PRIVACY_CATEGORIES:
        raise ValueError("INVALID_CATEGORY")
    if kind == "CONTACT" and values["category"] != "contact":
        raise ValueError("INVALID_CATEGORY")
    return PublicRequest(
        values["requestRef"],
        kind,
        values["category"],
        values["name"],
        values["email"],
        values["subject"],
        values["message"],
        values["locale"],
        values["noticeVersion"],
    )


@dataclass(frozen=True)
class RequestReceipt:
    request_id: str
    created_at: str
    kind: RequestKind
    delivery_status: DeliveryStatus

    def public(self) -> dict[str, object]:
        # Public contract intentionally reveals only that AXIGNAL received the
        # request durably. Provider delivery state remains private operations data.
        return {"status": "received", "requestId": self.request_id}


class PublicRequestStore(Protocol):
    def receive(self, request: PublicRequest, *, now: datetime) -> tuple[RequestReceipt, bool]: ...
    def complete(self, receipt: RequestReceipt, *, status: DeliveryStatus) -> RequestReceipt: ...


class ContactDeliveryPort(Protocol):
    def send(self, request: PublicRequest, *, receipt: RequestReceipt) -> None: ...


class PublicRequestService:
    def __init__(self, store: PublicRequestStore, delivery: ContactDeliveryPort | None = None):
        self.store = store
        self.delivery = delivery

    def submit(self, request: PublicRequest, *, now: datetime) -> RequestReceipt:
        receipt, inserted = self.store.receive(request, now=now)
        if not inserted:
            return receipt
        if self.delivery is None:
            return self.store.complete(receipt, status="UNAVAILABLE")
        try:
            self.delivery.send(request, receipt=receipt)
        except PermissionError:
            return self.store.complete(receipt, status="UNAVAILABLE")
        except (OSError, RuntimeError, ValueError):
            return self.store.complete(receipt, status="FAILED")
        return self.store.complete(receipt, status="DELIVERED")
