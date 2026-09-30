"""A planted Xeed owns the observation lifecycle; Xignals are emergent signals."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from domain.identity import XeedId
from domain.xeed.germination import XeedGerminationState, XeedGerminationStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
XIGNAL_DIR = REPO_ROOT / "domain" / "xignal"
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_xeed_germination_status_has_no_done_state() -> None:
    assert "DONE" not in XeedGerminationStatus.__members__
    assert {status.value for status in XeedGerminationStatus} == {
        "PLANTED",
        "RESOLVING",
        "OBSERVING",
        "PARTIAL_READY",
        "FIRST_XIGNAL_READY",
        "LIVE",
        "INSUFFICIENT_EVIDENCE",
        "FAILED",
        "BLOCKED",
    }


def test_planted_xeed_requires_governed_readiness_before_live() -> None:
    state = XeedGerminationState(
        xeed_id=XeedId("xeed-1"),
        initiated_by="user-1",
        created_at=NOW,
    )
    assert state.status is XeedGerminationStatus.PLANTED
    assert state.is_live is False
    assert not hasattr(state, "mark_live")


def test_xignal_package_no_longer_owns_observation_seed() -> None:
    assert not (XIGNAL_DIR / "observation_seed.py").exists()


def test_xeed_germination_exposes_no_canonical_mutation() -> None:
    public_methods = {name for name in dir(XeedGerminationState) if not name.startswith("_")}
    forbidden = {"update_organization", "edit_organization", "claim", "set_canonical_name"}
    assert public_methods & forbidden == set()
