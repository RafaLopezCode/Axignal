from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.subscriber_identity.runtime import (
    AuthIntent,
    IdentityRuntimeFailure,
    OidcProviderConfig,
    OidcProviderId,
    PurchaseScopeProvisioningReceipt,
    RegisteredSubscriber,
    SubscriberAuthenticationService,
    SubscriberIdentityError,
    VerifiedExternalIdentity,
)
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore


@dataclass
class MutableClock:
    value: datetime

    def now(self) -> datetime:
        return self.value


class FakeProvider:
    def __init__(self, identity: VerifiedExternalIdentity) -> None:
        self.identity = identity
        self.last_url = ""
        self.last_nonce = ""
        self.last_challenge = ""

    def authorization_url(
        self,
        config: OidcProviderConfig,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        from urllib.parse import parse_qs, urlparse

        self.last_url = (
            f"{config.authorization_endpoint}?state={state}&nonce={nonce}"
            f"&code_challenge={code_challenge}"
        )
        query = parse_qs(urlparse(self.last_url).query)
        self.last_nonce = query["nonce"][0]
        self.last_challenge = query["code_challenge"][0]
        return self.last_url

    def exchange_and_verify(self, config, transaction, code):
        assert code == "one-time-code"
        assert transaction.nonce == self.last_nonce
        assert transaction.client_id == config.client_id
        return self.identity


class FakeProvisioner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.fail = False

    def ensure_initial_purchase_scope(self, principal_id, initial_tenant_id, registration_key):
        self.calls.append((principal_id, initial_tenant_id, registration_key))
        if self.fail:
            raise RuntimeError("secret-bearing provider exception must not escape")
        return PurchaseScopeProvisioningReceipt(
            principal_id, initial_tenant_id, registration_key, True
        )


def _config(
    *,
    enabled: bool = True,
    client_id: str = "public-client-id",
    client_scope: str | None = None,
) -> OidcProviderConfig:
    return OidcProviderConfig(
        provider_id=OidcProviderId.GOOGLE,
        issuer="https://accounts.google.com",
        client_id=client_id,
        redirect_uri="http://127.0.0.1:3810/api/auth/callback/google",
        enabled=enabled,
        registered=True,
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
        client_scope=client_scope,
    )


def _service(path: Path, clock: MutableClock, identity=None, provisioner=None):
    identity = identity or VerifiedExternalIdentity("https://accounts.google.com", "subject-1")
    store = SqliteSubscriberIdentityStore(path)
    provider = FakeProvider(identity)
    provisioner = provisioner or FakeProvisioner()
    service = SubscriberAuthenticationService(
        {_config().provider_id: _config()},
        provider,
        store,
        store,
        store,
        provisioner,
        clock,
    )
    return service, store, provider, provisioner


def _callback(service, provider, intent=AuthIntent.REGISTER):
    from urllib.parse import parse_qs, urlparse

    start = service.begin_sign_in(OidcProviderId.GOOGLE, intent)
    state = parse_qs(urlparse(start.authorization_url).query)["state"][0]
    return (
        service.complete_sign_in(
            OidcProviderId.GOOGLE,
            start.transaction_token,
            state,
            "one-time-code",
        ),
        start,
        state,
    )


def test_login_unknown_never_bootstraps_and_register_is_durable(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    service, store, provider, provisioner = _service(tmp_path / "identity.sqlite3", clock)

    with pytest.raises(SubscriberIdentityError) as error:
        _callback(service, provider, AuthIntent.LOGIN)
    assert error.value.failure is IdentityRuntimeFailure.AUTHENTICATION_REQUIRED
    assert store.find(VerifiedExternalIdentity("https://accounts.google.com", "subject-1")) is None
    assert provisioner.calls == []

    issued, start, _ = _callback(service, provider)
    assert store.get_principal(issued.principal_id) is not None
    assert store.has_membership(issued.principal_id, issued.tenant_id)
    assert len(provisioner.calls) == 1
    assert issued.session_token not in repr(issued)
    assert start.transaction_token not in repr(start)

    reopened = SqliteSubscriberIdentityStore(tmp_path / "identity.sqlite3")
    assert reopened.find(VerifiedExternalIdentity("https://accounts.google.com", "subject-1")) == (
        RegisteredSubscriber(issued.principal_id, issued.tenant_id)
    )
    service2, _, provider2, provisioner2 = _service(
        tmp_path / "identity.sqlite3", clock, provisioner=provisioner
    )
    context = service2.resolve_session(issued.session_token)
    assert (context.principal_id, context.tenant_id) == (issued.principal_id, issued.tenant_id)
    logged_in, _, _ = _callback(service2, provider2, AuthIntent.LOGIN)
    assert logged_in.principal_id == issued.principal_id
    assert provisioner2.calls == provisioner.calls


def test_oidc_transaction_state_is_one_time_and_persistent(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    service, store, provider, _ = _service(tmp_path / "identity.sqlite3", clock)
    start = service.begin_sign_in(OidcProviderId.GOOGLE, AuthIntent.REGISTER)
    from urllib.parse import parse_qs, urlparse

    state = parse_qs(urlparse(start.authorization_url).query)["state"][0]
    with pytest.raises(SubscriberIdentityError) as error:
        service.complete_sign_in(
            OidcProviderId.GOOGLE, start.transaction_token, "wrong-state", "one-time-code"
        )
    assert error.value.failure is IdentityRuntimeFailure.INVALID_TRANSACTION
    assert store.find(provider.identity) is None

    issued = service.complete_sign_in(
        OidcProviderId.GOOGLE, start.transaction_token, state, "one-time-code"
    )
    service2, _, _, _ = _service(tmp_path / "identity.sqlite3", clock)
    with pytest.raises(SubscriberIdentityError) as replay:
        service2.complete_sign_in(
            OidcProviderId.GOOGLE, start.transaction_token, state, "one-time-code"
        )
    assert replay.value.failure is IdentityRuntimeFailure.INVALID_TRANSACTION
    assert store.get_principal(issued.principal_id) is not None


def test_registration_retries_initial_purchase_scope_after_billing_outage(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    provisioner = FakeProvisioner()
    provisioner.fail = True
    service, store, provider, _ = _service(
        tmp_path / "identity.sqlite3", clock, provisioner=provisioner
    )
    with pytest.raises(SubscriberIdentityError) as error:
        _callback(service, provider, AuthIntent.REGISTER)
    assert error.value.failure is IdentityRuntimeFailure.PURCHASE_SCOPE_PENDING
    subscriber = store.find(provider.identity)
    assert subscriber is not None
    assert store.has_membership(subscriber.principal_id, subscriber.tenant_id)
    assert len(provisioner.calls) == 1

    provisioner.fail = False
    service2, _, provider2, _ = _service(
        tmp_path / "identity.sqlite3", clock, provisioner=provisioner
    )
    issued, _, _ = _callback(service2, provider2, AuthIntent.REGISTER)
    assert (issued.principal_id, issued.tenant_id) == (
        subscriber.principal_id,
        subscriber.tenant_id,
    )
    assert len(provisioner.calls) == 2
    assert provisioner.calls[0] == provisioner.calls[1]


def test_session_expiry_revocation_and_membership_revocation_survive_restart(
    tmp_path: Path,
) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    database = tmp_path / "identity.sqlite3"
    service, store, provider, _ = _service(database, clock)
    issued, _, _ = _callback(service, provider)
    assert service.revoke_session(issued.session_token)
    with pytest.raises(SubscriberIdentityError):
        _service(database, clock)[0].resolve_session(issued.session_token)

    issued2, _, _ = _callback(service, provider)
    clock.value += timedelta(days=15)
    with pytest.raises(SubscriberIdentityError):
        _service(database, clock)[0].resolve_session(issued2.session_token)

    clock.value = datetime(2026, 10, 6, tzinfo=UTC)
    issued3, _, _ = _callback(service, provider)
    assert store.remove_membership(issued3.principal_id, issued3.tenant_id)
    with pytest.raises(SubscriberIdentityError) as error:
        _service(database, clock)[0].resolve_session(issued3.session_token)
    assert error.value.failure is IdentityRuntimeFailure.MEMBERSHIP_UNAVAILABLE


def test_configured_client_scope_is_server_bound_and_separates_pairwise_subjects(
    tmp_path: Path,
) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    path = tmp_path / "identity.sqlite3"
    store = SqliteSubscriberIdentityStore(path)
    provisioner = FakeProvisioner()
    results = []
    for client_id in ("client-a", "client-b"):
        config = _config(client_id=client_id, client_scope=client_id)
        provider = FakeProvider(VerifiedExternalIdentity(config.issuer, "pairwise-subject"))
        service = SubscriberAuthenticationService(
            {config.provider_id: config}, provider, store, store, store, provisioner, clock
        )
        issued, _, _ = _callback(service, provider)
        results.append(issued.principal_id)
    assert results[0] != results[1]


def test_disabled_provider_fails_with_safe_error(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 10, 6, tzinfo=UTC))
    store = SqliteSubscriberIdentityStore(tmp_path / "identity.sqlite3")
    service = SubscriberAuthenticationService(
        {_config(enabled=False).provider_id: _config(enabled=False)},
        FakeProvider(VerifiedExternalIdentity("https://accounts.google.com", "subject")),
        store,
        store,
        store,
        FakeProvisioner(),
        clock,
    )
    with pytest.raises(SubscriberIdentityError) as error:
        service.begin_sign_in(OidcProviderId.GOOGLE, AuthIntent.REGISTER)
    assert error.value.failure is IdentityRuntimeFailure.PROVIDER_UNAVAILABLE
