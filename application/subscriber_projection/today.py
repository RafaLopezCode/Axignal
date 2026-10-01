"""Insight-first Today projection for subscriber comprehension.

Today is a comprehension layer, not a dashboard. It surfaces at most three
material, explainable items and preserves exact deep-link/evidence actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.subscriber_projection.xignal import ExplainableXignalProjection
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState


class TodayDisposition(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class TodayCandidate:
    projection: ExplainableXignalProjection
    focus_ref: str
    changed_at: datetime | None
    material: bool = True

    def __post_init__(self) -> None:
        if not self.focus_ref.strip():
            raise ValueError("Today candidate focus ref is required")
        if self.changed_at is not None and self.changed_at.tzinfo is None:
            raise ValueError("Today candidate changed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TodayPolicy:
    policy_id: str
    version: str
    max_items: int = 3

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("Today policy identity is required")
        if not 1 <= self.max_items <= 3:
            raise ValueError("Today policy must surface between one and three items")


@dataclass(frozen=True, slots=True)
class TodayItem:
    xignal_id: str
    focus_ref: str
    what_changed: str
    why_it_matters: str
    epistemic_state: XignalEpistemicState
    currentness: Currentness
    observed_at: datetime
    changed_at: datetime | None
    show_how_ref: str

    def __post_init__(self) -> None:
        for value in (
            self.xignal_id,
            self.focus_ref,
            self.what_changed,
            self.why_it_matters,
            self.show_how_ref,
        ):
            if not value.strip():
                raise ValueError("Today item requires complete human-facing meaning")
        if self.observed_at.tzinfo is None:
            raise ValueError("Today observation time must be timezone-aware")
        if self.changed_at is not None and self.changed_at.tzinfo is None:
            raise ValueError("Today change time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TodayProjection:
    disposition: TodayDisposition
    policy_id: str
    policy_version: str
    items: tuple[TodayItem, ...]
    message: str

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("Today projection policy identity is required")
        if not self.message.strip():
            raise ValueError("Today projection requires human-readable state copy")
        if len(self.items) > 3:
            raise ValueError("Today projection may not contain more than three items")
        if self.disposition is TodayDisposition.READY and not self.items:
            raise ValueError("READY Today projection requires material items")
        if self.disposition is TodayDisposition.EMPTY and self.items:
            raise ValueError("EMPTY Today projection cannot contain items")


def _candidate_sort_key(candidate: TodayCandidate) -> tuple[float, float, str]:
    projection = candidate.projection
    changed = (
        candidate.changed_at.timestamp() if candidate.changed_at is not None else float("-inf")
    )
    observed = projection.last_observed_at.timestamp()
    return (-changed, -observed, projection.xignal.xignal_id)


def project_today(
    *,
    candidates: tuple[TodayCandidate, ...],
    policy: TodayPolicy,
) -> TodayProjection:
    """Select up to three material items without scores or graph-size heuristics."""

    material = [candidate for candidate in candidates if candidate.material]
    material.sort(key=_candidate_sort_key)
    selected = material[: policy.max_items]

    items = tuple(
        TodayItem(
            xignal_id=candidate.projection.xignal.xignal_id,
            focus_ref=candidate.focus_ref,
            what_changed=candidate.projection.xignal.title,
            why_it_matters=candidate.projection.xignal.why_attention,
            epistemic_state=candidate.projection.xignal.epistemic_state,
            currentness=candidate.projection.xignal.currentness,
            observed_at=candidate.projection.last_observed_at,
            changed_at=candidate.changed_at,
            show_how_ref=candidate.projection.trail.xignal_id,
        )
        for candidate in selected
    )

    if items:
        return TodayProjection(
            disposition=TodayDisposition.READY,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            items=items,
            message="What deserves attention now.",
        )

    if candidates:
        return TodayProjection(
            disposition=TodayDisposition.PARTIAL,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            items=(),
            message="Observation is active, but nothing material is ready to surface yet.",
        )

    return TodayProjection(
        disposition=TodayDisposition.EMPTY,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        items=(),
        message="No material item is ready to surface from the current observed state.",
    )
