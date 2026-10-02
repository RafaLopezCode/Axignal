from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler


def _runtime(tmp_path: Path, *, enabled: bool):
    root = Path(__file__).resolve().parents[2]
    return build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="a" * 40,
            data_dir=tmp_path / ("enabled" if enabled else "disabled"),
            web_root=root / "apps" / "web",
            weekly_brief_requests_enabled=enabled,
        )
    )


def _serve(runtime):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_weekly_brief_public_ingress_is_closed_by_default(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=False)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request("GET", "/api/weekly-brief/status")
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read()) == {"enabled": False}

        connection.request(
            "POST",
            "/api/weekly-brief/requests",
            body=b"{}",
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 404
        assert runtime.admin_acquisition_store.all_events() == ()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_enabled_weekly_brief_ingress_persists_request_and_consent(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=True)
    server, thread = _serve(runtime)
    payload = {
        "companyName": "Acme Industrial",
        "companyDomain": "acme.example",
        "professionalEmail": "contact@acme.example",
        "purpose": "Observe material public changes.",
        "requestNoticeVersion": "weekly-brief-request-v1",
        "newsletterConsent": True,
        "newsletterNoticeVersion": "weekly-newsletter-consent-v1",
    }
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request(
            "POST",
            "/api/weekly-brief/requests",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        assert response.status == 202
        assert body["status"] == "received"
        assert body["reviewState"] == "REQUESTED"
        assert "professionalEmail" not in body
        assert len(runtime.admin_acquisition_store.all_events()) == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
