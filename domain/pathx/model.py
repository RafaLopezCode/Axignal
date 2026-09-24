"""PATHX model.

A PATHX is a sequence of explainable edges. It is a projection over canonical
state and must not be used to write canonical truth.

Doctrine: MASTER §4.7, §17.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PathxError(Exception):
    """Raised for invalid PATHX construction."""


class PathxType(StrEnum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    CORPORATE = "CORPORATE"
    ECONOMIC = "ECONOMIC"
    POTENTIAL = "POTENTIAL"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True)
class PathxEdge:
    """One explainable hop in a PATHX."""

    source_org: str
    relationship_type: str
    target_org: str


@dataclass(frozen=True)
class PATHX:
    """An explainable economic path (MASTER §4.7, §17)."""

    id: str
    origin: str
    destination: str
    edges: tuple[PathxEdge, ...]
    path_type: PathxType
    computed_at: datetime
    explanation_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.edges:
            raise PathxError("PATHX requires at least one edge")
        if self.edges[0].source_org != self.origin:
            raise PathxError("first edge must start at origin")
        if self.edges[-1].target_org != self.destination:
            raise PathxError("last edge must end at destination")
        for previous, following in zip(self.edges, self.edges[1:], strict=False):
            if previous.target_org != following.source_org:
                raise PathxError("PATHX edges must be contiguous")

    @property
    def is_direct(self) -> bool:
        return len(self.edges) == 1
