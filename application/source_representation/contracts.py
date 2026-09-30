"""Provider-neutral contracts for derived document representation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("document-representation identity and values must be non-empty")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DocumentRepresentation:
    """Disposable, reconstructible representation of one acquired document."""

    representation_id: str
    observation_id: str
    subject_id: str
    source_ref: str
    source_type: str
    observed_at: datetime
    source_observation_fingerprint: str
    source_content_fingerprint: str
    media_type: str
    charset: str
    title: str | None
    language: str | None
    description: str | None
    canonical_uri: str | None
    visible_text: str
    visible_text_fingerprint: str
    structured_data: tuple[str, ...]
    representation_version: str
    normalization_version: str
    artifact_ref: str

    def __post_init__(self) -> None:
        _required(
            self.representation_id,
            self.observation_id,
            self.subject_id,
            self.source_ref,
            self.source_type,
            self.source_observation_fingerprint,
            self.source_content_fingerprint,
            self.media_type,
            self.charset,
            self.visible_text,
            self.visible_text_fingerprint,
            self.representation_version,
            self.normalization_version,
            self.artifact_ref,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("representation observation time must be timezone-aware")
        if any(not item.strip() for item in self.structured_data):
            raise ValueError("structured-data entries cannot be empty")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "observation_id": self.observation_id,
                "source_observation_fingerprint": self.source_observation_fingerprint,
                "source_content_fingerprint": self.source_content_fingerprint,
                "media_type": self.media_type,
                "charset": self.charset,
                "title": self.title,
                "language": self.language,
                "description": self.description,
                "canonical_uri": self.canonical_uri,
                "visible_text_fingerprint": self.visible_text_fingerprint,
                "structured_data": self.structured_data,
                "representation_version": self.representation_version,
                "normalization_version": self.normalization_version,
            }
        )


class RepresentationArtifactReader(Protocol):
    """Read immutable acquisition artifacts by reference."""

    def read(self, reference: str) -> bytes: ...


@dataclass(frozen=True, slots=True)
class RichStateDatum:
    name: str
    value: str
    observation_id: str
    representation_id: str
    source_ref: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _required(
            self.name,
            self.value,
            self.observation_id,
            self.representation_id,
            self.source_ref,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("rich-state datum time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class RichSubjectState:
    subject_id: str
    data: tuple[RichStateDatum, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        _required(self.subject_id, self.fingerprint)
        names = [item.name for item in self.data]
        if len(names) != len(set(names)):
            raise ValueError("rich subject state requires unique datum names")

    @property
    def available_fields(self) -> frozenset[str]:
        return frozenset(item.name for item in self.data)

    def get(self, name: str) -> RichStateDatum | None:
        return next((item for item in self.data if item.name == name), None)
