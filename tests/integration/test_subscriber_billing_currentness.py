"""Billing currentness: freshness follows AXIGNAL's verification, not the provider's last change.

A paid subscription can stay unchanged at the provider for weeks and remain valid. Its
capacity is CURRENT only while a recent verification (a provider read that re-validates
items, payment, lifecycle and paid-through) confirms it; time alone never refreshes it,
and an old, ambiguous or contradictory read never does either.

Provider, OIDC and catalogue are the controlled ports of the paid journey; identity,
portfolio, entitlements, reconciliation and SQLite stores are the real composition.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from application.admin_billing.subscriber_billing import PaymentState, SubscriptionLifecycle
from application.admin_billing.subscriber_checkout import BillingProjection
from application.admin_billing.subscriber_reconciliation import _verification_time
from domain.admin_billing.checkout_binding import CurrentSubscriptionItems, SnapshotCurrentness
from domain.evidence.epistemics import Currentness
from domain.identity import TenantId
from pipeline.admin_billing.subscriber_store import SubscriberStoreConflict
from tests.integration.test_subscriber_paid_journey import (  # noqa: F401
    _signup,
    paid_journey,
)


class _Paid:
    """One paying subscriber, observed through the HTTP facade and its stores."""

    def __init__(self, journey: Any, subject: str = "subject:currentness") -> None:
        _data, self.clock, self.provider, _catalogue, build_facade, self.stores = journey
        self.facade = build_facade()
        self.subject = subject
        self.sign_in()
        self.provider_reads: list[datetime] = []
        self.requests = 0
        original = self.provider.read_current_subscription

        def counted(projection: BillingProjection) -> Any:
            self.provider_reads.append(self.clock.now())
            return original(projection)

        self.provider.read_current_subscription = counted
        bought = self.post({"action": "purchase", "desiredOrganizationTotal": 1})
        assert bought["state"] == "PENDING_PURCHASE", bought
        self.provider.mark_paid()
        assert self.post({"action": "refresh_purchase"})["state"] == "REFRESHED"
        assert self.entitlement().currentness is Currentness.CURRENT
        self.state_at = self.projection().provider_state_at
        self.provider_reads.clear()

    def sign_in(self) -> None:
        """Sessions expire on their own clock; billing currentness is independent of them."""
        token, self.tenant = _signup(self.facade, self.subject)
        self.write = {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"}
        self.read = {"Authorization": self.write["Authorization"]}

    def post(self, body: dict[str, object]) -> dict[str, Any]:
        self.clock.advance()
        self.requests += 1
        ref = f"{body['action']}-{self.requests}"
        response = self.facade.handle(
            "POST", "/subscriber/portfolio", self.write, {"requestRef": ref, **body}
        )
        assert response.status == 200, response.body
        return dict(response.body)

    def portfolio(self) -> dict[str, Any]:
        response = self.facade.handle("GET", "/subscriber/portfolio", self.read)
        assert response.status == 200, response.body
        return dict(response.body)

    def entitlement(self) -> Any:
        """The entitlement as the policy reads it, without triggering a provider read."""
        return self.facade.workflow._entitlements.snapshot(self.tenant)

    def projection(self) -> BillingProjection:
        projection = self.stores[-1].get_billing_projection(self.tenant)
        assert projection is not None
        return projection

    def wait(self, delta: timedelta) -> None:
        self.clock.value += delta
        self.sign_in()


def test_unchanged_paid_subscription_is_reverified_at_5_minutes_10_minutes_and_24_hours(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))

    # Within the verification window: current, with no provider read.
    paid.wait(timedelta(minutes=4, seconds=50))
    assert paid.entitlement().currentness is Currentness.CURRENT
    assert paid.provider_reads == []

    # Past the window without a new verification: not current, and no capacity assumed.
    paid.wait(timedelta(seconds=20))
    stale = paid.entitlement()
    assert stale.currentness is Currentness.STALE and stale.capacity is None

    for elapsed in (timedelta(minutes=10), timedelta(hours=24)):
        paid.wait(elapsed)
        assert paid.entitlement().currentness is Currentness.STALE
        reads = len(paid.provider_reads)
        portfolio = paid.portfolio()
        # Recovered only by reading the provider again, never by time or a longer TTL.
        assert len(paid.provider_reads) == reads + 1
        assert portfolio["capacity"] == 1 and portfolio["capacityCurrentness"] == "CURRENT"
        projection = paid.projection()
        # The provider state did not change; only AXIGNAL's verification moved forward.
        assert projection.provider_state_at == paid.state_at
        assert projection.verified_at == paid.provider_reads[-1]

    # The subscriber can use the paid capacity a day later.
    added = paid.post({"action": "add", "locator": "Journey Example SLU"})
    assert added["state"] == "CREATED", added


def test_refresh_purchase_recovers_a_stale_projection_by_consulting_the_provider(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    paid.wait(timedelta(minutes=10))
    assert paid.entitlement().currentness is Currentness.STALE

    refreshed = paid.post({"action": "refresh_purchase"})

    assert refreshed["state"] == "REFRESHED", refreshed
    assert len(paid.provider_reads) == 1
    assert paid.entitlement().currentness is Currentness.CURRENT
    assert paid.entitlement().capacity == 1


def test_expired_paid_period_is_never_refreshed_into_capacity(request: pytest.FixtureRequest):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    # The provider still reports the old period: nothing was renewed or paid.
    paid.wait(timedelta(days=31))

    portfolio = paid.portfolio()

    assert len(paid.provider_reads) == 1
    assert portfolio["capacity"] is None and portfolio["capacityCurrentness"] != "CURRENT"
    assert paid.post({"action": "add", "locator": "Journey Example SLU"})["state"] == (
        "CAPACITY_UNKNOWN"
    )


def test_contradictory_provider_read_for_the_same_state_does_not_refresh(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    paid.wait(timedelta(minutes=10))
    # Same provider state time, different items: an ambiguous/contradictory read.
    paid.provider.current_capacity = 2

    portfolio = paid.portfolio()

    assert len(paid.provider_reads) == 1
    assert portfolio["capacity"] is None and portfolio["capacityCurrentness"] != "CURRENT"
    assert paid.projection().effective_capacity in (1, None)
    assert paid.entitlement().currentness is not Currentness.CURRENT


def test_reverification_is_bounded_per_tenant_and_a_provider_failure_keeps_capacity_unconfirmed(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    paid.wait(timedelta(minutes=10))
    calls = 0
    original = paid.provider.read_current_subscription

    def failing(projection: BillingProjection) -> Any:
        nonlocal calls
        calls += 1
        raise RuntimeError("provider unavailable")

    paid.provider.read_current_subscription = failing
    first = paid.portfolio()
    second = paid.portfolio()

    assert calls == 1  # bounded: one provider read per Tenant per window
    for portfolio in (first, second):
        assert portfolio["capacity"] is None and portfolio["capacityCurrentness"] == "STALE"

    paid.provider.read_current_subscription = original
    paid.wait(timedelta(seconds=61))
    assert paid.portfolio()["capacityCurrentness"] == "CURRENT"


def test_an_older_verification_never_replaces_a_newer_one_and_contradictions_conflict(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    store = paid.stores[-1]
    current = paid.projection()
    assert current.verified_at is not None

    store.commit_billing_projection(replace(current, verified_at=paid.state_at))
    assert paid.projection().verified_at == current.verified_at

    newer = current.verified_at + timedelta(minutes=3)
    store.commit_billing_projection(replace(current, verified_at=newer))
    assert paid.projection().verified_at == newer

    with pytest.raises(SubscriberStoreConflict):
        store.commit_billing_projection(
            replace(current, effective_capacity=2, verified_at=newer + timedelta(minutes=1))
        )
    assert paid.projection().effective_capacity == 1


def test_projection_written_before_verification_time_keeps_the_provider_state_rule(
    request: pytest.FixtureRequest,
):
    paid = _Paid(request.getfixturevalue("paid_journey"))
    store = paid.stores[-1]
    with sqlite3.connect(store.path) as database:
        (payload,) = database.execute(
            "SELECT payload_json FROM subscriber_billing_projection WHERE tenant_id = ?",
            (str(paid.tenant),),
        ).fetchone()
        legacy = json.loads(payload)
        legacy.pop("verified_at")
        database.execute(
            "UPDATE subscriber_billing_projection SET payload_json = ? WHERE tenant_id = ?",
            (json.dumps(legacy, sort_keys=True, separators=(",", ":")), str(paid.tenant)),
        )
    assert paid.projection().verified_at is None

    paid.wait(timedelta(minutes=6))
    assert paid.entitlement().currentness is Currentness.STALE

    assert paid.portfolio()["capacityCurrentness"] == "CURRENT"
    assert paid.projection().verified_at is not None


def _snapshot(state_at: datetime, retrieved_at: datetime) -> CurrentSubscriptionItems:
    return CurrentSubscriptionItems(
        evidence_ref="evidence:1",
        customer_ref="customer:1",
        subscription_ref="subscription:1",
        environment_ref="environment:1",
        provider_state_ref="state:1",
        provider_state_at=state_at,
        retrieved_at=retrieved_at,
        currentness=SnapshotCurrentness.CURRENT,
        enumeration_complete=True,
        has_more=False,
        items=(),
    )


def test_a_retrieval_that_precedes_its_state_or_lies_in_the_future_is_no_verification():
    now = datetime(2026, 10, 11, 12, tzinfo=UTC)
    state = now - timedelta(days=20)
    assert _verification_time(_snapshot(state, now - timedelta(seconds=1)), now=now) == (
        now - timedelta(seconds=1)
    )
    assert _verification_time(_snapshot(state, state - timedelta(seconds=1)), now=now) is None
    assert _verification_time(_snapshot(state, now + timedelta(seconds=1)), now=now) is None


def test_a_projection_cannot_claim_a_verification_before_its_provider_state():
    state = datetime(2026, 10, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="verification cannot precede"):
        BillingProjection(
            tenant_id=TenantId("tenant:1"),
            customer_ref="customer:1",
            subscription_ref="subscription:1",
            checkout_session_ref="session:1",
            environment_ref="environment:1",
            additional_item_ref=None,
            effective_capacity=1,
            payment_state=PaymentState.VERIFIED,
            lifecycle=SubscriptionLifecycle.ELIGIBLE,
            binding=None,
            provider_state_ref="state:1",
            provider_state_at=state,
            paid_through=state + timedelta(days=30),
            verified_at=state - timedelta(seconds=1),
        )
