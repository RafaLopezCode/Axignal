"""Subscriber transport boundary. Identity, billing and truth remain application-owned."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import unquote, urlsplit

from application.admin_billing.subscriber_checkout import SubscriberCheckoutError
from application.subscriber_identity.runtime import (
    AuthIntent,
    OidcProviderId,
    SubscriberIdentityError,
    TrustedSubscriberContext,
)
from application.subscriber_portfolio.models import PortfolioError
from application.xeed_access.reader import XeedReadError
from domain.identity import XeedId
from tools.runtime.subscriber_checkout import SubscriberBillingWebhook
from tools.runtime.subscriber_configuration import SubscriberSettings
from tools.runtime.subscriber_identity import SubscriberIdentityRuntime

_REFERENCE = re.compile(r"[A-Za-z0-9:_-]{1,160}\Z")


class SubscriberWorkflowPort(Protocol):
    def portfolio(self, context: TrustedSubscriberContext) -> dict[str, object]: ...

    def command(
        self, context: TrustedSubscriberContext, command: dict[str, object]
    ) -> dict[str, object]: ...


class SubscriberOutputPort(Protocol):
    def output(
        self, context: TrustedSubscriberContext, focus_id: XeedId, as_of: datetime
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class SubscriberHttpResponse:
    status: int
    body: dict[str, object]


class SubscriberRequestError(ValueError):
    """Malformed public command without its private input values."""


def _text(payload: dict[str, object], name: str, maximum: int) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise SubscriberRequestError("invalid request field")
    return value


def validate_subscriber_command(payload: dict[str, object]) -> dict[str, object]:
    action = _text(payload, "action", 16)
    request_ref = _text(payload, "requestRef", 160)
    if not _REFERENCE.fullmatch(request_ref):
        raise SubscriberRequestError("invalid request reference")
    expected = {"action", "requestRef"}
    if action in {"add", "replace"}:
        locator = _text(payload, "locator", 2048)
        if any(ord(character) < 32 for character in locator):
            raise SubscriberRequestError("invalid locator")
        expected.add("locator")
    if action in {
        "pause",
        "resume",
        "remove",
        "replace",
        "reobserve",
        "retry_pending",
        "cancel_pending",
    }:
        if not _REFERENCE.fullmatch(_text(payload, "focusId", 160)):
            raise SubscriberRequestError("invalid focus reference")
        expected.add("focusId")
    elif action in {"purchase", "expand"}:
        total = payload.get("desiredOrganizationTotal")
        if type(total) is not int or not 1 <= total <= 100000:
            raise SubscriberRequestError("invalid capacity")
        expected.add("desiredOrganizationTotal")
    elif action == "refresh_purchase":
        pass
    elif action != "add":
        raise SubscriberRequestError("unknown action")
    if set(payload) != expected:
        raise SubscriberRequestError("unexpected request fields")
    return payload


class SubscriberHttpFacade:
    def __init__(
        self,
        *,
        settings: SubscriberSettings,
        identity: SubscriberIdentityRuntime,
        workflow: SubscriberWorkflowPort,
        outputs: SubscriberOutputPort,
        billing_webhook: SubscriberBillingWebhook | None = None,
        available_providers: frozenset[str] | None = None,
    ) -> None:
        self.settings = settings
        self.identity = identity
        self.workflow = workflow
        self.outputs = outputs
        self.billing_webhook = billing_webhook
        self.available_providers = available_providers

    def handle_webhook(self, raw_body: bytes, signature: str) -> SubscriberHttpResponse:
        if not self.settings.enabled or self.billing_webhook is None:
            return self._denied("BILLING_INGRESS_NOT_CONFIGURED", 503)
        receipt = self.billing_webhook.handle_signed_webhook(raw_body, signature, datetime.now(UTC))
        return SubscriberHttpResponse(
            200 if receipt.accepted else 400,
            {"accepted": receipt.accepted, "disposition": receipt.disposition},
        )

    def _provider_available(self, provider: str) -> bool:
        return self.settings.provider_ready(provider) and (
            self.available_providers is None or provider in self.available_providers
        )

    @staticmethod
    def _denied(code: str, status: int) -> SubscriberHttpResponse:
        return SubscriberHttpResponse(status, {"state": "rejected", "code": code})

    def handle(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        payload: dict[str, object] | None = None,
    ) -> SubscriberHttpResponse:
        if not self.settings.enabled:
            return self._denied("SUBSCRIBER_RUNTIME_DISABLED", 503)
        if method == "POST" and headers.get("Origin") != self.settings.origin:
            return self._denied("ORIGIN_REQUIRED", 403)
        try:
            if method == "GET" and path == "/subscriber/auth/status":
                return SubscriberHttpResponse(
                    200,
                    {
                        "providers": [
                            {
                                "id": provider,
                                "status": "AVAILABLE"
                                if self._provider_available(provider)
                                else "UNAVAILABLE",
                                "registrationRequired": not self._provider_available(provider),
                            }
                            for provider in ("google", "openai")
                        ],
                        "identityScopes": ["openid", "profile", "email"],
                        "sessionCreated": False,
                    },
                )
            if method == "POST" and path == "/subscriber/auth/start":
                body = payload or {}
                if set(body) != {"provider", "intent"}:
                    raise SubscriberRequestError("invalid auth request")
                provider = OidcProviderId(_text(body, "provider", 16))
                intent = {"login": AuthIntent.LOGIN, "signup": AuthIntent.REGISTER}.get(
                    _text(body, "intent", 16)
                )
                if intent is None:
                    raise SubscriberRequestError("invalid auth intent")
                started = self.identity.start(provider, intent)
                return SubscriberHttpResponse(
                    200,
                    {
                        "authorizationUrl": started.authorization_url,
                        "transactionToken": started.transaction_token,
                    },
                )
            if method == "POST" and path == "/subscriber/auth/callback":
                body = payload or {}
                if set(body) != {"provider", "transactionToken", "state", "code"}:
                    raise SubscriberRequestError("invalid callback")
                issued = self.identity.callback(
                    OidcProviderId(_text(body, "provider", 16)),
                    _text(body, "transactionToken", 256),
                    _text(body, "state", 512),
                    _text(body, "code", 4096),
                )
                seconds = max(
                    1, min(86400, int((issued.expires_at - datetime.now(UTC)).total_seconds()))
                )
                return SubscriberHttpResponse(
                    200, {"sessionToken": issued.session_token, "maxAge": seconds}
                )
            authorization = headers.get("Authorization", "")
            scheme, separator, token = authorization.partition(" ")
            if scheme != "Bearer" or separator != " " or not token or len(token) > 256:
                return self._denied("AUTHENTICATION_REQUIRED", 401)
            context = self.identity.authenticate(token)
            if method == "POST" and path == "/subscriber/auth/logout":
                if payload != {}:
                    raise SubscriberRequestError("logout body must be empty")
                self.identity.logout(token)
                return SubscriberHttpResponse(200, {"state": "signed_out"})
            if path == "/subscriber/portfolio":
                if method == "GET":
                    return SubscriberHttpResponse(200, self.workflow.portfolio(context))
                if method == "POST":
                    body = validate_subscriber_command(payload or {})
                    if (
                        body["action"] in {"purchase", "expand"}
                        and not self.settings.contracting_enabled
                    ):
                        return self._denied("CONTRACTING_NOT_READY", 409)
                    return SubscriberHttpResponse(200, self.workflow.command(context, body))
            if (
                method == "GET"
                and path.startswith("/subscriber/organizations/")
                and path.endswith("/output")
            ):
                focus_id = unquote(
                    path.removeprefix("/subscriber/organizations/").removesuffix("/output")
                )
                if not _REFERENCE.fullmatch(focus_id):
                    raise SubscriberRequestError("invalid focus reference")
                return SubscriberHttpResponse(
                    200, self.outputs.output(context, XeedId(focus_id), datetime.now(UTC))
                )
            return self._denied("NOT_FOUND", 404)
        except SubscriberIdentityError as exc:
            return self._denied(
                exc.failure.value, 503 if exc.failure.value == "AUTH_PROVIDER_UNAVAILABLE" else 401
            )
        except XeedReadError:
            return self._denied("ACCESS_DENIED", 403)
        except PortfolioError as exc:
            return self._denied(
                exc.failure.value, 403 if exc.failure.value == "ACCESS_DENIED" else 409
            )
        except SubscriberCheckoutError as exc:
            return self._denied(exc.failure.value, 409)
        except (SubscriberRequestError, ValueError):
            return self._denied("INVALID_REQUEST", 400)


def is_subscriber_path(path: str) -> bool:
    resource = urlsplit(path).path
    return resource == "/subscriber/portfolio" or resource.startswith(
        ("/subscriber/auth/", "/subscriber/organizations/")
    )
