"""Fail-closed public-network dispatch policy for source acquisition."""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import SplitResult, unquote, urlsplit, urlunsplit

from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceTargetRule,
)


class SourcePolicyRejected(ValueError):
    """The target is not authorized for public-network dispatch."""


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    uri: str
    scheme: str
    host: str
    port: int
    path_and_query: str
    addresses: tuple[str, ...]


def _normalized_host(host: str) -> str:
    return host.rstrip(".").encode("idna").decode("ascii").lower()


def _path_allowed(path: str, prefix: str) -> bool:
    if prefix == "/":
        return True
    normalized = prefix.rstrip("/")
    return path == normalized or path.startswith(f"{normalized}/")


def _decoded_safe_path(path: str) -> str:
    decoded = unquote(path or "/")
    if "\\" in decoded or any(ord(char) < 32 for char in decoded):
        raise SourcePolicyRejected("unsafe_path_encoding")
    if re.search(r"%[0-9a-fA-F]{2}", decoded):
        raise SourcePolicyRejected("ambiguous_path_encoding")
    if any(segment in {".", ".."} for segment in decoded.split("/")):
        raise SourcePolicyRejected("dot_segment_not_allowed")
    return decoded


def _matches(rule: SourceTargetRule, parsed: SplitResult, host: str) -> bool:
    path = _decoded_safe_path(parsed.path)
    prefix = _decoded_safe_path(rule.path_prefix)
    return (
        host == _normalized_host(rule.host)
        and parsed.scheme in rule.schemes
        and _path_allowed(path, prefix)
    )


class PublicSourcePolicyGate:
    """Resolve each authorized hop and reject every non-public address."""

    def resolve(self, uri: str, policy: SourceDispatchPolicy) -> ResolvedTarget:
        if policy.disposition is not DispatchDisposition.ALLOW:
            raise SourcePolicyRejected("policy_denied")

        parsed = urlsplit(uri)
        if parsed.scheme not in {"http", "https"}:
            raise SourcePolicyRejected("scheme_not_http_or_https")
        if parsed.username or parsed.password or not parsed.hostname:
            raise SourcePolicyRejected("userinfo_or_missing_host")
        if parsed.fragment:
            raise SourcePolicyRejected("fragment_not_allowed")
        try:
            parsed_port = parsed.port
        except ValueError as exc:
            raise SourcePolicyRejected("invalid_port") from exc
        if parsed_port not in {None, 80, 443}:
            raise SourcePolicyRejected("nonstandard_port")
        expected_port = 443 if parsed.scheme == "https" else 80
        if parsed_port is not None and parsed_port != expected_port:
            raise SourcePolicyRejected("scheme_port_mismatch")

        host = _normalized_host(parsed.hostname)
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise SourcePolicyRejected("ip_literal_not_allowed")
        if host == "localhost" or host.endswith(".localhost"):
            raise SourcePolicyRejected("localhost_not_allowed")
        if not any(_matches(rule, parsed, host) for rule in policy.targets):
            raise SourcePolicyRejected("host_path_or_scheme_not_authorized")

        port = parsed_port or (443 if parsed.scheme == "https" else 80)
        try:
            answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise SourcePolicyRejected(f"dns_resolution_failed:{type(exc).__name__}") from exc
        addresses = tuple(sorted({str(answer[4][0]).split("%", 1)[0] for answer in answers}))
        if not addresses:
            raise SourcePolicyRejected("dns_returned_no_addresses")
        if any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise SourcePolicyRejected("dns_returned_nonpublic_address")

        path_and_query = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        canonical_uri = urlunsplit((parsed.scheme, host, parsed.path or "/", parsed.query, ""))
        return ResolvedTarget(
            uri=canonical_uri,
            scheme=parsed.scheme,
            host=host,
            port=port,
            path_and_query=path_and_query,
            addresses=addresses,
        )
