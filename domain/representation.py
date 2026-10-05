"""Immutable representation text and exact code-point spans (MASTER §§14, 56).

These values preserve support, not truth. Offsets are half-open Python string
indices in the identified normalized surface, never raw HTML byte offsets.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum


class TextSurface(StrEnum):
    VISIBLE_TEXT = "VISIBLE_TEXT"
    STRUCTURED_DATA = "STRUCTURED_DATA"
    EXTRACTED_TEXT = "EXTRACTED_TEXT"


def text_fingerprint(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TextRepresentation:
    representation_id: str
    observation_id: str
    subject_id: str
    source_ref: str
    source_type: str
    observed_at: datetime
    text: str
    surface: TextSurface
    representation_version: str
    normalization_version: str
    source_content_fingerprint: str
    source_observation_fingerprint: str
    source_artifact_ref: str
    source_observation_artifact_ref: str
    artifact_ref: str
    document_fingerprint: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"text representation requires {name}")
        if not isinstance(self.surface, TextSurface):
            raise ValueError("text representation surface must be explicit")
        if not isinstance(self.observed_at, datetime):
            raise ValueError("text representation requires observation time")

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["observed_at"] = self.observed_at.isoformat()
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return text_fingerprint(encoded)

    @property
    def currentness_dependency(self) -> str:
        """Resolve currentness from observation lifecycle; never assume CURRENT."""
        return self.observation_id

    def span(self, start: int, end: int) -> RepresentationSpan:
        span = RepresentationSpan(self.representation_id, self.fingerprint, start, end)
        span.extract(self)
        return span

    def unique_span(self, excerpt: str) -> RepresentationSpan:
        if not excerpt:
            raise ValueError("supporting excerpt is empty")
        start = self.text.find(excerpt)
        if start < 0:
            raise ValueError("supporting excerpt is not grounded in representation text")
        if self.text.find(excerpt, start + 1) >= 0:
            raise ValueError("ambiguous excerpt requires explicit offsets")
        return self.span(start, start + len(excerpt))


@dataclass(frozen=True, slots=True)
class RepresentationSpan:
    representation_id: str
    representation_fingerprint: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.representation_id.strip() or not self.representation_fingerprint.strip():
            raise ValueError("span requires representation identity and fingerprint")
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or not 0 <= self.start < self.end
        ):
            raise ValueError("span requires non-empty half-open integer offsets")

    def extract(self, representation: TextRepresentation) -> str:
        if (
            self.representation_id != representation.representation_id
            or self.representation_fingerprint != representation.fingerprint
        ):
            raise ValueError("span belongs to another representation")
        if self.end > len(representation.text):
            raise ValueError("span is out of range")
        return representation.text[self.start : self.end]
