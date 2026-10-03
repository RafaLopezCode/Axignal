"""Exact material and graph verification for subscriber evidence narratives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class NarrativeMaterialContribution(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"


@dataclass(frozen=True, slots=True)
class NarrativeMaterial:
    observation_id: str
    subject_id: str
    candidate_id: str
    source_ref: str
    source_type: str
    observed_at: datetime
    excerpt_or_summary: str
    contribution: NarrativeMaterialContribution
    representation_fingerprint: str
    extraction_fingerprint: str | None

    def __post_init__(self) -> None:
        for value, name in (
            (self.observation_id, "observation_id"),
            (self.subject_id, "subject_id"),
            (self.candidate_id, "candidate_id"),
            (self.source_ref, "source_ref"),
            (self.source_type, "source_type"),
            (self.excerpt_or_summary, "excerpt_or_summary"),
            (self.representation_fingerprint, "representation_fingerprint"),
        ):
            if not value.strip():
                raise ValueError(f"narrative material requires {name}")
        if self.extraction_fingerprint is not None and not self.extraction_fingerprint.strip():
            raise ValueError("narrative material extraction fingerprint cannot be empty")
        if self.observed_at.tzinfo is None:
            raise ValueError("narrative material time must be timezone-aware")


class NarrativeMaterialResolver(Protocol):
    def resolve(self, observation_id: str) -> NarrativeMaterial | None: ...

    def considered_observation_ids(
        self,
        *,
        subject_id: str,
        candidate_id: str,
    ) -> tuple[str, ...]: ...


class NarrativeMaterialMapResolver:
    def __init__(self, materials: tuple[NarrativeMaterial, ...]) -> None:
        self._materials = {item.observation_id: item for item in materials}
        if len(self._materials) != len(materials):
            raise ValueError("narrative materials require unique observation ids")

    def resolve(self, observation_id: str) -> NarrativeMaterial | None:
        return self._materials.get(observation_id)

    def considered_observation_ids(
        self,
        *,
        subject_id: str,
        candidate_id: str,
    ) -> tuple[str, ...]:
        return tuple(
            item.observation_id
            for item in self._materials.values()
            if item.subject_id == subject_id and item.candidate_id == candidate_id
        )


class NarrativeGraphKind(StrEnum):
    RELATIONSHIP = "RELATIONSHIP"
    PATHX = "PATHX"


@dataclass(frozen=True, slots=True)
class NarrativeGraphReference:
    ref: str
    kind: NarrativeGraphKind
    label: str
    subject_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.ref.strip() or not self.label.strip():
            raise ValueError("narrative graph reference identity is required")
        if not self.subject_ids or any(not value.strip() for value in self.subject_ids):
            raise ValueError("narrative graph reference requires governed subjects")


class NarrativeGraphResolver(Protocol):
    def resolve(
        self,
        *,
        ref: str,
        kind: NarrativeGraphKind,
        authorized_subject_id: str,
    ) -> NarrativeGraphReference | None: ...


class NarrativeGraphMapResolver:
    def __init__(self, references: tuple[NarrativeGraphReference, ...]) -> None:
        self._references = {(item.kind, item.ref): item for item in references}

    def resolve(
        self,
        *,
        ref: str,
        kind: NarrativeGraphKind,
        authorized_subject_id: str,
    ) -> NarrativeGraphReference | None:
        item = self._references.get((kind, ref))
        if item is None or authorized_subject_id not in item.subject_ids:
            return None
        return item
