"""Signature-verified Stripe webhook inbox and reconciliation trigger."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from application.admin_billing.subscriber_reconciliation import (
    ReconciliationDisposition,
    SubscriberPurchaseReconciler,
)
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore


@dataclass(frozen=True, slots=True)
class WebhookReceipt:
    accepted: bool
    disposition: str
    event_ref: str | None


class StripeWebhookVerifier:
    """Verify exact raw bytes and account/environment before durable dedupe."""

    def __init__(
        self,
        *,
        signing_secret: str,
        account_ref: str,
        environment_ref: str,
        live_mode: bool,
        store: SqliteSubscriberBillingStore,
        reconciler: SubscriberPurchaseReconciler,
        tolerance_seconds: int = 300,
        maximum_body_bytes: int = 1_000_000,
    ) -> None:
        if not signing_secret or not account_ref.startswith("acct_") or not environment_ref:
            raise ValueError("webhook secret, account and environment are required")
        if type(tolerance_seconds) is not int or not 30 <= tolerance_seconds <= 900:
            raise ValueError("signature tolerance must be 30 to 900 seconds")
        self._secret = signing_secret.encode("utf-8")
        self._account_ref = account_ref
        self._environment_ref = environment_ref
        self._live_mode = live_mode
        self._store = store
        self._reconciler = reconciler
        self._tolerance = timedelta(seconds=tolerance_seconds)
        self._max_bytes = maximum_body_bytes

    def handle_signed_webhook(
        self, raw_body: bytes, stripe_signature: str, received_at: datetime
    ) -> WebhookReceipt:
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            return WebhookReceipt(False, "INVALID_RECEIVED_AT", None)
        if not isinstance(raw_body, bytes) or not 0 < len(raw_body) <= self._max_bytes:
            return WebhookReceipt(False, "INVALID_BODY_SIZE", None)
        timestamp = _verify_signature(raw_body, stripe_signature, self._secret)
        if timestamp is None:
            return WebhookReceipt(False, "INVALID_SIGNATURE", None)
        signed_at = datetime.fromtimestamp(timestamp, UTC)
        if abs(received_at.astimezone(UTC) - signed_at) > self._tolerance:
            return WebhookReceipt(False, "SIGNATURE_OUTSIDE_TOLERANCE", None)
        try:
            event = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return WebhookReceipt(False, "INVALID_EVENT_JSON", None)
        if not isinstance(event, dict):
            return WebhookReceipt(False, "INVALID_EVENT", None)
        event_ref = _text(event.get("id"))
        event_type = _text(event.get("type"))
        created = event.get("created")
        account = _text(event.get("account"))
        live_mode = event.get("livemode")
        if (
            event_ref is None
            or event_type is None
            or type(created) is not int
            or (account is not None and account != self._account_ref)
            or live_mode is not self._live_mode
        ):
            return WebhookReceipt(False, "EVENT_SCOPE_MISMATCH", event_ref)
        created_at = datetime.fromtimestamp(created, UTC)
        if created_at > received_at.astimezone(UTC) + timedelta(minutes=5):
            return WebhookReceipt(False, "FUTURE_PROVIDER_EVENT", event_ref)
        data = event.get("data")
        obj = data.get("object") if isinstance(data, dict) else None
        if not isinstance(obj, dict):
            return WebhookReceipt(False, "MISSING_EVENT_OBJECT", event_ref)
        safe_refs = _safe_refs(obj)
        fingerprint = "sha256:" + hashlib.sha256(raw_body).hexdigest()
        disposition = self._store.accept_webhook(
            event_ref=event_ref,
            payload_fingerprint=fingerprint,
            event_type=event_type,
            provider_created_at=created_at,
            received_at=received_at,
            environment_ref=self._environment_ref,
            account_ref=self._account_ref,
            safe_refs=safe_refs,
        )
        if disposition != "STORED":
            return WebhookReceipt(disposition == "EXACT_REPLAY", disposition, event_ref)
        outcome = self._dispatch(event_type, obj, received_at)
        return WebhookReceipt(
            outcome is not ReconciliationDisposition.MISMATCH,
            outcome.value,
            event_ref,
        )

    def _dispatch(
        self, event_type: str, obj: dict[str, object], now: datetime
    ) -> ReconciliationDisposition:
        if event_type.startswith("checkout.session."):
            session_ref = _text(obj.get("id"))
            if session_ref is None:
                return ReconciliationDisposition.UNKNOWN
            return self._reconciler.reconcile_session(session_ref, now=now)
        # Subscription/invoice events only trigger re-reads. Their payload is
        # never used to establish payment, lifecycle or capacity.
        subscription_ref = _text(obj.get("subscription")) or _text(obj.get("id"))
        if subscription_ref is None:
            return ReconciliationDisposition.UNKNOWN
        return self._reconciler.reconcile_subscription(subscription_ref, now=now)


def _verify_signature(raw: bytes, header: str, secret: bytes) -> int | None:
    values: dict[str, list[str]] = {}
    try:
        for fragment in header.split(","):
            key, value = fragment.split("=", 1)
            values.setdefault(key, []).append(value)
        timestamp = values.get("t", [""])[0]
        if not timestamp.isascii() or not timestamp.isdigit():
            return None
        signed = timestamp.encode("ascii") + b"." + raw
        expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
        signatures = values.get("v1", [])
        if not signatures or not any(hmac.compare_digest(expected, item) for item in signatures):
            return None
        return int(timestamp)
    except (ValueError, UnicodeEncodeError):
        return None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _safe_refs(obj: dict[str, object]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for name in ("id", "customer", "subscription", "payment_intent"):
        value = obj.get(name)
        if isinstance(value, str) and value.strip():
            refs[name] = value[:200]
        elif isinstance(value, dict):
            ref = value.get("id")
            if isinstance(ref, str) and ref.strip():
                refs[name] = ref[:200]
    return refs
