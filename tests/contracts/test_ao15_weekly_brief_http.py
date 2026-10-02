from __future__ import annotations

import http.client
import json
import threading
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from domain.admin_access import AdminAssurance, AdminPrincipalId
from pipeline.admin_access import SqliteAdminAccessStore
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
        "requestProcessingAcknowledged": True,
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


class _FounderAuthenticator:
    def __init__(self, identity: VerifiedAdminIdentity) -> None:
        self._identity = identity

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identity if credential == "founder-auth" else None


def _compose_founder_admin(runtime, tmp_path: Path) -> str:
    now = datetime.now(UTC)
    identity = VerifiedAdminIdentity(
        principal_id=AdminPrincipalId("admin:founder"),
        authenticated_at=now,
        assurance=AdminAssurance.STEP_UP,
        auth_source="ao15-test-provider",
    )
    service = AdminAccessService(
        SqliteAdminAccessStore(tmp_path / "admin-access.sqlite3"),
        _FounderAuthenticator(identity),
    )
    service.bootstrap_founder(
        "founder-auth",
        occurred_at=now,
        reason="AO-15 founder fixture",
    )
    session = service.issue_session("founder-auth", authenticated_at=now)
    runtime.admin_access = service
    return session.token


def test_request_can_be_submitted_without_newsletter_consent(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=True)
    server, thread = _serve(runtime)
    payload = {
        "companyName": "Acme Industrial",
        "companyDomain": "acme.example",
        "professionalEmail": "contact@acme.example",
        "purpose": "Review public coverage before deciding on the newsletter.",
        "requestNoticeVersion": "weekly-brief-request-v1",
        "requestProcessingAcknowledged": True,
        "newsletterConsent": False,
        "newsletterNoticeVersion": None,
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
        events = runtime.admin_acquisition_store.all_events()
        assert len(events) == 1
        assert events[0].kind.value == "REQUEST_SUBMITTED"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_admin_http_can_accept_review_with_step_up_bearer(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=True)
    token = _compose_founder_admin(runtime, tmp_path)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        request_payload = {
            "companyName": "Acme Industrial",
            "companyDomain": "acme.example",
            "professionalEmail": "contact@acme.example",
            "purpose": "Observe material public changes.",
            "requestNoticeVersion": "weekly-brief-request-v1",
            "requestProcessingAcknowledged": True,
            "newsletterConsent": True,
            "newsletterNoticeVersion": "weekly-newsletter-consent-v1",
        }
        connection.request(
            "POST",
            "/api/weekly-brief/requests",
            body=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        created = json.loads(response.read())
        assert response.status == 202
        request_id = created["requestId"]

        action_payload = {
            "subjectReference": "organization:acme",
            "reason": "Entity resolved with sufficient public coverage.",
        }
        action_path = (
            "/internal/admin/acquisition/requests/" + quote(request_id, safe="") + "/accept"
        )
        connection.request(
            "POST",
            action_path,
            body=json.dumps(action_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        response = connection.getresponse()
        result = json.loads(response.read())
        assert response.status == 200
        assert result["reviewState"] == "ACCEPTED"
        assert result["coverageState"] == "SUFFICIENT"
        assert result["consentState"] == "GRANTED"
        assert result["deliveryEligible"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_admin_acquisition_mutation_requires_authentication(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, enabled=True)
    _compose_founder_admin(runtime, tmp_path)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request(
            "POST",
            "/internal/admin/acquisition/requests/brief%3Aunknown/decline",
            body=json.dumps({"reason": "No coverage."}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response.read()
        assert response.status == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_landing_keeps_request_and_newsletter_consent_separate() -> None:
    root = Path(__file__).resolve().parents[2]
    landing = (root / "apps" / "web" / "landing" / "index.html").read_text(encoding="utf-8")
    newsletter = (root / "apps" / "web" / "landing" / "newsletter.js").read_text(encoding="utf-8")
    privacy = (
        root / "apps" / "web" / "landing" / "legal" / "privacidad-rgpd" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'id="newsletterRequestNotice" type="checkbox" required' in landing
    assert 'id="newsletterConsent" type="checkbox">' in landing
    assert 'id="newsletterPrivacyLink"' in landing
    assert "newsletterNoticeVersion:$('newsletterConsent').checked?" in newsletter
    assert "endpoint permanece deshabilitado por defecto" in privacy
