"""Transport admitted observation metadata to the accepted cognitive renderer.

Callers supply observations already selected by their authorized read path.
This adapter does not acquire evidence, infer a family, or invent measurements.
"""

from __future__ import annotations

from datetime import datetime

from application.economic_discovery.observation_memory import GovernedObservation
from domain.evidence.epistemics import Currentness


def observation_cognition(
    observations: tuple[tuple[GovernedObservation, Currentness], ...],
    *,
    as_of: datetime,
    signals: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    """Retain provenance and the explicit time at which currentness was evaluated."""
    if as_of.tzinfo is None:
        raise ValueError("cognitive projection requires a timezone-aware cut")
    allowed_families = {
        "presence",
        "reputation",
        "value",
        "markets",
        "relationships",
        "demand",
        "activity",
        "economics",
        "context",
        "organization",
    }
    if any(family not in allowed_families or not ref.strip() for ref, family in signals):
        raise ValueError("cognitive signal requires an explicit accepted family")
    sources: list[dict[str, object]] = []
    for observation, currentness in observations:
        record = observation.record
        if record.observed_at > as_of:
            continue
        provenance = observation.raw_artifact_ref or observation.reuse_authority.provenance_ref
        if not provenance:
            # Raw text alone has no navigable immutable provenance reference.
            continue
        sources.append(
            {
                "id": record.observation_id,
                "title": record.source_ref,
                "observedAt": record.observed_at.isoformat(),
                "currentness": currentness.value,
                "currentnessEvaluatedAt": as_of.isoformat(),
                "instrument": "UNKNOWN — acquisition instrument is not recorded in this read contract",
                "limitation": "One authorized source observation; coverage beyond this document remains unknown.",
                "sourceRef": record.source_ref,
                "provenanceRef": provenance,
            }
        )
    return {
        "asOf": as_of.isoformat(),
        "sources": sources,
        "signals": [{"id": ref, "familyId": family} for ref, family in signals],
        "opportunities": [],
    }
