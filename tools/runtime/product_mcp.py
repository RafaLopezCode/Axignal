"""HTTP edge of the subscriber Product MCP (ADR-0086) and its runtime wiring.

Endpoints (all on the public subscriber origin):

* ``/.well-known/oauth-protected-resource`` (RFC 9728) and
  ``/.well-known/oauth-authorization-server`` (RFC 8414): discovery.
* ``POST /oauth/register`` (RFC 7591), ``GET /oauth/authorize``,
  ``POST /oauth/token``: OAuth 2.1 with PKCE S256 for public clients.
* ``POST /mcp``: MCP Streamable HTTP, JSON responses, stateless.

The subscriber approves a client on ``/account/connect`` from its own
first-party session; consent and connection management go through the
subscriber facade (``/subscriber/mcp/...``). Every MCP call re-checks the
tenant's effective entitlement (paid plan or pilot grant) and Xeed ownership
through the same subscriber runtime the web product uses.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from application.product_mcp.oauth import SCOPE, OAuthError, OAuthService
from application.product_mcp.server import (
    McpDenied,
    ProductMcpServer,
    SubscriberMemoryPort,
    XeedSummary,
)
from application.subscriber_portfolio.models import FocusStatus
from application.subscriber_portfolio.service import EntitlementPort
from application.subscriber_projection.subscriber_runtime import SubscriberEconomicRuntime
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import XeedId

MAX_BODY = 65_536
_JSON = "application/json"


@dataclass(frozen=True, slots=True)
class HttpResult:
    status: int
    body: bytes = b""
    headers: tuple[tuple[str, str], ...] = ()

    @classmethod
    def json(cls, status: int, payload: object, *headers: tuple[str, str]) -> HttpResult:
        return cls(
            status,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            (("Content-Type", _JSON), ("Cache-Control", "no-store"), *headers),
        )


@dataclass
class SubscriberMemory(SubscriberMemoryPort):
    """Authorized Xeeds = active foci of the tenant, within its effective entitlement."""

    portfolio: Any
    entitlements: EntitlementPort
    economic: SubscriberEconomicRuntime
    _names: dict[str, str] = field(default_factory=dict)

    def authorized_xeeds(
        self, context: TrustedRequestContext, *, now: datetime
    ) -> tuple[XeedSummary, ...]:
        snapshot = self.entitlements.snapshot(context.tenant_id)
        if (
            snapshot is None
            or snapshot.currentness is not Currentness.CURRENT
            or not snapshot.capacity
        ):
            raise McpDenied("ENTITLEMENT_INACTIVE")
        # The portfolio read re-checks principal membership and the tenant.
        active = sorted(
            (e for e in self.portfolio.list(context) if e.status is FocusStatus.ACTIVE),
            key=lambda e: (e.created_at, e.focus_id),
        )[: snapshot.capacity]
        summaries = []
        for entry in active:
            name = entry.xeed.label or self._names.get(entry.focus_id)
            if name is None:
                projection = self.economic.read(context, entry.focus_id, now).to_wire()[
                    "projection"
                ]
                organization = (
                    projection.get("organization") if isinstance(projection, dict) else None
                )
                label = organization.get("name") if isinstance(organization, dict) else None
                name = str(label or entry.focus_id)
                self._names[entry.focus_id] = name
            summaries.append(XeedSummary(str(entry.focus_id), name))
        return tuple(summaries)

    def reading(
        self, context: TrustedRequestContext, xeed_id: str, *, now: datetime
    ) -> Mapping[str, Any]:
        return self.economic.read(context, XeedId(xeed_id), now).to_wire()


class ProductMcpHttp:
    def __init__(
        self,
        *,
        origin: str,
        oauth: OAuthService,
        server: ProductMcpServer,
        clock: Callable[[], datetime],
    ) -> None:
        self.origin = origin.rstrip("/")
        self.oauth = oauth
        self.server = server
        self._clock = clock

    @property
    def resource(self) -> str:
        return self.origin + "/mcp"

    @staticmethod
    def handles(path: str) -> bool:
        return (
            path in {"/mcp", "/oauth/register", "/oauth/authorize", "/oauth/token"}
            or path.startswith("/.well-known/oauth-protected-resource")
            or path == "/.well-known/oauth-authorization-server"
        )

    def _challenge(self, error: str | None = None) -> tuple[str, str]:
        value = f'Bearer resource_metadata="{self.origin}/.well-known/oauth-protected-resource", scope="{SCOPE}"'
        if error:
            value += f', error="{error}"'
        return ("WWW-Authenticate", value)

    def handle(
        self, method: str, target: str, headers: Mapping[str, str], body: bytes
    ) -> HttpResult:
        parts = urlsplit(target)
        path = parts.path
        now = self._clock()
        if path.startswith("/.well-known/oauth-protected-resource") and method == "GET":
            return HttpResult.json(
                200,
                {
                    "resource": self.resource,
                    "authorization_servers": [self.origin],
                    "scopes_supported": [SCOPE],
                    "bearer_methods_supported": ["header"],
                    "resource_name": "AXIGNAL",
                },
            )
        if path == "/.well-known/oauth-authorization-server" and method == "GET":
            return HttpResult.json(
                200,
                {
                    "issuer": self.origin,
                    "authorization_endpoint": self.origin + "/oauth/authorize",
                    "token_endpoint": self.origin + "/oauth/token",
                    "registration_endpoint": self.origin + "/oauth/register",
                    "response_types_supported": ["code"],
                    "grant_types_supported": ["authorization_code", "refresh_token"],
                    "code_challenge_methods_supported": ["S256"],
                    "token_endpoint_auth_methods_supported": ["none"],
                    "scopes_supported": [SCOPE],
                },
            )
        if path == "/oauth/register" and method == "POST":
            try:
                client = self.oauth.register(json.loads(body or b"null"), now=now)
            except (ValueError, json.JSONDecodeError):
                return HttpResult.json(400, {"error": "invalid_client_metadata"})
            except OAuthError as error:
                return HttpResult.json(
                    400, {"error": error.code, "error_description": error.description}
                )
            return HttpResult.json(
                201,
                {
                    "client_id": client.client_id,
                    "client_name": client.client_name,
                    "redirect_uris": list(client.redirect_uris),
                    "token_endpoint_auth_method": "none",
                    "grant_types": ["authorization_code", "refresh_token"],
                    "response_types": ["code"],
                    "client_id_issued_at": int(client.created_at.timestamp()),
                },
            )
        if path == "/oauth/authorize" and method == "GET":
            params = dict(parse_qsl(parts.query, keep_blank_values=True))
            try:
                request = self.oauth.begin(params, now=now)
            except OAuthError as error:
                # Never redirect to an unverified redirect_uri: show the error here.
                return HttpResult.json(
                    400, {"error": error.code, "error_description": error.description}
                )
            # The subscriber decides in the product, from its own authenticated session.
            location = (
                self.origin + "/account/connect?" + urlencode({"request": request.request_id})
            )
            return HttpResult(302, b"", (("Location", location), ("Cache-Control", "no-store")))
        if path == "/oauth/token" and method == "POST":
            content_type = headers.get("content-type", "").split(";")[0].strip()
            if content_type != "application/x-www-form-urlencoded":
                return HttpResult.json(
                    400, {"error": "invalid_request", "error_description": "form encoding required"}
                )
            form = dict(parse_qsl(body.decode("utf-8", "replace"), keep_blank_values=True))
            try:
                tokens = self.oauth.exchange(form, now=now)
            except OAuthError as error:
                return HttpResult.json(
                    400, {"error": error.code, "error_description": error.description}
                )
            return HttpResult.json(200, tokens.to_wire(), ("Pragma", "no-cache"))
        if path == "/mcp":
            return self._mcp(method, headers, body, now=now)
        return HttpResult.json(404, {"error": "not_found"})

    def _mcp(
        self, method: str, headers: Mapping[str, str], body: bytes, *, now: datetime
    ) -> HttpResult:
        auth = headers.get("authorization", "")
        token = auth[7:].strip() if auth[:7].lower() == "bearer " else ""
        grant = self.oauth.authenticate(token, now=now) if token else None
        if grant is None:
            return HttpResult.json(
                401,
                {"error": "invalid_token" if token else "unauthorized"},
                self._challenge("invalid_token" if token else None),
            )
        if method != "POST":
            # Stateless server: no server-initiated stream and no session to delete.
            return HttpResult.json(405, {"error": "method_not_allowed"}, ("Allow", "POST"))
        if headers.get("content-type", "").split(";")[0].strip() != _JSON:
            return HttpResult.json(415, {"error": "application/json required"})
        try:
            message = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            return HttpResult.json(
                400,
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            )
        if isinstance(message, list):
            return HttpResult.json(
                400,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32600, "message": "Batching is not supported"},
                },
            )
        response = self.server.handle(message, grant=grant)
        if response is None:
            return HttpResult(202, b"", (("Cache-Control", "no-store"),))
        return HttpResult.json(200, response)


class SubscriberMcpConsent:
    """Consent and connection management, called from the authenticated subscriber facade."""

    def __init__(
        self, oauth: OAuthService, memory: SubscriberMemoryPort, clock: Callable[[], datetime]
    ) -> None:
        self._oauth = oauth
        self._memory = memory
        self._clock = clock

    def describe(self, context: TrustedRequestContext, request_id: str) -> dict[str, object]:
        request, client = self._oauth.pending(request_id, now=self._clock())
        try:
            xeeds = [
                x.organization for x in self._memory.authorized_xeeds(context, now=self._clock())
            ]
            access = "ACTIVE"
        except McpDenied:
            xeeds, access = [], "ENTITLEMENT_INACTIVE"
        return {
            "client": client.client_name,
            "redirectHost": urlsplit(request.redirect_uri).netloc,
            "scope": request.scope,
            "expiresAt": request.expires_at.isoformat(),
            "access": access,
            "xeeds": xeeds,
        }

    def decide(
        self, context: TrustedRequestContext, request_id: str, approve: bool
    ) -> dict[str, object]:
        redirect = self._oauth.decide(
            request_id,
            principal_id=context.principal_id,
            tenant_id=context.tenant_id,
            approve=approve,
            now=self._clock(),
        )
        return {"redirect": redirect}

    def connections(self, context: TrustedRequestContext) -> dict[str, object]:
        return {
            "connections": [
                {
                    "grantId": g.grant_id,
                    "client": self._oauth.client_name(g.client_id),
                    "connectedAt": g.created_at.isoformat(),
                    "scope": g.scope,
                }
                for g in self._oauth.connections(context.principal_id, context.tenant_id)
            ]
        }

    def revoke(self, context: TrustedRequestContext, grant_id: str) -> dict[str, object]:
        revoked = self._oauth.revoke(
            grant_id,
            principal_id=context.principal_id,
            tenant_id=context.tenant_id,
            now=self._clock(),
        )
        return {"revoked": revoked}
