"""Root-only SSH operator adapter for issuing internal AO-01 Admin sessions.

This is not a public login provider. The trusted outer authentication event is the
operator's successful SSH access to the production host. The runtime itself uses
a validation-only authenticator and cannot exchange SSH credentials for sessions.
"""

from __future__ import annotations

import argparse
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from domain.admin_access import AdminAssurance, AdminPrincipalId
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.admin_access import RejectingAdminAuthenticator


@dataclass(frozen=True, slots=True)
class _SshOperatorAuthenticator:
    principal_id: AdminPrincipalId
    nonce: str

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        if not secrets.compare_digest(credential, self.nonce):
            return None
        return VerifiedAdminIdentity(
            principal_id=self.principal_id,
            authenticated_at=now.astimezone(UTC),
            assurance=AdminAssurance.PRIMARY,
            auth_source="ssh-root-operator",
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
            output_file=args.output_file.expanduser().resolve(),
            now=now,
            lifetime=timedelta(hours=args.hours),
        )
        print(f"session_id={session_id}")
        print(f"token_file={args.output_file}")
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
