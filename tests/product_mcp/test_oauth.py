"""OAuth 2.1 authorization server for the subscriber Product MCP (ADR-0086)."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from application.product_mcp.oauth import (
    ACCESS_TTL,
    CODE_TTL,
    REFRESH_TTL,
    REQUEST_TTL,
    OAuthError,
    OAuthService,
    TokenPair,
    digest,
)
from domain.identity import PrincipalId, TenantId
from pipeline.product_mcp.sqlite_store import SqliteProductMcpStore

NOW = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
RESOURCE = "https://axignal.example/mcp"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"
VERIFIER = "v" * 64
CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip("=")
)
ALICE, TENANT_A = PrincipalId("principal:alice"), TenantId("tenant:a")
BOB, TENANT_B = PrincipalId("principal:bob"), TenantId("tenant:b")


@pytest.fixture
def oauth(tmp_path: Path) -> OAuthService:
    return OAuthService(SqliteProductMcpStore(tmp_path / "mcp.sqlite3"), resource=RESOURCE)


def _client(oauth: OAuthService, *uris: str) -> str:
    return oauth.register(
        {"redirect_uris": list(uris or (REDIRECT,)), "client_name": "Claude"}, now=NOW
    ).client_id


def _params(client_id: str, **extra: str) -> dict[str, str]:
    return {
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "code_challenge": CHALLENGE,
        "code_challenge_method": "S256",
        "scope": "xeed:read",
        "resource": RESOURCE,
        "state": "s-1",
        **extra,
    }


def _code(oauth: OAuthService, client_id: str, *, approve: bool = True) -> dict[str, list[str]]:
    request = oauth.begin(_params(client_id), now=NOW)
    redirect = oauth.decide(
        request.request_id, principal_id=ALICE, tenant_id=TENANT_A, approve=approve, now=NOW
    )
    assert redirect.startswith(REDIRECT + "?")
    return parse_qs(urlsplit(redirect).query)


def _exchange(oauth: OAuthService, client_id: str, code: str, **extra: str) -> TokenPair:
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "code_verifier": VERIFIER,
        "resource": RESOURCE,
        **extra,
    }
    return oauth.exchange(form, now=NOW)


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        [],
        {},
        {"redirect_uris": []},
        {"redirect_uris": ["http://evil.example/cb"]},
        {"redirect_uris": ["https://ok.example/cb#frag"]},
        {"redirect_uris": ["https://user:pw@ok.example/cb"]},
        {"redirect_uris": ["javascript:alert(1)"]},
        {"redirect_uris": [f"https://ok.example/{i}" for i in range(6)]},
        {"redirect_uris": [REDIRECT], "token_endpoint_auth_method": "client_secret_basic"},
        {"redirect_uris": [REDIRECT], "grant_types": ["client_credentials"]},
    ],
)
def test_registration_rejects_unsafe_metadata(oauth: OAuthService, metadata: object) -> None:
    with pytest.raises(OAuthError):
        oauth.register(metadata, now=NOW)


def test_registration_accepts_https_and_loopback_public_clients(oauth: OAuthService) -> None:
    client = oauth.register(
        {"redirect_uris": [REDIRECT, "http://127.0.0.1:33418/callback"], "client_name": " x" * 90},
        now=NOW,
    )
    assert client.client_id.startswith("mcp_") and len(client.client_name) <= 100


@pytest.mark.parametrize(
    ("override", "error"),
    [
        ({"client_id": "mcp_unknown"}, "invalid_client"),
        ({"redirect_uri": "https://claude.ai/other"}, "invalid_request"),
        ({"response_type": "token"}, "unsupported_response_type"),
        ({"code_challenge_method": "plain"}, "invalid_request"),
        ({"code_challenge": "short"}, "invalid_request"),
        ({"scope": "xeed:read xeed:write"}, "invalid_scope"),
        ({"resource": "https://other.example/mcp"}, "invalid_target"),
        ({"state": "s" * 513}, "invalid_request"),
    ],
)
def test_authorization_request_validation(
    oauth: OAuthService, override: dict[str, str], error: str
) -> None:
    client_id = _client(oauth)
    with pytest.raises(OAuthError) as exc:
        oauth.begin({**_params(client_id), **override}, now=NOW)
    assert exc.value.code == error


def test_code_flow_issues_read_only_tokens_bound_to_one_tenant(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    query = _code(oauth, client_id)
    assert query["state"] == ["s-1"]
    pair = _exchange(oauth, client_id, query["code"][0])
    wire = pair.to_wire()
    assert wire["scope"] == "xeed:read" and wire["expires_in"] == ACCESS_TTL.total_seconds()
    grant = oauth.authenticate(str(wire["access_token"]), now=NOW)
    assert grant is not None and (grant.principal_id, grant.tenant_id) == (ALICE, TENANT_A)
    assert oauth.authenticate(str(wire["access_token"]), now=NOW + ACCESS_TTL) is None
    assert oauth.authenticate(str(wire["refresh_token"]), now=NOW) is None
    assert (
        oauth.authenticate("", now=NOW) is None and oauth.authenticate("x" * 300, now=NOW) is None
    )


def test_denied_consent_returns_access_denied_without_code(oauth: OAuthService) -> None:
    query = _code(oauth, _client(oauth), approve=False)
    assert query == {"error": ["access_denied"], "state": ["s-1"]}


def test_requests_are_single_use_and_expire(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    request = oauth.begin(_params(client_id), now=NOW)
    with pytest.raises(OAuthError):
        oauth.pending(request.request_id, now=NOW + REQUEST_TTL)
    oauth.decide(request.request_id, principal_id=ALICE, tenant_id=TENANT_A, approve=True, now=NOW)
    with pytest.raises(OAuthError):
        oauth.decide(
            request.request_id, principal_id=BOB, tenant_id=TENANT_B, approve=True, now=NOW
        )
    late = oauth.begin(_params(client_id), now=NOW)
    with pytest.raises(OAuthError):
        oauth.decide(
            late.request_id,
            principal_id=ALICE,
            tenant_id=TENANT_A,
            approve=True,
            now=NOW + REQUEST_TTL,
        )


@pytest.mark.parametrize(
    "override",
    [
        {"code_verifier": "w" * 64},
        {"code_verifier": ""},
        {"redirect_uri": "https://claude.ai/other"},
        {"resource": "https://other.example/mcp"},
    ],
)
def test_code_exchange_requires_pkce_redirect_and_resource(
    oauth: OAuthService, override: dict[str, str]
) -> None:
    client_id = _client(oauth)
    code = _code(oauth, client_id)["code"][0]
    with pytest.raises(OAuthError):
        _exchange(oauth, client_id, code, **override)
    # The failed attempt consumed the code: it cannot be retried with the right values.
    with pytest.raises(OAuthError):
        _exchange(oauth, client_id, code)


def test_code_is_bound_to_its_client_single_use_and_short_lived(oauth: OAuthService) -> None:
    client_id, other = _client(oauth), _client(oauth)
    code = _code(oauth, client_id)["code"][0]
    with pytest.raises(OAuthError):
        _exchange(oauth, other, code)
    code = _code(oauth, client_id)["code"][0]
    _exchange(oauth, client_id, code)
    with pytest.raises(OAuthError):
        _exchange(oauth, client_id, code)
    code = _code(oauth, client_id)["code"][0]
    with pytest.raises(OAuthError):
        oauth.exchange(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "redirect_uri": REDIRECT,
                "code_verifier": VERIFIER,
            },
            now=NOW + CODE_TTL,
        )


def test_refresh_rotates_and_replay_revokes_the_grant(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    first = _exchange(oauth, client_id, _code(oauth, client_id)["code"][0]).to_wire()
    refresh = {"grant_type": "refresh_token", "refresh_token": first["refresh_token"]}
    with pytest.raises(OAuthError):
        oauth.exchange(refresh, now=NOW)  # public client must identify itself
    second = oauth.exchange({**refresh, "client_id": client_id}, now=NOW).to_wire()
    assert second["refresh_token"] != first["refresh_token"]
    assert oauth.authenticate(str(second["access_token"]), now=NOW) is not None
    with pytest.raises(OAuthError) as exc:
        oauth.exchange({**refresh, "client_id": client_id}, now=NOW)
    assert "reuse" in exc.value.description
    assert oauth.authenticate(str(second["access_token"]), now=NOW) is None
    with pytest.raises(OAuthError):
        oauth.exchange(
            {
                "grant_type": "refresh_token",
                "refresh_token": str(second["refresh_token"]),
                "client_id": client_id,
            },
            now=NOW,
        )


def test_refresh_token_expires(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    pair = _exchange(oauth, client_id, _code(oauth, client_id)["code"][0]).to_wire()
    with pytest.raises(OAuthError):
        oauth.exchange(
            {
                "grant_type": "refresh_token",
                "refresh_token": str(pair["refresh_token"]),
                "client_id": client_id,
            },
            now=NOW + REFRESH_TTL,
        )


def test_only_the_owner_can_revoke_and_list_a_connection(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    pair = _exchange(oauth, client_id, _code(oauth, client_id)["code"][0]).to_wire()
    (grant,) = oauth.connections(ALICE, TENANT_A)
    assert oauth.connections(BOB, TENANT_B) == ()
    assert oauth.connections(ALICE, TENANT_B) == ()
    assert not oauth.revoke(grant.grant_id, principal_id=BOB, tenant_id=TENANT_B, now=NOW)
    assert not oauth.revoke(grant.grant_id, principal_id=ALICE, tenant_id=TENANT_B, now=NOW)
    assert oauth.authenticate(str(pair["access_token"]), now=NOW) is not None
    assert oauth.revoke(grant.grant_id, principal_id=ALICE, tenant_id=TENANT_A, now=NOW)
    assert oauth.authenticate(str(pair["access_token"]), now=NOW) is None
    assert oauth.connections(ALICE, TENANT_A) == ()


def test_store_keeps_only_digests(oauth: OAuthService, tmp_path: Path) -> None:
    client_id = _client(oauth)
    pair = _exchange(oauth, client_id, _code(oauth, client_id)["code"][0]).to_wire()
    raw = (tmp_path / "mcp.sqlite3").read_bytes()
    for secret in (pair["access_token"], pair["refresh_token"]):
        assert str(secret).encode() not in raw
    assert digest(str(pair["access_token"])).encode() in raw


def test_unsupported_grant_type(oauth: OAuthService) -> None:
    with pytest.raises(OAuthError) as exc:
        oauth.exchange({"grant_type": "client_credentials"}, now=NOW)
    assert exc.value.code == "unsupported_grant_type"


def test_resource_must_be_https() -> None:
    with pytest.raises(ValueError):
        OAuthService(object(), resource="http://axignal.example/mcp")  # type: ignore[arg-type]


def test_expired_access_after_ttl_boundary(oauth: OAuthService) -> None:
    client_id = _client(oauth)
    pair = _exchange(oauth, client_id, _code(oauth, client_id)["code"][0]).to_wire()
    just_before = NOW + ACCESS_TTL - timedelta(seconds=1)
    assert oauth.authenticate(str(pair["access_token"]), now=just_before) is not None
