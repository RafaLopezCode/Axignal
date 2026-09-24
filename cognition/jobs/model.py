"""Cognitive job and structured-result models.

A ``StructuredResult`` is model output. It is NOT canonical truth and can never
become canonical without evidence admission in the domain layer.

Doctrine: MASTER §12 (scheduler/batch/cognitive provider), §14 (models are not
canonical authority), §15.1 (CLAIM != WRITE).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class JobKind(StrEnum):
    """Kinds of cognitive work AXENT schedules (MASTER §12, §14)."""

    ENTITY_RESOLUTION = "ENTITY_RESOLUTION"
    RELATIONSHIP_VERIFICATION = "RELATIONSHIP_VERIFICATION"
    CAPABILITY_DISCOVERY = "CAPABILITY_DISCOVERY"
    CURRENTNESS = "CURRENTNESS"
    CORPORATE_STRUCTURE = "CORPORATE_STRUCTURE"
    GAP_ENRICHMENT = "GAP_ENRICHMENT"


@dataclass(frozen=True)
class CognitiveJob:
    """A unit of investigation handed to a cognitive provider."""

    id: str
    kind: JobKind
    instruction: str
    context: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredResult:
    """Provider output. Never canonical truth by itself."""

    job_id: str
    provider: str
    payload: Mapping[str, object] = field(default_factory=dict)

    @property
    def is_canonical_truth(self) -> bool:
        """Always False. Canonical state requires domain evidence admission."""

        return False
