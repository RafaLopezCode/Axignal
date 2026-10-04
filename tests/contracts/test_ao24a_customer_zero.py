"""AO-24A staff authority over the existing FR-30 runtime, never economic edits."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from domain.admin_access import AdminAssurance, AdminPrincipalId, AdminRole, PrivilegeChangeKind
from pipeline.admin_access import SqliteAdminAccessStore
from tests.contracts.test_fr30_production_first_proof import _install_source
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler


class LocalAuthenticator:
    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        if credential not in {"ao24a-controlled-admin", "ao24a-support"}:
            return None
        return VerifiedAdminIdentity(
            AdminPrincipalId(
                "admin:ao24a-test"
                if credential == "ao24a-controlled-admin"
                else "admin:ao24a-support"
            ),
            now,
            AdminAssurance.STEP_UP,
            "controlled-test",
        )


def test_staff_authority_precedes_fr30_read_and_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = build_runtime(
        RuntimeConfig(
            "development",
            "127.0.0.1",
            8765,
            "a" * 40,
            tmp_path,
            Path(__file__).resolve().parents[2] / "apps/web",
            "axignal.com",
        )
    )
    now = datetime.now(UTC)
    authority = AdminAccessService(
        SqliteAdminAccessStore(tmp_path / "admin-access.sqlite3"), LocalAuthenticator()
    )
    authority.bootstrap_founder("ao24a-controlled-admin", occurred_at=now, reason="controlled QA")
    session = authority.issue_session("ao24a-controlled-admin", authenticated_at=now)
    authority.change_role(
        session.token,
        target_principal_id=AdminPrincipalId("admin:ao24a-support"),
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now,
        reason="Controlled read-only product access",
    )
    support = authority.issue_session("ao24a-support", authenticated_at=now)
    runtime.admin_access = authority
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"

    def request(path: str, *, token: str | None = None, body: dict[str, str] | None = None):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        data = None if body is None else json.dumps(body).encode()
        try:
            with urllib.request.urlopen(
                urllib.request.Request(origin + path, headers=headers, data=data), timeout=5
            ) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    try:
        assert request("/api/subscriber-context")[0] == 401
        assert request("/internal/admin/customer-zero/access", token="invalid")[0] == 401
        assert request("/internal/admin/customer-zero/access", token=session.token) == (
            200,
            {"authorized": True, "canObserve": True},
        )
        assert request("/internal/admin/customer-zero/access", token=support.token) == (
            200,
            {"authorized": True, "canObserve": False},
        )
        status, empty = request("/api/subscriber-context", token=session.token)
        assert status == 200 and empty["state"] == "NO_XEED"
        command = {"label": "attention", "targetUri": "https://example.org/"}
        assert request("/api/xeeds", body=command)[0] == 401
        assert request("/api/xeeds", token=support.token, body=command)[0] == 403
        status, rejected = request("/api/xeeds", token=session.token, body=command)
        assert status == 400 and rejected["status"] == "rejected"
        assert runtime.first_proof is not None
        assert runtime.first_proof.current_projection() is None
        assert runtime.first_proof.observation_memory.for_subject("org:axignal") == ()
        assert request("/api/organizations")[0] == 401
        assert request("/api/organizations", token=support.token)[1]["canObserve"] is False
        attention = {"action": "add", "name": "AXIGNAL", "targetUri": "https://axignal.com/"}
        assert request("/api/xeeds", token=support.token, body=attention)[0] == 403
        assert (
            request(
                "/api/xeeds", token=session.token, body={**attention, "epistemicState": "OBSERVED"}
            )[0]
            == 400
        )
        _install_source(monkeypatch, runtime.first_proof)
        status, projection = request("/api/xeeds", token=session.token, body=attention)
        assert status == 201
        inventory = request("/api/organizations", token=session.token)[1]
        assert len(inventory["organizations"]) == 1
        identifier = inventory["selectedId"]
        assert request("/api/subscriber-context", token=session.token)[1] == projection
        assert request("/api/xeeds", token=session.token, body=attention)[1] == projection
        assert (
            request("/api/xeeds", token=session.token, body={"action": "select", "id": identifier})[
                1
            ]
            == projection
        )
        assert len(runtime.first_proof.observation_memory.for_subject("org:axignal")) == 1
        status, unresolved = request(
            "/api/xeeds",
            token=session.token,
            body={"action": "add", "name": "Unknown", "targetUri": "https://unresolved.example/"},
        )
        assert status == 202 and unresolved["state"] == "IDENTITY_UNRESOLVED"
        assert request("/api/subscriber-context", token=session.token)[1] == projection
        assert (
            request("/api/xeeds", token=support.token, body={"action": "select", "id": identifier})[
                0
            ]
            == 403
        )
        assert (
            request("/api/xeeds", token=session.token, body={"action": "select", "id": "foreign"})[
                0
            ]
            == 400
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
