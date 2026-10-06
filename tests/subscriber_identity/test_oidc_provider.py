from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qs
from urllib.request import Request

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from application.subscriber_identity.runtime import (
    AuthIntent,
    OidcProviderConfig,
    OidcProviderId,
    OidcTransaction,
)
from pipeline.subscriber_identity import oidc_provider
from pipeline.subscriber_identity.oidc_provider import ConfiguredOidcProvider, OidcProtocolError


def _config(provider: OidcProviderId, secret_path: Path | None = None) -> OidcProviderConfig:
    openai = provider is OidcProviderId.OPENAI
    return OidcProviderConfig(
        provider_id=provider,
        issuer="https://auth.openai.com" if openai else "https://accounts.google.com",
        client_id="oaiapp_test" if openai else "google-client",
        redirect_uri="https://axignal.com/api/auth/callback/openai"
        if openai
        else "https://axignal.com/api/auth/callback/google",
        enabled=True,
        registered=True,
        authorization_endpoint="https://auth.openai.com/oauth/authorize"
        if openai
        else "https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://auth.openai.com/oauth/token"
        if openai
        else "https://oauth2.googleapis.com/token",
        jwks_uri="https://auth.openai.com/.well-known/jwks.json"
        if openai
        else "https://www.googleapis.com/oauth2/v3/certs",
        client_secret_path=secret_path,
    )


def _transaction(config: OidcProviderConfig) -> OidcTransaction:
    now = datetime.now(UTC)
    return OidcTransaction(
        config.provider_id,
        config.client_id,
        config.redirect_uri,
        "state-digest",
        "expected-nonce",
        "pkce-verifier",
        AuthIntent.LOGIN,
        now,
        now + timedelta(minutes=10),
    )


def test_openai_token_exchange_uses_client_secret_basic_and_bounded_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_path = tmp_path / "oauth-client-secret.txt"
    secret_path.write_text("private-value", encoding="utf-8")
    provider = ConfiguredOidcProvider()
    config = _config(OidcProviderId.OPENAI, secret_path)
    captured: dict[str, object] = {}

    def read_json(request: Request) -> dict[str, object]:
        captured["request"] = request
        return {"id_token": "fake.jwt.token"}

    monkeypatch.setattr(provider, "_read_json_response", read_json)
    provider._exchange_code(config, _transaction(config), "authorization-code")
    request = captured["request"]
    assert isinstance(request, Request)
    auth = request.get_header("Authorization")
    assert auth is not None and auth.startswith("Basic ")
    assert base64.b64decode(auth.removeprefix("Basic ")).decode() == "oaiapp_test:private-value"
    body = parse_qs(request.data.decode("ascii"))
    assert "client_secret" not in body
    assert "client_id" not in body
    assert body["code"] == ["authorization-code"]
    assert "private-value" not in repr(request)


def test_token_exchange_rejects_cross_host_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = ConfiguredOidcProvider()
    redirect_seen: list[bool] = []

    class RedirectingOpener:
        def open(self, request, timeout):
            redirect_seen.append(True)
            raise HTTPError(
                request.full_url,
                302,
                "Found",
                Message(),
                BytesIO(b""),
            )

    def make_opener(handler):
        assert isinstance(handler, oidc_provider._NoRedirect)
        return RedirectingOpener()

    monkeypatch.setattr(oidc_provider, "build_opener", make_opener)
    with pytest.raises(OidcProtocolError):
        provider._read_json_response(Request("https://auth.openai.com/oauth/token"))
    assert redirect_seen == [True]


def test_token_exchange_rejects_oversized_provider_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = ConfiguredOidcProvider()

    class OversizedResponse:
        status = 200

        def __init__(self):
            self.headers = {"Content-Length": "1048577"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, limit):
            assert limit == 1_048_577
            return b"{}" * (limit // 2)

    class Opener:
        def open(self, request, timeout):
            return OversizedResponse()

    monkeypatch.setattr(oidc_provider, "build_opener", lambda handler: Opener())
    with pytest.raises(OidcProtocolError):
        provider._read_json_response(Request("https://auth.openai.com/oauth/token"))


def _provider_with_key(monkeypatch: pytest.MonkeyPatch, public_key):
    class FakeJwkClient:
        def __init__(self, uri, **kwargs):
            assert uri.startswith("https://")
            assert kwargs["timeout"] > 0

        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr(jwt, "PyJWKClient", FakeJwkClient)


def _signed_token(
    private_key,
    *,
    nonce: str = "expected-nonce",
    issuer: str = "https://auth.openai.com",
    audience="oaiapp_test",
) -> str:
    now = int(datetime.now(UTC).timestamp())
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "subscriber-subject",
            "aud": audience,
            "exp": now + 120,
            "iat": now,
            "nonce": nonce,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def test_verified_oidc_signature_and_required_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _provider_with_key(monkeypatch, private_key.public_key())
    provider = ConfiguredOidcProvider()
    config = _config(OidcProviderId.OPENAI)
    transaction = _transaction(config)
    token = _signed_token(private_key)
    monkeypatch.setattr(provider, "_exchange_code", lambda *_: {"id_token": token})
    identity = provider.exchange_and_verify(config, transaction, "code")
    assert identity.issuer == config.issuer
    assert identity.subject == "subscriber-subject"


@pytest.mark.parametrize(
    ("nonce", "issuer", "audience"),
    [
        ("wrong-nonce", "https://auth.openai.com", "oaiapp_test"),
        ("expected-nonce", "https://evil.example", "oaiapp_test"),
        ("expected-nonce", "https://auth.openai.com", "other-client"),
    ],
)
def test_oidc_claim_mismatch_is_non_authorizing(
    monkeypatch: pytest.MonkeyPatch,
    nonce: str,
    issuer: str,
    audience: str,
) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _provider_with_key(monkeypatch, private_key.public_key())
    provider = ConfiguredOidcProvider()
    config = _config(OidcProviderId.OPENAI)
    token = _signed_token(private_key, nonce=nonce, issuer=issuer, audience=audience)
    monkeypatch.setattr(provider, "_exchange_code", lambda *_: {"id_token": token})
    with pytest.raises(OidcProtocolError):
        provider.exchange_and_verify(config, _transaction(config), "code")


def test_oidc_signature_mismatch_is_non_authorizing(monkeypatch: pytest.MonkeyPatch) -> None:
    trusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _provider_with_key(monkeypatch, trusted_key.public_key())
    provider = ConfiguredOidcProvider()
    config = _config(OidcProviderId.OPENAI)
    token = _signed_token(other_key)
    monkeypatch.setattr(provider, "_exchange_code", lambda *_: {"id_token": token})
    with pytest.raises(OidcProtocolError):
        provider.exchange_and_verify(config, _transaction(config), "code")
