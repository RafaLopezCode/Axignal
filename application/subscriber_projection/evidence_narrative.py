"""Product-grade evidence narrative for subscriber-safe Xignal explanation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.explanation import BasisContribution, ExplainableBasis
from application.economic_discovery.observation_memory import GovernedObservation, ObservationMemory
from application.subscriber_projection.narrative_verification import (
    NarrativeGraphKind,
    NarrativeGraphResolver,
    NarrativeMaterialContribution,
    NarrativeMaterialResolver,
)
from application.subscriber_projection.xignal import ExplainableXignalProjection
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from domain.faxt.model import FAXT


class ArtifactIntegrityPort(Protocol):
    def verify(self, reference: str) -> bool: ...


class EvidenceNarrativeKind(StrEnum):
    XIGNAL = "XIGNAL"
    CLAIM = "CLAIM"
    RELATIONSHIP = "RELATIONSHIP"
    PATHX = "PATHX"
    OBSERVATION = "OBSERVATION"
    SOURCE = "SOURCE"
    CONTRADICTION = "CONTRADICTION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EvidenceNarrativeStep:
    step_id: str
    kind: EvidenceNarrativeKind
    label: str
    parent_step_id: str | None
    source_ref: str | None = None
    observed_at: datetime | None = None
    currentness: str | None = None
    artifact_verified: bool | None = None

    def __post_init__(self) -> None:
        if not self.step_id.strip() or not self.label.strip():
            raise ValueError("evidence narrative step identity is required")
        if self.observed_at is not None and self.observed_at.tzinfo is None:
            raise ValueError("evidence narrative time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class EvidenceNarrative:
    xignal_id: str
    focus_step_id: str
    return_focus_step_id: str
    steps: tuple[EvidenceNarrativeStep, ...]

    def __post_init__(self) -> None:
        if not self.xignal_id.strip() or not self.focus_step_id.strip():
            raise ValueError("evidence narrative identity is required")
        if not self.return_focus_step_id.strip():
            raise ValueError("evidence narrative return focus is required")
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence narrative step ids must be unique")
        if self.focus_step_id not in ids or self.return_focus_step_id not in ids:
            raise ValueError("evidence narrative focus refs must resolve inside the narrative")


def _observation_by_id(
    *,
    memory: ObservationMemory,
    subject_id: str,
    observation_id: str,
) -> GovernedObservation:
    matches = [
        item
        for item in memory.for_subject(subject_id)
        if item.record.observation_id == observation_id
    ]
    if len(matches) != 1:
        raise ValueError("evidence narrative observation reference does not resolve uniquely")
    return matches[0]


def build_evidence_narrative(
    *,
    organization_context: AuthorizedXeedOrganization,
    projection: ExplainableXignalProjection,
    basis: ExplainableBasis,
    observation_memory: ObservationMemory,
    artifact_integrity: ArtifactIntegrityPort,
    material_resolver: NarrativeMaterialResolver,
    graph_resolver: NarrativeGraphResolver | None = None,
    canonical_faxts: tuple[FAXT, ...] = (),
) -> EvidenceNarrative:
    """Resolve Xignal lineage to stored observations and return a UI-safe causal narrative."""

    subject_id = organization_context.organization.id
    xeed_id = organization_context.authorized_xeed.xeed.id
    xignal = projection.xignal
    if xignal.subject_id != subject_id or xignal.xeed_id != xeed_id:
        raise ValueError("evidence narrative cannot cross authorized Xeed/subject context")
    if basis.basis_id != xignal.basis_ref or basis.subject_id != subject_id:
        raise ValueError("evidence narrative basis does not match Xignal")
    if projection.trail.basis_id != basis.basis_id:
        raise ValueError("evidence narrative trail/basis mismatch")

    root_id = f"narrative:xignal:{xignal.xignal_id}"
    steps: list[EvidenceNarrativeStep] = [
        EvidenceNarrativeStep(
            step_id=root_id,
            kind=EvidenceNarrativeKind.XIGNAL,
            label=xignal.why_attention,
            parent_step_id=None,
            currentness=xignal.currentness.value,
        )
    ]

    faxt_by_id = {str(item.id): item for item in canonical_faxts}
    for ref in xignal.canonical_support_refs:
        faxt = faxt_by_id.get(str(ref))
        if faxt is None or faxt.subject_id != subject_id:
            raise ValueError("canonical Xignal support does not resolve in authorized subject")
        claim_id = f"narrative:claim:{faxt.id}"
        steps.append(
            EvidenceNarrativeStep(
                step_id=claim_id,
                kind=EvidenceNarrativeKind.CLAIM,
                label=f"{faxt.predicate} · {faxt.object_or_value}",
                parent_step_id=root_id,
                observed_at=faxt.observed_at,
                currentness=faxt.currentness.value,
            )
        )

    for graph_ref_id, graph_kind, narrative_kind in (
        (
            xignal.relationship_ref,
            NarrativeGraphKind.RELATIONSHIP,
            EvidenceNarrativeKind.RELATIONSHIP,
        ),
        (xignal.pathx_ref, NarrativeGraphKind.PATHX, EvidenceNarrativeKind.PATHX),
    ):
        if graph_ref_id is None:
            continue
        if graph_resolver is None:
            raise ValueError("evidence narrative graph reference requires governed resolver")
        graph_ref = graph_resolver.resolve(
            ref=graph_ref_id,
            kind=graph_kind,
            authorized_subject_id=subject_id,
        )
        if graph_ref is None:
            raise ValueError("evidence narrative graph reference is unresolved or unauthorized")
        steps.append(
            EvidenceNarrativeStep(
                step_id=f"narrative:{graph_kind.value.lower()}:{graph_ref_id}",
                kind=narrative_kind,
                label=graph_ref.label,
                parent_step_id=root_id,
            )
        )

    parent_for_observation = next(
        (step.step_id for step in steps if step.kind is EvidenceNarrativeKind.CLAIM),
        root_id,
    )
    contribution_order = {
        BasisContribution.SUPPORTS: 0,
        BasisContribution.CONTRADICTS: 1,
        BasisContribution.CONTEXT: 2,
    }
    considered = material_resolver.considered(
        subject_id=subject_id,
        candidate_id=basis.candidate_id,
    )
    material_contradictions = {
        item.observation_id
        for item in considered
        if item.contribution is NarrativeMaterialContribution.CONTRADICTS
    }
    basis_contradictions = {
        item.observation_id
        for item in basis.data
        if item.contribution is BasisContribution.CONTRADICTS
    }
    if not material_contradictions.issubset(basis_contradictions):
        raise ValueError("evidence narrative basis omits material contradiction")

    for datum in sorted(
        basis.data,
        key=lambda item: (
            contribution_order[item.contribution],
            item.observed_at,
            item.datum_id,
        ),
    ):
        observation = _observation_by_id(
            memory=observation_memory,
            subject_id=subject_id,
            observation_id=datum.observation_id,
        )
        material = material_resolver.resolve(datum.observation_id)
        if material is None:
            raise ValueError("basis observation has no exact governed narrative material")
        expected_contribution = NarrativeMaterialContribution(datum.contribution.value)
        if material.subject_id != subject_id or material.candidate_id != basis.candidate_id:
            raise ValueError("basis narrative material crosses subject/candidate boundary")
        if (
            observation.record.source_ref != datum.source_ref
            or material.source_ref != datum.source_ref
        ):
            raise ValueError("basis source does not match stored observation/material")
        if (
            observation.record.source_type != datum.source_type
            or material.source_type != datum.source_type
        ):
            raise ValueError("basis source type does not match stored observation/material")
        if (
            observation.record.observed_at != datum.observed_at
            or material.observed_at != datum.observed_at
        ):
            raise ValueError("basis observed time does not match stored observation/material")
        if material.excerpt_or_summary != datum.excerpt_or_summary:
            raise ValueError("basis summary does not match exact governed material")
        if material.contribution is not expected_contribution:
            raise ValueError("basis contribution does not match considered evidence ledger")
        if datum.representation_fingerprint != material.representation_fingerprint:
            raise ValueError("basis representation fingerprint does not match governed material")
        if datum.extraction_fingerprint != material.extraction_fingerprint:
            raise ValueError("basis extraction fingerprint does not match governed material")
        verified = False
        if observation.raw_artifact_ref is not None:
            verified = artifact_integrity.verify(observation.raw_artifact_ref)
            if not verified:
                raise ValueError("stored observation artifact failed integrity verification")
        observation_step_id = f"narrative:observation:{datum.datum_id}"
        steps.append(
            EvidenceNarrativeStep(
                step_id=observation_step_id,
                kind=(
                    EvidenceNarrativeKind.CONTRADICTION
                    if datum.contribution is BasisContribution.CONTRADICTS
                    else EvidenceNarrativeKind.OBSERVATION
                ),
                label=datum.excerpt_or_summary,
                parent_step_id=parent_for_observation,
                observed_at=observation.record.observed_at,
                artifact_verified=verified,
            )
        )
        steps.append(
            EvidenceNarrativeStep(
                step_id=f"narrative:source:{datum.datum_id}",
                kind=EvidenceNarrativeKind.SOURCE,
                label=datum.source_type,
                parent_step_id=observation_step_id,
                source_ref=datum.source_ref,
                observed_at=observation.record.observed_at,
                artifact_verified=verified,
            )
        )

    for index, unknown in enumerate(xignal.unknowns):
        steps.append(
            EvidenceNarrativeStep(
                step_id=f"narrative:unknown:{index}",
                kind=EvidenceNarrativeKind.UNKNOWN,
                label=unknown,
                parent_step_id=root_id,
            )
        )

    return EvidenceNarrative(
        xignal_id=xignal.xignal_id,
        focus_step_id=root_id,
        return_focus_step_id=root_id,
        steps=tuple(steps),
    )
