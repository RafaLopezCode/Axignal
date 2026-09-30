"""Product-grade evidence narrative for subscriber-safe Xignal explanation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.explanation import BasisContribution, ExplainableBasis
from application.economic_discovery.observation_memory import GovernedObservation, ObservationMemory
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

    if xignal.relationship_ref is not None:
        steps.append(
            EvidenceNarrativeStep(
                step_id=f"narrative:relationship:{xignal.relationship_ref}",
                kind=EvidenceNarrativeKind.RELATIONSHIP,
                label="Relevant economic relationship",
                parent_step_id=root_id,
            )
        )
    if xignal.pathx_ref is not None:
        steps.append(
            EvidenceNarrativeStep(
                step_id=f"narrative:pathx:{xignal.pathx_ref}",
                kind=EvidenceNarrativeKind.PATHX,
                label="Relevant economic path",
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
        if observation.record.source_ref != datum.source_ref:
            raise ValueError("basis source does not match stored observation")
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
