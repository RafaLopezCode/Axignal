"""Subscriber OIDC, registration and first-party session contracts."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from application.subscriber_identity.service import VerifiedExternalIdentity
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import PrincipalId, TenantId
from domain.tenancy.model import Principal


class OidcProviderId(StrEnum):
    GOOGLE = "google"
    OPENAI = "openai"


class AuthIntent(StrEnum):
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"


class IdentityRuntimeFailure(StrEnum):
    PROVIDER_UNAVAILABLE = "AUTH_PROVIDER_UNAVAILABLE"
    INVALID_TRANSACTION = "AUTH_TRANSACTION_INVALID"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    MEMBERSHIP_UNAVAILABLE = "ACCESS_DENIED"
    PURCHASE_SCOPE_PENDING = "PURCHASE_SCOPE_PROVISIONING_PENDING"


class SubscriberIdentityError(Exception):
    """Safe, non-secret-bearing subscriber identity failure."""

    def __init__(self, failure: IdentityRuntimeFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True, slots=True)
class OidcProviderConfig:
    provider_id: OidcProviderId
    issuer: str
    client_id: str
    redirect_uri: str
    enabled: bool
    registered: bool
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    allowed_algorithms: tuple[str, ...] = ("RS256",)
    client_secret_path: Path | None = None
    client_scope: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, OidcProviderId):
            raise ValueError("provider id is invalid")
        required = (
            self.issuer,
            self.client_id,
            self.redirect_uri,
            self.authorization_endpoint,
            self.token_endpoint,
            self.jwks_uri,
        )
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("OIDC provider configuration is incomplete")
        if not self.allowed_algorithms or any(
            algorithm not in {"RS256", "ES256", "PS256"} for algorithm in self.allowed_algorithms
        ):
            raise ValueError("OIDC algorithm policy must use approved asymmetric algorithms")
        if (
            self.provider_id is OidcProviderId.GOOGLE
            and self.issuer != "https://accounts.google.com"
        ):
            raise ValueError("Google issuer must match the configured Google OIDC issuer")
        if self.provider_id is OidcProviderId.OPENAI and self.issuer != "https://auth.openai.com":
            raise ValueError("OpenAI issuer must match the official SIWC issuer")


@dataclass(frozen=True, slots=True)
class SignInStart:
    authorization_url: str
    transaction_token: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class OidcTransaction:
    provider_id: OidcProviderId
    client_id: str
    redirect_uri: str
    state_digest: str
    nonce: str = field(repr=False)
    pkce_verifier: str = field(repr=False)
    intent: AuthIntent
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RegisteredSubscriber:
    principal_id: PrincipalId
    tenant_id: TenantId


@dataclass(frozen=True, slots=True)
class IssuedSubscriberSession:
    principal_id: PrincipalId
    tenant_id: TenantId
    session_token: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ActiveSubscriberSession:
    principal_id: PrincipalId
    tenant_id: TenantId
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RevocationResult:
    revoked: bool


TrustedSubscriberContext = TrustedRequestContext


@dataclass(frozen=True, slots=True)
class PurchaseScopeProvisioningReceipt:
    principal_id: PrincipalId
    tenant_id: TenantId
    registration_key: str
    provisioned: bool


class OidcProviderPort(Protocol):
    def authorization_url(
        self,
        config: OidcProviderConfig,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str: ...

    def exchange_and_verify(
        self,
        config: OidcProviderConfig,
        transaction: OidcTransaction,
        code: str,
    ) -> VerifiedExternalIdentity: ...


class OidcTransactionStore(Protocol):
    def create(
        self,
        provider_id: OidcProviderId,
        transaction_token_digest: str,
        transaction: OidcTransaction,
    ) -> None: ...

    def consume_once(
        self,
        provider_id: OidcProviderId,
        client_id: str,
        transaction_token_digest: str,
        state_digest: str,
        now: datetime,
    ) -> OidcTransaction | None: ...


class SubscriberBootstrapStore(Protocol):
    def find(self, identity: VerifiedExternalIdentity) -> RegisteredSubscriber | None: ...

    def register(
        self,
        identity: VerifiedExternalIdentity,
        now: datetime,
    ) -> RegisteredSubscriber: ...

    def get_principal(self, principal_id: PrincipalId) -> Principal | None: ...

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool: ...


class PrincipalTenantMembershipReader(Protocol):
    def get_principal(self, principal_id: PrincipalId) -> Principal | None: ...

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool: ...


class SubscriberSessionStore(Protocol):
    def issue(
        self,
        subscriber: RegisteredSubscriber,
        token_digest: str,
        now: datetime,
        expires_at: datetime,
    ) -> None: ...

    def resolve(self, token_digest: str, now: datetime) -> ActiveSubscriberSession | None: ...

    def revoke(self, token_digest: str, now: datetime) -> bool: ...


class InitialPurchaseScopeProvisioner(Protocol):
    """Billing-owned idempotent authority for purchases against the first scope."""

    def ensure_initial_purchase_scope(
        self,
        principal_id: PrincipalId,
        initial_tenant_id: TenantId,
        registration_key: str,
    ) -> PurchaseScopeProvisioningReceipt: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class SystemClock:
    def now(self) -> datetime:
        from datetime import UTC

        return datetime.now(UTC)


class SubscriberAuthenticationService:
    """Provider-neutral OIDC transaction and subscriber session policy."""

    def __init__(
        self,
        provider_configs: Mapping[OidcProviderId, OidcProviderConfig],
        provider: OidcProviderPort,
        transactions: OidcTransactionStore,
        bootstrap: SubscriberBootstrapStore,
        sessions: SubscriberSessionStore,
        purchase_scope_provisioner: InitialPurchaseScopeProvisioner,
        clock: Clock,
        *,
        transaction_ttl_seconds: int = 600,
        session_ttl_seconds: int = 60 * 60 * 24,
    ) -> None:
        if transaction_ttl_seconds <= 0 or session_ttl_seconds <= 0:
            raise ValueError("identity runtime TTLs must be positive")
        self._provider_configs = dict(provider_configs)
        self._provider = provider
        self._transactions = transactions
        self._bootstrap = bootstrap
        self._sessions = sessions
        self._purchase_scope_provisioner = purchase_scope_provisioner
        self._clock = clock
        self._transaction_ttl_seconds = transaction_ttl_seconds
        self._session_ttl_seconds = session_ttl_seconds

    @staticmethod
    def _digest(value: str) -> str:
        import hashlib

        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _registration_key(identity: VerifiedExternalIdentity) -> str:
        raw = "\x00".join((identity.issuer, identity.client_id or "", identity.subject))
        return SubscriberAuthenticationService._digest(raw)

    def begin_sign_in(self, provider_id: OidcProviderId, intent: AuthIntent) -> SignInStart:
        import base64
        import hashlib
        import secrets
        from datetime import timedelta

        config = self._provider_configs.get(provider_id)
        if config is None or not config.enabled or not config.registered:
            raise SubscriberIdentityError(IdentityRuntimeFailure.PROVIDER_UNAVAILABLE)
        now = self._clock.now()
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        challenge_text = challenge.rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        transaction_token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(seconds=self._transaction_ttl_seconds)
        transaction = OidcTransaction(
            provider_id=provider_id,
            client_id=config.client_id,
            redirect_uri=config.redirect_uri,
            state_digest=self._digest(state),
            nonce=nonce,
            pkce_verifier=verifier,
            intent=intent,
            created_at=now,
            expires_at=expires_at,
        )
        authorization_url = self._provider.authorization_url(
            config,
            state=state,
            nonce=nonce,
            code_challenge=challenge_text,
        )
        self._transactions.create(provider_id, self._digest(transaction_token), transaction)
        return SignInStart(authorization_url, transaction_token, expires_at)

    def complete_sign_in(
        self,
        provider_id: OidcProviderId,
        transaction_token: str,
        state: str,
        code: str,
    ) -> IssuedSubscriberSession:
        import secrets
        from datetime import timedelta

        config = self._provider_configs.get(provider_id)
        if config is None or not config.enabled or not config.registered:
            raise SubscriberIdentityError(IdentityRuntimeFailure.PROVIDER_UNAVAILABLE)
        if not all(isinstance(value, str) and value for value in (transaction_token, state, code)):
            raise SubscriberIdentityError(IdentityRuntimeFailure.INVALID_TRANSACTION)
        now = self._clock.now()
        transaction = self._transactions.consume_once(
            provider_id,
            config.client_id,
            self._digest(transaction_token),
            self._digest(state),
            now,
        )
        if transaction is None or transaction.redirect_uri != config.redirect_uri:
            raise SubscriberIdentityError(IdentityRuntimeFailure.INVALID_TRANSACTION)
        try:
            identity = self._provider.exchange_and_verify(config, transaction, code)
        except Exception:
            raise SubscriberIdentityError(IdentityRuntimeFailure.INVALID_TRANSACTION) from None
        if not isinstance(identity, VerifiedExternalIdentity) or identity.issuer != config.issuer:
            raise SubscriberIdentityError(IdentityRuntimeFailure.INVALID_TRANSACTION)
        identity = VerifiedExternalIdentity(
            issuer=identity.issuer,
            subject=identity.subject,
            client_id=config.client_id if config.client_scope is not None else None,
        )

        subscriber = self._bootstrap.find(identity)
        if transaction.intent is AuthIntent.LOGIN:
            if subscriber is None:
                raise SubscriberIdentityError(IdentityRuntimeFailure.AUTHENTICATION_REQUIRED)
        else:
            subscriber = self._bootstrap.register(identity, now)
            try:
                receipt = self._purchase_scope_provisioner.ensure_initial_purchase_scope(
                    subscriber.principal_id,
                    subscriber.tenant_id,
                    self._registration_key(identity),
                )
            except Exception:
                logging.getLogger(__name__).warning(
                    "initial purchase scope provisioning failed; registration can be retried",
                    extra={"event": "subscriber_purchase_scope_provisioning_failed"},
                )
                raise SubscriberIdentityError(
                    IdentityRuntimeFailure.PURCHASE_SCOPE_PENDING
                ) from None
            if (
                receipt.principal_id != subscriber.principal_id
                or receipt.tenant_id != subscriber.tenant_id
                or receipt.registration_key != self._registration_key(identity)
                or not receipt.provisioned
            ):
                raise SubscriberIdentityError(IdentityRuntimeFailure.PURCHASE_SCOPE_PENDING)

        if subscriber is None:
            raise SubscriberIdentityError(IdentityRuntimeFailure.AUTHENTICATION_REQUIRED)
        if not self._bootstrap.has_membership(subscriber.principal_id, subscriber.tenant_id):
            raise SubscriberIdentityError(IdentityRuntimeFailure.MEMBERSHIP_UNAVAILABLE)
        session_token = secrets.token_urlsafe(48)
        expires_at = now + timedelta(seconds=self._session_ttl_seconds)
        self._sessions.issue(subscriber, self._digest(session_token), now, expires_at)
        return IssuedSubscriberSession(
            subscriber.principal_id,
            subscriber.tenant_id,
            session_token,
            expires_at,
        )

    def resolve_session(self, session_token: str) -> TrustedSubscriberContext:
        if not isinstance(session_token, str) or not session_token:
            raise SubscriberIdentityError(IdentityRuntimeFailure.AUTHENTICATION_REQUIRED)
        session = self._sessions.resolve(self._digest(session_token), self._clock.now())
        if session is None:
            raise SubscriberIdentityError(IdentityRuntimeFailure.AUTHENTICATION_REQUIRED)
        if self._bootstrap.get_principal(session.principal_id) is None:
            raise SubscriberIdentityError(IdentityRuntimeFailure.MEMBERSHIP_UNAVAILABLE)
        if not self._bootstrap.has_membership(session.principal_id, session.tenant_id):
            raise SubscriberIdentityError(IdentityRuntimeFailure.MEMBERSHIP_UNAVAILABLE)
        return TrustedRequestContext(session.principal_id, session.tenant_id)

    def revoke_session(self, session_token: str) -> bool:
        if not isinstance(session_token, str) or not session_token:
            return False
        return self._sessions.revoke(self._digest(session_token), self._clock.now())


__all__ = [
    "ActiveSubscriberSession",
    "AuthIntent",
    "Clock",
    "IdentityRuntimeFailure",
    "InitialPurchaseScopeProvisioner",
    "IssuedSubscriberSession",
    "OidcProviderConfig",
    "OidcProviderId",
    "OidcProviderPort",
    "OidcTransaction",
    "OidcTransactionStore",
    "PrincipalTenantMembershipReader",
    "PurchaseScopeProvisioningReceipt",
    "RegisteredSubscriber",
    "RevocationResult",
    "SignInStart",
    "SubscriberAuthenticationService",
    "SubscriberBootstrapStore",
    "SubscriberIdentityError",
    "SubscriberSessionStore",
    "SystemClock",
    "TrustedSubscriberContext",
    "VerifiedExternalIdentity",
]
