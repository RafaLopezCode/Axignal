"""A planted Xeed owns the observation lifecycle; Xignals are emergent signals."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from domain.identity import XeedId
from domain.xeed.germination import XeedGerminationState, XeedGerminationStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
XIGNAL_DIR = REPO_ROOT / "domain" / "xignal"


def test_xeed_germination_status_has_no_done_state() -> None:
    assert "DONE" not in XeedGerminationStatus.__members__
    assert {status.value for status in XeedGerminationStatus} == {"GERMINATING", "LIVE"}


def test_planted_xeed_can_become_live_but_never_done() -> None:
    state = XeedGerminationState(
        xeed_id=XeedId("xeed-1"),
        initiated_by="user-1",
        created_at=datetime(2026, 1, 1),
    )
    state.mark_live()
    assert state.is_live is True
    assert state.status is not XeedGerminationStatus.__members__.get("DONE", None)


def test_xignal_package_no_longer_owns_observation_seed() -> None:
    assert not (XIGNAL_DIR / "observation_seed.py").exists()


def test_xeed_germination_exposes_no_canonical_mutation() -> None:
    public_methods = {name for name in dir(XeedGerminationState) if not name.startswith("_")}
    forbidden = {"update_organization", "edit_organization", "claim", "set_canonical_name"}
    assert public_methods & forbidden == set()
