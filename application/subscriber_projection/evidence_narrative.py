"""Product-grade evidence narrative for subscriber-safe Xignal explanation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.explanation import BasisContribution, ExplainableBasis
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_projection.narrative_access import (
    NarrativeAccessContext,
    NarrativeEvidenceScope,
    NarrativeObservationMemory,
    authorize_narrative_observation,
)
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
    evidence_scope: NarrativeEvidenceScope | None = None

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


def _authorized_scope_by_id(
    *,
    memory: NarrativeObservationMemory,
    subject_id: str,
    observation_id: str,
    access_context: NarrativeAccessContext,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
) -> tuple[NarrativeEvidenceScope, str]:
    metadata = memory.access_metadata(subject_id, observation_id)
    if metadata is None:
        raise ValueError("evidence narrative observation reference does not resolve")
    authorization = authorize_narrative_observation(
        metadata,
        context=access_context,
        policy=reuse_policy,
        temporal_policy=temporal_policy,
    )
    return authorization.evidence_scope, authorization.decision.effective_currentness.value


def build_evidence_narrative(
    *,
    organization_context: AuthorizedXeedOrganization,
    projection: ExplainableXignalProjection,
    basis: ExplainableBasis,
    observation_memory: NarrativeObservationMemory,
    artifact_integrity: ArtifactIntegrityPort,
    material_resolver: NarrativeMaterialResolver,
    access_context: NarrativeAccessContext,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
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

    if (
        access_context.subject_id != subject_id
        or access_context.xeed_id != xeed_id
        or access_context.tenant_id != organization_context.authorized_xeed.xeed.tenant_id
    ):
        raise ValueError("evidence narrative access context does not match authorized Xeed")

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
    considered_ids = material_resolver.considered_observation_ids(
        subject_id=subject_id,
        candidate_id=basis.candidate_id,
    )
    if not considered_ids:
        raise ValueError("evidence narrative requires governed considered evidence")
    if len(considered_ids) != len(set(considered_ids)):
        raise ValueError("considered evidence ids must be unique")

    evidence_scope_by_id = {
        observation_id: _authorized_scope_by_id(
            memory=observation_memory,
            subject_id=subject_id,
            observation_id=observation_id,
            access_context=access_context,
            reuse_policy=reuse_policy,
            temporal_policy=temporal_policy,
        )
        for observation_id in considered_ids
    }
    effective_values = [value[1] for value in evidence_scope_by_id.values()]
    currentness_rank = {
        "CURRENT": 0,
        "STALE": 1,
        "HISTORICAL": 2,
        "UNKNOWN": 3,
    }
    root_currentness = max(
        effective_values,
        key=lambda value: currentness_rank.get(value, currentness_rank["UNKNOWN"]),
    )
    steps[0] = replace(steps[0], currentness=root_currentness)
    material_by_id = {}
    for observation_id in considered_ids:
        material = material_resolver.resolve(observation_id)
        if material is None:
            raise ValueError("considered evidence has no governed narrative material")
        material_by_id[observation_id] = material

    material_contradictions = {
        item.observation_id
        for item in material_by_id.values()
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
        if datum.observation_id not in material_by_id:
            raise ValueError("basis observation was not in governed considered evidence")
        evidence_scope, effective_currentness = evidence_scope_by_id[datum.observation_id]
        observation = observation_memory.get_observation(subject_id, datum.observation_id)
        if observation is None:
            raise ValueError("authorized evidence narrative observation disappeared")
        material = material_by_id[datum.observation_id]
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
                currentness=effective_currentness,
                artifact_verified=verified,
                evidence_scope=evidence_scope,
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
                currentness=effective_currentness,
                artifact_verified=verified,
                evidence_scope=evidence_scope,
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
