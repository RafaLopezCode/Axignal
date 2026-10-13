from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from application.admin_shell import accessible_navigation, project_admin_shell
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    PrivilegeChangeKind,
    scopes_for_roles,
)
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
SHA = "b" * 40


class FakeAdminAuthenticator:
    def __init__(self, identities: dict[str, VerifiedAdminIdentity]) -> None:
        self._identities = identities

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identities.get(credential)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha=SHA,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )


def _grant(role: AdminRole) -> AdminAuthorizationGrant:
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("admin-session:test"),
        principal_id=AdminPrincipalId("admin:test"),
        roles=frozenset({role}),
        scopes=scopes_for_roles(frozenset({role})),
        assurance=AdminAssurance.PRIMARY,
    )


def _admin_runtime(
    tmp_path: Path,
) -> tuple[object, str, str]:
    runtime = build_runtime(_config(tmp_path))
    now = datetime.now(UTC)
    founder = AdminPrincipalId("admin:founder")
    support = AdminPrincipalId("admin:support")
    authenticator = FakeAdminAuthenticator(
        {
            "founder-auth": VerifiedAdminIdentity(
                principal_id=founder,
                authenticated_at=now,
                assurance=AdminAssurance.STEP_UP,
                auth_source="ao02-test-provider",
            ),
            "support-auth": VerifiedAdminIdentity(
                principal_id=support,
                authenticated_at=now,
                assurance=AdminAssurance.PRIMARY,
                auth_source="ao02-test-provider",
            ),
        }
    )
    service = AdminAccessService(
        SqliteAdminAccessStore(tmp_path / "admin-access.sqlite3"),
        authenticator,
    )
    service.bootstrap_founder(
        "founder-auth",
        occurred_at=now,
        reason="AO-02 founder fixture",
    )
    founder_session = service.issue_session(
        "founder-auth",
        authenticated_at=now,
    )
    service.change_role(
        founder_session.token,
        target_principal_id=support,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(seconds=1),
        reason="AO-02 support fixture",
    )
    support_session = service.issue_session(
        "support-auth",
        authenticated_at=now,
    )
    runtime.admin_access = service
    return runtime, founder_session.token, support_session.token


def _request(url: str, token: str | None = None) -> urllib.request.Request:
    headers = {} if token is None else {"Authorization": f"Bearer {token}"}
    return urllib.request.Request(url, headers=headers)


def test_admin_shell_navigation_is_scope_derived() -> None:
    founder = project_admin_shell(_grant(AdminRole.FOUNDER))
    assert founder.mode == "ADMIN"
    assert len(founder.navigation) == 12
    assert founder.current_slug == "command-center"

    support = project_admin_shell(_grant(AdminRole.SUPPORT))
    slugs = tuple(item.slug for item in accessible_navigation(_grant(AdminRole.SUPPORT)))
    assert slugs == ("customers-crm", "xeeds")
    assert support.current_slug == "customers-crm"
    assert "finance-fiscal" not in slugs
    assert "system" not in slugs


def test_admin_is_not_exposed_when_security_plane_is_not_composed(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"http://{host}:{port}/admin", timeout=3)
        assert exc_info.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_admin_http_shell_is_authenticated_role_limited_and_deep_linked(
    tmp_path: Path,
) -> None:
    runtime, founder_token, support_token = _admin_runtime(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        with pytest.raises(urllib.error.HTTPError) as unauthenticated:
            urllib.request.urlopen(base + "/admin", timeout=3)
        assert unauthenticated.value.code == 401
        assert unauthenticated.value.headers["WWW-Authenticate"] == 'Bearer realm="AXIGNAL Admin"'

        with pytest.raises(urllib.error.HTTPError) as invalid:
            urllib.request.urlopen(_request(base + "/admin", "subscriber-token"), timeout=3)
        assert invalid.value.code == 401

        with urllib.request.urlopen(
            _request(base + "/admin", founder_token), timeout=3
        ) as response:
            founder_html = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        assert 'data-mode="ADMIN"' in founder_html
        assert "Command Center" in founder_html
        assert "Finance / Fiscal" in founder_html
        assert "Frontier Advisor" in founder_html
        assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in founder_html
        assert founder_token not in founder_html
        assert "__AXIGNAL_ADMIN_BOOTSTRAP_JSON__" not in founder_html

        with urllib.request.urlopen(
            _request(base + "/admin/customers-crm", support_token), timeout=3
        ) as response:
            support_html = response.read().decode("utf-8")
        assert '"currentSlug":"customers-crm"' in support_html
        assert '"slug":"xeeds"' in support_html
        assert '"slug":"finance-fiscal"' not in support_html
        assert '"slug":"system"' not in support_html

        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(
                _request(base + "/admin/finance-fiscal", support_token),
                timeout=3,
            )
        assert denied.value.code == 403

        with pytest.raises(urllib.error.HTTPError) as unknown:
            urllib.request.urlopen(
                _request(base + "/admin/not-a-domain", founder_token),
                timeout=3,
            )
        assert unknown.value.code == 404

        for asset in ("/admin.css", "/admin.js"):
            with urllib.request.urlopen(base + asset, timeout=3) as response:
                assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_admin_shell_assets_preserve_visual_and_epistemic_separation() -> None:
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "admin" / "admin.css").read_text(encoding="utf-8")
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")

    assert "/subscriber.css" in html
    assert 'class="app2 admin-shell"' in html
    assert 'class="gov admin-gov"' in html
    assert 'class="axent admin-axent"' in html
    assert "Operational projection" in html
    assert "not AXIGLAND evidence" in html
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in html
    assert "@media (max-width: 680px)" in css
    assert ".admin-shell .admin-axent" in css
    assert "position: relative !important" in css
    assert "visibility: visible !important" in css
    assert "pointer-events: auto !important" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "aria-current" in js
    assert "ArrowDown" in js
    assert "ArrowUp" in js


@pytest.mark.parametrize(
    "slug,sections",
    [
        ("command-center", ["commandCenter"]),
        ("xeeds", ["xeedObservatory"]),
        ("axigland-quality", ["xeedObservatory"]),
        ("axent-brain", ["brainObservatory"]),
        ("governance", ["governance"]),
        ("acquisition", ["acquisition", "gsc"]),
        ("integrations", ["integrations", "apiOperations"]),
        (
            "finance-fiscal",
            ["financialDocuments", "accountingReconciliation", "fiscalCompliance", "taxOperations"],
        ),
        ("frontier-advisor", ["measurementRegistry"]),
        ("revenue", ["commandCenter"]),
        ("system", ["commandCenter"]),
    ],
)
def test_operational_json_is_live_authorized_and_secret_free(
    tmp_path: Path, slug: str, sections: list[str]
) -> None:
    runtime, token, support = _admin_runtime(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/admin/{slug}"

    def request(credential: str | None):
        headers = {"Accept": "application/json"}
        if credential:
            headers["Authorization"] = "Bearer " + credential
        return urllib.request.Request(base, headers=headers)

    try:
        with pytest.raises(urllib.error.HTTPError) as absent:
            urllib.request.urlopen(request(None), timeout=3)
        assert absent.value.code == 401
        assert json.load(absent.value) == {"reason": "ADMIN_SESSION_REQUIRED"}
        with urllib.request.urlopen(request(token), timeout=3) as response:
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["Content-Type"].startswith("application/json")
            raw = response.read().decode()
            payload = json.loads(raw)
        assert token not in raw and support not in raw
        assert payload["mode"] == "ADMIN" and payload["currentSlug"] == slug
        assert all(isinstance(payload[key], dict) for key in sections)
        if slug in {"command-center", "revenue", "system"}:
            metrics = payload["commandCenter"]["metrics"]
            assert all(item["value"] is None for item in metrics)
            assert all(item["unknownReason"] == "SOURCE_PROJECTION_UNAVAILABLE" for item in metrics)
            if slug == "revenue":
                assert {item["metricId"] for item in metrics} == {"mrr", "arr", "paying_accounts"}
            if slug == "system":
                assert {item["metricId"] for item in metrics} == {
                    "source_health",
                    "provider_health",
                    "system_health",
                }
        if slug != "xeeds":
            with pytest.raises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(request(support), timeout=3)
            assert denied.value.code == 403
            assert json.load(denied.value) == {"reason": "ADMIN_SCOPE_REQUIRED"}
        runtime.admin_access.revoke_own_session(
            token, revoked_at=datetime.now(UTC), reason="Read revocation test"
        )
        with pytest.raises(urllib.error.HTTPError) as revoked:
            urllib.request.urlopen(request(token), timeout=3)
        assert revoked.value.code == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
