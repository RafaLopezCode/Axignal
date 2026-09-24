"""ObservationSeed: the technical shape of a XIGNAL.

The seed describes AXIGNAL's work, not the company's declared identity. An
organization is referenced only by opaque id; this module never imports the
canonical organization model.

Doctrine: MASTER §4.4, §7.2 (ObservationSeed), §26 (the Xignal in UX).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class XignalError(Exception):
    """Raised for invalid Xignal state."""


class ObservationStatus(StrEnum):
    """Observation lifecycle. There is no DONE state (MASTER §10)."""

    EXPANDING = "EXPANDING"
    LIVE = "LIVE"


@dataclass
class ObservationSeed:
    """Persistent observation allocation for one organization (MASTER §7.2)."""

    id: str
    organization_id: str
    initiated_by: str
    created_at: datetime
    status: ObservationStatus = ObservationStatus.EXPANDING
    observation_depth: int = 0
    monitoring_state: str = "EXPANDING"
    knowledge_frontier_id: str = ""
    expansion_budget: float = 0.0
    last_observed_at: datetime | None = None
    next_observation_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.organization_id.strip():
            raise XignalError("ObservationSeed requires an organization reference")

    def mark_live(self) -> None:
        """Transition to LIVE. Never to DONE."""

        self.status = ObservationStatus.LIVE
        self.monitoring_state = "LIVE"

    @property
    def is_live(self) -> bool:
        return self.status is ObservationStatus.LIVE
