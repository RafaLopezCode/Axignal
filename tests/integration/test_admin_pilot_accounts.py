"""Real HTTP, AO-01 authorization and durable pilot-preparation lifecycle."""

import json
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from application.admin_access import AdminAuthorizationError
from application.admin_pilot_accounts import PilotAccountsConflict, save_pilot_accounts
from domain.admin_access import (
    AdminPrincipalId,
    AdminPrivilegeEvent,
    AdminPrivilegeEventId,
    AdminRole,
    AdminSessionId,
    PrivilegeChangeKind,
)
from pipeline.admin_access import SqliteAdminAccessStore
from pipeline.admin_pilot_accounts import SqlitePilotAccountsStore
from tools.runtime.admin_access import AdminHttpAccessGuard
from tools.runtime.admin_pilot_accounts import pilot_accounts_request
from tools.runtime.admin_session import issue_ssh_operator_session, revoke_ssh_operator_session
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler

NOW = datetime.now(UTC)
WEB = Path(__file__).resolve().parents[2] / "apps" / "web"


def runtime_for(root: Path):
    return build_runtime(
        RuntimeConfig(
            environment="test",
            bind_host="127.0.0.1",
            port=0,
            code_sha="a" * 40,
            data_dir=root,
            web_root=WEB,
            admin_access_enabled=True,
        )
    )


def test_real_http_save_survives_restart_and_revocation(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    key = tmp_path / "session.key"
    issue_ssh_operator_session(
        data_dir=root, principal_id="admin:founder", output_file=key, now=NOW
    )
    token = key.read_text().strip()
    runtime = runtime_for(root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method: str, body=None, credential=token):
        conn = HTTPConnection(*server.server_address)
        headers = {"Content-Type": "application/json"}
        if credential:
            headers["Authorization"] = "Bearer " + credential
        conn.request(
            method,
            "/internal/admin/pilot-test-accounts",
            json.dumps(body) if body is not None else None,
            headers,
        )
        response = conn.getresponse()
        status, result = response.status, json.loads(response.read())
        assert response.getheader("Cache-Control") == "no-store"
        conn.close()
        return status, result

    try:
        assert request("GET", credential="")[0] == 401
        assert not (root / "admin-pilot-accounts.sqlite3").exists()
        status, initial = request("GET")
        assert status == 200 and initial["a"] == initial["b"] == ""
        assert initial["authorizedForTest"] is False
        saved = request("POST", {"a": "a@example.com", "b": "b@example.com", "expectedRevision": 0})
        assert saved[0] == 200 and saved[1]["authorizedForTest"] is True
        assert saved[1]["savedBy"] == "admin:founder" and saved[1]["savedAt"]
        assert request("POST", {"a": "other@example.com", "b": "", "expectedRevision": 0})[0] == 409
        restarted = runtime_for(root)
        assert restarted.admin_access is not None
        payload = pilot_accounts_request(
            AdminHttpAccessGuard(restarted.admin_access),
            authorization="Bearer " + token,
            data_dir=root,
            now=NOW,
        )
        assert payload == saved[1]
        assert request("POST", {"a": "bad", "b": "", "expectedRevision": 1})[0] == 400
        assert (
            request("POST", {"a": "A@example.com", "b": "a@example.com", "expectedRevision": 1})[0]
            == 400
        )
        assert (
            request("POST", {"a": "c@example.com", "b": "d@example.com", "expectedRevision": 1})[1][
                "revision"
            ]
            == 2
        )
        cleared = request("POST", {"a": "", "b": "", "expectedRevision": 2})
        assert cleared[1]["revision"] == 3 and cleared[1]["authorizedForTest"] is False
        assert SqlitePilotAccountsStore(root / "admin-pilot-accounts.sqlite3").read().a == ""
        revoke_ssh_operator_session(data_dir=root, token_file=key, now=NOW + timedelta(seconds=1))
        assert request("GET")[0] == 401
        assert request("POST", {"a": "", "b": "", "expectedRevision": 3})[0] == 401
        # Preparation never creates subscriber identity, grants, billing or truth.
        assert not (root / "subscriber-identity.sqlite3").exists()
        assert not (root / "subscriber-pilot.sqlite3").exists()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_scope_revocation_is_checked_for_each_save(tmp_path: Path) -> None:
    root, key = tmp_path / "runtime", tmp_path / "session.key"
    session_id = issue_ssh_operator_session(
        data_dir=root, principal_id="admin:founder", output_file=key, now=NOW
    )
    token = key.read_text().strip()
    store = SqliteAdminAccessStore(root / "admin-access.sqlite3")
    store.append_privilege_event(
        AdminPrivilegeEvent(
            event_id=AdminPrivilegeEventId("test-revoke"),
            target_principal_id=AdminPrincipalId("admin:founder"),
            role=AdminRole.FOUNDER,
            kind=PrivilegeChangeKind.REVOKE_ROLE,
            occurred_at=NOW,
            actor_principal_id=AdminPrincipalId("admin:founder"),
            actor_session_id=AdminSessionId(session_id),
            reason="controlled test scope revocation",
        )
    )
    runtime = runtime_for(root)
    assert runtime.admin_access is not None
    with pytest.raises(AdminAuthorizationError):
        pilot_accounts_request(
            AdminHttpAccessGuard(runtime.admin_access),
            authorization="Bearer " + token,
            data_dir=root,
            now=NOW,
            payload={"a": "a@example.com", "b": "b@example.com", "expectedRevision": 0},
        )
    assert not (root / "admin-pilot-accounts.sqlite3").exists()


def test_conflicts_do_not_overwrite_durable_pair(tmp_path: Path) -> None:
    path = tmp_path / "accounts.sqlite3"
    first, second = SqlitePilotAccountsStore(path), SqlitePilotAccountsStore(path)
    save_pilot_accounts(
        first,
        a="a@example.com",
        b="b@example.com",
        expected_revision=0,
        actor="admin:test",
        now=NOW,
    )
    with pytest.raises(PilotAccountsConflict):
        save_pilot_accounts(
            second,
            a="x@example.com",
            b="y@example.com",
            expected_revision=0,
            actor="admin:other",
            now=NOW,
        )
    assert second.read().a == "a@example.com"
