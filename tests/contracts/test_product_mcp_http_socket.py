"""The real runtime HTTP server routes the Product MCP safely (ADR-0086)."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from application.product_mcp.oauth import OAuthService
from application.product_mcp.server import McpDenied, ProductMcpServer
from pipeline.product_mcp.sqlite_store import SqliteProductMcpStore
from tools.runtime.product_mcp import MAX_BODY, ProductMcpHttp
from tools.runtime.service import RuntimeConfig, build_runtime, make_handler

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://axignal.example"
NOW = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)


class _NoMemory:
    def authorized_xeeds(self, context: object, *, now: datetime) -> tuple[()]:
        raise McpDenied("ENTITLEMENT_INACTIVE")

    def reading(self, context: object, xeed_id: str, *, now: datetime) -> dict[str, object]:
        raise McpDenied("XEED_NOT_AVAILABLE")


@pytest.fixture
def base(tmp_path: Path) -> Iterator[tuple[str, int]]:
    from http.server import ThreadingHTTPServer

    runtime = build_runtime(
        RuntimeConfig(
            environment="production",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="a" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=ROOT / "apps" / "web",
        )
    )
    store = SqliteProductMcpStore(tmp_path / "mcp.sqlite3")
    edge = ProductMcpHttp(
        origin=ORIGIN,
        oauth=OAuthService(store, resource=ORIGIN + "/mcp"),
        server=ProductMcpServer(_NoMemory(), clock=lambda: NOW, audit=store),  # type: ignore[arg-type]
        clock=lambda: NOW,
    )
    runtime.subscriber = SimpleNamespace(mcp_http=edge)  # type: ignore[assignment]
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield str(server.server_address[0]), int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def _send(
    base: tuple[str, int],
    method: str,
    path: str,
    body: bytes | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection(*base, timeout=5)
    try:
        connection.putrequest(method, path)
        for name, value in headers or []:
            connection.putheader(name, value)
        if body is not None and not any(n.lower() == "transfer-encoding" for n, _ in headers or []):
            connection.putheader("Content-Length", str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_discovery_and_unauthenticated_challenge_over_real_http(base: tuple[str, int]) -> None:
    status, _, body = _send(base, "GET", "/.well-known/oauth-protected-resource")
    assert status == 200 and json.loads(body)["resource"] == ORIGIN + "/mcp"
    status, _, body = _send(base, "GET", "/.well-known/oauth-authorization-server")
    metadata = json.loads(body)
    assert status == 200 and metadata["code_challenge_methods_supported"] == ["S256"]
    status, headers, _ = _send(base, "POST", "/mcp", b"{}", [("Content-Type", "application/json")])
    assert status == 401
    assert "resource_metadata=" in headers["WWW-Authenticate"]
    status, _, _ = _send(base, "DELETE", "/mcp", None, [("Authorization", "Bearer nope")])
    assert status == 401


def test_body_limits_and_ambiguous_requests_fail_closed(base: tuple[str, int]) -> None:
    big = b"{" + b" " * MAX_BODY + b"}"
    status, _, _ = _send(base, "POST", "/mcp", big, [("Content-Type", "application/json")])
    assert status == 413
    status, _, _ = _send(
        base,
        "POST",
        "/mcp",
        b"2\r\n{}\r\n0\r\n\r\n",
        [("Content-Type", "application/json"), ("Transfer-Encoding", "chunked")],
    )
    assert status == 400
    status, _, _ = _send(
        base,
        "POST",
        "/mcp",
        b"{}",
        [
            ("Content-Type", "application/json"),
            ("Authorization", "Bearer a"),
            ("Authorization", "Bearer b"),
        ],
    )
    assert status == 400


def test_authorize_never_redirects_to_an_unregistered_uri(base: tuple[str, int]) -> None:
    status, headers, _ = _send(
        base,
        "GET",
        "/oauth/authorize?client_id=mcp_unknown&redirect_uri=https%3A%2F%2Fevil.example%2F"
        "&response_type=code&code_challenge=" + "a" * 43 + "&code_challenge_method=S256",
    )
    assert status == 400 and "Location" not in headers


def test_access_log_keeps_the_path_only(
    base: tuple[str, int], capsys: pytest.CaptureFixture[str]
) -> None:
    _send(base, "GET", "/oauth/authorize?state=secret-state&code_challenge=secret-challenge")
    err = capsys.readouterr().err
    assert "product-mcp GET /oauth/authorize" in err
    assert "secret-state" not in err and "secret-challenge" not in err
