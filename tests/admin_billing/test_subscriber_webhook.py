from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime

from pipeline.admin_billing.stripe_webhook import StripeWebhookVerifier
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore


class _Reconciler:
    def __init__(self) -> None:
        self.session_refs: list[str] = []

    def reconcile_session(self, session_ref: str, *, now: datetime):
        self.session_refs.append(session_ref)
        from application.admin_billing.subscriber_reconciliation import (
            ReconciliationDisposition,
        )

        return ReconciliationDisposition.UNKNOWN

    def reconcile_subscription(self, subscription_ref: str, *, now: datetime):
        from application.admin_billing.subscriber_reconciliation import (
            ReconciliationDisposition,
        )

        return ReconciliationDisposition.UNKNOWN


def _signature(body: bytes, timestamp: int, secret: str) -> str:
    signed = str(timestamp).encode() + b"." + body
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_signed_direct_account_event_is_deduplicated_without_persisting_raw_body(tmp_path):
    secret = "whsec_offline_fixture"
    now = datetime.now(UTC).replace(microsecond=0)
    event = {
        "id": "evt_fixture_1",
        "type": "checkout.session.completed",
        "created": int(now.timestamp()),
        "livemode": True,
        "data": {"object": {"id": "cs_fixture_1", "metadata": {"private": "do-not-store"}}},
    }
    body = json.dumps(event, separators=(",", ":")).encode()
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber.sqlite3")
    reconciler = _Reconciler()
    verifier = StripeWebhookVerifier(
        signing_secret=secret,
        account_ref="acct_fixture",
        environment_ref="stripe-live-fixture",
        live_mode=True,
        store=store,
        reconciler=reconciler,  # type: ignore[arg-type]
    )

    receipt = verifier.handle_signed_webhook(
        body, _signature(body, int(now.timestamp()), secret), now
    )
    replay = verifier.handle_signed_webhook(
        body, _signature(body, int(now.timestamp()), secret), now
    )

    assert receipt.accepted is True
    assert receipt.disposition == "UNKNOWN"
    assert replay.disposition == "EXACT_REPLAY"
    assert reconciler.session_refs == ["cs_fixture_1"]
    with store._connect() as connection:
        persisted = " ".join(
            str(row[0])
            for row in connection.execute(
                "SELECT safe_refs_json, payload_fingerprint FROM subscriber_webhook_inbox"
            )
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM subscriber_webhook_inbox").fetchone()[0] == 1
        )
    assert "do-not-store" not in persisted


def test_webhook_signature_and_environment_fail_before_inbox_acceptance(tmp_path):
    secret = "whsec_offline_fixture"
    now = datetime.now(UTC).replace(microsecond=0)
    event = {
        "id": "evt_fixture_2",
        "type": "invoice.paid",
        "created": int(now.timestamp()),
        "livemode": False,
        "data": {"object": {"id": "in_fixture"}},
    }
    body = json.dumps(event, separators=(",", ":")).encode()
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber.sqlite3")
    verifier = StripeWebhookVerifier(
        signing_secret=secret,
        account_ref="acct_fixture",
        environment_ref="stripe-live-fixture",
        live_mode=True,
        store=store,
        reconciler=_Reconciler(),  # type: ignore[arg-type]
    )

    wrong_sig = verifier.handle_signed_webhook(body, "t=1,v1=bad", now)
    wrong_mode = verifier.handle_signed_webhook(
        body, _signature(body, int(now.timestamp()), secret), now
    )

    assert wrong_sig.disposition == "INVALID_SIGNATURE"
    assert wrong_mode.disposition == "EVENT_SCOPE_MISMATCH"
    with store._connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM subscriber_webhook_inbox").fetchone()[0] == 0
        )
