"""Source Capability Registry: resolution, adoption gate and governed discovery.

Resolution maps an abstract capability and a jurisdiction to concrete sources
and says, per source, whether it can be routed now and why not. AXENT may
*propose* sources; only this gate can adopt them, and nothing adopts itself.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from application.observation_intelligence.catalog import CATALOG_VERSION, SOURCES
from application.observation_intelligence.contracts import (
    AdoptionStatus,
    Band,
    RightsStatus,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
)


@dataclass(frozen=True, slots=True)
class SourceResolution:
    capability: SourceCapability
    jurisdiction: TaxonomyCode
    routable: tuple[SourceDescriptor, ...]
    pending: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True, slots=True)
class AdoptionEvidence:
    """What a reviewer must establish before a source becomes routable."""

    rights_reference: str | None
    adapter_contract_tested: bool
    live_probe_passed: bool
    cost_per_request_microunits: int | None
    reliability: Band
    reviewed_by: str
    reviewed_at: datetime


class AdoptionRejected(ValueError):
    def __init__(self, source_id: str, failures: tuple[str, ...]) -> None:
        super().__init__(f"{source_id} failed adoption gate: {', '.join(failures)}")
        self.failures = failures


@dataclass(frozen=True, slots=True)
class SourceDiscoveryRequest:
    """A governed research ask for AXENT: which reliable public sources answer this?"""

    capability: SourceCapability
    jurisdiction: TaxonomyCode
    classification_systems: tuple[str, ...]
    question_ids: tuple[str, ...]
    known_candidates: tuple[str, ...]
    reason: str


class SourceRegistry:
    def __init__(
        self, sources: tuple[SourceDescriptor, ...] = SOURCES, *, version: str = CATALOG_VERSION
    ) -> None:
        ids = [source.source_id for source in sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source ids must be unique in a registry version")
        self.version = version
        self._sources = {source.source_id: source for source in sources}

    @property
    def sources(self) -> tuple[SourceDescriptor, ...]:
        return tuple(self._sources.values())

    def get(self, source_id: str) -> SourceDescriptor:
        return self._sources[source_id]

    def resolve(self, capability: SourceCapability, jurisdiction: TaxonomyCode) -> SourceResolution:
        implementing = sorted(
            (
                source
                for source in self._sources.values()
                if capability in source.capabilities and source.covers(jurisdiction)
            ),
            key=lambda source: source.source_id,
        )
        return SourceResolution(
            capability=capability,
            jurisdiction=jurisdiction,
            routable=tuple(source for source in implementing if source.routable),
            pending=tuple(
                (source.source_id, source.eligibility)
                for source in implementing
                if not source.routable
            ),
        )

    def propose_candidate(self, proposal: SourceDescriptor) -> SourceDescriptor:
        """Register a discovered source as CANDIDATE, whatever the proposal claims."""

        if proposal.source_id in self._sources:
            raise ValueError("source already registered")
        candidate = replace(
            proposal,
            adoption=AdoptionStatus.CANDIDATE,
            rights=RightsStatus.UNKNOWN,
            adoption_blockers=proposal.adoption_blockers or ("ADOPTION_REVIEW_PENDING",),
        )
        self._sources[candidate.source_id] = candidate
        return candidate

    def adopt(self, source_id: str, evidence: AdoptionEvidence) -> SourceDescriptor:
        failures = adoption_gate(self._sources[source_id], evidence)
        if failures:
            raise AdoptionRejected(source_id, failures)
        adopted = replace(
            self._sources[source_id],
            adoption=AdoptionStatus.ADOPTED,
            rights=RightsStatus.REUSE_DOCUMENTED,
            cost_per_request_microunits=evidence.cost_per_request_microunits,
            reliability=evidence.reliability,
            adoption_blockers=(),
        )
        self._sources[source_id] = adopted
        return adopted


def adoption_gate(source: SourceDescriptor, evidence: AdoptionEvidence) -> tuple[str, ...]:
    failures = []
    if not evidence.rights_reference:
        failures.append("RIGHTS_NOT_DOCUMENTED")
    if not evidence.adapter_contract_tested:
        failures.append("ADAPTER_CONTRACT_UNTESTED")
    if not evidence.live_probe_passed:
        failures.append("LIVE_PROBE_MISSING")
    if evidence.cost_per_request_microunits is None:
        failures.append("COST_UNKNOWN")
    if evidence.reliability is Band.UNKNOWN:
        failures.append("RELIABILITY_UNASSESSED")
    if not evidence.reviewed_by.strip():
        failures.append("REVIEWER_REQUIRED")
    if source.authentication_required and "API_KEY_NOT_PROVISIONED" in source.adoption_blockers:
        failures.append("API_KEY_NOT_PROVISIONED")
    return tuple(failures)
