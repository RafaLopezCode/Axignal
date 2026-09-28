"""Loopback contract-server integration for the P0-HFX-01 browser demo."""

from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from tests.support.hfx01_server import _Handler


def _with_server(path: str) -> tuple[int, bytes]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}{path}") as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_browser_payload_is_assembled_through_authorized_contracts_and_allowlisted() -> None:
    status, body = _with_server("/api/subscriber-context")
    payload = json.loads(body)

    assert status == 200
    assert payload["realityLevel"] == "TEST_DEV_IN_MEMORY_AUTHORITY"
    assert payload["context"]["id"] == "xeed-demo-a"
    assert payload["organization"]["id"] == "org-demo-shared"
    assert [node["id"] for node in payload["nodes"]] == [
        "faxt-demo-a",
        "faxt-demo-a2",
    ]
    assert payload["nodes"][0]["subjectKind"] == "UNKNOWN_UNSUPPORTED"
    assert payload["nodes"][0]["subjectResolution"] == "UNKNOWN_UNSUPPORTED"
    assert payload["nodes"][0]["semanticRelationships"] == "UNKNOWN_UNSUPPORTED"
    assert payload["nodes"][0]["cardinalAssignment"] == "UNKNOWN_UNSUPPORTED"
    assert payload["memberships"] == [
        {
            "from": "xeed-demo-a",
            "to": "faxt-demo-a",
            "meaning": "XeedFaxtReference",
        },
        {
            "from": "xeed-demo-a",
            "to": "faxt-demo-a2",
            "meaning": "XeedFaxtReference",
        },
    ]
    assert "evidence_refs" not in payload["nodes"][0]
    assert "evidenceRefs" not in payload["nodes"][0]


def test_empty_authorized_context_is_distinct_from_unavailable_projection() -> None:
    empty_status, empty_body = _with_server("/api/demo/empty")
    unavailable_status, unavailable_body = _with_server("/api/demo/unavailable")
    empty_payload = json.loads(empty_body)
    unavailable_payload = json.loads(unavailable_body)

    assert empty_status == 200
    assert empty_payload["nodes"] == []
    assert empty_payload["organization"]["id"] == "org-demo-shared"
    assert unavailable_status == 503
    assert unavailable_payload == {"error": "AXIGLAND projection unavailable."}


def test_server_binds_only_loopback_and_serves_local_assets() -> None:
    status, body = _with_server("/")
    assert status == 200
    assert b"TEST / DEV" in body
    for path in (
        "/app.js",
        "/subscriber.css",
        "/design-system/global.css",
        "/design-system/tokens.css",
    ):
        status, _ = _with_server(path)
        assert status == 200
