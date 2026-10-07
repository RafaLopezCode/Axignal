"""Operator-only CLI for private design-partner pilot invitations."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.subscriber_access.pilot import PilotAccessService
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AXIGNAL private pilot invitations")
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue", help="Issue a one-use invitation token")
    issue.add_argument("--data-dir", required=True)
    issue.add_argument("--issued-by", required=True)
    issue.add_argument("--reason", required=True)
    issue.add_argument("--invite-hours", type=int, default=168)
    grants = sub.add_parser("grants", help="List live pilot grants (no personal data)")
    grants.add_argument("--data-dir", required=True)
    revoke = sub.add_parser("revoke", help="Revoke one pilot grant; observed memory is kept")
    revoke.add_argument("--data-dir", required=True)
    revoke.add_argument("--grant-ref", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = Path(args.data_dir).expanduser().resolve()
    service = PilotAccessService(SqlitePilotAccessStore(root / "subscriber-pilot.sqlite3"))
    if args.command == "issue":
        if args.invite_hours <= 0 or args.invite_hours > 24 * 30:
            raise SystemExit("invite hours must be between 1 and 720")
        invite = service.issue_invite(
            issued_by=args.issued_by,
            reason=args.reason,
            now=datetime.now(UTC),
            invite_ttl=timedelta(hours=args.invite_hours),
        )
        print(f"invite_ref={invite.invite_ref}")
        print(f"expires_at={invite.expires_at.isoformat()}")
        print(f"invite_token={invite.invite_token}")
        print("The invite token is shown once. Send it only to the intended design partner.")
        return 0
    store = SqlitePilotAccessStore(root / "subscriber-pilot.sqlite3")
    if args.command == "grants":
        for grant in store.active_grants(now=datetime.now(UTC)):
            print(
                f"grant_ref={grant.grant_ref} tenant_id={grant.tenant_id} "
                f"expires_at={grant.expires_at.isoformat()}"
            )
        return 0
    if args.command == "revoke":
        # Revocation stops capacity-dependent access (web, MCP); AXIGLAND and history stay.
        revoked = store.revoke_grant(args.grant_ref, revoked_at=datetime.now(UTC))
        print("revoked=true" if revoked else "revoked=false")
        return 0 if revoked else 1
    raise SystemExit("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
