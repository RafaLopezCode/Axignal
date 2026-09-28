"""Loopback-only HTTP server for the P0-HFX-01 synthetic browser demo.

This test/dev entry point has no production auth, database, API, or external
provider. It creates a synthetic TrustedRequestContext and invokes the real
domain/application readers before sending a minimum allowlisted projection.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from tests.support.hfx01_demo import Hfx01Demo

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPOSITORY_ROOT / "apps" / "web" / "subscriber"
DESIGN_ROOT = REPOSITORY_ROOT / "apps" / "web" / "design-system"
BRAND_ROOT = WEB_ROOT / "assets" / "brand"


def serialize_projection(projection: Any) -> dict[str, Any]:
    """Serialize only subscriber-approved direct fields; never Evidence refs."""

    return {
        "realityLevel": projection.reality_level,
        "context": {
            "id": projection.xeed_id,
            "label": projection.xeed_label,
        },
        "organization": {
            "id": projection.organization.identity,
            "name": projection.organization.label,
            "capabilities": list(projection.organization.capabilities),
            "markets": list(projection.organization.markets),
        },
        "nodes": [
            {
                "id": node.identity,
                "kind": node.node_kind,
                "label": node.label,
                "subjectId": node.subject_id,
                "predicate": node.predicate,
                "objectOrValue": node.object_or_value,
                "epistemicState": node.epistemic_state,
                "currentness": node.currentness,
                "observedAt": node.observed_at,
                "subjectKind": node.subject_kind.value,
                "subjectResolution": node.subject_resolution.value,
                "semanticRelationships": node.semantic_relationships.value,
                "cardinalAssignment": node.cardinal_assignment.value,
                "evidenceAccess": node.evidence_access.value,
                "provenance": node.provenance.value,
                "membership": node.membership_status.value,
            }
            for node in projection.faxt_nodes
        ],
        "memberships": [
            {
                "from": projection.xeed_id,
                "to": node.identity,
                "meaning": "XeedFaxtReference",
            }
            for node in projection.faxt_nodes
        ],
    }


class _Handler(BaseHTTPRequestHandler):
    server_version = "AXIGNAL-HFX01-Demo/1.0"
    demo = Hfx01Demo()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/subscriber-context":
            self._serve_projection()
            return
        if path == "/api/demo/empty":
            self._serve_projection(empty_context=True)
            return
        if path == "/api/demo/unavailable":
            self._send_json(503, {"error": "AXIGLAND projection unavailable."})
            return

        static_files = {
            "/": WEB_ROOT / "index.html",
            "/index.html": WEB_ROOT / "index.html",
            "/app.js": WEB_ROOT / "app.js",
            "/presentation.js": WEB_ROOT / "presentation.js",
            "/subscriber.css": WEB_ROOT / "subscriber.css",
            "/design-system/global.css": DESIGN_ROOT / "global.css",
            "/design-system/tokens.css": DESIGN_ROOT / "tokens.css",
            "/brand/logo-light.svg": BRAND_ROOT / "logo-light.svg",
            "/brand/logo-dark.svg": BRAND_ROOT / "logo-dark.svg",
            "/brand/isotope.svg": BRAND_ROOT / "isotope.svg",
            "/brand/favicon.svg": BRAND_ROOT / "favicon.svg",
            "/brand/favicon-16x16.png": BRAND_ROOT / "favicon-16x16.png",
            "/brand/favicon-32x32.png": BRAND_ROOT / "favicon-32x32.png",
            "/brand/favicon.ico": BRAND_ROOT / "favicon.ico",
        }
        source = static_files.get(path)
        if source is None or not source.is_file():
            self.send_error(404)
            return

        content_type = {
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/vnd.microsoft.icon",
        }.get(source.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(source.stat().st_size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", _csp())
        self.end_headers()
        self.wfile.write(source.read_bytes())

    def _serve_projection(self, *, empty_context: bool = False) -> None:
        try:
            projection = (
                self.demo.empty_demo_projection()
                if empty_context
                else self.demo.selected_demo_projection()
            )
            self._send_json(200, serialize_projection(projection))
        except Exception:  # a local demo fails closed with no cross-context detail
            self._send_json(503, {"error": "AXIGLAND projection unavailable."})

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", _csp())
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _csp() -> str:
    return "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be 0..65535")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), _Handler)
    except OSError:
        if args.port == 0:
            raise
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    print(f"P0-HFX-01 synthetic test/dev server: http://127.0.0.1:{server.server_port}/")
    print("Reality level: TEST_DEV_IN_MEMORY_AUTHORITY; no external services.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
