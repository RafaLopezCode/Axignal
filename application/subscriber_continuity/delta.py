"""Semantic delta between two continuity states of the same Focus.

Compares economic meaning by stable item keys: value fingerprints, epistemic state and
currentness. Clocks, ordering and serialization never produce a change. UNKNOWN stays
UNKNOWN, STALE is not WITHDRAWN, and a disappearing item is WITHDRAWN, not FALSE.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from application.subscriber_continuity.dependencies import DependencyEvaluation
from application.subscriber_continuity.model import (
    ContinuityItem,
    ContinuityState,
    InvalidationAction,
)


class DeltaKind(StrEnum):
    NEW = "NEW"
    CHANGED = "CHANGED"
    RESOLVED = "RESOLVED"
    INVALIDATED = "INVALIDATED"
    STALE = "STALE"
    WITHDRAWN = "WITHDRAWN"
    UNCHANGED = "UNCHANGED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class DeltaEntry:
    key: str
    subject: str  # ITEM | QUESTION
    kind: DeltaKind
    reason: str

    def to_wire(self) -> dict[str, object]:
        return {
            "key": self.key,
            "subject": self.subject,
            "kind": self.kind.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ContinuityDelta:
    entries: tuple[DeltaEntry, ...]

    @property
    def counts(self) -> dict[str, int]:
        return dict(sorted(Counter(item.kind.value for item in self.entries).items()))

    @property
    def changed(self) -> bool:
        return any(item.kind is not DeltaKind.UNCHANGED for item in self.entries)

    def to_wire(self) -> dict[str, object]:
        return {
            "counts": self.counts,
            "entries": [
                item.to_wire() for item in self.entries if item.kind is not DeltaKind.UNCHANGED
            ],
        }


def _item_kind(before: ContinuityItem, after: ContinuityItem) -> tuple[DeltaKind, str]:
    if before.value_fingerprint != after.value_fingerprint:
        return DeltaKind.CHANGED, "MEANING_CHANGED"
    if before.epistemic == "UNKNOWN" and after.epistemic != "UNKNOWN":
        return DeltaKind.RESOLVED, f"UNKNOWN_TO_{after.epistemic}"
    if before.epistemic != "UNKNOWN" and after.epistemic == "UNKNOWN":
        return DeltaKind.UNKNOWN, f"{before.epistemic}_TO_UNKNOWN"
    if before.epistemic != after.epistemic:
        return DeltaKind.CHANGED, f"{before.epistemic}_TO_{after.epistemic}"
    if before.currentness == "CURRENT" and after.currentness != "CURRENT":
        return DeltaKind.STALE, f"SUPPORT_{after.currentness}"
    if before.currentness != "CURRENT" and after.currentness == "CURRENT":
        return DeltaKind.RESOLVED, "SUPPORT_CURRENT_AGAIN"
    if before.dependency_keys != after.dependency_keys:
        return DeltaKind.CHANGED, "SUPPORT_REPLACED"
    return DeltaKind.UNCHANGED, "SAME_MEANING"


def state_delta(before: ContinuityState | None, after: ContinuityState) -> ContinuityDelta:
    """Delta between two recorded states (S1 → S2)."""

    entries: list[DeltaEntry] = []
    old = {} if before is None else {item.key: item for item in before.items}
    new = {item.key: item for item in after.items}
    for key in sorted(old.keys() | new.keys()):
        if key not in old:
            entries.append(DeltaEntry(key, "ITEM", DeltaKind.NEW, "NEW_CONCLUSION"))
        elif key not in new:
            entries.append(DeltaEntry(key, "ITEM", DeltaKind.WITHDRAWN, "NO_LONGER_SUPPORTED"))
        else:
            entries.append(DeltaEntry(key, "ITEM", *_item_kind(old[key], new[key])))
    old_q = {} if before is None else {item.key: item for item in before.questions}
    new_q = {item.key: item for item in after.questions}
    for key in sorted(old_q.keys() | new_q.keys()):
        if key not in old_q:
            entries.append(DeltaEntry(key, "QUESTION", DeltaKind.NEW, new_q[key].kind.value))
        elif key not in new_q:
            entries.append(DeltaEntry(key, "QUESTION", DeltaKind.RESOLVED, old_q[key].kind.value))
        else:
            entries.append(DeltaEntry(key, "QUESTION", DeltaKind.UNCHANGED, new_q[key].kind.value))
    return ContinuityDelta(tuple(entries))


def invalidation_delta(
    state: ContinuityState, evaluations: dict[str, DependencyEvaluation]
) -> ContinuityDelta:
    """What a recorded state would no longer support now, before any recomputation.

    Selective: only items whose own declared dependencies moved are reported.
    """

    entries: list[DeltaEntry] = []
    for item in state.items:
        moved = [
            evaluations[key]
            for key in item.dependency_keys
            if key in evaluations and evaluations[key].action is not InvalidationAction.NONE
        ]
        if not moved:
            entries.append(DeltaEntry(item.key, "ITEM", DeltaKind.UNCHANGED, "SUPPORT_HOLDS"))
            continue
        worst = sorted(moved, key=lambda item: _ACTION_RANK[item.action])[0]
        kind = (
            DeltaKind.STALE
            if worst.action is InvalidationAction.REVALIDATE
            else DeltaKind.UNKNOWN
            if worst.action is InvalidationAction.UNKNOWN
            else DeltaKind.INVALIDATED
        )
        entries.append(DeltaEntry(item.key, "ITEM", kind, f"{worst.status.value}:{worst.key}"))
    return ContinuityDelta(tuple(entries))


_ACTION_RANK = {
    InvalidationAction.UNKNOWN: 0,
    InvalidationAction.RECOMPUTE: 1,
    InvalidationAction.REVALIDATE: 2,
    InvalidationAction.NONE: 3,
}
