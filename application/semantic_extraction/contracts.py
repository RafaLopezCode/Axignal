"""Provider-neutral contracts for grounded semantic claim proposals."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_TARGET = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("semantic extraction identity and values must be non-empty")


def fingerprint(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class GroundingSurface(StrEnum):
    VISIBLE_TEXT = "VISIBLE_TEXT"
    STRUCTURED_DATA = "STRUCTURED_DATA"


@dataclass(frozen=True, slots=True)
class SemanticTarget:
    target_id: str
    meaning: str

    def __post_init__(self) -> None:
        _required(self.target_id, self.meaning)
        if not _TARGET.fullmatch(self.target_id):
            raise ValueError("semantic target id must be a stable lowercase identifier")


@dataclass(frozen=True, slots=True)
class SemanticExtractionContract:
    contract_id: str
    version: str
    targets: tuple[SemanticTarget, ...]
    max_candidates: int = 24

    def __post_init__(self) -> None:
        _required(self.contract_id, self.version)
        if not self.targets:
            raise ValueError("semantic extraction contract requires at least one target")
        ids = [target.target_id for target in self.targets]
        if len(ids) != len(set(ids)):
            raise ValueError("semantic extraction target ids must be unique")
        if self.max_candidates < 1 or self.max_candidates > 100:
            raise ValueError("semantic extraction candidate budget must be between 1 and 100")

    @property
    def target_ids(self) -> frozenset[str]:
        return frozenset(target.target_id for target in self.targets)

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "contract_id": self.contract_id,
                "version": self.version,
                "targets": [(target.target_id, target.meaning) for target in self.targets],
                "max_candidates": self.max_candidates,
            }
        )


@dataclass(frozen=True, slots=True)
class EconomicClaimCandidate:
    """Grounded model proposal. It is neither evidence nor canonical truth."""

    candidate_id: str
    subject_id: str
    observation_id: str
    representation_id: str
    semantic_target: str
    statement: str
    excerpt: str
    grounding_surface: GroundingSurface
    source_ref: str
    source_type: str
    observed_at: datetime
    extractor: str
    extractor_version: str
    contract_fingerprint: str
    result_fingerprint: str

    def __post_init__(self) -> None:
        _required(
            self.candidate_id,
            self.subject_id,
            self.observation_id,
            self.representation_id,
            self.semantic_target,
            self.statement,
            self.excerpt,
            self.source_ref,
            self.source_type,
            self.extractor,
            self.extractor_version,
            self.contract_fingerprint,
            self.result_fingerprint,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("semantic candidate observation time must be timezone-aware")

    @property
    def is_canonical_truth(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SemanticCandidateSet:
    extraction_id: str
    subject_id: str
    representation_id: str
    contract_fingerprint: str
    provider: str
    provider_version: str
    result_fingerprint: str
    candidates: tuple[EconomicClaimCandidate, ...]

    def __post_init__(self) -> None:
        _required(
            self.extraction_id,
            self.subject_id,
            self.representation_id,
            self.contract_fingerprint,
            self.provider,
            self.provider_version,
            self.result_fingerprint,
        )
        ids = [candidate.candidate_id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("semantic candidate ids must be unique")
        if any(candidate.subject_id != self.subject_id for candidate in self.candidates):
            raise ValueError("semantic candidate set cannot mix subjects")
        if any(
            candidate.representation_id != self.representation_id for candidate in self.candidates
        ):
            raise ValueError("semantic candidate set cannot mix representations")

    @property
    def is_canonical_truth(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SemanticExtractionRequest:
    request_id: str
    representation_id: str
    contract_fingerprint: str
    instruction: str
    context: Mapping[str, object]

    def __post_init__(self) -> None:
        _required(
            self.request_id,
            self.representation_id,
            self.contract_fingerprint,
            self.instruction,
        )
