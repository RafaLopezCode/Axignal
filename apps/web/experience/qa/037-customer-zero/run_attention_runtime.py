"""Isolated attention browser harness; never compose this in production."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pytest
from run_runtime import LocalQAIdentity

from application.admin_access import AdminAccessService
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.admin_access import SqliteAdminAccessStore
from tests.contracts.test_fr30_production_first_proof import _install_source
from tools.runtime.config import RuntimeConfig
from tools.runtime.first_proof import FirstProofInsufficientEvidence
from tools.runtime.organization_attention import (
    CanonicalObservationTarget,
    OrganizationAttention,
    load_observation_catalog,
)
from tools.runtime.service import build_runtime, serve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    data = args.data_dir.resolve()
    if data.is_relative_to(root) or not data.is_relative_to(Path("D:/AXIGNAL")):
        raise ValueError("Isolated QA data only")
    runtime = build_runtime(
        RuntimeConfig(
            "development", "127.0.0.1", 8766, "c" * 40, data, root / "apps/web", "axignal.com"
        )
    )
    proof = runtime.first_proof
    assert proof is not None
    catalog = (
        *load_observation_catalog(None, "axignal.com"),
        *(
            CanonicalObservationTarget(
                Organization(OrganizationId("org:qa:" + name), name),
                "https://" + host + "/",
                "identity:controlled-browser-test:" + name,
            )
            for name, host in [
                ("Controlled second", "controlled.example"),
                ("Insufficient case", "insufficient.example"),
                ("Failure case", "failure.example"),
            ]
        ),
    )
    runtime.organization_attention = OrganizationAttention(proof, catalog)
    store = SqliteAdminAccessStore(data / "admin-access.sqlite3")
    authority = AdminAccessService(store, LocalQAIdentity())
    now = datetime.now(UTC)
    if not store.has_privilege_history():
        authority.bootstrap_founder(
            "ao24a-local-validation", occurred_at=now, reason="Isolated AO-24A browser harness"
        )
    (data / "admin-session.key").write_text(
        authority.issue_session("ao24a-local-validation", authenticated_at=now).token,
        encoding="utf-8",
    )
    runtime.admin_access = authority
    patch = pytest.MonkeyPatch()
    _install_source(patch, proof)
    original = proof.observe_resolved

    def controlled(self, *, label, target_uri, organization):
        del self
        if target_uri == "https://insufficient.example/":
            raise FirstProofInsufficientEvidence("CONTROLLED_BROWSER_INSUFFICIENT")
        if target_uri == "https://failure.example/":
            raise RuntimeError("CONTROLLED_BROWSER_FAILURE")
        return original(label=label, target_uri=target_uri, organization=organization)

    patch.setattr(type(proof), "observe_resolved", controlled)
    print("Isolated attention QA loopback:8766; no credentials logged", flush=True)
    serve(runtime)


if __name__ == "__main__":
    main()
