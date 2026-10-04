"""Credential-safe public source URI classification and projection."""

from __future__ import annotations

from urllib.parse import unquote_plus, urlsplit, urlunsplit

_EXACT_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "api-key",
        "authorization",
        "auth_token",
        "bearer_token",
        "client_secret",
        "credential",
        "key",
        "password",
        "passwd",
        "pwd",
        "secret",
        "signature",
        "sig",
        "token",
        "x_amz_credential",
        "x_amz_signature",
        "x_goog_credential",
        "x_goog_signature",
    }
)

_SENSITIVE_SUFFIXES = (
    "_token",
    "-token",
    "_secret",
    "-secret",
    "_password",
    "-password",
    "_credential",
    "-credential",
    "_signature",
    "-signature",
)


def _normalized_query_key(raw_key: str) -> str:
    return unquote_plus(raw_key).strip().lower()


def is_sensitive_query_key(raw_key: str) -> bool:
    key = _normalized_query_key(raw_key)
    return key in _EXACT_SENSITIVE_QUERY_KEYS or key.endswith(_SENSITIVE_SUFFIXES)


def public_acquisition_rejection_reason(uri: str) -> str | None:
    """Return a non-secret-bearing rejection reason for unsafe public acquisition URIs."""
    parsed = urlsplit(uri)
    if parsed.username is not None or parsed.password is not None:
        return "userinfo_not_allowed"
    for item in parsed.query.split("&"):
        if not item:
            continue
        raw_key = item.split("=", 1)[0]
        if is_sensitive_query_key(raw_key):
            return "credential_query_not_allowed"
    return None


def public_source_reference(uri: str) -> str:
    """Return a UI/persistence-safe source reference while retaining safe query semantics.

    Non-HTTP(S) references are returned unchanged because their authority is governed by
    their own adapter/domain contracts rather than public-network URL policy.
    """
    parsed = urlsplit(uri)
    if parsed.scheme not in {"http", "https"}:
        return uri

    safe_items = []
    for item in parsed.query.split("&"):
        if not item:
            continue
        raw_key = item.split("=", 1)[0]
        if not is_sensitive_query_key(raw_key):
            safe_items.append(item)

    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = hostname
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        netloc = f"{netloc}:{port}"

    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path or "/",
            "&".join(safe_items),
            "",
        )
    )
