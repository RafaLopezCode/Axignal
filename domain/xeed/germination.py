"""Xeed germination state: persistent observation lifecycle for one planted Xeed."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from domain.identity import XeedId


class XeedGerminationError(ValueError):
    """Raised for invalid Xeed germination state or transition."""


class XeedGerminationStatus(StrEnum):
    """Operational lifecycle for a Living Xeed. LIVE never means DONE."""

    PLANTED = "PLANTED"
    RESOLVING = "RESOLVING"
    OBSERVING = "OBSERVING"
    PARTIAL_READY = "PARTIAL_READY"
    FIRST_XIGNAL_READY = "FIRST_XIGNAL_READY"
    LIVE = "LIVE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


_ALLOWED_TRANSITIONS: dict[XeedGerminationStatus, frozenset[XeedGerminationStatus]] = {
    XeedGerminationStatus.PLANTED: frozenset(
        {
            XeedGerminationStatus.RESOLVING,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.RESOLVING: frozenset(
        {
            XeedGerminationStatus.OBSERVING,
            XeedGerminationStatus.INSUFFICIENT_EVIDENCE,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.OBSERVING: frozenset(
        {
            XeedGerminationStatus.PARTIAL_READY,
            XeedGerminationStatus.FIRST_XIGNAL_READY,
            XeedGerminationStatus.INSUFFICIENT_EVIDENCE,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.PARTIAL_READY: frozenset(
        {
            XeedGerminationStatus.OBSERVING,
            XeedGerminationStatus.FIRST_XIGNAL_READY,
            XeedGerminationStatus.INSUFFICIENT_EVIDENCE,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.FIRST_XIGNAL_READY: frozenset(
        {
            XeedGerminationStatus.OBSERVING,
            XeedGerminationStatus.PARTIAL_READY,
            XeedGerminationStatus.LIVE,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.LIVE: frozenset(
        {
            XeedGerminationStatus.LIVE,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.INSUFFICIENT_EVIDENCE: frozenset(
        {
            XeedGerminationStatus.RESOLVING,
            XeedGerminationStatus.OBSERVING,
            XeedGerminationStatus.BLOCKED,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.BLOCKED: frozenset(
        {
            XeedGerminationStatus.RESOLVING,
            XeedGerminationStatus.OBSERVING,
            XeedGerminationStatus.FAILED,
        }
    ),
    XeedGerminationStatus.FAILED: frozenset(
        {
            XeedGerminationStatus.RESOLVING,
            XeedGerminationStatus.OBSERVING,
        }
    ),
}


@dataclass(frozen=True, slots=True)
class XeedGerminationTransition:
    from_status: XeedGerminationStatus
    to_status: XeedGerminationStatus
    occurred_at: datetime
    reason_code: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise XeedGerminationError("Xeed transition time must be timezone-aware")
        if not self.reason_code.strip():
            raise XeedGerminationError("Xeed transition reason is required")


@dataclass
class XeedGerminationState:
    """Operational/cognitive lifecycle for a planted Xeed.

    This state governs observation work only and has no canonical-write authority.
    """

    xeed_id: XeedId
    initiated_by: str
    created_at: datetime
    status: XeedGerminationStatus = XeedGerminationStatus.PLANTED
    observation_depth: int = 0
    knowledge_frontier_id: str = ""
    expansion_budget: float = 0.0
    last_observed_at: datetime | None = None
    next_observation_at: datetime | None = None
    first_xignal_id: str | None = None
    transitions: list[XeedGerminationTransition] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.xeed_id, str) or not self.xeed_id.strip():
            raise XeedGerminationError("Xeed germination requires a Xeed id")
        if not self.initiated_by.strip():
            raise XeedGerminationError("Xeed germination requires an initiator")
        if self.created_at.tzinfo is None:
            raise XeedGerminationError("Xeed germination creation time must be timezone-aware")
        if self.observation_depth < 0:
            raise XeedGerminationError("Xeed observation depth cannot be negative")
        if self.first_xignal_id is not None and not self.first_xignal_id.strip():
            raise XeedGerminationError("first Xignal id must be non-empty when provided")

    def transition(
        self,
        to_status: XeedGerminationStatus,
        *,
        occurred_at: datetime,
        reason_code: str,
    ) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if to_status not in allowed:
            raise XeedGerminationError(
                f"illegal Xeed germination transition {self.status.value} -> {to_status.value}"
            )
        transition = XeedGerminationTransition(
            from_status=self.status,
            to_status=to_status,
            occurred_at=occurred_at,
            reason_code=reason_code,
        )
        self.transitions.append(transition)
        self.status = to_status

    def note_observation(self, *, observed_at: datetime) -> None:
        if observed_at.tzinfo is None:
            raise XeedGerminationError("Xeed observation time must be timezone-aware")
        self.observation_depth += 1
        self.last_observed_at = observed_at

    def note_first_xignal(self, xignal_id: str) -> None:
        if not xignal_id.strip():
            raise XeedGerminationError("first Xignal id is required")
        if self.first_xignal_id is None:
            self.first_xignal_id = xignal_id
        elif self.first_xignal_id != xignal_id:
            raise XeedGerminationError("first Xignal identity is immutable once recorded")

    @property
    def is_live(self) -> bool:
        return self.status is XeedGerminationStatus.LIVE
