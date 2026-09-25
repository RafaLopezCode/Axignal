"""Tests for exact-host public target controls used only by P0-SOURCE-01C."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

GUARD_PATH = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "source-acquisition-bakeoff"
    / "public_guard.py"
)
SPEC = importlib.util.spec_from_file_location("p0_source01c_public_guard", GUARD_PATH)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)
PublicTargetRejected = GUARD.PublicTargetRejected
validate_public_url = GUARD.validate_public_url


def test_public_guard_rejects_reserved_dns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "P0_SOURCE01C_ALLOWED_TARGETS",
        json.dumps({"docs.example.org": ["/guide/"]}),
    )
    monkeypatch.setattr(
        GUARD.socket,
        "getaddrinfo",
        lambda *_args: [(None, None, None, None, ("203.0.113.2", 443))],
    )
    # 203.0.113.2 is reserved documentation space, so it must be rejected.
    with pytest.raises(PublicTargetRejected, match="nonpublic"):
        validate_public_url("https://docs.example.org/guide/start.html")


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("file:///C:/Windows/win.ini", "scheme_not_http_or_https"),
        ("http://localhost/", "localhost_not_allowed"),
        ("https://127.0.0.1/", "ip_literal_not_allowed"),
        ("https://docs.example.org:8443/guide/", "nonstandard_port"),
    ],
)
def test_public_guard_rejects_forbidden_url_forms(
    monkeypatch: pytest.MonkeyPatch, url: str, reason: str
) -> None:
    monkeypatch.setenv(
        "P0_SOURCE01C_ALLOWED_TARGETS",
        json.dumps({"docs.example.org": ["/guide/"]}),
    )
    with pytest.raises(PublicTargetRejected, match=reason):
        validate_public_url(url)


def test_public_guard_rejects_unallowlisted_host_or_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "P0_SOURCE01C_ALLOWED_TARGETS",
        json.dumps({"docs.example.org": ["/guide/"]}),
    )
    with pytest.raises(PublicTargetRejected, match="host_or_path"):
        validate_public_url("https://docs.example.org/admin/")
