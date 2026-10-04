from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domain.admin_access import AdminRole
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.admin_session import (
    _require_root_operator,
    issue_ssh_operator_session,
    revoke_ssh_operator_session,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
SHA = "a" * 40


def test_production_admin_validator_is_explicit_and_fail_closed(tmp_path: Path) -> None:
    disabled = RuntimeConfig(
        environment="production",
        bind_host="127.0.0.1",
        port=8765,
        code_sha=SHA,
        data_dir=tmp_path / "disabled",
        web_root=WEB_ROOT,
    )
    assert build_runtime(disabled).admin_access is None
    enabled = RuntimeConfig(
        environment="production",
        bind_host="127.0.0.1",
        port=8765,
        code_sha=SHA,
        data_dir=tmp_path / "enabled",
        web_root=WEB_ROOT,
        admin_access_enabled=True,
    )
    runtime = build_runtime(enabled)
    assert runtime.admin_access is not None
    with pytest.raises(PermissionError):
        runtime.admin_access.issue_session(
            "external-credential", authenticated_at=datetime.now(UTC)
        )


def test_ssh_operator_issuer_bootstraps_once_and_writes_secret_only_to_0600_file(
    tmp_path: Path,
) -> None:
    token_path = tmp_path / "run" / "session.key"
    now = datetime(2026, 10, 4, 18, 0, tzinfo=UTC)
    session_id = issue_ssh_operator_session(
        data_dir=tmp_path / "runtime",
        principal_id="admin:founder:operator",
        output_file=token_path,
        now=now,
    )
    assert session_id.startswith("admin-session:")
    token = token_path.read_text(encoding="utf-8").strip()
    assert len(token) >= 48
    if os.name == "posix":
        assert os.stat(token_path).st_mode & 0o777 == 0o600
    store = SqliteAdminAccessStore(tmp_path / "runtime" / "admin-access.sqlite3")
    events = store.privilege_events()
    assert len(events) == 1
    assert events[0].role is AdminRole.FOUNDER
    assert token not in (tmp_path / "runtime" / "admin-access.sqlite3").read_bytes().decode(
        "latin-1"
    )
    second_path = tmp_path / "run" / "second.key"
    issue_ssh_operator_session(
        data_dir=tmp_path / "runtime",
        principal_id="admin:founder:operator",
        output_file=second_path,
        now=now,
    )
    assert len(store.privilege_events()) == 1

    revoked = revoke_ssh_operator_session(
        data_dir=tmp_path / "runtime",
        token_file=token_path,
        now=now,
    )
    assert revoked == session_id
    assert not token_path.exists()


def test_ssh_operator_issuer_requires_root_outer_channel() -> None:
    _require_root_operator(0)
    with pytest.raises(PermissionError, match="root SSH operator"):
        _require_root_operator(1000)
