"""Local AO-24A QA composition; never a production authentication adapter.

All economic execution is the unchanged FR-30 service. Controlled failure modes
exercise recovery without manufacturing observations or successful projections.
Private data and credentials are written only outside the repository.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from application.admin_access.service import AdminAuthenticationError
from domain.admin_access import (
    AdminAccessError,
    AdminAssurance,
    AdminPrincipalId,
    AdminRiskClass,
    AdminScope,
)
from pipeline.admin_access import SqliteAdminAccessStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.first_proof import FirstProofInsufficientEvidence, FirstProofService
from tools.runtime.service import build_runtime, serve


class LocalQAIdentity:
    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        if credential != "ao24a-local-validation":
            return None
        return VerifiedAdminIdentity(
            AdminPrincipalId("admin:ao24a-local-validation"),
            now,
            AdminAssurance.PRIMARY,
            "AO24A_LOCAL_QA_ONLY",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--sha", required=True)
    parser.add_argument(
        "--scenario", choices=("real", "insufficient", "failure", "rejection"), default="real"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    data = args.data_dir.resolve()
    if data.is_relative_to(root) or not data.is_relative_to(Path("D:/AXIGNAL")):
        raise ValueError("QA data must remain outside the repository, inside D:/AXIGNAL")
    runtime = build_runtime(
        RuntimeConfig(
            "development",
            "127.0.0.1",
            8765,
            args.sha,
            data,
            root / "apps/web",
            "axignal.com",
        )
    )
    store = SqliteAdminAccessStore(data / "admin-access.sqlite3")
    authority = AdminAccessService(store, LocalQAIdentity())
    now = datetime.now(UTC)
    if not store.has_privilege_history():
        authority.bootstrap_founder(
            "ao24a-local-validation",
            occurred_at=now,
            reason="AO-24A isolated local browser verification",
        )
    token_path = data / "admin-session.key"
    renew_session = not token_path.exists()
    if not renew_session:
        try:
            authority.authorize(
                token_path.read_text(encoding="utf-8"),
                required_scope=AdminScope.XEEDS_READ,
                risk=AdminRiskClass.READ,
                now=now,
            )
        except (AdminAccessError, AdminAuthenticationError):
            renew_session = True
    if renew_session:
        token_path.write_text(
            authority.issue_session("ao24a-local-validation", authenticated_at=now).token,
            encoding="utf-8",
        )
    runtime.admin_access = authority
    if args.scenario != "real":

        def controlled_failure(
            self: FirstProofService, *, label: str, target_uri: str
        ) -> dict[str, object]:
            del self, label, target_uri
            if args.scenario == "insufficient":
                raise FirstProofInsufficientEvidence("CONTROLLED_QA_SOURCE_NOT_EVALUABLE")
            if args.scenario == "rejection":
                raise ValueError("CONTROLLED_QA_GOVERNED_REJECTION")
            raise RuntimeError("CONTROLLED_QA_RUNTIME_FAILURE")

        FirstProofService.plant = controlled_failure  # type: ignore[method-assign]
    print(
        f"AO-24A local QA runtime: {args.scenario}; loopback:8765; no credentials logged",
        flush=True,
    )
    serve(runtime)


if __name__ == "__main__":
    main()
