"""Configured OIDC code-flow adapter with library-verified ID tokens."""

from __future__ import annotations

import base64
import hmac
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from application.subscriber_identity.runtime import (
    OidcProviderConfig,
    OidcTransaction,
    VerifiedExternalIdentity,
)


class OidcProtocolError(Exception):
    """Sanitized provider protocol failure; does not include code or token data."""

    def __init__(self) -> None:
        super().__init__("OIDC provider exchange or validation failed")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: object,
        code: int,
        msg: str,
        headers: Message,
        new_url: str,
    ) -> Request | None:
        return None


class ConfiguredOidcProvider:
    """Authorization Code + PKCE provider using PyJWT for JOSE verification."""

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("OIDC timeout must be positive")
        self._timeout = timeout_seconds

    @staticmethod
    def _https_endpoint(value: str) -> bool:
        parsed = urlparse(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )

    @classmethod
    def _endpoint_allowed(cls, config: OidcProviderConfig, value: str) -> bool:
        if not cls._https_endpoint(value):
            return False
        host = urlparse(value).hostname
        hosts = (
            {"accounts.google.com", "oauth2.googleapis.com", "www.googleapis.com"}
            if config.provider_id.value == "google"
            else {"auth.openai.com"}
        )
        return host in hosts

    def _read_json_response(self, request: Request) -> dict[str, object]:
        opener = build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=self._timeout) as response:
                if response.status != 200:
                    raise OidcProtocolError
                content_length = response.headers.get("Content-Length")
                if content_length is not None and int(content_length) > 1_048_576:
                    raise OidcProtocolError
                raw_payload = response.read(1_048_577)
                if len(raw_payload) > 1_048_576:
                    raise OidcProtocolError
                payload = json.loads(raw_payload)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
            raise OidcProtocolError from None
        if not isinstance(payload, dict):
            raise OidcProtocolError
        return payload

    def authorization_url(
        self,
        config: OidcProviderConfig,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        if not self._endpoint_allowed(config, config.authorization_endpoint):
            raise OidcProtocolError
        parameters = urlencode(
            {
                "client_id": config.client_id,
                "redirect_uri": config.redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        separator = "&" if "?" in config.authorization_endpoint else "?"
        return f"{config.authorization_endpoint}{separator}{parameters}"

    @staticmethod
    def _client_secret(config: OidcProviderConfig) -> str | None:
        if config.client_secret_path is None:
            return None
        try:
            secret = Path(config.client_secret_path).read_text(encoding="utf-8").strip()
        except OSError:
            raise OidcProtocolError from None
        return secret or None

    def _exchange_code(
        self,
        config: OidcProviderConfig,
        transaction: OidcTransaction,
        code: str,
    ) -> dict[str, object]:
        if not self._endpoint_allowed(config, config.token_endpoint):
            raise OidcProtocolError
        body: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": transaction.redirect_uri,
            "code_verifier": transaction.pkce_verifier,
        }
        secret = self._client_secret(config)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if config.provider_id.value == "openai":
            if secret is None:
                raise OidcProtocolError
            basic_pair = f"{quote_plus(config.client_id)}:{quote_plus(secret)}".encode("ascii")
            headers["Authorization"] = f"Basic {base64.b64encode(basic_pair).decode('ascii')}"
        else:
            body["client_id"] = config.client_id
            if secret is not None:
                body["client_secret"] = secret
        request = Request(
            config.token_endpoint,
            data=urlencode(body).encode("ascii"),
            headers=headers,
            method="POST",
        )
        return self._read_json_response(request)

    def exchange_and_verify(
        self,
        config: OidcProviderConfig,
        transaction: OidcTransaction,
        code: str,
    ) -> VerifiedExternalIdentity:
        if (
            transaction.client_id != config.client_id
            or transaction.redirect_uri != config.redirect_uri
        ):
            raise OidcProtocolError
        payload = self._exchange_code(config, transaction, code)
        id_token = payload.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OidcProtocolError
        try:
            import jwt

            self_outer = self

            class StrictPyJWKClient(jwt.PyJWKClient):
                def fetch_data(self) -> dict[str, object]:
                    if not ConfiguredOidcProvider._endpoint_allowed(config, self.uri):
                        raise OidcProtocolError
                    request = Request(self.uri, headers={"Accept": "application/json"})
                    return self_outer._read_json_response(request)

            signing_key = StrictPyJWKClient(
                config.jwks_uri,
                cache_jwk_set=True,
                timeout=self._timeout,
            ).get_signing_key_from_jwt(id_token)
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=list(config.allowed_algorithms),
                audience=config.client_id,
                issuer=config.issuer,
                options={
                    "require": ["iss", "sub", "aud", "exp", "iat", "nonce"],
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
                leeway=60,
            )
        except Exception:
            raise OidcProtocolError from None
        nonce = claims.get("nonce")
        subject = claims.get("sub")
        if (
            not isinstance(nonce, str)
            or not hmac.compare_digest(nonce, transaction.nonce)
            or not isinstance(subject, str)
            or not subject.strip()
        ):
            raise OidcProtocolError
        authorized_party = claims.get("azp")
        audience = claims.get("aud")
        if authorized_party is not None and authorized_party != config.client_id:
            raise OidcProtocolError
        if (
            isinstance(audience, list)
            and len(audience) > 1
            and authorized_party != config.client_id
        ):
            raise OidcProtocolError
        return VerifiedExternalIdentity(config.issuer, subject)


__all__ = ["ConfiguredOidcProvider", "OidcProtocolError"]
