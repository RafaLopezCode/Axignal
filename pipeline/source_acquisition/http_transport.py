"""Pinned-address HTTP transport with bounded raw response capture."""

from __future__ import annotations

import http.client
import socket
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass

from pipeline.source_acquisition.policy import ResolvedTarget


class SourceDeadlineExceeded(TimeoutError):
    """The governed source acquisition exceeded its monotonic deadline."""


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

    instrument_ref = "stdlib-pinned-http/0.2"

    def __init__(
        self,
        *,
        ssl_context: ssl.SSLContext | None = None,
        monotonic_ns: Callable[[], int] | None = None,
    ) -> None:
        self._ssl_context = ssl_context or ssl.create_default_context()
        self._monotonic_ns = monotonic_ns or time.monotonic_ns

    def _remaining_seconds(self, deadline_ns: int) -> float:
        remaining_ns = deadline_ns - self._monotonic_ns()
        if remaining_ns <= 0:
            raise SourceDeadlineExceeded("source acquisition deadline exceeded")
        return max(0.001, remaining_ns / 1_000_000_000)

    def _apply_remaining_timeout(
        self,
        connection: http.client.HTTPConnection,
        deadline_ns: int,
    ) -> None:
        remaining = self._remaining_seconds(deadline_ns)
        connection.timeout = remaining
        if connection.sock is not None:
            connection.sock.settimeout(remaining)

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        deadline_ns = self._monotonic_ns() + timeout_ms * 1_000_000
        errors: list[OSError] = []

        for address in target.addresses:
            connection: http.client.HTTPConnection
            remaining = self._remaining_seconds(deadline_ns)
            if target.scheme == "https":
                connection = _PinnedHTTPSConnection(
                    target.host,
                    target.port,
                    address,
                    remaining,
                    self._ssl_context,
                )
            else:
                connection = _PinnedHTTPConnection(
                    target.host,
                    target.port,
                    address,
                    remaining,
                )
            try:
                self._apply_remaining_timeout(connection, deadline_ns)
                connection.request(
                    "GET",
                    target.path_and_query,
                    headers={
                        "Host": target.host,
                        "User-Agent": "AXIGNAL-SourceObserver/0.2",
                        "Accept": "*/*",
                        "Accept-Encoding": "identity",
                        "Connection": "close",
                    },
                )
                self._apply_remaining_timeout(connection, deadline_ns)
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

                parts: list[bytes] = []
                total = 0
                failure: str | None = None
                while True:
                    self._apply_remaining_timeout(connection, deadline_ns)
                    remaining_bytes = max_response_bytes + 1 - total
                    if remaining_bytes <= 0:
                        failure = "response_too_large"
                        break
                    chunk = response.read1(min(65_536, remaining_bytes))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_response_bytes:
                        failure = "response_too_large"
                        break
                    parts.append(chunk)

                body = b"" if failure is not None else b"".join(parts)
                return RawHttpResponse(
                    status=response.status,
                    headers=headers,
                    body=body,
                    peer_ip=address,
                    failure_state=failure,
                )
            except SourceDeadlineExceeded:
                raise
            except (OSError, http.client.HTTPException) as exc:
                if self._monotonic_ns() >= deadline_ns:
                    raise SourceDeadlineExceeded("source acquisition deadline exceeded") from exc
                if isinstance(exc, OSError):
                    errors.append(exc)
                else:
                    errors.append(OSError(type(exc).__name__))
            finally:
                connection.close()

        if errors:
            raise OSError(f"all validated source addresses failed: {type(errors[-1]).__name__}")
        raise OSError("source policy returned no connectable address")
