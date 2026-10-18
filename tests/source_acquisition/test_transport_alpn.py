"""The website transport declares the protocol it speaks (ALPN http/1.1).

Without it Shopify storefronts answered 429 to every request (ecoalf.com,
tonyschocolonely.com, einhorn.my, mymuesli.com; 2026-10-18), while the same request through
the standard library, which declares it, got 200: their sites were read only via archives.
"""

from __future__ import annotations

import ssl
from typing import Any

import pytest

from pipeline.source_acquisition import http_transport


def test_the_default_tls_context_declares_http_1_1(monkeypatch: pytest.MonkeyPatch) -> None:
    declared: list[list[str]] = []
    real = ssl.create_default_context

    def spy(*args: Any, **kwargs: Any) -> ssl.SSLContext:
        context = real(*args, **kwargs)

        class Watched:
            def __getattr__(self, name: str) -> Any:
                return getattr(context, name)

            def set_alpn_protocols(self, protocols: list[str]) -> None:
                declared.append(list(protocols))
                context.set_alpn_protocols(protocols)

        return Watched()  # type: ignore[return-value]

    monkeypatch.setattr(http_transport.ssl, "create_default_context", spy)
    http_transport.PinnedHttpTransport()
    assert declared == [["http/1.1"]]


def test_a_caller_supplied_context_is_used_as_given() -> None:
    context = ssl.create_default_context()
    transport = http_transport.PinnedHttpTransport(ssl_context=context)
    assert transport._ssl_context is context
