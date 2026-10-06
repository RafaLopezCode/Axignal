"""Provider-neutral findings returned by source adapters.

A record is an immutable assertion about what a source published at retrieval
time. A named buyer or winner is a source claim, not an admitted relationship.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode


@dataclass(frozen=True, slots=True)
class ProcurementRecord:
    record_id: str
    source_id: str
    kind: SourceCapability
    title: str
    buyer_name: str | None
    places: tuple[TaxonomyCode, ...]
    demand_codes: tuple[TaxonomyCode, ...]
    published_at: datetime
    source_url: str
    deadline: str | None = None
    winners: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.record_id.strip() or not self.source_id.strip() or not self.title.strip():
            raise ValueError("procurement record identity and title are required")
        if self.kind not in {
            SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
            SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
        }:
            raise ValueError("procurement record kind must be a notice or an award")
        if self.published_at.tzinfo is None:
            raise ValueError("procurement publication time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class SourceFindings:
    source_id: str
    retrieved_at: datetime
    requests: int
    amount_microunits: int | None
    latency_ms: int | None
    records: tuple[ProcurementRecord, ...] = ()
    total_available: int | None = None
    failure: str | None = None

    def __post_init__(self) -> None:
        if self.requests < 0:
            raise ValueError("findings request count cannot be negative")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("findings retrieval time must be timezone-aware")
