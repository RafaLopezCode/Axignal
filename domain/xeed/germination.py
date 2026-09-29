"""Xeed germination state: persistent observation lifecycle for one planted Xeed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.identity import XeedId


class XeedGerminationError(ValueError):
    """Raised for invalid Xeed germination state."""


class XeedGerminationStatus(StrEnum):
    """A Living Xeed can become LIVE but is never epistemically DONE."""

    GERMINATING = "GERMINATING"
    LIVE = "LIVE"


@dataclass
class XeedGerminationState:
    """Operational/cognitive lifecycle for a planted Xeed.

    Canonical Organization identity remains on the Xeed reference itself.
    This state governs observation work only and has no canonical write authority.
    """

    xeed_id: XeedId
    initiated_by: str
    created_at: datetime
    status: XeedGerminationStatus = XeedGerminationStatus.GERMINATING
    observation_depth: int = 0
    knowledge_frontier_id: str = ""
    expansion_budget: float = 0.0
    last_observed_at: datetime | None = None
    next_observation_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.xeed_id, str) or not self.xeed_id.strip():
            raise XeedGerminationError("Xeed germination requires a Xeed id")
        if not self.initiated_by.strip():
            raise XeedGerminationError("Xeed germination requires an initiator")

    def mark_live(self) -> None:
        """Transition to LIVE after the governed readiness gate."""

        self.status = XeedGerminationStatus.LIVE

    @property
    def is_live(self) -> bool:
        return self.status is XeedGerminationStatus.LIVE
