"""TCP adapter for one runtime frontier journey; application services stay real."""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, overload

from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler
from tools.runtime.subscriber_http import SubscriberHttpResponse


@dataclass(frozen=True)
class WireResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


class TcpSubscriber:
    """Reuse subscriber/OAuth test clients while every request crosses real TCP."""

    def __init__(self, address: tuple[str, int], facade: Any) -> None:
        self.address = address
        self.identity = facade.identity
        self.mcp_http = self

    def wire(
        self,
        method: str,
        target: str,
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> WireResponse:
        connection = http.client.HTTPConnection(*self.address, timeout=5)
        try:
            connection.request(method, target, body=body, headers=dict(headers or {}))
            response = connection.getresponse()
            return WireResponse(response.status, tuple(response.getheaders()), response.read())
        finally:
            connection.close()

    @overload
    def handle(
        self, method: str, target: str, headers: Mapping[str, str], payload: bytes
    ) -> WireResponse: ...

    @overload
    def handle(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str],
        payload: dict[str, object] | None = None,
    ) -> SubscriberHttpResponse: ...

    def handle(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str],
        payload: dict[str, object] | bytes | None = None,
    ) -> SubscriberHttpResponse | WireResponse:
        if isinstance(payload, bytes):
            return self.wire(method, target, payload, headers)
        request_headers = dict(headers)
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        response = self.wire(method, target, body, request_headers)
        return SubscriberHttpResponse(response.status, json.loads(response.body))


@contextmanager
def serve(root: Path, facade: Any) -> Iterator[TcpSubscriber]:
    """Use the production handler and stores, with a composed test-port subscriber."""

    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="runtime-frontier-synthetic-e2e",
            data_dir=root,
            web_root=Path(__file__).resolve().parents[2] / "apps" / "web",
        )
    )
    runtime.subscriber = facade
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield TcpSubscriber((str(server.server_address[0]), int(server.server_address[1])), facade)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()
