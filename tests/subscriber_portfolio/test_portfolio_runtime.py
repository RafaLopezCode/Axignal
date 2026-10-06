from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

import pytest

from application.subscriber_identity.runtime import VerifiedExternalIdentity
from application.subscriber_portfolio.models import (
    AddOrganizationRequest,
    AddStatus,
    CheckoutRequestResult,
    EntitlementSnapshot,
    FocusStatus,
    OrganizationIdentityPending,
    PortfolioError,
    PortfolioFailure,
    PurchaseScopeAuthorization,
)
from application.subscriber_portfolio.service import SubscriberPortfolioService
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore


@dataclass
class MutableClock:
    value: datetime

    def now(self) -> datetime:
        return self.value


class FakeEntitlement:
    def __init__(self, capacity, currentness=Currentness.CURRENT, confirmed_at=None):
        self.capacity = capacity
        self.currentness = currentness
        self.confirmed_at = confirmed_at

    def snapshot(self, tenant_id):
        return EntitlementSnapshot(self.capacity, self.currentness, self.confirmed_at)


class FakePurchaseAuthority:
    def __init__(self):
        self.receipt = None
        self.calls = 0

    def resolve(self, context, now):
        self.calls += 1
        if self.receipt is not None:
            return self.receipt
        return PurchaseScopeAuthorization(
            context.principal_id,
            context.tenant_id,
            "billing-authority-ref",
            "membership-ref",
            now,
        )


class FakeCheckout:
    def __init__(self):
        self.requests = []

    def request_checkout(self, request):
        self.requests.append(request)
        return CheckoutRequestResult(f"checkout:{request.idempotency_key}", True, "CREATED")


class FakeOrganizationResolver:
    def __init__(self):
        self.pending: set[str] = set()
        self.rejected: set[str] = set()
        self.calls = []
        self.canonical_results: list[Organization] = []
        self._cache: dict[str, Organization] = {}

    def resolve(self, locator):
        self.calls.append(locator)
        if locator in self.pending:
            return OrganizationIdentityPending("INSUFFICIENT_IDENTITY_EVIDENCE")
        if locator in self.rejected:
            from application.subscriber_portfolio.models import OrganizationIdentityRejected

            return OrganizationIdentityRejected("NO_CANONICAL_MATCH")
        organization = self._cache.get(locator)
        if organization is None:
            import hashlib

            org_id = hashlib.sha256(locator.encode()).hexdigest()[:16]
            organization = Organization(OrganizationId(f"org-{org_id}"), locator)
            self._cache[locator] = organization
            self.canonical_results.append(organization)
        return organization


class FakeObservationTrigger:
    def __init__(self):
        self.calls = []
        self.lock = Lock()

    def trigger(self, context, focus_id, idempotency_key):
        with self.lock:
            self.calls.append((context, focus_id, idempotency_key))
        return f"run:{idempotency_key}"


class TracedPortfolioStore(SqliteSubscriberPortfolioStore):
    def __init__(self, database_path):
        self.statements: list[str] = []
        super().__init__(database_path)

    def _connect(self):
        connection = super()._connect()
        connection.set_trace_callback(self.statements.append)
        return connection


def _runtime(tmp_path: Path, capacity=1, currentness=Currentness.CURRENT, trace=False):
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    database = tmp_path / "subscriber-runtime.sqlite3"
    identities = SqliteSubscriberIdentityStore(database)
    subscriber = identities.register(
        VerifiedExternalIdentity("https://accounts.google.com", "subject-one"), clock.now()
    )
    context = TrustedRequestContext(subscriber.principal_id, subscriber.tenant_id)
    store_type = TracedPortfolioStore if trace else SqliteSubscriberPortfolioStore
    portfolio = store_type(database)
    entitlement = FakeEntitlement(capacity, currentness, clock.now())
    purchase = FakePurchaseAuthority()
    checkout = FakeCheckout()
    organizations = FakeOrganizationResolver()
    observations = FakeObservationTrigger()
    service = SubscriberPortfolioService(
        portfolio,
        identities,
        entitlement,
        purchase,
        checkout,
        organizations,
        observations,
        clock,
    )
    return (
        clock,
        identities,
        subscriber,
        context,
        portfolio,
        entitlement,
        purchase,
        checkout,
        organizations,
        observations,
        service,
    )


@pytest.mark.parametrize("capacity", [1, 2, 100])
def test_confirmed_capacity_allows_exactly_one_two_or_one_hundred(
    tmp_path: Path, capacity: int
) -> None:
    (
        _clock,
        _identities,
        _subscriber,
        context,
        portfolio,
        _entitlement,
        purchase,
        checkout,
        _organizations,
        observations,
        service,
    ) = _runtime(tmp_path, capacity)
    for index in range(capacity):
        result = service.add(
            context,
            AddOrganizationRequest(f"add-{index}", f"candidate-{index}"),
        )
        assert result.status is AddStatus.CREATED
    assert len(portfolio.list_authorized(context)) == capacity
    blocked = service.add(context, AddOrganizationRequest("excess", "candidate-excess"))
    assert blocked.status is AddStatus.CHECKOUT_REQUIRED
    assert len(portfolio.list_authorized(context)) == capacity
    assert len(checkout.requests) == 1
    assert checkout.requests[0].additional_count == 1
    assert checkout.requests[0].context == context
    assert checkout.requests[0].authorization.principal_id == context.principal_id
    assert checkout.requests[0].desired_capacity == capacity + 1
    assert purchase.calls == 1
    assert len(observations.calls) == capacity


@pytest.mark.parametrize(
    ("capacity", "currentness"),
    [(None, Currentness.UNKNOWN), (3, Currentness.UNKNOWN), (3, Currentness.STALE)],
)
def test_unknown_or_stale_capacity_blocks_without_checkout_or_identity_resolution(
    tmp_path: Path,
    capacity: int | None,
    currentness: Currentness,
) -> None:
    runtime = _runtime(tmp_path / "second", capacity, currentness)
    context = runtime[3]
    result = runtime[10].add(context, AddOrganizationRequest("add-unknown", "locator"))
    assert result.status is AddStatus.CAPACITY_UNKNOWN
    assert runtime[4].list_authorized(context) == ()
    assert runtime[6].calls == 0
    assert runtime[7].requests == []
    assert runtime[8].calls == []


def test_pending_identity_never_creates_focus_or_canonical_economic_truth(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=0)
    context, portfolio, organizations = runtime[3], runtime[4], runtime[8]
    organizations.pending.add("ambiguous-name")
    result = runtime[10].add(context, AddOrganizationRequest("pending-1", "ambiguous-name"))
    assert result.status is AddStatus.IDENTITY_PENDING
    assert portfolio.list_authorized(context) == ()
    with portfolio._connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM subscriber_portfolio_pending").fetchone()[0]
            == 1
        )
        assert connection.execute("SELECT COUNT(*) FROM subscriber_focuses").fetchone()[0] == 0
        assert "faxt" not in {
            str(row[0]).lower()
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    reopened = SqliteSubscriberPortfolioStore(portfolio.path)
    assert reopened.list_authorized(context) == ()


def test_checkout_requires_matching_fresh_billing_authority_receipt(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=0)
    context, purchase, checkout = runtime[3], runtime[6], runtime[7]
    purchase.receipt = PurchaseScopeAuthorization(
        "other-principal", context.tenant_id, "authority", "membership", runtime[0].now()
    )
    # A canonical Organization is needed before capacity checkout is considered.
    result = runtime[10].add(context, AddOrganizationRequest("checkout-1", "canonical-candidate"))
    assert result.status is AddStatus.ACCESS_DENIED
    assert checkout.requests == []

    purchase.receipt = PurchaseScopeAuthorization(
        context.principal_id,
        context.tenant_id,
        "authority",
        "membership",
        runtime[0].now().replace(year=2020),
    )
    result = runtime[10].add(context, AddOrganizationRequest("checkout-2", "another-candidate"))
    assert result.status is AddStatus.ACCESS_DENIED
    assert checkout.requests == []


def test_lifecycle_pause_resume_replace_reobserve_remove_and_restart(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=1)
    clock, context, portfolio, organizations, observations, service = (
        runtime[0],
        runtime[3],
        runtime[4],
        runtime[8],
        runtime[9],
        runtime[10],
    )
    added = service.add(context, AddOrganizationRequest("add-original", "original"))
    assert added.entry is not None
    focus_id = added.entry.focus_id
    service.pause(context, focus_id, "pause-1")
    assert portfolio.list_authorized(context)[0].status is FocusStatus.PAUSED
    blocked = service.add(context, AddOrganizationRequest("add-while-paused", "new"))
    assert blocked.status is AddStatus.CHECKOUT_REQUIRED
    assert len(portfolio.list_authorized(context)) == 1
    service.resume(context, focus_id, "resume-1")
    assert portfolio.list_authorized(context)[0].status is FocusStatus.ACTIVE

    replacement = service.replace(
        context,
        focus_id,
        AddOrganizationRequest("target", "replacement"),
        "replace-1",
    )
    assert replacement.previous_organization_id == organizations._cache["original"].id
    assert replacement.entry.xeed.organization_id == organizations._cache["replacement"].id
    assert observations.calls[-1] == (context, focus_id, "replace-1")
    run = service.reobserve(context, focus_id, "reobserve-1")
    assert run.run_id == "run:reobserve-1"
    assert run.accepted

    organizations.pending.add("not-yet-resolved")
    with pytest.raises(PortfolioError) as error:
        service.replace(
            context,
            focus_id,
            AddOrganizationRequest("pending-target", "not-yet-resolved"),
            "replace-2",
        )
    assert error.value.failure is PortfolioFailure.IDENTITY_PENDING
    unchanged = portfolio.get_authorized(context, focus_id)
    assert unchanged is not None
    assert unchanged.xeed.organization_id == organizations._cache["replacement"].id

    service.remove(context, focus_id, "remove-1")
    assert portfolio.list_authorized(context) == ()
    assert portfolio.get_xeed(focus_id) is None
    restarted = SqliteSubscriberPortfolioStore(portfolio.path)
    assert restarted.list_authorized(context) == ()
    assert clock.now().tzinfo is UTC


def test_membership_is_checked_before_any_private_focus_select(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=1, trace=True)
    identities, subscriber, context, portfolio, service = (
        runtime[1],
        runtime[2],
        runtime[3],
        runtime[4],
        runtime[10],
    )
    service.add(context, AddOrganizationRequest("add-1", "organization"))
    identities.remove_membership(subscriber.principal_id, subscriber.tenant_id)
    portfolio.statements.clear()
    with pytest.raises(PortfolioError) as error:
        portfolio.list_authorized(context)
    assert error.value.failure is PortfolioFailure.ACCESS_DENIED
    assert any("subscriber_memberships" in statement for statement in portfolio.statements)
    assert not any("FROM subscriber_focuses" in statement for statement in portfolio.statements)
    portfolio.statements.clear()
    with pytest.raises(PortfolioError):
        portfolio.get_authorized(context, "any-focus")
    assert not any("FROM subscriber_focuses" in statement for statement in portfolio.statements)


def test_concurrent_adds_never_exceed_confirmed_capacity(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=1)
    context, portfolio, service = runtime[3], runtime[4], runtime[10]

    def add(index: int):
        return service.add(
            context, AddOrganizationRequest(f"parallel-{index}", f"candidate-{index}")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(add, (1, 2)))
    assert sum(result.status is AddStatus.CREATED for result in results) == 1
    assert sum(result.status is AddStatus.CHECKOUT_REQUIRED for result in results) == 1
    assert len(portfolio.list_authorized(context)) == 1


def test_idempotent_add_creates_one_focus_and_one_observation(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=2)
    context, portfolio, observations, service = runtime[3], runtime[4], runtime[9], runtime[10]
    request = AddOrganizationRequest("stable-idempotency", "same-organization")
    first = service.add(context, request)
    second = service.add(context, request)
    assert first.status is AddStatus.CREATED
    assert second.status is AddStatus.ALREADY_PRESENT
    assert first.entry == second.entry
    assert len(portfolio.list_authorized(context)) == 1
    assert len(observations.calls) == 1


def test_pending_request_is_durable_and_resolves_under_same_request_identity(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, capacity=1)
    context, portfolio, organizations, service = runtime[3], runtime[4], runtime[8], runtime[10]
    organizations.pending.add("resolvable-locator")
    initial = service.add(
        context,
        AddOrganizationRequest("pending-to-add", "resolvable-locator", "Candidate"),
    )
    assert initial.status is AddStatus.IDENTITY_PENDING
    pending = service.list_pending(context)
    assert len(pending) == 1
    pending_id = pending[0].pending_id
    assert pending[0].organization_id is None
    assert pending[0].locator == "resolvable-locator"

    reopened = SqliteSubscriberPortfolioStore(portfolio.path)
    assert reopened.list_pending_authorized(context) == pending
    organizations.pending.remove("resolvable-locator")
    result = service.retry_pending(context, pending_id)
    assert result.status is AddStatus.CREATED
    assert result.entry is not None
    assert service.list_pending(context) == ()
    assert reopened.list_authorized(context) == (result.entry,)
    assert reopened.list_pending_authorized(context) == ()


def test_pending_request_can_be_cancelled_and_retains_tombstone(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=1)
    context, portfolio, organizations, service = runtime[3], runtime[4], runtime[8], runtime[10]
    organizations.pending.add("cancel-locator")
    service.add(context, AddOrganizationRequest("cancel-me", "cancel-locator"))
    pending = service.list_pending(context)[0]
    cancelled = service.cancel_pending(context, pending.pending_id, "cancel-command")
    assert cancelled.status.value == "CANCELLED"
    assert service.list_pending(context) == ()
    reopened = SqliteSubscriberPortfolioStore(portfolio.path)
    with reopened._connect() as connection:
        row = connection.execute(
            "SELECT status FROM subscriber_portfolio_pending WHERE pending_id = ?",
            (pending.pending_id,),
        ).fetchone()
    assert row is not None and row[0] == "CANCELLED"


def test_pending_portfolio_read_checks_membership_before_select(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, capacity=1, trace=True)
    identities, subscriber, context, portfolio, organizations = (
        runtime[1],
        runtime[2],
        runtime[3],
        runtime[4],
        runtime[8],
    )
    organizations.pending.add("private-pending")
    runtime[10].add(context, AddOrganizationRequest("private-request", "private-pending"))
    identities.remove_membership(subscriber.principal_id, subscriber.tenant_id)
    portfolio.statements.clear()
    with pytest.raises(PortfolioError) as error:
        portfolio.list_pending_authorized(context)
    assert error.value.failure is PortfolioFailure.ACCESS_DENIED
    assert any("subscriber_memberships" in statement for statement in portfolio.statements)
    assert not any(
        "FROM subscriber_portfolio_pending" in statement for statement in portfolio.statements
    )
