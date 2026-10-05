"""Human-First read model for the public-evidence economic vertical.

Internal immutable snapshot only. A future subscriber route must authorize
evidence access and refresh currentness before publishing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.brain_contracts import AttentionDisposition
from application.economic_discovery.economic_state import fingerprint
from application.economic_discovery.first_vertical import EconomicReasoningResult
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState


@dataclass(frozen=True, slots=True)
class EconomicHumanOutput:
    output_id: str
    result: EconomicReasoningResult
    headline: str
    one_sentence_meaning: str
    why_it_may_matter: str
    temporal_state: Currentness
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    semantic_family: str = "OPPORTUNITY"
    archetype: str = "CAPABILITY_NEED_RELEVANCE"
    revision: str = "1"

    def to_wire(self) -> dict[str, object]:
        """Keep meanings, uncertainty, provenance and raw judgment separate."""
        result = self.result
        candidate = result.candidate
        basis_by_axis = {item.semantic_target: item for item in result.dimension_bases}
        observations = (*candidate.subject.observations, *candidate.activity.observations)
        return {
            "output_id": self.output_id,
            "revision": self.revision,
            "subject_ref": candidate.subject.state.subject_id,
            "activity_subject_ref": candidate.activity.state.subject_id,
            "candidate_ref": candidate.candidate_id,
            "semantic_family": self.semantic_family,
            "archetype": self.archetype,
            "as_of": candidate.as_of.isoformat(),
            "state_fingerprint": result.vector.state_fingerprint,
            "epistemic_state": result.interpretation.epistemic_state.value,
            "temporal_state": self.temporal_state.value,
            "attention": result.interpretation.attention.value,
            "headline": self.headline,
            "one_sentence_meaning": self.one_sentence_meaning,
            "why_it_may_matter": self.why_it_may_matter,
            "policy_version": result.interpretation.policy_version,
            "reason_codes": result.interpretation.reason_codes,
            "basis_ref": result.basis.basis_id,
            "basis_interpretation": result.basis.interpretation,
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "coverage_limits": (
                "One capability and one source-stated project, not the organization's whole market.",
                "Roles concern source-stated activities; no relationship between the two subjects is established.",
                "Functional relevance does not establish commercial fit or a sale probability.",
            ),
            "dimensions": tuple(
                {
                    "dimension_id": item.dimension_id,
                    "disposition": item.disposition.value,
                    "value": None
                    if item.selected_option in (None, "UNKNOWN")
                    else item.selected_option,
                    "reason": item.reason,
                    "contract_fingerprint": item.contract_fingerprint,
                    "basis_ref": basis_by_axis[item.dimension_id].basis_id
                    if item.dimension_id in basis_by_axis
                    else None,
                    "evidence_refs": tuple(
                        datum.evidence_ref for datum in basis_by_axis[item.dimension_id].data
                    )
                    if item.dimension_id in basis_by_axis
                    else (),
                    "interpretation": basis_by_axis[item.dimension_id].interpretation
                    if item.dimension_id in basis_by_axis
                    else None,
                }
                for item in result.vector.evaluations
            ),
            "evidence": tuple(
                {
                    "datum_ref": item.basis.datum_id,
                    "observation_ref": item.datum.observation_id,
                    "evidence_ref": item.basis.evidence_ref,
                    "source_ref": item.basis.source_ref,
                    "source_type": item.basis.source_type,
                    "excerpt": item.basis.excerpt_or_summary,
                    "observed_at": item.datum.observed_at.isoformat(),
                    "epistemic_state": item.epistemic_state.value,
                    "currentness": item.effective_currentness(
                        as_of=candidate.as_of, policy=candidate.temporal_policy
                    ).value,
                    "valid_from": item.valid_from.isoformat() if item.valid_from else None,
                    "valid_until": item.valid_until.isoformat() if item.valid_until else None,
                    "contribution": item.basis.contribution.value,
                    "representation_ref": item.datum.representation_id,
                    "representation_fingerprint": item.basis.representation_fingerprint,
                    "support_span": (
                        {
                            "representation_id": item.datum.supporting_span.representation_id,
                            "representation_fingerprint": (
                                item.datum.supporting_span.representation_fingerprint
                            ),
                            "start": item.datum.supporting_span.start,
                            "end": item.datum.supporting_span.end,
                        }
                        if item.datum.supporting_span is not None
                        else None
                    ),
                    "extraction_fingerprint": item.basis.extraction_fingerprint,
                    "canonical_support_ref": item.canonical_support.id
                    if item.canonical_support
                    else None,
                    "rights_basis_ref": item.rights_basis_ref,
                }
                for item in observations
            ),
            "judgment_refs": tuple(item.replay_reference for item in result.raw_judgments),
        }


def compile_economic_human_output(
    result: EconomicReasoningResult, *, as_of: datetime
) -> EconomicHumanOutput:
    """Compile only the same evaluated snapshot; an advanced clock requires a new run."""
    candidate = result.candidate
    if as_of != candidate.as_of:
        raise ValueError("Human Output requires reevaluation at the requested consumption time")
    potential = result.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL
    observations = (*candidate.subject.observations, *candidate.activity.observations)
    effective = {
        item.effective_currentness(as_of=as_of, policy=candidate.temporal_policy)
        for item in observations
    }
    temporal_state = next(
        status
        for status in (
            Currentness.UNKNOWN,
            Currentness.HISTORICAL,
            Currentness.STALE,
            Currentness.CURRENT,
        )
        if status in effective
    )
    capability = candidate.state.get("subject.capability")
    need = candidate.state.get("activity.required_capability")
    unknowns = (
        *(
            f"{item.dimension_id}: {item.reason or 'UNKNOWN'}"
            for item in result.vector.evaluations
            if item.selected_option in (None, "UNKNOWN")
            and item.disposition.value != "NOT_APPLICABLE"
        ),
        "Price, capacity, incumbent and commercial access have not been assessed.",
    )
    contradictions = tuple(
        item.basis.excerpt_or_summary for item in observations if item.contradicts_fields
    ) + tuple(
        ref
        for item in observations
        if item.canonical_support
        for ref in item.canonical_support.contradictions
    )
    meaning = (
        f"The capability '{capability.value}' could address the project's stated need '{need.value}'."
        if potential and capability is not None and need is not None
        else "Available evidence does not currently warrant a positive opportunity interpretation."
    )
    return EconomicHumanOutput(
        output_id="economic-output:"
        + fingerprint(
            (
                result.basis.basis_id,
                result.interpretation.policy_version,
                tuple(
                    (
                        item.dimension_id,
                        item.selected_option,
                        item.evaluator,
                        item.evaluator_version,
                        item.replay_reference,
                        item.distribution,
                        item.confidence,
                    )
                    for item in result.vector.evaluations
                ),
            )
        ),
        result=result,
        headline="Potential project relevance"
        if potential
        else "Project relevance remains unresolved",
        one_sentence_meaning=meaning,
        why_it_may_matter=(
            "Functional alignment, delivery scope, an open attention window and eligibility support investigating this project."
            if potential
            else "Retain the evidence and resolve the stated limits before drawing a business conclusion."
            if result.interpretation.attention is AttentionDisposition.INVESTIGATE
            else "A scoped negative judgment or known constraint prevents positive presentation; the candidate remains available for inspection."
        ),
        temporal_state=temporal_state,
        unknowns=unknowns,
        contradictions=contradictions,
    )
