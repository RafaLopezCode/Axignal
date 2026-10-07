"""OAuth 2.1 authorization for the subscriber Product MCP (ADR-0086).

AXIGNAL acts as the authorization server for its own MCP resource. A client
registers dynamically (RFC 7591), sends the subscriber through an authorization
code request with PKCE S256, and the subscriber approves it from an
authenticated first-party session. Tokens are opaque, stored only as SHA-256
digests, bound to exactly one principal + tenant + client + resource, scoped
read-only, short-lived, and refresh tokens rotate on use (reuse revokes the
grant). Nothing here authorizes a Xeed: every MCP call still re-checks
membership, tenant, effective entitlement and Xeed ownership.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlencode, urlsplit

from domain.identity import PrincipalId, TenantId

SCOPE = "xeed:read"
ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=30)
CODE_TTL = timedelta(minutes=5)
REQUEST_TTL = timedelta(minutes=10)
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})


class OAuthError(Exception):
    """An RFC 6749 error; ``code`` is the standard error identifier."""

    def __init__(self, code: str, description: str) -> None:
        super().__init__(description)
        self.code = code
        self.description = description


def digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _pkce_s256(verifier: str) -> str:
    raw = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _valid_redirect(uri: str) -> bool:
    parts = urlsplit(uri)
    if parts.fragment or not parts.netloc or parts.username or parts.password:
        return False
    if parts.scheme == "https":
        return True
    # Native clients (e.g. a local Claude) receive the code on a loopback port.
    return parts.scheme == "http" and (parts.hostname or "") in _LOOPBACK


@dataclass(frozen=True, slots=True)
class McpClient:
    client_id: str
    client_name: str
    redirect_uris: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    request_id: str
    client_id: str
    redirect_uri: str
    state: str | None
    code_challenge: str
    scope: str
    resource: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class McpGrant:
    """One subscriber's authorization of one client. Revocation ends all its tokens."""

    grant_id: str
    principal_id: PrincipalId
    tenant_id: TenantId
    client_id: str
    scope: str
    resource: str
    created_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class IssuedCode:
    code_digest: str
    grant_id: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    resource: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str

    def to_wire(self) -> dict[str, object]:
        return {
            "access_token": self.access_token,
            "token_type": "Bearer",
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
        }


class OAuthStore(Protocol):
    def put_client(self, client: McpClient) -> None: ...
    def client(self, client_id: str) -> McpClient | None: ...
    def put_request(self, request: AuthorizationRequest) -> None: ...
    def request(self, request_id: str) -> AuthorizationRequest | None: ...
    def take_request(self, request_id: str) -> AuthorizationRequest | None:
        """Single use: returns and deletes."""

    def put_grant(self, grant: McpGrant) -> None: ...
    def grant(self, grant_id: str) -> McpGrant | None: ...
    def grants_for(
        self, principal_id: PrincipalId, tenant_id: TenantId
    ) -> tuple[McpGrant, ...]: ...
    def revoke_grant(self, grant_id: str, *, revoked_at: datetime) -> bool: ...
    def put_code(self, code: IssuedCode) -> None: ...
    def take_code(self, code_digest: str) -> IssuedCode | None:
        """Single use: returns and deletes."""

    def put_token(
        self, token_digest: str, *, kind: str, grant_id: str, expires_at: datetime
    ) -> None: ...
    def token(self, token_digest: str, *, kind: str) -> tuple[str, datetime, bool] | None:
        """(grant_id, expires_at, used) for a token of this kind."""

    def mark_used(self, token_digest: str) -> bool:
        """Mark a refresh token used; False if it already was (replay)."""


class OAuthService:
    def __init__(self, store: OAuthStore, *, resource: str) -> None:
        if not resource.startswith("https://") and not resource.startswith("http://127.0.0.1"):
            raise ValueError("the MCP resource must be an absolute HTTPS URL")
        self._store = store
        self.resource = resource

    # RFC 7591 dynamic client registration (public clients, PKCE only).
    def register(self, metadata: object, *, now: datetime) -> McpClient:
        if not isinstance(metadata, dict):
            raise OAuthError("invalid_client_metadata", "metadata must be a JSON object")
        uris = metadata.get("redirect_uris")
        if (
            not isinstance(uris, list)
            or not 1 <= len(uris) <= 5
            or not all(isinstance(u, str) and len(u) <= 512 and _valid_redirect(u) for u in uris)
        ):
            raise OAuthError("invalid_redirect_uri", "redirect_uris must be HTTPS or loopback URLs")
        method = metadata.get("token_endpoint_auth_method", "none")
        if method != "none":
            raise OAuthError("invalid_client_metadata", "only public clients (PKCE) are supported")
        grant_types = metadata.get("grant_types", ["authorization_code", "refresh_token"])
        if not isinstance(grant_types, list) or not set(grant_types) <= {
            "authorization_code",
            "refresh_token",
        }:
            raise OAuthError("invalid_client_metadata", "unsupported grant_types")
        name = metadata.get("client_name")
        label = name.strip()[:100] if isinstance(name, str) and name.strip() else "MCP client"
        client = McpClient(f"mcp_{secrets.token_urlsafe(18)}", label, tuple(uris), now)
        self._store.put_client(client)
        return client

    def begin(self, params: dict[str, str], *, now: datetime) -> AuthorizationRequest:
        """Validate an authorization request. Client/redirect errors are never redirected."""

        client = self._store.client(params.get("client_id", ""))
        if client is None:
            raise OAuthError("invalid_client", "unknown client")
        redirect = params.get("redirect_uri", "")
        if redirect not in client.redirect_uris:
            raise OAuthError("invalid_request", "redirect_uri is not registered for this client")
        if params.get("response_type") != "code":
            raise OAuthError("unsupported_response_type", "only the code flow is supported")
        challenge = params.get("code_challenge", "")
        if params.get("code_challenge_method") != "S256" or not 43 <= len(challenge) <= 128:
            raise OAuthError("invalid_request", "PKCE S256 is required")
        scope = params.get("scope") or SCOPE
        if set(scope.split()) - {SCOPE}:
            raise OAuthError("invalid_scope", "only xeed:read is available")
        resource = params.get("resource") or self.resource
        if resource.rstrip("/") != self.resource.rstrip("/"):
            raise OAuthError("invalid_target", "tokens are only issued for this MCP resource")
        state = params.get("state")
        if state is not None and len(state) > 512:
            raise OAuthError("invalid_request", "state is too long")
        request = AuthorizationRequest(
            request_id=secrets.token_urlsafe(24),
            client_id=client.client_id,
            redirect_uri=redirect,
            state=state,
            code_challenge=challenge,
            scope=SCOPE,
            resource=self.resource,
            created_at=now,
            expires_at=now + REQUEST_TTL,
        )
        self._store.put_request(request)
        return request

    def pending(self, request_id: str, *, now: datetime) -> tuple[AuthorizationRequest, McpClient]:
        request = self._store.request(request_id)
        if request is None or request.expires_at <= now:
            raise OAuthError("invalid_request", "authorization request expired")
        client = self._store.client(request.client_id)
        if client is None:
            raise OAuthError("invalid_client", "unknown client")
        return request, client

    def decide(
        self,
        request_id: str,
        *,
        principal_id: PrincipalId,
        tenant_id: TenantId,
        approve: bool,
        now: datetime,
    ) -> str:
        """The subscriber's decision; returns the redirect back to the client."""

        request = self._store.take_request(request_id)
        if request is None or request.expires_at <= now:
            raise OAuthError("invalid_request", "authorization request expired")
        params: dict[str, str] = {}
        if approve:
            grant = McpGrant(
                grant_id=f"mcpgrant_{secrets.token_hex(12)}",
                principal_id=principal_id,
                tenant_id=tenant_id,
                client_id=request.client_id,
                scope=request.scope,
                resource=request.resource,
                created_at=now,
            )
            self._store.put_grant(grant)
            code = secrets.token_urlsafe(32)
            self._store.put_code(
                IssuedCode(
                    digest(code),
                    grant.grant_id,
                    request.client_id,
                    request.redirect_uri,
                    request.code_challenge,
                    request.resource,
                    now + CODE_TTL,
                )
            )
            params["code"] = code
        else:
            params["error"] = "access_denied"
        if request.state is not None:
            params["state"] = request.state
        separator = "&" if urlsplit(request.redirect_uri).query else "?"
        return request.redirect_uri + separator + urlencode(params)

    def _issue(self, grant: McpGrant, *, now: datetime) -> TokenPair:
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self._store.put_token(
            digest(access), kind="access", grant_id=grant.grant_id, expires_at=now + ACCESS_TTL
        )
        self._store.put_token(
            digest(refresh), kind="refresh", grant_id=grant.grant_id, expires_at=now + REFRESH_TTL
        )
        return TokenPair(access, refresh, int(ACCESS_TTL.total_seconds()), grant.scope)

    def exchange(self, form: dict[str, str], *, now: datetime) -> TokenPair:
        grant_type = form.get("grant_type")
        if grant_type == "authorization_code":
            code = self._store.take_code(digest(form.get("code", "")))
            if code is None or code.expires_at <= now:
                raise OAuthError("invalid_grant", "authorization code is invalid or expired")
            if (
                form.get("client_id") != code.client_id
                or form.get("redirect_uri") != code.redirect_uri
            ):
                raise OAuthError("invalid_grant", "code was issued to another client or redirect")
            verifier = form.get("code_verifier", "")
            if not 43 <= len(verifier) <= 128 or _pkce_s256(verifier) != code.code_challenge:
                raise OAuthError("invalid_grant", "PKCE verification failed")
            resource = form.get("resource") or code.resource
            if resource.rstrip("/") != code.resource.rstrip("/"):
                raise OAuthError("invalid_target", "resource does not match the authorization")
            grant = self._live_grant(code.grant_id)
            return self._issue(grant, now=now)
        if grant_type == "refresh_token":
            token_digest = digest(form.get("refresh_token", ""))
            found = self._store.token(token_digest, kind="refresh")
            if found is None or found[1] <= now:
                raise OAuthError("invalid_grant", "refresh token is invalid or expired")
            grant = self._live_grant(found[0])
            # Public clients must identify themselves on refresh (OAuth 2.1 §4.3.1).
            if form.get("client_id") != grant.client_id:
                raise OAuthError("invalid_grant", "refresh token belongs to another client")
            if not self._store.mark_used(token_digest):
                # A rotated refresh token was replayed: treat the grant as compromised.
                self._store.revoke_grant(grant.grant_id, revoked_at=now)
                raise OAuthError("invalid_grant", "refresh token reuse detected; grant revoked")
            return self._issue(grant, now=now)
        raise OAuthError("unsupported_grant_type", "use authorization_code or refresh_token")

    def _live_grant(self, grant_id: str) -> McpGrant:
        grant = self._store.grant(grant_id)
        if grant is None or grant.revoked_at is not None:
            raise OAuthError("invalid_grant", "the authorization was revoked")
        return grant

    def authenticate(self, access_token: str, *, now: datetime) -> McpGrant | None:
        """Bearer token → live grant, or None (expired, unknown, revoked)."""

        if not access_token or len(access_token) > 256:
            return None
        found = self._store.token(digest(access_token), kind="access")
        if found is None or found[1] <= now:
            return None
        grant = self._store.grant(found[0])
        if grant is None or grant.revoked_at is not None or grant.resource != self.resource:
            return None
        return grant

    def client_name(self, client_id: str) -> str:
        client = self._store.client(client_id)
        return "MCP client" if client is None else client.client_name

    def connections(self, principal_id: PrincipalId, tenant_id: TenantId) -> tuple[McpGrant, ...]:
        return tuple(
            g for g in self._store.grants_for(principal_id, tenant_id) if g.revoked_at is None
        )

    def revoke(
        self, grant_id: str, *, principal_id: PrincipalId, tenant_id: TenantId, now: datetime
    ) -> bool:
        """A subscriber revokes one of its own connections; others' grants are invisible."""

        grant = self._store.grant(grant_id)
        if grant is None or grant.principal_id != principal_id or grant.tenant_id != tenant_id:
            return False
        return self._store.revoke_grant(grant_id, revoked_at=now)
