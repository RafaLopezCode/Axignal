"""XIGNAL is observation allocation, not ownership (MASTER §4.4, §7, §10, §32)."""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

from domain.xignal.observation_seed import ObservationSeed, ObservationStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
XIGNAL_DIR = REPO_ROOT / "domain" / "xignal"


def test_xignal_status_has_no_done_state() -> None:
    assert "DONE" not in ObservationStatus.__members__
    assert {status.value for status in ObservationStatus} == {"EXPANDING", "LIVE"}


def test_seed_can_go_live_but_never_done() -> None:
    seed = ObservationSeed(
        id="seed-1",
        organization_id="org-acme",
        initiated_by="user-1",
        created_at=datetime(2026, 1, 1),
    )
    seed.mark_live()
    assert seed.is_live is True
    assert seed.status is not ObservationStatus.__members__.get("DONE", None)


def test_xignal_source_does_not_import_organizations() -> None:
    offenders: list[str] = []
    for path in XIGNAL_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "organizations" in node.module:
                offenders.append(path.as_posix())
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "organizations" in alias.name:
                        offenders.append(path.as_posix())
    assert offenders == []


def test_observation_seed_exposes_no_canonical_mutation() -> None:
    public_methods = {name for name in dir(ObservationSeed) if not name.startswith("_")}
    forbidden = {"update_organization", "edit_organization", "claim", "set_canonical_name"}
    assert public_methods & forbidden == set()
