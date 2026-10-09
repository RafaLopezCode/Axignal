"""Isolated, loopback-only browser candidate with SYNTHETIC source/provider ports.

Run from repository root using the dev environment. Never load production settings,
credentials or data. All business/runtime composition stays real; identity provider,
public website and System One responses are controlled fixtures, NOT quality evidence.
"""

from __future__ import annotations

import argparse
import json
import threading
import urllib.error
import urllib.request
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from tests.first_observation import harness
from tests.first_observation.harness import KNOWN, runtime
from tests.first_observation.test_first_observation_e2e import _attend
from tests.first_observation.test_understanding_e2e import (
    AFTER,
    BEFORE,
    SERVICES,
    controlled_facade,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--web-port", type=int, default=3840)
    parser.add_argument("--gateway-port", type=int, default=3841)
    parser.add_argument("--runtime-port", type=int, default=3842)
    args = parser.parse_args()
    if args.data_dir.exists():
        raise SystemExit("Use a new isolated data directory; existing data is refused.")
    args.data_dir.mkdir(parents=True)
    patch = pytest.MonkeyPatch()
    facade, world = controlled_facade(args.data_dir, patch)
    world.judge.name = "synthetic-system-one"
    world.judge.model = "SYNTHETIC-offer-rule-v1"
    token, _added = _attend(facade, args.data_dir, "synthetic:browser-review", KNOWN)
    runtime(facade).drain()
    origin = f"http://127.0.0.1:{args.gateway_port}"
    facade.settings = replace(facade.settings, origin=origin)

    class RuntimeHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *values: object) -> None:
            pass  # No authorization/callback data in logs.

        def dispatch(self) -> None:
            payload = None
            if self.command == "POST":
                size = int(self.headers.get("Content-Length", "0"))
                if size > 4096:
                    self.send_error(413)
                    return
                payload = json.loads(self.rfile.read(size))
            response = facade.handle(
                self.command, urlsplit(self.path).path, dict(self.headers), payload
            )
            body = json.dumps(response.body, ensure_ascii=False).encode()
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            if self.command == "POST":
                runtime(facade).drain()

        do_GET = dispatch
        do_POST = dispatch

    class Gateway(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *values: object) -> None:
            pass

        def dispatch(self) -> None:
            path = urlsplit(self.path).path
            if path == "/__synthetic":
                body = (
                    "<!doctype html><html lang='en'><meta name='viewport' content='width=device-width'>"
                    "<title>AXIGNAL synthetic candidate 064</title><body><h1>Isolated synthetic candidate</h1>"
                    "<p>Controlled website, identity and interpretation instrument. No production data, "
                    "real Google login or real-client quality claim.</p><p><a href='/account'>Open subscriber</a></p>"
                    "<p>Choose a controlled source condition, then use Reobserve in the subscriber page.</p>"
                    "<a href='/__synthetic/clear'>Clear communication</a> · "
                    "<a href='/__synthetic/minimal'>Minimal communication</a> · "
                    "<a href='/__synthetic/missing'>Acquisition failure</a> · "
                    "<a href='/__synthetic/error'>Instrument failure</a></body></html>"
                ).encode()
                self.send_response(200)
                self.send_header(
                    "Set-Cookie",
                    f"__Host-axignal-subscriber={token}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=3600",
                )
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if path.startswith("/__synthetic/"):
                world.judge.fail = None
                mode = path.rsplit("/", 1)[1]
                harness.PAGES[SERVICES] = AFTER if mode == "clear" else BEFORE
                if mode == "missing":
                    harness.PAGES.pop(SERVICES, None)
                if mode == "error":
                    world.judge.fail = "SYNTHETIC_INSTRUMENT_FAILURE"
                    # Changed source state avoids a valid cached response hiding the error.
                    harness.PAGES[SERVICES] = BEFORE.replace("panels.", "panels today.")
                self.send_response(303)
                self.send_header("Location", "/account")
                self.end_headers()
                return
            size = int(self.headers.get("Content-Length", "0"))
            if size > 65536:
                self.send_error(413)
                return
            payload = self.rfile.read(size) if size else None
            headers = {
                k: v
                for k, v in self.headers.items()
                if k.lower() not in {"host", "connection", "accept-encoding", "content-length"}
            }
            headers["Host"] = f"127.0.0.1:{args.gateway_port}"
            req = urllib.request.Request(
                f"http://127.0.0.1:{args.web_port}{self.path}",
                data=payload,
                headers=headers,
                method=self.command,
            )
            try:
                response = urllib.request.urlopen(req, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            body = response.read()
            self.send_response(response.status)
            for key, value in response.headers.items():
                if key.lower() not in {
                    "transfer-encoding",
                    "content-length",
                    "connection",
                    "content-encoding",
                }:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = dispatch
        do_POST = dispatch

    backend = ThreadingHTTPServer(("127.0.0.1", args.runtime_port), RuntimeHandler)
    threading.Thread(target=backend.serve_forever, daemon=True).start()
    print(f"SYNTHETIC_ONLY; candidate={origin}/__synthetic; no production mounts", flush=True)
    with ThreadingHTTPServer(("127.0.0.1", args.gateway_port), Gateway) as gateway:
        gateway.serve_forever()


if __name__ == "__main__":
    main()
