"""Relationship models with a hard Observed/Potential boundary.

Doctrine: MASTER §16.1 (observed graph), §16.2 (potential graph), §16.5
(observed evidence outranks inferred compatibility).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar

from domain.evidence.admission import (
    AdmissionDecision,
    EvidenceAdmission,
    EvidenceAdmissionError,
    EvidenceAdmissionRequired,
)
from domain.evidence.epistemics import Currentness


class RelationshipError(EvidenceAdmissionError):
    """Raised for invalid relationship state."""


class RelationshipEpistemicClass(StrEnum):
    OBSERVED = "OBSERVED"
    POTENTIAL = "POTENTIAL"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True)
class ObservedRelationship:
    """A relationship with sufficient evidence (MASTER §16.1)."""

    id: str
    source_org: str
    target_org: str
    relationship_type: str
    evidence_refs: tuple[str, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    currentness: Currentness = Currentness.UNKNOWN
    last_verified_at: datetime | None = None
    derived_features: tuple[str, ...] = ()

    epistemic_class: ClassVar[RelationshipEpistemicClass] = RelationshipEpistemicClass.OBSERVED

    @classmethod
    def create(
        cls,
        *,
        relationship_id: str,
        source_org: str,
        target_org: str,
        relationship_type: str,
        evidence_ids: tuple[str, ...],
        decision: AdmissionDecision,
        first_observed_at: datetime,
        last_observed_at: datetime,
        currentness: Currentness = Currentness.UNKNOWN,
    ) -> ObservedRelationship:
        """Create an observed relationship. Requires evidence admission."""

        EvidenceAdmission.require(decision)
        if not evidence_ids:
            raise RelationshipError("an observed relationship requires evidence")
        return cls(
            id=relationship_id,
            source_org=source_org,
            target_org=target_org,
            relationship_type=relationship_type,
            evidence_refs=evidence_ids,
            first_observed_at=first_observed_at,
            last_observed_at=last_observed_at,
            currentness=currentness,
        )


@dataclass(frozen=True)
class PotentialRelationship:
    """An economically plausible but unobserved relationship (MASTER §16.2).

    ``fit`` is an internal compatibility signal, never a user-facing truth
    percentage (MASTER §19).
    """

    id: str
    source_org: str
    target_org: str
    relationship_type: str
    rationale: str
    fit: float | None = None

    epistemic_class: ClassVar[RelationshipEpistemicClass] = RelationshipEpistemicClass.POTENTIAL


def deserialize_relationship(
    payload: Mapping[str, Any],
    *,
    decision: AdmissionDecision | None = None,
) -> ObservedRelationship | PotentialRelationship:
    """Deserialize a relationship without leaking potential into observed.

    A payload may only become an ``ObservedRelationship`` when an admitted
    ``decision`` is supplied. Otherwise it fails closed.
    """

    epistemic_class = payload.get("epistemic_class")
    if epistemic_class == RelationshipEpistemicClass.OBSERVED.value:
        if decision is None:
            raise EvidenceAdmissionRequired(
                "OBSERVED relationship cannot be materialized without evidence admission"
            )
        EvidenceAdmission.require(decision)
        return ObservedRelationship(
            id=_require_str(payload, "id"),
            source_org=_require_str(payload, "source_org"),
            target_org=_require_str(payload, "target_org"),
            relationship_type=_require_str(payload, "relationship_type"),
            evidence_refs=tuple(_require_str_list(payload, "evidence_refs")),
            first_observed_at=_require_datetime(payload, "first_observed_at"),
            last_observed_at=_require_datetime(payload, "last_observed_at"),
        )
    if epistemic_class == RelationshipEpistemicClass.POTENTIAL.value:
        return PotentialRelationship(
            id=_require_str(payload, "id"),
            source_org=_require_str(payload, "source_org"),
            target_org=_require_str(payload, "target_org"),
            relationship_type=_require_str(payload, "relationship_type"),
            rationale=str(payload.get("rationale", "")),
            fit=None,
        )
    raise RelationshipError(f"unknown epistemic_class: {epistemic_class!r}")


def _require_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RelationshipError(f"missing or invalid field: {key}")
    return value


def _require_str_list(payload: Mapping[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, (list, tuple)):
        raise RelationshipError(f"missing or invalid field: {key}")
    if not all(isinstance(item, str) for item in value):
        raise RelationshipError(f"field {key} must contain only strings")
    return [item for item in value if isinstance(item, str)]


def _require_datetime(payload: Mapping[str, Any], key: str) -> datetime:
    value = payload.get(key)
    if not isinstance(value, datetime):
        raise RelationshipError(f"missing or invalid datetime field: {key}")
    return value
