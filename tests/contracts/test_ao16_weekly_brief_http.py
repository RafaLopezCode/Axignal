from __future__ import annotations

import http.client
import json
import threading
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from application.admin_acquisition.public_service import PublicBriefRequestService
from application.admin_acquisition.review_service import AdminBriefReviewService
from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
)
from domain.admin_access import AdminAssurance, AdminPrincipalId
from domain.evidence.epistemics import Currentness
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler


def _runtime(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    return build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="b" * 40,
            data_dir=tmp_path,
            web_root=root / "apps" / "web",
        )
    )


def _serve(runtime):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class _FounderAuthenticator:
    def __init__(self, identity: VerifiedAdminIdentity) -> None:
        self._identity = identity

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identity if credential == "founder-auth" else None


def _founder_token(runtime, tmp_path: Path) -> str:
    now = datetime.now(UTC)
    identity = VerifiedAdminIdentity(
        principal_id=AdminPrincipalId("admin:founder"),
        authenticated_at=now,
        assurance=AdminAssurance.STEP_UP,
        auth_source="ao16-test-provider",
    )
    service = AdminAccessService(
        SqliteAdminAccessStore(tmp_path / "admin-access.sqlite3"),
        _FounderAuthenticator(identity),
    )
    service.bootstrap_founder(
        "founder-auth",
        occurred_at=now,
        reason="AO-16 founder fixture",
    )
    session = service.issue_session("founder-auth", authenticated_at=now)
    runtime.admin_access = service
    return session.token


def _seed_eligible_evidence(runtime, token: str) -> None:
    now = datetime.now(UTC)
    PublicBriefRequestService(runtime.admin_acquisition_store).submit(
        request_id="brief:http",
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="contact@acme.example",
        purpose="Observe material public changes.",
        request_notice_version="brief-request-v1",
        newsletter_consent=True,
        newsletter_notice_version="newsletter-v1",
        now=now - timedelta(hours=2),
    )
    admin_access = runtime.admin_access
    assert admin_access is not None
    grant = admin_access.session_grant(token, now=now)
    AdminBriefReviewService(runtime.admin_acquisition_store).accept(
        grant=grant,
        request_id="brief:http",
        subject_reference="organization:acme",
        reason="Sufficient public coverage.",
        now=now - timedelta(hours=1),
    )
    runtime.observation_memory.append(
        GovernedObservation(
            record=ObservationRecord(
                observation_id="obs:http",
                subject_id="organization:acme",
                source_ref="https://example.com/change",
                source_type="PUBLIC_WEB",
                observed_at=now - timedelta(minutes=30),
                content_fingerprint="sha256:http",
                mode=ObservationMode.DETERMINISTIC_SENSOR,
            ),
            raw_content="public change",
            fields=(ObservedField("public.change", "new distributor page"),),
            reuse_authority=ObservationReuseAuthority(
                rights_status=ObservationRightsStatus.PERMITTED,
                access_status=ObservationAccessStatus.ACCESSIBLE,
                scope=ObservationReuseScope.GLOBAL_PUBLIC,
                currentness=Currentness.CURRENT,
                applicable_subject_ids=("organization:acme",),
                applicable_purposes=("weekly-brief",),
            ),
        )
    )


def test_private_http_composes_and_approves_but_exposes_no_delivery_endpoint(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path)
    token = _founder_token(runtime, tmp_path)
    _seed_eligible_evidence(runtime, token)
    server, thread = _serve(runtime)
    try:
        host, port = server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        payload = {
            "requestId": "brief:http",
            "issueId": "issue:http",
            "issueVersion": "2026-W40-v1",
            "candidates": [
                {
                    "observationId": "obs:http",
                    "whyMayMatter": "This may warrant a channel review.",
                    "unknowns": ["Commercial impact remains UNKNOWN."],
                }
            ],
        }
        connection.request(
            "POST",
            "/internal/admin/weekly-brief/issues",
            body=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        assert response.status == 201
        assert body["status"] == "composed"
        assert body["itemCount"] == 1
        assert body["humanApprovalRequired"] is True

        issue_path = quote("issue:http", safe="")
        connection.request(
            "POST",
            f"/internal/admin/weekly-brief/issues/{issue_path}/approve",
            body=b"{}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        response = connection.getresponse()
        approved = json.loads(response.read())
        assert response.status == 200
        assert approved["status"] == "approved"
        assert runtime.admin_weekly_brief_store.get_approval("issue:http") is not None
        assert (tmp_path / "admin-weekly-brief.sqlite3").exists()

        connection.request(
            "POST",
            f"/internal/admin/weekly-brief/issues/{issue_path}/deliver",
            body=b"{}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        response = connection.getresponse()
        response.read()
        assert response.status == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
