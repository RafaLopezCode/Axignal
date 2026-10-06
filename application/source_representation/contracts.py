"""Provider-neutral contracts for derived document representation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from domain.representation import (
    RepresentationSpan,
    TextRepresentation,
    TextSurface,
    text_fingerprint,
)


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
    source_artifact_ref: str
    source_observation_artifact_ref: str
    extracted_text: str | None = None
    extracted_text_fingerprint: str | None = None
    visibility_resolved: bool = True

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
            self.source_artifact_ref,
            self.source_observation_artifact_ref,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("representation observation time must be timezone-aware")
        if any(not item.strip() for item in self.structured_data):
            raise ValueError("structured-data entries cannot be empty")
        if self.visible_text_fingerprint != text_fingerprint(self.visible_text):
            raise ValueError("visible text does not match its fingerprint")
        extracted_text = self.extracted_text or self.visible_text
        extracted_fingerprint = self.extracted_text_fingerprint or text_fingerprint(extracted_text)
        if extracted_fingerprint != text_fingerprint(extracted_text):
            raise ValueError("extracted text does not match its fingerprint")
        if not self.visibility_resolved and self.extracted_text is None:
            raise ValueError("unresolved visibility requires explicit extracted text")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "representation_id": self.representation_id,
                "subject_id": self.subject_id,
                "source_ref": self.source_ref,
                "source_type": self.source_type,
                "observed_at": self.observed_at.isoformat(),
                "source_artifact_ref": self.source_artifact_ref,
                "source_observation_artifact_ref": self.source_observation_artifact_ref,
                "artifact_ref": self.artifact_ref,
                "observation_id": self.observation_id,
                "source_observation_fingerprint": self.source_observation_fingerprint,
                "source_content_fingerprint": self.source_content_fingerprint,
                "media_type": self.media_type,
                "charset": self.charset,
                "title": self.title,
                "language": self.language,
                "description": self.description,
                "canonical_uri": self.canonical_uri,
                "visible_text_fingerprint": (
                    self.visible_text_fingerprint if self.visibility_resolved else None
                ),
                "extracted_text_fingerprint": self.document_text_fingerprint,
                "visibility_resolved": self.visibility_resolved,
                "structured_data": self.structured_data,
                "representation_version": self.representation_version,
                "normalization_version": self.normalization_version,
            }
        )

    @property
    def document_text(self) -> str:
        """Deterministically extracted document text, independent of visual certainty."""
        return self.extracted_text or self.visible_text

    @property
    def document_text_fingerprint(self) -> str:
        return self.extracted_text_fingerprint or text_fingerprint(self.document_text)

    def text_representation(self, structured_index: int | None = None) -> TextRepresentation:
        """Project one exact surface for verifiable support; never grant truth."""
        if structured_index is not None:
            if type(structured_index) is not int or not 0 <= structured_index < len(
                self.structured_data
            ):
                raise ValueError("structured surface index is out of range")
            text = self.structured_data[structured_index]
            surface = TextSurface.STRUCTURED_DATA
            representation_id = f"{self.representation_id}#structured:{structured_index}"
        else:
            text = self.document_text
            surface = (
                TextSurface.VISIBLE_TEXT if self.visibility_resolved else TextSurface.EXTRACTED_TEXT
            )
            representation_id = self.representation_id
        return TextRepresentation(
            representation_id=representation_id,
            observation_id=self.observation_id,
            subject_id=self.subject_id,
            source_ref=self.source_ref,
            source_type=self.source_type,
            observed_at=self.observed_at,
            text=text,
            surface=surface,
            representation_version=self.representation_version,
            normalization_version=self.normalization_version,
            source_content_fingerprint=self.source_content_fingerprint,
            source_observation_fingerprint=self.source_observation_fingerprint,
            source_artifact_ref=self.source_artifact_ref,
            source_observation_artifact_ref=self.source_observation_artifact_ref,
            artifact_ref=self.artifact_ref,
            document_fingerprint=self.fingerprint,
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
    supporting_span: RepresentationSpan | None = None

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
