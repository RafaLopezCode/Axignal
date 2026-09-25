"""Fail-closed URL and DNS guard for the isolated P0-SOURCE-01C trial."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
from urllib.parse import urlsplit


class PublicTargetRejected(ValueError):
    """A public trial URL did not satisfy its explicit dispatch policy."""


def validate_public_url(url: str) -> str:
    """Validate one exact experiment URL and resolve it only to public IPs."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise PublicTargetRejected("scheme_not_http_or_https")
    if parsed.username or parsed.password or not parsed.hostname:
        raise PublicTargetRejected("userinfo_or_missing_host")
    if parsed.port not in {None, 80, 443}:
        raise PublicTargetRejected("nonstandard_port")
    host = parsed.hostname.rstrip(".").lower()
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        raise PublicTargetRejected("ip_literal_not_allowed")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise PublicTargetRejected("localhost_not_allowed")

    allowed = json.loads(os.environ.get("P0_SOURCE01C_ALLOWED_TARGETS", "{}"))
    prefixes = allowed.get(host)
    if not prefixes or not any(
        parsed.path == prefix if prefix == "/" else parsed.path.startswith(prefix)
        for prefix in prefixes
    ):
        raise PublicTargetRejected("host_or_path_not_allowlisted")

    try:
        answers = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except OSError as exc:
        raise PublicTargetRejected(f"dns_resolution_failed:{type(exc).__name__}") from exc
    addresses = {answer[4][0].split("%", 1)[0] for answer in answers}
    if not addresses:
        raise PublicTargetRejected("dns_returned_no_addresses")
    for value in addresses:
        address = ipaddress.ip_address(value)
        if not address.is_global:
            raise PublicTargetRejected("dns_returned_nonpublic_address")
    return host
