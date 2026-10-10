"""Root-only SSH operator adapter for issuing internal AO-01 Admin sessions.

This is not a public login provider. The trusted outer authentication event is the
operator's successful SSH access to the production host. The runtime itself uses
a validation-only authenticator and cannot exchange SSH credentials for sessions.
"""

from __future__ import annotations

import argparse
import getpass
import os
import secrets
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from domain.admin_access import AdminAssurance, AdminPrincipalId, AdminScope
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.admin_access import RejectingAdminAuthenticator


@dataclass(frozen=True, slots=True)
class _SshOperatorAuthenticator:
    principal_id: AdminPrincipalId
    nonce: str
    assurance: AdminAssurance = AdminAssurance.PRIMARY

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        if not secrets.compare_digest(credential, self.nonce):
            return None
        return VerifiedAdminIdentity(
            principal_id=self.principal_id,
            authenticated_at=now.astimezone(UTC),
            assurance=self.assurance,
            auth_source=(
                "ssh-root-operator+totp"
                if self.assurance is AdminAssurance.STEP_UP
                else "ssh-root-operator"
            ),
        )


def _require_root_operator(euid: int) -> None:
    if euid != 0:
        raise PermissionError("Admin session issuance requires the trusted root SSH operator")


def _write_token_exclusive(path: Path, token: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, (token + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def _read_operator_token(path: Path) -> str:
    if path.is_symlink():
        raise PermissionError("Admin session token file must not be a symlink")
    if os.name == "posix" and os.stat(path).st_mode & 0o077:
        raise PermissionError("Admin session token file must not be group/world accessible")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("Admin session token file is empty")
    return token


def issue_ssh_operator_session(
    *,
    data_dir: Path,
    principal_id: str,
    output_file: Path,
    now: datetime,
    lifetime: timedelta = timedelta(hours=8),
) -> str:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if not principal_id.strip():
        raise ValueError("principal id is required")
    nonce = secrets.token_urlsafe(32)
    authenticator = _SshOperatorAuthenticator(AdminPrincipalId(principal_id.strip()), nonce)
    store = SqliteAdminAccessStore(data_dir / "admin-access.sqlite3")
    service = AdminAccessService(store, authenticator)
    if not store.has_privilege_history():
        service.bootstrap_founder(
            nonce,
            occurred_at=now,
            reason="Initial founder established through authenticated SSH operator channel",
        )
    credential = service.issue_session(nonce, authenticated_at=now, lifetime=lifetime)
    _write_token_exclusive(output_file, credential.token)
    return str(credential.session_id)


def issue_step_up_operator_session(
    *,
    data_dir: Path,
    primary_token_file: Path,
    factor_file: Path,
    output_file: Path,
    otp: str,
    now: datetime,
) -> str:
    """SSH PRIMARY + independently verified TOTP; separate 10-minute credential.

    The SSH CLI enforces root. Never replace or revoke the PRIMARY token.
    No new authentication authority exists in the HTTP runtime.
    """
    from tools.runtime.admin_step_up import verify_totp

    store = SqliteAdminAccessStore(data_dir / "admin-access.sqlite3")
    primary = AdminAccessService(store, RejectingAdminAuthenticator()).session_grant(
        _read_operator_token(primary_token_file), now=now
    )
    if (
        primary.assurance is not AdminAssurance.PRIMARY
        or AdminScope.CUSTOMERS_WRITE not in primary.scopes
    ):
        raise PermissionError("a scoped PRIMARY Admin session is required")
    principal = primary.principal_id
    verify_totp(
        data_dir=data_dir,
        secret_file=factor_file,
        principal_id=str(principal),
        otp=otp,
        now=now,
    )
    nonce = secrets.token_urlsafe(32)
    service = AdminAccessService(
        store,
        _SshOperatorAuthenticator(principal, nonce, AdminAssurance.STEP_UP),
    )
    issued = service.issue_session(nonce, authenticated_at=now, lifetime=timedelta(minutes=10))
    _write_token_exclusive(output_file, issued.token)
    return str(issued.session_id)


def revoke_ssh_operator_session(
    *,
    data_dir: Path,
    token_file: Path,
    now: datetime,
) -> str:
    token = _read_operator_token(token_file)
    service = AdminAccessService(
        SqliteAdminAccessStore(data_dir / "admin-access.sqlite3"),
        RejectingAdminAuthenticator(),
    )
    revocation = service.revoke_own_session(
        token,
        revoked_at=now,
        reason="SSH operator session closed",
    )
    token_file.unlink()
    return str(revocation.session_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage internal AXIGNAL Admin sessions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue = subparsers.add_parser("issue", help="Issue one AO-01 Admin session")
    issue.add_argument("--data-dir", type=Path, required=True)
    issue.add_argument("--principal-id", required=True)
    issue.add_argument("--output-file", type=Path, required=True)
    issue.add_argument("--hours", type=int, default=8, choices=range(1, 13))

    enroll = subparsers.add_parser(
        "enroll-step-up", help="Create root-only TOTP factor (operator action)"
    )
    enroll.add_argument("--principal-id", required=True)
    enroll.add_argument("--factor-file", type=Path, required=True)
    enroll.add_argument("--provisioning-file", type=Path, required=True)

    elevate = subparsers.add_parser("step-up", help="Issue independent 10-minute STEP_UP")
    elevate.add_argument("--data-dir", type=Path, required=True)
    elevate.add_argument("--primary-token-file", type=Path, required=True)
    elevate.add_argument("--factor-file", type=Path, required=True)
    elevate.add_argument("--output-file", type=Path, required=True)

    revoke = subparsers.add_parser("revoke", help="Revoke the session stored in a token file")
    revoke.add_argument("--data-dir", type=Path, required=True)
    revoke.add_argument("--token-file", type=Path, required=True)

    args = parser.parse_args()
    _require_root_operator(os.geteuid() if hasattr(os, "geteuid") else -1)
    now = datetime.now(UTC)
    if args.command == "issue":
        session_id = issue_ssh_operator_session(
            data_dir=args.data_dir.expanduser().resolve(),
            principal_id=args.principal_id,
            output_file=args.output_file.expanduser(),
            now=now,
            lifetime=timedelta(hours=args.hours),
        )
        print(f"session_id={session_id}")
        print(f"token_file={args.output_file}")
        return

    if args.command == "enroll-step-up":
        from tools.runtime.admin_step_up import enroll_factor

        enroll_factor(
            args.factor_file.expanduser().resolve(),
            args.provisioning_file.expanduser().resolve(),
            principal_id=args.principal_id,
        )
        print("step_up_factor_enrolled=operator_only")
        print("provisioning_file=restricted; remove after enrollment")
        return
    if args.command == "step-up":
        if not sys.stdin.isatty():
            raise PermissionError("step-up requires interactive root operator input")
        session_id = issue_step_up_operator_session(
            data_dir=args.data_dir.expanduser().resolve(),
            primary_token_file=args.primary_token_file.expanduser(),
            factor_file=args.factor_file.expanduser(),
            output_file=args.output_file.expanduser(),
            otp=getpass.getpass("Authenticator code: "),
            now=now,
        )
        print(f"step_up_session_id={session_id}")
        print("step_up_token_file=restricted; expires in 10 minutes")
        return

    token_file = args.token_file.expanduser().resolve()
    session_id = revoke_ssh_operator_session(
        data_dir=args.data_dir.expanduser().resolve(),
        token_file=token_file,
        now=now,
    )
    print(f"revoked_session_id={session_id}")
    print("token_file=deleted")


if __name__ == "__main__":
    main()
