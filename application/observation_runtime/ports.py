"""Ports and operational records of the autonomous observation runtime.

Everything persisted through these ports is operational observation state:
schedule, frontier, spend, yield and fingerprints of what was looked at. None
of it is AXIGLAND truth; canonical writes stay behind EvidenceAdmission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.observation_intelligence.contracts import (
    MarketScope,
    SourceDescriptor,
    TaxonomyCode,
)
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.loop import OpportunityCandidate
from application.observation_runtime.budget import BudgetUsage
from application.observation_runtime.families import LeadKind, ObservationFamily
from application.observation_runtime.frontier import ResearchLead
from domain.evidence.epistemics import Currentness


@dataclass(frozen=True, slots=True)
class XeedAttention:
    """Where attention is directed for one Xeed. Attention is not observation."""

    xeed_id: str
    organization_name: str
    website: str | None
    markets: tuple[MarketScope, ...]

    def __post_init__(self) -> None:
        if not self.xeed_id.strip() or not self.organization_name.strip():
            raise ValueError("Xeed attention requires an id and a name")


@dataclass(frozen=True, slots=True)
class AcquiredEvidence:
    """A fingerprint of something a source returned; the evidence itself lives elsewhere."""

    key: str
    fingerprint: str
    observed_at: datetime
    provenance_ref: str

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.fingerprint.strip() or not self.provenance_ref.strip():
            raise ValueError("acquired evidence needs key, fingerprint and provenance")
        if self.observed_at.tzinfo is None:
            raise ValueError("acquired evidence time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class LeadHint:
    """What a finding suggests looking at next. The family policy decides if it may."""

    kind: LeadKind
    target: str
    geography: TaxonomyCode | None
    evidence_keys: tuple[str, ...]
    reason: str
    #: A finding may open a question in another family (awards -> regional demand);
    #: that family's own policy must allow it. None keeps the lead's family.
    family: ObservationFamily | None = None
    #: Machine-readable context the follow-up needs (e.g. revealed classification codes).
    detail: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.target.strip() or not self.evidence_keys or not self.reason.strip():
            raise ValueError("a lead hint needs a target, its evidence and a reason")


@dataclass(frozen=True, slots=True)
class AcquisitionRequest:
    lead: ResearchLead
    source: SourceDescriptor
    attention: XeedAttention
    as_of: datetime
    #: Requests this acquisition may spend; adapters must not exceed it.
    max_requests: int
    #: Evidence keys already seen for this Xeed (duplicates are not new evidence).
    known_evidence: frozenset[str]


@dataclass(frozen=True, slots=True)
class Acquisition:
    requests: int
    paid_cost_microunits: int
    latency_ms: int | None
    failure: str | None = None
    #: Not a source failure: the question cannot be asked now (no context, no policy).
    blocked: str | None = None
    evidence: tuple[AcquiredEvidence, ...] = ()
    candidates: tuple[OpportunityCandidate, ...] = ()
    hints: tuple[LeadHint, ...] = ()

    def __post_init__(self) -> None:
        if self.requests < 0 or self.paid_cost_microunits < 0:
            raise ValueError("acquisition spend cannot be negative")


class AcquisitionPort(Protocol):
    """One concrete source behind one abstract capability."""

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        """Same key ⇒ same fetch; leads of different families share one acquisition."""

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        """Upper bound reserved from the budget before the acquisition starts."""

    def acquire(self, request: AcquisitionRequest) -> Acquisition: ...


@dataclass(frozen=True, slots=True)
class EvidenceState:
    """Operational index of what one family relies on, and how current it is."""

    xeed_id: str
    family: ObservationFamily
    key: str
    fingerprint: str
    source_id: str
    provenance_ref: str
    lead_id: str
    first_observed_at: datetime
    #: Last time a real acquisition returned it; aging never moves this.
    observed_at: datetime
    changed_at: datetime
    currentness: Currentness


@dataclass(frozen=True, slots=True)
class StoredCandidate:
    """A POTENTIAL opportunity as derived; persisted for reading, never as truth."""

    candidate: OpportunityCandidate
    lead_id: str
    first_seen_at: datetime


class RecomputeTrigger(StrEnum):
    #: New or changed evidence: everything that depends on it.
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    #: Same content, different currentness: only freshness-dependent dimensions.
    CURRENTNESS_TRANSITION = "CURRENTNESS_TRANSITION"


@dataclass(frozen=True, slots=True)
class RecomputationRequest:
    xeed_id: str
    family: ObservationFamily
    trigger: RecomputeTrigger
    evidence_keys: tuple[str, ...]
    as_of: datetime


@dataclass(frozen=True, slots=True)
class PendingRecompute:
    """Downstream work owed for one Xeed x family; persisted until it has run."""

    xeed_id: str
    family: ObservationFamily
    trigger: RecomputeTrigger
    evidence_keys: tuple[str, ...]


class RecomputationPort(Protocol):
    """Downstream Brain work. It may use models; the scheduler that calls it never does."""

    def recompute(self, request: RecomputationRequest) -> None: ...


@dataclass(frozen=True, slots=True)
class TickClaim:
    day: str
    token: str
    resumed: bool


class LeaseLost(RuntimeError):
    """Another worker owns the day; this one must stop without writing."""


class ObservationRuntimeStore(Protocol):
    def claim_tick(self, day: str, *, now: datetime, lease_seconds: int) -> TickClaim | None:
        """Own the day's tick, or resume one whose lease expired; None if done or held."""

    def tick_report(self, day: str) -> dict[str, object] | None: ...

    def complete_tick(
        self, claim: TickClaim, *, completed_at: datetime, report: dict[str, object]
    ) -> None: ...

    def leads(self) -> tuple[ResearchLead, ...]: ...

    def evidence(self) -> tuple[EvidenceState, ...]: ...

    def candidates(self, xeed_id: str) -> tuple[StoredCandidate, ...]: ...

    def budget_usage(self, day: str) -> BudgetUsage: ...

    def learning(self) -> OperationalLearning: ...

    def receipts(self, day: str) -> dict[str, Acquisition]:
        """Acquisitions already made on this day, by acquisition key (survive a crash)."""

    def commit(
        self,
        claim: TickClaim,
        *,
        now: datetime,
        leads: tuple[ResearchLead, ...],
        evidence: tuple[EvidenceState, ...],
        candidates: tuple[StoredCandidate, ...],
        usage: BudgetUsage,
        learning: OperationalLearning,
        recompute: tuple[PendingRecompute, ...],
        receipts: tuple[tuple[str, Acquisition], ...] = (),
    ) -> None:
        """Persist one step atomically, only while the claim's lease is still owned."""

    def pending_recompute(self) -> tuple[PendingRecompute, ...]: ...

    def clear_recompute(self, claim: TickClaim, *, xeed_id: str, family: ObservationFamily) -> None:
        """Forget owed downstream work once it ran (fenced like commit)."""
