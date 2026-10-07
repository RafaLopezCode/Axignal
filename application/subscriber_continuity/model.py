"""Private economic continuity of one authorized Observation Focus (TASK-050 T022-T024).

Continuity is governed economic state, never conversation memory. A checkpoint records
what the Subscriber Brain held for one Focus at one temporal cut, what it depended on,
and what remained open. It references snapshots and evidence; it never copies AXIGLAND,
and the Tenant owns only this private continuity, never the Organization or its facts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


def semantic_hash(value: object) -> str:
    """Order- and serialization-stable hash; callers exclude clocks they do not mean."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class DependencyKind(StrEnum):
    #: A governed observation in Observation Memory (EB-06 temporal authority).
    OBSERVATION = "OBSERVATION"
    #: A published demand record carried by the opportunity projection itself.
    DEMAND_RECORD = "DEMAND_RECORD"


@dataclass(frozen=True, slots=True)
class DeclaredDependency:
    """What one checkpoint relied on, identified by content, not by evaluation time."""

    key: str
    kind: DependencyKind
    source_ref: str
    observed_at: datetime
    subject_id: str | None = None
    content_fingerprint: str | None = None
    #: Normalized state fields this observation contributed: (name, value, state).
    fields: tuple[tuple[str, str, str], ...] = ()

    def identity(self) -> dict[str, object]:
        return {
            "key": self.key,
            "kind": self.kind.value,
            "source_ref": self.source_ref,
            # UTC: the same instant must fingerprint the same in any offset.
            "observed_at": self.observed_at.astimezone(UTC).isoformat(),
            "subject_id": self.subject_id,
            "content_fingerprint": self.content_fingerprint,
            "fields": [list(item) for item in self.fields],
        }


class DependencyStatus(StrEnum):
    CURRENT = "CURRENT"
    #: Re-observed with the same meaning: not an economic change.
    REFRESHED = "REFRESHED"
    STALE = "STALE"
    REPLACED = "REPLACED"
    WITHDRAWN = "WITHDRAWN"
    RIGHTS_BLOCKED = "RIGHTS_BLOCKED"
    MISSING = "MISSING"


class InvalidationAction(StrEnum):
    NONE = "NONE"
    #: Stale is not false: re-observe; the output is not shown as current meanwhile.
    REVALIDATE = "REVALIDATE"
    #: Meaning changed underneath: recompute through the existing runtime.
    RECOMPUTE = "RECOMPUTE"
    #: Support can no longer be used: the item is UNKNOWN until new governed support.
    UNKNOWN = "UNKNOWN"


ACTION_FOR_STATUS = {
    DependencyStatus.CURRENT: InvalidationAction.NONE,
    DependencyStatus.REFRESHED: InvalidationAction.NONE,
    DependencyStatus.STALE: InvalidationAction.REVALIDATE,
    DependencyStatus.REPLACED: InvalidationAction.RECOMPUTE,
    DependencyStatus.WITHDRAWN: InvalidationAction.RECOMPUTE,
    DependencyStatus.RIGHTS_BLOCKED: InvalidationAction.UNKNOWN,
    DependencyStatus.MISSING: InvalidationAction.UNKNOWN,
}


@dataclass(frozen=True, slots=True)
class ContinuityItem:
    """One economic conclusion the Brain held (an opportunity, an EB-04 dimension)."""

    key: str
    kind: str
    family: str | None
    epistemic: str
    currentness: str
    value_fingerprint: str
    dependency_keys: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "key": self.key,
            "kind": self.kind,
            "family": self.family,
            "epistemic": self.epistemic,
            "currentness": self.currentness,
            "valueFingerprint": self.value_fingerprint,
            "dependencyKeys": list(self.dependency_keys),
        }


class QuestionKind(StrEnum):
    MISSING_CONTEXT = "MISSING_CONTEXT"
    DIMENSION_UNKNOWN = "DIMENSION_UNKNOWN"
    EVIDENCE_NOT_CURRENT = "EVIDENCE_NOT_CURRENT"
    FAMILY_UNOBSERVED = "FAMILY_UNOBSERVED"
    REPRESENTATION_UNMEASURED = "REPRESENTATION_UNMEASURED"


@dataclass(frozen=True, slots=True)
class OpenQuestion:
    """Derived from governed state; an open question is never a fact and never a task."""

    key: str
    kind: QuestionKind
    about: str
    reason: str
    dependency_keys: tuple[str, ...] = ()

    def to_wire(self) -> dict[str, object]:
        return {
            "key": self.key,
            "kind": self.kind.value,
            "about": self.about,
            "reason": self.reason,
            "dependencyKeys": list(self.dependency_keys),
        }


@dataclass(frozen=True, slots=True)
class ContinuityOrigin:
    """The deterministic point a private continuity is computed from."""

    previous_checkpoint_id: str | None
    organization_id: str
    snapshot_refs: tuple[str, ...]
    temporal_cut: datetime
    dependency_fingerprint: str


@dataclass(frozen=True, slots=True)
class ContinuityState:
    """Checkpoint content before it is placed in a Focus's history."""

    organization_id: str
    snapshot_refs: tuple[str, ...]
    temporal_cut: datetime
    items: tuple[ContinuityItem, ...]
    questions: tuple[OpenQuestion, ...]
    dependencies: tuple[DeclaredDependency, ...]
    trace: dict[str, object]

    @property
    def dependency_fingerprint(self) -> str:
        return semantic_hash(sorted((item.identity() for item in self.dependencies), key=str))

    @property
    def semantic_fingerprint(self) -> str:
        """Economic meaning only: no clocks, no ordering, no serialization noise."""
        return semantic_hash(
            {
                "organization": self.organization_id,
                "items": sorted((item.to_wire() for item in self.items), key=str),
                "questions": sorted((item.to_wire() for item in self.questions), key=str),
                "dependencies": self.dependency_fingerprint,
                "trace": self.trace,
            }
        )


@dataclass(frozen=True, slots=True)
class ContinuityCheckpoint:
    checkpoint_id: str
    tenant_id: str
    xeed_id: str
    sequence: int
    origin: ContinuityOrigin
    state: ContinuityState

    @property
    def semantic_fingerprint(self) -> str:
        return self.state.semantic_fingerprint

    def summary(self) -> dict[str, object]:
        return {
            "checkpointId": self.checkpoint_id,
            "sequence": self.sequence,
            "origin": {
                "previousCheckpointId": self.origin.previous_checkpoint_id,
                "organizationId": self.origin.organization_id,
                "snapshotRefs": list(self.origin.snapshot_refs),
                "temporalCut": self.origin.temporal_cut.isoformat(),
                "dependencyFingerprint": self.origin.dependency_fingerprint,
            },
            "semanticFingerprint": self.semantic_fingerprint,
            "trace": self.state.trace,
            "items": [item.to_wire() for item in self.state.items],
            "openQuestions": [item.to_wire() for item in self.state.questions],
        }


def checkpoint_id(
    *, tenant_id: str, xeed_id: str, previous: str | None, semantic_fingerprint: str
) -> str:
    """Same lineage + same meaning = same id, so replays never fork history."""
    return "continuity:" + semantic_hash([tenant_id, xeed_id, previous, semantic_fingerprint])[:40]
