"""Subscriber-safe explainable Xignal projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.explanation import (
    BasisContribution,
    ExplainableBasis,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from domain.evidence.epistemics import Currentness
from domain.faxt.model import FAXT
from domain.xignal import Xignal, XignalEpistemicState, XignalKind


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ExplanationStepKind(StrEnum):
    XIGNAL = "XIGNAL"
    CANONICAL_SUPPORT = "CANONICAL_SUPPORT"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class XignalExplanationStep:
    step_id: str
    kind: ExplanationStepKind
    ref: str
    label: str
    source_ref: str | None = None
    source_type: str | None = None
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        if any(not item.strip() for item in (self.step_id, self.ref, self.label)):
            raise ValueError("Xignal explanation step identity is required")
        if self.observed_at is not None and self.observed_at.tzinfo is None:
            raise ValueError("Xignal explanation step time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class XignalExplanationTrail:
    xignal_id: str
    basis_id: str
    steps: tuple[XignalExplanationStep, ...]

    def __post_init__(self) -> None:
        if not self.xignal_id.strip() or not self.basis_id.strip():
            raise ValueError("Xignal explanation trail identity is required")
        if not self.steps:
            raise ValueError("Xignal explanation trail cannot be empty")
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Xignal explanation trail step ids must be unique")


@dataclass(frozen=True, slots=True)
class ExplainableXignalProjection:
    xignal: Xignal
    semantic_target: str
    interpretation: str
    uncertainty: str
    source_refs: tuple[str, ...]
    source_types: tuple[str, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    trail: XignalExplanationTrail

    def __post_init__(self) -> None:
        if not self.semantic_target.strip() or not self.interpretation.strip():
            raise ValueError("subscriber Xignal projection requires semantic meaning")
        if not self.uncertainty.strip():
            raise ValueError("subscriber Xignal projection requires explicit uncertainty")
        if not self.source_refs or not self.source_types:
            raise ValueError("subscriber Xignal projection requires source provenance")
        if self.first_observed_at.tzinfo is None or self.last_observed_at.tzinfo is None:
            raise ValueError("subscriber Xignal projection times must be timezone-aware")
        if self.first_observed_at > self.last_observed_at:
            raise ValueError("Xignal observed interval is invalid")


def _trail(
    *,
    xignal: Xignal,
    basis: ExplainableBasis,
) -> XignalExplanationTrail:
    steps: list[XignalExplanationStep] = [
        XignalExplanationStep(
            step_id=f"step:xignal:{xignal.xignal_id}",
            kind=ExplanationStepKind.XIGNAL,
            ref=xignal.xignal_id,
            label=xignal.why_attention,
        )
    ]
    for ref in sorted(xignal.canonical_support_refs):
        steps.append(
            XignalExplanationStep(
                step_id=f"step:canonical:{ref}",
                kind=ExplanationStepKind.CANONICAL_SUPPORT,
                ref=ref,
                label="Admitted canonical support",
            )
        )

    rank = {
        BasisContribution.SUPPORTS: 0,
        BasisContribution.CONTRADICTS: 1,
        BasisContribution.CONTEXT: 2,
    }
    for datum in sorted(
        basis.data,
        key=lambda item: (
            rank[item.contribution],
            item.observed_at,
            item.datum_id,
        ),
    ):
        steps.append(
            XignalExplanationStep(
                step_id=f"step:datum:{datum.datum_id}",
                kind=ExplanationStepKind(datum.contribution.value),
                ref=datum.evidence_ref or datum.observation_id,
                label=datum.excerpt_or_summary,
                source_ref=datum.source_ref,
                source_type=datum.source_type,
                observed_at=datum.observed_at,
            )
        )

    for index, unknown in enumerate(xignal.unknowns):
        steps.append(
            XignalExplanationStep(
                step_id=f"step:unknown:{index}:{_fingerprint(unknown)[:12]}",
                kind=ExplanationStepKind.UNKNOWN,
                ref=f"unknown:{_fingerprint(unknown)[:16]}",
                label=unknown,
            )
        )

    return XignalExplanationTrail(
        xignal_id=xignal.xignal_id,
        basis_id=basis.basis_id,
        steps=tuple(steps),
    )


def _validate_observed_support(*, basis: ExplainableBasis, faxt: FAXT) -> None:
    if basis.subject_id != faxt.subject_id:
        raise ValueError("OBSERVED Xignal basis subject must match canonical FAXT subject")
    support_evidence = {
        datum.evidence_ref
        for datum in basis.data
        if datum.contribution is BasisContribution.SUPPORTS and datum.evidence_ref is not None
    }
    if not support_evidence.intersection(faxt.evidence_refs):
        raise ValueError("OBSERVED Xignal basis must reference admitted FAXT evidence")


def project_explainable_xignal(
    *,
    organization_context: AuthorizedXeedOrganization,
    candidate_id: str,
    kind: XignalKind,
    epistemic_state: XignalEpistemicState,
    title: str,
    why_attention: str,
    basis: ExplainableBasis,
    emitted_at: datetime,
    policy_version: str,
    canonical_faxt: FAXT | None = None,
    currentness: Currentness = Currentness.UNKNOWN,
    relationship_ref: str | None = None,
    pathx_ref: str | None = None,
    unknowns: tuple[str, ...] = (),
) -> ExplainableXignalProjection:
    """Project one explainable Xignal without granting canonical-write authority."""

    if not isinstance(organization_context, AuthorizedXeedOrganization):
        raise TypeError("Xignal projection requires AuthorizedXeedOrganization")
    xeed = organization_context.authorized_xeed.xeed
    subject_id = organization_context.organization.id

    if basis.subject_id != subject_id:
        raise ValueError("Xignal basis must be bound to the canonical observed subject")
    if basis.candidate_id != candidate_id:
        raise ValueError("Xignal basis candidate must match projection candidate")

    canonical_refs: tuple[str, ...] = ()
    effective_currentness = currentness
    if epistemic_state is XignalEpistemicState.OBSERVED:
        if canonical_faxt is None:
            raise ValueError("OBSERVED Xignal requires admitted canonical support")
        if canonical_faxt.subject_id != subject_id:
            raise ValueError("canonical Xignal support cannot cross subjects")
        _validate_observed_support(basis=basis, faxt=canonical_faxt)
        canonical_refs = (canonical_faxt.id,)
        effective_currentness = canonical_faxt.currentness
    elif canonical_faxt is not None:
        raise ValueError("only OBSERVED Xignal may claim canonical FAXT support")

    contradictions = tuple(
        datum.excerpt_or_summary
        for datum in basis.data
        if datum.contribution is BasisContribution.CONTRADICTS
    )
    digest = _fingerprint(
        {
            "xeed_id": xeed.id,
            "subject_id": subject_id,
            "candidate_id": candidate_id,
            "kind": kind.value,
            "epistemic_state": epistemic_state.value,
            "basis_id": basis.basis_id,
            "state_fingerprint": basis.state_fingerprint,
            "policy_version": policy_version,
        }
    )
    xignal = Xignal(
        xignal_id=f"xignal:{digest[:32]}",
        xeed_id=xeed.id,
        subject_id=subject_id,
        candidate_id=candidate_id,
        kind=kind,
        epistemic_state=epistemic_state,
        title=title,
        why_attention=why_attention,
        basis_ref=basis.basis_id,
        emitted_at=emitted_at,
        currentness=effective_currentness,
        policy_version=policy_version,
        canonical_support_refs=canonical_refs,
        relationship_ref=relationship_ref,
        pathx_ref=pathx_ref,
        contradictions=contradictions,
        unknowns=unknowns,
    )

    observed = sorted(datum.observed_at for datum in basis.data)
    source_refs = tuple(dict.fromkeys(datum.source_ref for datum in basis.data))
    source_types = tuple(dict.fromkeys(datum.source_type for datum in basis.data))
    return ExplainableXignalProjection(
        xignal=xignal,
        semantic_target=basis.semantic_target,
        interpretation=basis.interpretation,
        uncertainty=basis.uncertainty,
        source_refs=source_refs,
        source_types=source_types,
        first_observed_at=observed[0],
        last_observed_at=observed[-1],
        trail=_trail(xignal=xignal, basis=basis),
    )
