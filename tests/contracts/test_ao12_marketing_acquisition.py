from __future__ import annotations

import http.client
import json
import threading
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.admin_acquisition.marketing_service import (
    PublicMarketingEventService,
    summarize_marketing,
)
from domain.admin_acquisition import MarketingEventKind, MarketingIdentityClass
from pipeline.admin_acquisition import SqliteAdminAcquisitionStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def _store(tmp_path: Path) -> SqliteAdminAcquisitionStore:
    return SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")


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
            acquisition_events_enabled=enabled,
        )
    )


def _serve(runtime):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_marketing_event_is_replay_safe_and_minimized(tmp_path: Path) -> None:
    store = _store(tmp_path)
    service = PublicMarketingEventService(store)
    kwargs = dict(
        event_id="mkt:event:1",
        session_ref="session:abc123",
        kind=MarketingEventKind.LANDING_VIEWED,
        occurred_at=NOW,
        received_at=NOW + timedelta(seconds=1),
        surface="landing",
        locale="es",
        path="/?utm_source=should-never-persist",
        referrer="https://example.com/path/private?token=secret",
        utm_source="youtube",
        utm_medium="referral",
        utm_campaign="launch-1",
    )

    assert service.ingest(**kwargs) is True
    replay = dict(kwargs)
    replay["received_at"] = NOW + timedelta(seconds=2)
    assert service.ingest(**replay) is False

    events = store.marketing_events()
    assert len(events) == 1
    event = events[0]
    assert event.identity_class is MarketingIdentityClass.ANONYMOUS_SESSION
    assert event.path == "/"
    assert event.referrer_origin == "https://example.com"
    assert event.utm_source == "youtube"
    serialized = store._marketing_payload(event)
    assert "token=secret" not in serialized
    assert "should-never-persist" not in serialized


def test_conflicting_replay_fails_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    service = PublicMarketingEventService(store)
    common = dict(
        event_id="mkt:event:2",
        session_ref="session:def456",
        occurred_at=NOW,
        received_at=NOW + timedelta(seconds=1),
        surface="landing",
        locale="en",
        path="/",
    )
    service.ingest(kind=MarketingEventKind.LANDING_VIEWED, **common)

    with pytest.raises(ValueError, match="reused"):
        service.ingest(kind=MarketingEventKind.CTA_ACTIVATED, cta="plant-xeed", **common)


def test_attribution_summary_is_observed_touch_not_causal_claim(tmp_path: Path) -> None:
    store = _store(tmp_path)
    service = PublicMarketingEventService(store)
    service.ingest(
        event_id="mkt:event:3",
        session_ref="session:ghi789",
        kind=MarketingEventKind.LANDING_VIEWED,
        occurred_at=NOW,
        received_at=NOW,
        surface="landing",
        locale="es",
        path="/",
        utm_source="seo",
        utm_campaign="knowledge",
    )
    service.link_brief_request(
        event_id="mkt:req:1",
        session_ref="session:ghi789",
        request_id="brief:request1",
        occurred_at=NOW + timedelta(seconds=2),
        received_at=NOW + timedelta(seconds=2),
        surface="landing",
        locale="es",
        path="/",
    )

    summary = summarize_marketing(store.marketing_events())
    assert summary.model_version.value == "OBSERVED_TOUCH_V1"
    assert summary.event_count == 2
    assert summary.anonymous_session_count == 1
    assert summary.linked_request_count == 1
    assert ("seo", 1) in summary.source_counts


def test_public_marketing_http_is_closed_by_default(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=False)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request("GET", "/api/acquisition/status")
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read()) == {
            "enabled": False,
            "model": "OBSERVED_TOUCH_V1",
        }

        connection.request(
            "POST",
            "/api/acquisition/events",
            body=b"{}",
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 404
        assert runtime.admin_acquisition_store.marketing_events() == ()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_enabled_marketing_http_accepts_only_non_pii_schema(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=True)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        payload = {
            "eventId": "mkt:http:1",
            "sessionRef": "session:http123",
            "kind": "CHAPTER_VIEWED",
            "occurredAt": datetime.now(UTC).isoformat(),
            "surface": "landing",
            "locale": "es",
            "path": "/?email=never",
            "chapter": 14,
            "referrer": "https://search.example/query?q=private",
            "utmSource": "organic",
            "utmCampaign": "pricing",
        }
        connection.request(
            "POST",
            "/api/acquisition/events",
            body=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        assert response.status == 202
        assert body == {"status": "accepted", "replayed": False}

        events = runtime.admin_acquisition_store.marketing_events()
        assert len(events) == 1
        assert events[0].path == "/"
        assert events[0].referrer_origin == "https://search.example"

        payload["eventId"] = "mkt:http:2"
        payload["professionalEmail"] = "someone@example.com"
        connection.request(
            "POST",
            "/api/acquisition/events",
            body=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        rejected = json.loads(response.read())
        assert response.status == 400
        assert rejected["reason"] == "PII_NOT_ALLOWED"
        assert len(runtime.admin_acquisition_store.marketing_events()) == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_marketing_client_contains_no_cookie_or_fingerprint_tracking() -> None:
    source = Path("apps/web/landing/marketing.js").read_text(encoding="utf-8")
    lowered = source.lower()
    assert "document.cookie" not in lowered
    assert "localstorage" not in lowered
    assert "useragent" not in lowered
    assert "fingerprint" not in lowered
    assert "sessionstorage" in lowered


def test_production_proxy_exposes_only_exact_ao12_routes() -> None:
    source = Path("deploy/production/docker/landing-nginx.conf").read_text(encoding="utf-8")
    assert "location = /api/acquisition/status" in source
    assert "location = /api/acquisition/events" in source
    assert "location /api/" not in source


def test_admin_projection_traces_observed_touch_without_causal_language(tmp_path: Path) -> None:
    from application.admin_acquisition.projection import project_admin_acquisition
    from application.admin_acquisition.public_service import PublicBriefRequestService
    from domain.admin_access import (
        AdminAssurance,
        AdminAuthorizationGrant,
        AdminPrincipalId,
        AdminRole,
        AdminSessionId,
        scopes_for_roles,
    )

    store = _store(tmp_path)
    service = PublicMarketingEventService(store)
    service.ingest(
        event_id="mkt:event:projection",
        session_ref="session:projection",
        kind=MarketingEventKind.LANDING_VIEWED,
        occurred_at=NOW,
        received_at=NOW,
        surface="landing",
        locale="es",
        path="/",
        utm_source="youtube",
        utm_campaign="launch",
    )
    PublicBriefRequestService(store).submit(
        request_id="brief:projection",
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="contact@acme.example",
        purpose="Observe public changes.",
        request_notice_version="weekly-brief-request-v1",
        now=NOW + timedelta(seconds=1),
    )
    service.link_brief_request(
        event_id="mkt:req:projection",
        session_ref="session:projection",
        request_id="brief:projection",
        occurred_at=NOW + timedelta(seconds=2),
        received_at=NOW + timedelta(seconds=2),
        surface="landing",
        locale="es",
        path="/",
    )
    roles = frozenset({AdminRole.FOUNDER})
    grant = AdminAuthorizationGrant(
        session_id=AdminSessionId("session:founder"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )
    projection = project_admin_acquisition(
        store=store,
        grant=grant,
        generated_at=NOW + timedelta(seconds=3),
    )
    request = projection.requests[0]
    assert request.observed_source == "youtube"
    assert request.observed_campaign == "launch"
    assert request.attribution_event_id == "mkt:event:projection"
    assert projection.attribution_model == "OBSERVED_TOUCH_V1"
    assert any("does not claim causal influence" in note for note in projection.coverage_notes)
