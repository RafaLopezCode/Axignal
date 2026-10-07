"""Explicit Admin read/write authority for private pilot preparation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from application.admin_pilot_accounts import PilotAccounts, save_pilot_accounts
from domain.admin_access import AdminRiskClass, AdminScope
from pipeline.admin_pilot_accounts import SqlitePilotAccountsStore
from tools.runtime.admin_access import AdminHttpAccessGuard


def pilot_accounts_payload(accounts: PilotAccounts) -> dict[str, object]:
    return {
        "a": accounts.a,
        "b": accounts.b,
        "revision": accounts.revision,
        "authorizedForTest": accounts.authorized_for_test,
        "savedBy": accounts.saved_by,
        "savedAt": accounts.saved_at.isoformat() if accounts.saved_at else None,
    }


def pilot_accounts_request(
    guard: AdminHttpAccessGuard,
    *,
    authorization: str | None,
    data_dir: Path,
    now: datetime,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    write = payload is not None
    grant = guard.authorize_header(
        authorization,
        required_scope=AdminScope.CUSTOMERS_WRITE if write else AdminScope.CUSTOMERS_READ,
        risk=AdminRiskClass.WRITE if write else AdminRiskClass.READ,
        now=now,
    )
    store = SqlitePilotAccountsStore(data_dir / "admin-pilot-accounts.sqlite3")
    if payload is None:
        return pilot_accounts_payload(store.read())
    if set(payload) != {"a", "b", "expectedRevision"}:
        raise ValueError("invalid pilot preparation fields")
    a, b, revision = payload["a"], payload["b"], payload["expectedRevision"]
    if not isinstance(a, str) or not isinstance(b, str) or type(revision) is not int:
        raise ValueError("invalid pilot preparation values")
    return pilot_accounts_payload(
        save_pilot_accounts(
            store,
            a=a,
            b=b,
            expected_revision=revision,
            actor=str(grant.principal_id),
            now=now.astimezone(UTC),
        )
    )
