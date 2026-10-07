"""Edge routing contract for the subscriber Product MCP (ADR-0086)."""

from __future__ import annotations

import re
from pathlib import Path

from tools.runtime.product_mcp import ProductMcpHttp

ROOT = Path(__file__).resolve().parents[2]
EDGE = (ROOT / "deploy" / "production" / "subscriber-edge-nginx.conf").read_text(encoding="utf-8")
MCP_PATHS = (
    "/mcp",
    "/oauth/register",
    "/oauth/authorize",
    "/oauth/token",
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/oauth-protected-resource/mcp",
)


def _block(path: str) -> str:
    match = re.search(r"location = " + re.escape(path) + r" \{(.*?)\n    \}", EDGE, re.S)
    assert match, path
    return match.group(1)


def test_every_mcp_path_is_an_exact_runtime_route() -> None:
    for path in MCP_PATHS:
        assert ProductMcpHttp.handles(path), path
        block = _block(path)
        assert "proxy_pass http://axignal_runtime;" in block, path
        assert "axignal_experience" not in block, path


def test_mcp_routing_is_not_widened() -> None:
    assert "location ^~ /.well-known" not in EDGE
    assert "location /.well-known" not in EDGE
    assert "location ^~ /oauth" not in EDGE
    assert "location /oauth" not in EDGE
    assert "location ^~ /mcp" not in EDGE
    assert "location ^~ /subscriber/" not in EDGE  # runtime subscriber API stays behind Next


def test_write_only_and_read_only_methods_are_bounded() -> None:
    for path in ("/oauth/register", "/oauth/token"):
        assert "limit_except POST { deny all; }" in _block(path)
        assert "client_max_body_size 64k;" in _block(path)
    for path in (*MCP_PATHS[4:], "/oauth/authorize"):
        assert "limit_except GET { deny all; }" in _block(path)
    assert "client_max_body_size 64k;" in _block("/mcp")
