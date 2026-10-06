"""Content-addressed reuse of grounded semantic extraction across reobservations.

A reobservation of an unchanged document gets a new observation identity, so the
provider request identity changes although the provider-visible content does
not. This port decorator reuses an earlier provider extraction only when that
content is exactly identical, then re-grounds every candidate against the new
representation through the normal fail-closed normalizer. It never matches by
similarity, never extends trust beyond ``max_reuse_age`` and never creates truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol

from application.semantic_extraction.contracts import (
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    fingerprint,
)
from application.semantic_extraction.runtime import (
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)
from application.source_representation import DocumentRepresentation

_STRUCTURED_SUFFIX = re.compile(r"#structured:(\d+)$")


class SemanticExtractionPort(Protocol):
    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet: ...


def extraction_content_key(
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
    *,
    extractor_identity: str,
) -> str:
    """Key on everything the provider sees except observation identity and time."""

    if not extractor_identity.strip():
        raise ValueError("semantic extraction reuse requires an extractor identity")
    return fingerprint(
        {
            "extractor_identity": extractor_identity,
            "instruction": build_semantic_extraction_request(representation, contract).instruction,
            "contract_fingerprint": contract.fingerprint,
            "subject_id": representation.subject_id,
            "source_ref": representation.source_ref,
            "source_type": representation.source_type,
            "title": representation.title,
            "language": representation.language,
            "description": representation.description,
            "visibility_resolved": representation.visibility_resolved,
            "visible_text": (
                representation.visible_text if representation.visibility_resolved else None
            ),
            "document_text": representation.document_text,
            "structured_data": representation.structured_data,
            "representation_version": representation.representation_version,
            "normalization_version": representation.normalization_version,
        }
    )


@dataclass(frozen=True, slots=True)
class ReusableCandidate:
    """The provider's proposal, minus everything bound to one observation."""

    semantic_target: str
    statement: str
    excerpt: str
    grounding_surface: GroundingSurface
    start: int
    end: int
    structured_index: int | None = None

    def __post_init__(self) -> None:
        if (self.structured_index is None) != (
            self.grounding_surface is not GroundingSurface.STRUCTURED_DATA
        ):
            raise ValueError("reusable candidate surface lineage is inconsistent")


@dataclass(frozen=True, slots=True)
class SemanticExtractionRecord:
    """One original provider extraction, anchored at the observation it was made for."""

    content_key: str
    extracted_for_observed_at: datetime
    extraction_id: str
    provider: str
    provider_version: str
    candidates: tuple[ReusableCandidate, ...]

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.content_key,
                self.extraction_id,
                self.provider,
                self.provider_version,
            )
        ):
            raise ValueError("semantic extraction record identity is required")
        if self.extracted_for_observed_at.tzinfo is None:
            raise ValueError("semantic extraction record time must be timezone-aware")

    @classmethod
    def from_candidate_set(
        cls,
        candidate_set: SemanticCandidateSet,
        *,
        content_key: str,
        extracted_for_observed_at: datetime,
    ) -> SemanticExtractionRecord:
        if candidate_set.reused_from_extraction_id is not None:
            raise ValueError("only original provider extractions can anchor reuse")
        rows = []
        for candidate in candidate_set.candidates:
            match = _STRUCTURED_SUFFIX.search(candidate.supporting_representation.representation_id)
            rows.append(
                ReusableCandidate(
                    semantic_target=candidate.semantic_target,
                    statement=candidate.statement,
                    excerpt=candidate.excerpt,
                    grounding_surface=candidate.grounding_surface,
                    start=candidate.supporting_span.start,
                    end=candidate.supporting_span.end,
                    structured_index=int(match.group(1)) if match else None,
                )
            )
        return cls(
            content_key=content_key,
            extracted_for_observed_at=extracted_for_observed_at,
            extraction_id=candidate_set.extraction_id,
            provider=candidate_set.provider,
            provider_version=candidate_set.provider_version,
            candidates=tuple(rows),
        )


class SemanticExtractionRecordStore(Protocol):
    def get(self, content_key: str) -> SemanticExtractionRecord | None: ...

    def put(self, record: SemanticExtractionRecord) -> None: ...


class InMemorySemanticExtractionRecordStore:
    def __init__(self) -> None:
        self._records: dict[str, SemanticExtractionRecord] = {}

    def get(self, content_key: str) -> SemanticExtractionRecord | None:
        return self._records.get(content_key)

    def put(self, record: SemanticExtractionRecord) -> None:
        self._records[record.content_key] = record


class ContentAddressedSemanticExtractor:
    """Reuse exact-content provider extractions; delegate everything else."""

    def __init__(
        self,
        inner: SemanticExtractionPort,
        store: SemanticExtractionRecordStore,
        *,
        extractor_identity: str,
        max_reuse_age: timedelta,
    ) -> None:
        if not extractor_identity.strip():
            raise ValueError("semantic extraction reuse requires an extractor identity")
        if max_reuse_age <= timedelta(0):
            raise ValueError("semantic extraction reuse age must be positive")
        self._inner = inner
        self._store = store
        self._extractor_identity = extractor_identity
        self._max_reuse_age = max_reuse_age

    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet:
        key = extraction_content_key(
            representation, contract, extractor_identity=self._extractor_identity
        )
        record = self._store.get(key)
        if record is not None and self._within_reuse_window(record, representation):
            try:
                return _reground(record, representation, contract)
            except ValueError:
                pass  # Fail closed to a fresh provider extraction, never to a guess.
        fresh = self._inner.extract(representation=representation, contract=contract)
        if fresh.reused_from_extraction_id is None:
            self._store.put(
                SemanticExtractionRecord.from_candidate_set(
                    fresh,
                    content_key=key,
                    extracted_for_observed_at=representation.observed_at,
                )
            )
        return fresh

    def _within_reuse_window(
        self,
        record: SemanticExtractionRecord,
        representation: DocumentRepresentation,
    ) -> bool:
        age = representation.observed_at - record.extracted_for_observed_at
        return timedelta(0) <= age <= self._max_reuse_age


def _reground(
    record: SemanticExtractionRecord,
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
) -> SemanticCandidateSet:
    """Re-validate the original proposals against the new, identical-content surfaces."""

    rows: list[dict[str, object]] = []
    for candidate in record.candidates:
        surface = representation.text_representation(candidate.structured_index)
        span: dict[str, object] = {
            "representation_id": surface.representation_id,
            "representation_fingerprint": surface.fingerprint,
            "start": candidate.start,
            "end": candidate.end,
        }
        if candidate.structured_index is not None:
            span["structured_index"] = candidate.structured_index
        rows.append(
            {
                "semantic_target": candidate.semantic_target,
                "statement": candidate.statement,
                "excerpt": candidate.excerpt,
                "grounding_surface": candidate.grounding_surface.value,
                "span": span,
            }
        )
    regrounded = normalize_semantic_extraction_payload(
        request=build_semantic_extraction_request(representation, contract),
        provider=record.provider,
        payload={"provider_version": record.provider_version, "candidates": rows},
        representation=representation,
        contract=contract,
    )
    return replace(regrounded, reused_from_extraction_id=record.extraction_id)
