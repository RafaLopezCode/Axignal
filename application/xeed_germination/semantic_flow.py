"""Governed first semantic-retrieval flow for Xeed germination.

Retrieval only chooses where to investigate. Canonical state is produced only
from an investigator finding that survives EvidenceAdmission and FAXT creation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.semantic_retrieval import SemanticIndex
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from domain.evidence.admission import Evidence, EvidenceAdmission
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId, OrganizationId


class GerminationQueryFamily(StrEnum):
    CAPABILITY_ADJACENCY = "CAPABILITY_ADJACENCY"
    MARKET_ADJACENCY = "MARKET_ADJACENCY"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    ECONOMIC_NEIGHBORHOOD = "ECONOMIC_NEIGHBORHOOD"


@dataclass(frozen=True, slots=True)
class GerminationCandidate:
    representation_id: str
    organization_id: OrganizationId
    locale: str
    geographies: tuple[str, ...]
    currentness: Currentness
    query_family: GerminationQueryFamily

    def __post_init__(self) -> None:
        if not self.representation_id.strip() or not self.organization_id.strip():
            raise ValueError("germination candidate identities are required")
        if not self.locale.strip():
            raise ValueError("germination candidate locale is required")
        if any(not geography.strip() for geography in self.geographies):
            raise ValueError("candidate geographies cannot contain empty values")


@dataclass(frozen=True, slots=True)
class GerminationBudget:
    retrieval_k: int = 50
    max_investigations: int = 10
    locale: str | None = None
    geography: str | None = None

    def __post_init__(self) -> None:
        if self.retrieval_k < 1 or self.max_investigations < 1:
            raise ValueError("germination budgets must be positive")
        if self.max_investigations > self.retrieval_k:
            raise ValueError("investigation budget cannot exceed retrieval budget")
        if self.locale is not None and not self.locale.strip():
            raise ValueError("locale filter cannot be empty")
        if self.geography is not None and not self.geography.strip():
            raise ValueError("geography filter cannot be empty")


@dataclass(frozen=True, slots=True)
class InvestigationFinding:
    faxt_id: FaxtId
    subject_id: OrganizationId
    predicate: str
    object_or_value: str
    evidence: Evidence
    epistemic_state: EpistemicState = EpistemicState.OBSERVED
    currentness: Currentness = Currentness.UNKNOWN

    def __post_init__(self) -> None:
        if not self.faxt_id.strip() or not self.subject_id.strip():
            raise ValueError("investigation finding identities are required")
        if not self.predicate.strip():
            raise ValueError("investigation finding predicate is required")
        if not self.object_or_value.strip():
            raise ValueError("investigation finding value is required")
        if not isinstance(self.evidence, Evidence):
            raise TypeError("investigation finding requires Evidence")


@dataclass(frozen=True, slots=True)
class AdmittedGerminationFinding:
    representation_id: str
    similarity: float
    faxt: FAXT


@dataclass(frozen=True, slots=True)
class GerminationRun:
    retrieved_count: int
    eligible_count: int
    investigated_count: int
    rejected_evidence_count: int
    admitted: tuple[AdmittedGerminationFinding, ...]


class SemanticEncoder(Protocol):
    def encode(self, text: str) -> tuple[float, ...]: ...


class GerminationCandidateCatalog(Protocol):
    def get(self, representation_id: str) -> GerminationCandidate | None: ...


class CandidateInvestigator(Protocol):
    def investigate(
        self,
        *,
        seed: AuthorizedXeedOrganization,
        candidate: GerminationCandidate,
    ) -> InvestigationFinding | None: ...


class EvidenceWriter(Protocol):
    def append(self, evidence: Evidence) -> None: ...


class CanonicalFaxtWriter(Protocol):
    def write(self, faxt: FAXT) -> None: ...


class XeedSemanticGermination:
    """Retrieve -> filter -> investigate -> admit -> canonical FAXT write."""

    def __init__(
        self,
        *,
        encoder: SemanticEncoder,
        index: SemanticIndex,
        catalog: GerminationCandidateCatalog,
        investigator: CandidateInvestigator,
        evidence_writer: EvidenceWriter,
        faxt_writer: CanonicalFaxtWriter,
    ) -> None:
        self._encoder = encoder
        self._index = index
        self._catalog = catalog
        self._investigator = investigator
        self._evidence_writer = evidence_writer
        self._faxt_writer = faxt_writer

    @staticmethod
    def _probe(seed: AuthorizedXeedOrganization) -> str:
        org = seed.organization
        parts: list[str] = [org.canonical_name]
        parts.extend(org.aliases)
        parts.extend(org.capabilities)
        parts.extend(org.products)
        parts.extend(org.markets)
        parts.extend(org.locations)
        return " | ".join(part.strip() for part in parts if part.strip())

    @staticmethod
    def _eligible(
        candidate: GerminationCandidate,
        *,
        seed_org_id: OrganizationId,
        budget: GerminationBudget,
    ) -> bool:
        if candidate.organization_id == seed_org_id:
            return False
        if candidate.currentness is Currentness.STALE:
            return False
        if budget.locale is not None and candidate.locale != budget.locale:
            return False
        return budget.geography is None or budget.geography in candidate.geographies

    def run(
        self,
        seed: AuthorizedXeedOrganization,
        *,
        budget: GerminationBudget,
    ) -> GerminationRun:
        if not isinstance(seed, AuthorizedXeedOrganization):
            raise TypeError("germination requires an AuthorizedXeedOrganization")

        vector = self._encoder.encode(self._probe(seed))
        retrieved = self._index.search(vector, k=budget.retrieval_k)

        eligible: list[tuple[GerminationCandidate, float]] = []
        seen_organizations: set[OrganizationId] = set()
        for hit in retrieved:
            candidate = self._catalog.get(hit.representation_id)
            if candidate is None:
                continue
            if candidate.organization_id in seen_organizations:
                continue
            if not self._eligible(candidate, seed_org_id=seed.organization.id, budget=budget):
                continue
            seen_organizations.add(candidate.organization_id)
            eligible.append((candidate, hit.similarity))

        admitted: list[AdmittedGerminationFinding] = []
        rejected_evidence_count = 0
        investigated_count = 0
        for candidate, similarity in eligible[: budget.max_investigations]:
            investigated_count += 1
            finding = self._investigator.investigate(seed=seed, candidate=candidate)
            if finding is None:
                continue
            if finding.subject_id != candidate.organization_id:
                raise ValueError("investigation finding subject does not match retrieved candidate")
            decision = EvidenceAdmission.admit(finding.evidence)
            if not decision.is_canonical:
                rejected_evidence_count += 1
                continue
            faxt = FAXT.create(
                faxt_id=finding.faxt_id,
                subject_id=finding.subject_id,
                predicate=finding.predicate,
                object_or_value=finding.object_or_value,
                evidence=finding.evidence,
                decision=decision,
                epistemic_state=finding.epistemic_state,
                currentness=finding.currentness,
            )
            self._evidence_writer.append(finding.evidence)
            self._faxt_writer.write(faxt)
            admitted.append(
                AdmittedGerminationFinding(
                    representation_id=candidate.representation_id,
                    similarity=similarity,
                    faxt=faxt,
                )
            )

        return GerminationRun(
            retrieved_count=len(retrieved),
            eligible_count=len(eligible),
            investigated_count=investigated_count,
            rejected_evidence_count=rejected_evidence_count,
            admitted=tuple(admitted),
        )
