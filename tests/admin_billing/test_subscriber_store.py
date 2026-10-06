from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from application.admin_billing.subscriber_checkout import (
    AttemptKind,
    AttemptStatus,
    PurchaseAttempt,
)
from domain.identity import PrincipalId, TenantId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore


def _attempt() -> PurchaseAttempt:
    return PurchaseAttempt(
        tenant_id=TenantId("tenant_fixture"),
        principal_id=PrincipalId("principal_fixture"),
        authority_ref="authority_fixture",
        membership_ref="membership_fixture",
        request_ref="request_fixture",
        intent_ref="intent_fixture",
        attempt_ref="attempt_fixture",
        idempotency_key="idem_fixture",
        kind=AttemptKind.INITIAL,
        desired_total=100,
        previous_effective_capacity=None,
        catalogue_ref="catalogue_fixture",
        catalogue_version="v1",
        environment_ref="stripe-live-fixture",
        authorized_at=datetime.now(UTC),
        status=AttemptStatus.PREPARED,
    )


def test_attempt_and_checkout_session_binding_survive_store_reopen(tmp_path):
    path = tmp_path / "subscriber.sqlite3"
    store = SqliteSubscriberBillingStore(path)
    prepared = store.prepare_attempt(_attempt())
    with_session = replace(
        prepared,
        status=AttemptStatus.PENDING_PURCHASE,
        checkout_session_ref="cs_fixture_100",
        checkout_url="https://checkout.stripe.com/c/pay_fixture",
    )

    store.record_initial_session(with_session)
    reopened = SqliteSubscriberBillingStore(path)

    assert reopened.get_attempt(TenantId("tenant_fixture"), "request_fixture") == with_session
    assert reopened.get_attempt_by_session("cs_fixture_100") == with_session
    assert reopened.list_pending_attempts(TenantId("tenant_fixture")) == (with_session,)


def test_store_keeps_unverified_capacity_absent(tmp_path):
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber.sqlite3")

    assert store.get_billing_projection(TenantId("tenant_missing")) is None


def test_initial_purchase_owner_provisioning_is_idempotent_and_unknown_is_not_owner(tmp_path):
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber.sqlite3")
    principal_id = PrincipalId("principal_fixture")
    tenant_id = TenantId("tenant_fixture")

    assert store.is_purchase_owner(principal_id, tenant_id) is None
    first = store.ensure_initial_purchase_scope(principal_id, tenant_id, "registration-key")
    retry = store.ensure_initial_purchase_scope(principal_id, tenant_id, "registration-key")
    reopened_retry = SqliteSubscriberBillingStore(
        tmp_path / "subscriber.sqlite3"
    ).ensure_initial_purchase_scope(principal_id, tenant_id, "registration-key")

    assert first.provisioned is True
    assert retry.provisioned is True
    assert reopened_retry == retry
    assert store.is_purchase_owner(principal_id, tenant_id) is True
    assert store.is_purchase_owner(PrincipalId("other_principal"), tenant_id) is False
