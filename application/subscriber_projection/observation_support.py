"""Governed direct-observation support for subscriber-visible OBSERVED Xignals.

Direct observations prove only the phenomenon that the registered instrument
measured. They do not establish canonical business truth.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from domain.evidence.epistemics import Currentness
from domain.xignal import XignalKind


class ObservationPhenomenon(StrEnum):
    PUBLIC_REPRESENTATION = "PUBLIC_REPRESENTATION"


@dataclass(frozen=True, slots=True)
class ObservationSupport:
    observation_id: str
    subject_id: str
    phenomenon: ObservationPhenomenon
    instrument_ref: str
    instrument_version: str
    scope_ref: str
    provenance_ref: str
    source_ref: str
    observed_at: datetime
    currentness: Currentness

    def __post_init__(self) -> None:
        for value, name in (
            (self.observation_id, "observation_id"),
            (self.subject_id, "subject_id"),
            (self.instrument_ref, "instrument_ref"),
            (self.instrument_version, "instrument_version"),
            (self.scope_ref, "scope_ref"),
            (self.provenance_ref, "provenance_ref"),
            (self.source_ref, "source_ref"),
        ):
            if not value.strip():
                raise ValueError(f"observation support requires {name}")
        if self.observed_at.tzinfo is None:
            raise ValueError("observation support time must be timezone-aware")


class GovernedObservationSupportResolver(Protocol):
    def resolve(self, observation_id: str) -> ObservationSupport | None:
        """Return governed support or None when the observation is not eligible."""


class ObservationSupportMapResolver:
    """Small adapter over already-governed observation support values."""

    def __init__(self, supports: Mapping[str, ObservationSupport]) -> None:
        self._supports = dict(supports)

    def resolve(self, observation_id: str) -> ObservationSupport | None:
        return self._supports.get(observation_id)


_ALLOWED_DIRECT_OBSERVATION_SUPPORT: dict[XignalKind, frozenset[ObservationPhenomenon]] = {
    XignalKind.REPRESENTATION: frozenset({ObservationPhenomenon.PUBLIC_REPRESENTATION}),
}


def validate_direct_observation_support(
    *,
    kind: XignalKind,
    subject_id: str,
    support: ObservationSupport,
) -> None:
    allowed = _ALLOWED_DIRECT_OBSERVATION_SUPPORT.get(kind)
    if not allowed or support.phenomenon not in allowed:
        raise ValueError(
            "OBSERVED business Xignal requires canonical support; direct observation "
            "is not authoritative for this Xignal kind"
        )
    if support.subject_id != subject_id:
        raise ValueError("observation support cannot cross subjects")
    if support.currentness is not Currentness.CURRENT:
        raise ValueError("OBSERVED direct observation support must be CURRENT")
