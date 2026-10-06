"""Composition façade for subscriber authentication and durable sessions."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from application.subscriber_identity.runtime import (
    AuthIntent,
    Clock,
    InitialPurchaseScopeProvisioner,
    IssuedSubscriberSession,
    OidcProviderConfig,
    OidcProviderId,
    RevocationResult,
    SignInStart,
    SubscriberAuthenticationService,
    TrustedSubscriberContext,
)
from pipeline.subscriber_identity.oidc_provider import ConfiguredOidcProvider
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore


class SubscriberIdentityRuntime:
    """Stable HTTP integration surface; HTTP owns cookie attributes and routing."""

    def __init__(
        self, authentication: SubscriberAuthenticationService, store: SqliteSubscriberIdentityStore
    ) -> None:
        self.auth = authentication
        self.store = store

    def start(self, provider_id: OidcProviderId, intent: AuthIntent) -> SignInStart:
        return self.auth.begin_sign_in(provider_id, intent)

    def callback(
        self,
        provider_id: OidcProviderId,
        transaction_token: str,
        state: str,
        code: str,
    ) -> IssuedSubscriberSession:
        return self.auth.complete_sign_in(provider_id, transaction_token, state, code)

    def authenticate(self, session_token: str) -> TrustedSubscriberContext:
        return self.auth.resolve_session(session_token)

    def logout(self, session_token: str) -> RevocationResult:
        return RevocationResult(self.auth.revoke_session(session_token))


def build_subscriber_identity_runtime(
    data_dir: str | Path,
    providers: Mapping[OidcProviderId, OidcProviderConfig],
    clock: Clock,
    purchase_scope_provisioner: InitialPurchaseScopeProvisioner,
) -> SubscriberIdentityRuntime:
    """Build the durable subscriber authority runtime under AXIGNAL_DATA_DIR."""

    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    store = SqliteSubscriberIdentityStore(root / "subscriber-runtime.sqlite3")
    service = SubscriberAuthenticationService(
        provider_configs=providers,
        provider=ConfiguredOidcProvider(),
        transactions=store,
        bootstrap=store,
        sessions=store,
        purchase_scope_provisioner=purchase_scope_provisioner,
        clock=clock,
    )
    return SubscriberIdentityRuntime(service, store)


__all__ = [
    "SubscriberIdentityRuntime",
    "build_subscriber_identity_runtime",
]
