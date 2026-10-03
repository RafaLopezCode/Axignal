"""Economic relationships with hard canonical materialization boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar

from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    Evidence,
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


@dataclass(frozen=True, init=False)
class ObservedRelationship:
    """A relationship materialized only from exact admitted evidence."""

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

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError(
            "ObservedRelationship can only be materialized through create/verified replay"
        )

    @classmethod
    def _materialize(
        cls,
        *,
        relationship_id: str,
        source_org: str,
        target_org: str,
        relationship_type: str,
        evidence_refs: tuple[str, ...],
        first_observed_at: datetime,
        last_observed_at: datetime,
        currentness: Currentness,
    ) -> ObservedRelationship:
        value = object.__new__(cls)
        object.__setattr__(value, "id", relationship_id)
        object.__setattr__(value, "source_org", source_org)
        object.__setattr__(value, "target_org", target_org)
        object.__setattr__(value, "relationship_type", relationship_type)
        object.__setattr__(value, "evidence_refs", evidence_refs)
        object.__setattr__(value, "first_observed_at", first_observed_at)
        object.__setattr__(value, "last_observed_at", last_observed_at)
        object.__setattr__(value, "currentness", currentness)
        object.__setattr__(value, "last_verified_at", None)
        object.__setattr__(value, "derived_features", ())
        return value

    @classmethod
    def create(
        cls,
        *,
        relationship_id: str,
        source_org: str,
        target_org: str,
        relationship_type: str,
        evidence: Evidence,
        decision: AdmissionDecision,
        first_observed_at: datetime,
        last_observed_at: datetime,
        claim_proposition: str | None = None,
        currentness: Currentness = Currentness.UNKNOWN,
    ) -> ObservedRelationship:
        """Create one exact observed relationship from admitted evidence."""

        for value, name in (
            (relationship_id, "relationship id"),
            (source_org, "source organization"),
            (target_org, "target organization"),
            (relationship_type, "relationship type"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise RelationshipError(f"an observed relationship requires {name}")
        if source_org == target_org:
            raise RelationshipError("an observed relationship requires distinct endpoints")
        if not isinstance(first_observed_at, datetime) or not isinstance(
            last_observed_at, datetime
        ):
            raise RelationshipError("observed relationship times must be datetimes")
        if first_observed_at > last_observed_at:
            raise RelationshipError("observed relationship interval is invalid")
        if not first_observed_at <= evidence.observed_at <= last_observed_at:
            raise RelationshipError(
                "admitted evidence observed_at must fall inside relationship interval"
            )

        proposition = (
            claim_proposition if claim_proposition is not None else evidence.extracted_claim
        )
        request = AdmissionRequest(
            evidence=evidence,
            subject_id=source_org,
            predicate=relationship_type,
            object_or_value=target_org,
            claim_proposition=proposition,
        )
        EvidenceAdmission.require_claim(decision, request)

        return cls._materialize(
            relationship_id=relationship_id,
            source_org=source_org,
            target_org=target_org,
            relationship_type=relationship_type,
            evidence_refs=(evidence.id,),
            first_observed_at=first_observed_at,
            last_observed_at=last_observed_at,
            currentness=currentness,
        )


@dataclass(frozen=True)
class PotentialRelationship:
    """An economically plausible but unobserved relationship."""

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
    evidence: Evidence | None = None,
    decision: AdmissionDecision | None = None,
) -> ObservedRelationship | PotentialRelationship:
    """Verified replay for observed relationships; potential remains non-canonical."""

    epistemic_class = payload.get("epistemic_class")
    if epistemic_class == RelationshipEpistemicClass.OBSERVED.value:
        if evidence is None or decision is None:
            raise EvidenceAdmissionRequired(
                "OBSERVED relationship replay requires exact evidence and admission"
            )
        evidence_refs = tuple(_require_str_list(payload, "evidence_refs"))
        if evidence_refs != (evidence.id,):
            raise RelationshipError(
                "OBSERVED relationship evidence refs must exactly match admitted evidence"
            )
        return ObservedRelationship.create(
            relationship_id=_require_str(payload, "id"),
            source_org=_require_str(payload, "source_org"),
            target_org=_require_str(payload, "target_org"),
            relationship_type=_require_str(payload, "relationship_type"),
            evidence=evidence,
            decision=decision,
            first_observed_at=_require_datetime(payload, "first_observed_at"),
            last_observed_at=_require_datetime(payload, "last_observed_at"),
            currentness=_optional_currentness(payload),
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
    if not isinstance(value, (list, tuple)) or not value:
        raise RelationshipError(f"missing or invalid field: {key}")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise RelationshipError(f"field {key} must contain non-empty strings")
    return list(value)


def _require_datetime(payload: Mapping[str, Any], key: str) -> datetime:
    value = payload.get(key)
    if not isinstance(value, datetime):
        raise RelationshipError(f"missing or invalid datetime field: {key}")
    return value


def _optional_currentness(payload: Mapping[str, Any]) -> Currentness:
    value = payload.get("currentness")
    if value is None:
        return Currentness.UNKNOWN
    try:
        return Currentness(str(value))
    except ValueError as exc:
        raise RelationshipError("invalid currentness") from exc
