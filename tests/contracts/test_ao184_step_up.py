"""ADR-0092 secure second-factor operator step-up, separate from PRIMARY."""

import base64
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_access import AdminAccessService, AdminAuthorizationError
from domain.admin_access import AdminRiskClass, AdminScope
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.admin_access import RejectingAdminAuthenticator
from tools.runtime.admin_session import (
    _read_operator_token,
    issue_ssh_operator_session,
    issue_step_up_operator_session,
    revoke_ssh_operator_session,
)
from tools.runtime.admin_step_up import (
    StepUpDenied,
    _code,
    enroll_factor,
    verify_totp,
)

NOW = datetime(2026, 10, 10, 10, 0, tzinfo=UTC)
PRINCIPAL = "admin:operator:founder"


@pytest.fixture
def world(tmp_path: Path):
    root = tmp_path / "state"
    root.mkdir()
    primary = tmp_path / "primary.key"
    factor = tmp_path / "factor.key"
    provisioning = tmp_path / "provisioning.uri"
    issue_ssh_operator_session(data_dir=root, principal_id=PRINCIPAL, output_file=primary, now=NOW)
    enroll_factor(factor, provisioning, principal_id=PRINCIPAL)
    seed = base64.b32decode(json.loads(factor.read_text(encoding="ascii"))["secret"])

    def otp(at: datetime) -> str:
        return _code(seed, int(at.timestamp()) // 30)

    return root, primary, factor, provisioning, otp


def test_root_factor_enrollment_never_replaces_provisioning_and_is_private(world):
    root, _, factor, provisioning, _ = world
    assert factor.read_text().strip() not in (root / "admin-access.sqlite3").read_bytes().decode(
        "latin-1"
    )
    assert "otpauth://totp/" in provisioning.read_text()
    assert f"secret={json.loads(factor.read_text())['secret']}" in provisioning.read_text()
    if os.name == "posix":
        assert os.stat(factor).st_mode & 0o777 == 0o600
        assert os.stat(provisioning).st_mode & 0o777 == 0o600
    with pytest.raises(ValueError):
        enroll_factor(factor, provisioning, principal_id=PRINCIPAL)


def test_independent_totp_issues_distinct_ten_minute_step_up_and_primary_survives(world, tmp_path):
    root, primary, factor, _, otp = world
    elevated_file = tmp_path / "step-up.key"
    issued_id = issue_step_up_operator_session(
        data_dir=root,
        primary_token_file=primary,
        factor_file=factor,
        output_file=elevated_file,
        otp=otp(NOW),
        now=NOW,
    )
    primary_token = _read_operator_token(primary)
    elevated_token = _read_operator_token(elevated_file)
    assert primary.exists() and primary_token != elevated_token
    assert issued_id.startswith("admin-session:")
    if os.name == "posix":
        assert os.stat(elevated_file).st_mode & 0o777 == 0o600
    service = AdminAccessService(
        SqliteAdminAccessStore(root / "admin-access.sqlite3"), RejectingAdminAuthenticator()
    )
    assert (
        service.authorize(
            elevated_token,
            required_scope=AdminScope.CUSTOMERS_WRITE,
            risk=AdminRiskClass.SENSITIVE,
            now=NOW + timedelta(minutes=9),
        ).principal_id
        == PRINCIPAL
    )
    with pytest.raises((PermissionError, FileNotFoundError)):
        service.authorize(
            elevated_token,
            required_scope=AdminScope.CUSTOMERS_WRITE,
            risk=AdminRiskClass.SENSITIVE,
            now=NOW + timedelta(minutes=10),
        )
    with pytest.raises(AdminAuthorizationError, match="step-up"):
        service.authorize(
            primary_token,
            required_scope=AdminScope.CUSTOMERS_WRITE,
            risk=AdminRiskClass.SENSITIVE,
            now=NOW + timedelta(minutes=9),
        )
    assert (
        service.authorize(
            primary_token,
            required_scope=AdminScope.CUSTOMERS_READ,
            risk=AdminRiskClass.READ,
            now=NOW + timedelta(minutes=20),
        ).principal_id
        == PRINCIPAL
    )
    assert elevated_token not in (root / "admin-access.sqlite3").read_bytes().decode("latin-1")


def test_replay_denied_even_when_concurrently_requested(world, tmp_path):
    root, primary, factor, _, otp = world
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                issue_step_up_operator_session,
                data_dir=root,
                primary_token_file=primary,
                factor_file=factor,
                output_file=tmp_path / f"elevated-{i}",
                otp=otp(NOW),
                now=NOW,
            )
            for i in range(2)
        ]
        outcomes = []
        for f in futures:
            try:
                outcomes.append(f.result())
            except StepUpDenied:
                outcomes.append("DENIED")
    assert len([x for x in outcomes if x != "DENIED"]) == 1
    assert outcomes.count("DENIED") == 1
    with pytest.raises(StepUpDenied):
        verify_totp(
            data_dir=root, secret_file=factor, principal_id=PRINCIPAL, otp=otp(NOW), now=NOW
        )


def test_five_failures_lock_otp_until_cooldown(world):
    root, _, factor, _, otp = world
    for _ in range(5):
        with pytest.raises(StepUpDenied):
            verify_totp(
                data_dir=root,
                secret_file=factor,
                principal_id=PRINCIPAL,
                otp="abcdef",
                now=NOW,
            )
    with pytest.raises(StepUpDenied):
        verify_totp(
            data_dir=root,
            secret_file=factor,
            principal_id=PRINCIPAL,
            otp=otp(NOW),
            now=NOW,
        )
    later = NOW + timedelta(minutes=6)
    verify_totp(
        data_dir=root,
        secret_file=factor,
        principal_id=PRINCIPAL,
        otp=otp(later),
        now=later,
    )


def test_primary_revoked_or_incorrect_assurance_never_elevates(world, tmp_path):
    root, primary, factor, _, otp = world
    revoke_ssh_operator_session(data_dir=root, token_file=primary, now=NOW)
    with pytest.raises((PermissionError, FileNotFoundError)):
        issue_step_up_operator_session(
            data_dir=root,
            primary_token_file=primary,
            factor_file=factor,
            output_file=tmp_path / "should-not-exist",
            otp=otp(NOW),
            now=NOW,
        )
    assert not (tmp_path / "should-not-exist").exists()


def test_replayed_or_expired_primary_rejected_even_with_fresh_totp(world, tmp_path):
    root, primary, factor, _, otp = world
    with pytest.raises((PermissionError, FileNotFoundError)):
        issue_step_up_operator_session(
            data_dir=root,
            primary_token_file=primary,
            factor_file=factor,
            output_file=tmp_path / "late",
            otp=otp(NOW + timedelta(hours=9)),
            now=NOW + timedelta(hours=9),
        )
    assert not (tmp_path / "late").exists()


def test_factor_rejects_world_readable_and_symlinks(world, tmp_path):
    root, _, factor, _, otp = world
    if os.name != "posix":
        pytest.skip("POSIX file-mode contract")
    os.chmod(factor, 0o644)
    with pytest.raises(StepUpDenied):
        verify_totp(
            data_dir=root, secret_file=factor, principal_id=PRINCIPAL, otp=otp(NOW), now=NOW
        )
    os.chmod(factor, 0o600)
    link = tmp_path / "factor-link"
    link.symlink_to(factor)
    with pytest.raises(StepUpDenied):
        verify_totp(data_dir=root, secret_file=link, principal_id=PRINCIPAL, otp=otp(NOW), now=NOW)


def test_success_leaves_no_raw_totp_in_state(world):
    root, _, factor, _, otp = world
    verify_totp(data_dir=root, secret_file=factor, principal_id=PRINCIPAL, otp=otp(NOW), now=NOW)
    binary = (root / "admin-step-up.sqlite3").read_bytes()
    assert otp(NOW).encode() not in binary
    with sqlite3.connect(root / "admin-step-up.sqlite3") as db:
        counter, failures = db.execute(
            "SELECT last_counter, failed FROM step_up_otp_state WHERE principal=?",
            (PRINCIPAL,),
        ).fetchone()
    assert counter == int(NOW.timestamp()) // 30 and failures == 0


def test_second_factor_is_bound_to_the_specific_admin_principal(world):
    root, _, factor, _, otp = world
    with pytest.raises(StepUpDenied):
        verify_totp(
            data_dir=root,
            secret_file=factor,
            principal_id="admin:another-operator",
            otp=otp(NOW),
            now=NOW,
        )
