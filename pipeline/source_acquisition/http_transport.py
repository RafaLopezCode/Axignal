"""Pinned-address HTTP transport with bounded raw response capture."""

from __future__ import annotations

import http.client
import socket
import ssl
from dataclasses import dataclass

from pipeline.source_acquisition.policy import ResolvedTarget


@dataclass(frozen=True, slots=True)
class RawHttpResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    peer_ip: str
    failure_state: str | None = None

    def header(self, name: str) -> str | None:
        wanted = name.lower()
        for key, value in self.headers:
            if key.lower() == wanted:
                return value
        return None


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, connect_ip: str, timeout: float) -> None:
        super().__init__(host=host, port=port, timeout=timeout)
        self._connect_ip = connect_ip

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._connect_ip, self.port),
            self.timeout,
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        host: str,
        port: int,
        connect_ip: str,
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(host=host, port=port, timeout=timeout, context=context)
        self._connect_ip = connect_ip
        self._ssl_context = context

    def connect(self) -> None:
        raw = socket.create_connection(
            (self._connect_ip, self.port),
            self.timeout,
        )
        self.sock = self._ssl_context.wrap_socket(raw, server_hostname=self.host)


class PinnedHttpTransport:
    """Direct GET transport. DNS decisions are supplied by the policy gate."""

    instrument_ref = "stdlib-pinned-http/0.1"

    def __init__(self, *, ssl_context: ssl.SSLContext | None = None) -> None:
        self._ssl_context = ssl_context or ssl.create_default_context()

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        errors: list[OSError] = []
        for address in target.addresses:
            connection: http.client.HTTPConnection
            if target.scheme == "https":
                connection = _PinnedHTTPSConnection(
                    target.host,
                    target.port,
                    address,
                    timeout_ms / 1000,
                    self._ssl_context,
                )
            else:
                connection = _PinnedHTTPConnection(
                    target.host,
                    target.port,
                    address,
                    timeout_ms / 1000,
                )
            try:
                connection.request(
                    "GET",
                    target.path_and_query,
                    headers={
                        "Host": target.host,
                        "User-Agent": "AXIGNAL-SourceObserver/0.1",
                        "Accept": "*/*",
                        "Accept-Encoding": "identity",
                        "Connection": "close",
                    },
                )
                response = connection.getresponse()
                headers = tuple((key, value) for key, value in response.getheaders())
                content_length = response.getheader("Content-Length")
                if content_length is not None:
                    try:
                        announced = int(content_length)
                    except ValueError:
                        announced = None
                    if announced is not None and announced > max_response_bytes:
                        return RawHttpResponse(
                            status=response.status,
                            headers=headers,
                            body=b"",
                            peer_ip=address,
                            failure_state="response_too_large",
                        )
                body = response.read(max_response_bytes + 1)
                if len(body) > max_response_bytes:
                    body = b""
                    failure = "response_too_large"
                else:
                    failure = None
                return RawHttpResponse(
                    status=response.status,
                    headers=headers,
                    body=body,
                    peer_ip=address,
                    failure_state=failure,
                )
            except (OSError, http.client.HTTPException) as exc:
                if isinstance(exc, OSError):
                    errors.append(exc)
                else:
                    errors.append(OSError(type(exc).__name__))
            finally:
                connection.close()

        if errors:
            raise OSError(f"all validated source addresses failed: {type(errors[-1]).__name__}")
        raise OSError("source policy returned no connectable address")
