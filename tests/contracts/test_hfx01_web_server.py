"""Loopback contract-server integration for the P0-HFX-01 browser demo."""

from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from tests.support.hfx01_server import _Handler


def _with_server(path: str) -> tuple[int, bytes]:
    status, body, _ = _with_server_response(path)
    return status, body


def _with_server_response(path: str) -> tuple[int, bytes, str | None]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}{path}") as response:
                return response.status, response.read(), response.headers.get("Content-Type")
        except HTTPError as error:
            return error.code, error.read(), error.headers.get("Content-Type")
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
    assert "relationships" not in payload
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
    assert b"DEMO \xc2\xb7 EXAMPLE DATA" in body
    for path in (
        "/app.js",
        "/presentation.js",
        "/subscriber.css",
        "/design-system/global.css",
        "/design-system/tokens.css",
    ):
        status, _ = _with_server(path)
        assert status == 200


def test_brand_assets_are_allowlisted_and_served_with_image_media_types() -> None:
    assets = {
        "/brand/logo-light.svg": "image/svg+xml",
        "/brand/logo-dark.svg": "image/svg+xml",
        "/brand/isotope.svg": "image/svg+xml",
        "/brand/favicon.svg": "image/svg+xml",
        "/brand/favicon-16x16.png": "image/png",
        "/brand/favicon-32x32.png": "image/png",
        "/brand/favicon.ico": "image/vnd.microsoft.icon",
    }
    for path, expected_type in assets.items():
        status, body, content_type = _with_server_response(path)
        assert status == 200
        assert body
        assert content_type == expected_type


def test_canonical_dashboard_icon_sprite_is_served_locally() -> None:
    status, body, content_type = _with_server_response("/assets/icons/lucide/axignal-ui.svg")
    assert status == 200
    assert body
    assert content_type == "image/svg+xml"
    assert b'id="settings"' in body
    assert b'id="rotate-ccw"' in body


def test_synthetic_ux_lab_route_is_allowlisted_and_not_a_production_fallback() -> None:
    nominal_status, nominal_body = _with_server(
        "/api/subscriber-context?scenario=SYNTHETIC_NOMINAL"
    )
    invalid_status, invalid_body = _with_server("/api/subscriber-context?scenario=UNLISTED")
    canonical_status, canonical_body = _with_server("/api/subscriber-context")
    nominal = json.loads(nominal_body)
    invalid = json.loads(invalid_body)
    canonical = json.loads(canonical_body)

    assert nominal_status == 200
    assert nominal["realityLevel"] == "SYNTHETIC_PRESENTATION_LAB"
    assert nominal["uxLab"]["scenario"] == "SYNTHETIC_NOMINAL"
    assert nominal["uxLab"]["scenarioObjectCount"] == 9
    assert invalid_status == 404
    assert invalid == {"error": "Synthetic UX scenario not found."}
    assert canonical_status == 200
    assert canonical["realityLevel"] == "TEST_DEV_IN_MEMORY_AUTHORITY"
    assert "uxLab" not in canonical
    assert "relationships" not in canonical


def test_lab_controls_are_outside_product_geometry_and_default_route_has_no_scenario_ui() -> None:
    status, body, _ = _with_server_response("/")
    html = body.decode("utf-8")
    assert status == 200
    assert 'id="lab-toolbar"' not in html
    assert 'id="lab-scenario"' not in html
    assert 'id="lab-contexts" hidden' in html
    assert 'id="relationship-layer"' in html
    assert 'id="minimap-relationships"' in html
