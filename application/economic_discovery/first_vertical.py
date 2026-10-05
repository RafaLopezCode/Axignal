"""One capability/announced-need vertical; all output is non-canonical.

No acquisition or canonical writer is invoked. The caller supplies normalized,
rights-cleared public evidence. Provider adapters can implement the existing
StructuredEvaluatorPort; a future concrete adapter belongs behind cognition's
ModelRouter/CognitiveProvider, not in this policy.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from application.economic_discovery.brain_contracts import (
    AttentionDisposition,
    DimensionDisposition,
    DimensionEvaluation,
    SemanticPrimitive,
    TypedJudgmentVector,
    TypingDimensionContract,
)
from application.economic_discovery.contracts import (
    ChoiceOption,
    ChoiceSpaceContract,
    StructuredEvaluationRequest,
    StructuredEvaluatorPort,
    StructuredJudgment,
    evaluate_structured,
)
from application.economic_discovery.economic_state import (
    EconomicObservation,
    EvidenceBackedEconomicState,
    fingerprint,
)
from application.economic_discovery.explanation import BasisContribution, ExplainableBasis
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.source_representation import RichSubjectState, compile_rich_subject_state
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.xignal import XignalEpistemicState

POLICY_VERSION = "capability-announced-need:v1"


def _dimension(
    dimension_id: str, question: str, requirements: tuple[str, ...]
) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.CHOICE,
        question=question,
        state_requirements=requirements,
        dependencies=(*requirements, "source.currentness", "source.contradictions"),
        mutually_exclusive=True,
        abstention_policy="Missing, conflicting or non-current material remains UNKNOWN.",
    )


DIMENSIONS = (
    _dimension(
        "supplier_role",
        "Does the source describe this organization offering goods/services in the stated scope?",
        ("subject.supply_activity",),
    ),
    _dimension(
        "customer_role",
        "Does the source describe this organization purchasing inputs in the stated scope?",
        ("subject.purchase_activity",),
    ),
    _dimension(
        "functional_alignment",
        "Could the stated capability address the project's stated need functionally? "
        "This does not establish commercial fit or a relationship.",
        ("subject.capability", "activity.required_capability", "activity.event"),
    ),
    _dimension(
        "delivery_reach",
        "Does the stated capability delivery scope cover the project's region and delivery mode?",
        (
            "subject.reach_region",
            "subject.delivery_mode",
            "activity.region",
            "activity.delivery_mode",
        ),
    ),
    _dimension(
        "timing",
        "Is the explicitly stated project attention window still open as of evaluation?",
        ("activity.event", "activity.action_until"),
    ),
    _dimension(
        "eligibility",
        "Does the source-stated qualification match the project's stated certification requirement?",
        ("subject.certification", "activity.required_certification"),
    ),
)
_SEMANTIC = frozenset({"supplier_role", "customer_role", "functional_alignment"})
_CORE = frozenset({"functional_alignment", "delivery_reach", "timing", "eligibility"})


def _choice_space(contract: TypingDimensionContract) -> ChoiceSpaceContract:
    return ChoiceSpaceContract(
        choice_space_id=f"economic:{contract.dimension_id}",
        version="1",
        semantic_target=contract.semantic_target,
        options=(
            ChoiceOption(
                "YES", "The supplied material supports the proposition within this scope."
            ),
            ChoiceOption(
                "NO", "The supplied material explicitly supports its negation in this scope."
            ),
            ChoiceOption(
                "UNKNOWN", "Neither conclusion is warranted, or material ambiguity remains."
            ),
        ),
        mutually_exclusive=True,
        coverage_policy="UNKNOWN covers unresolved alternatives; no forced classification.",
        scope="One capability and one announced project; source-stated public economic context.",
        composition_policy=POLICY_VERSION,
    )


@dataclass(frozen=True, slots=True)
class EconomicCandidate:
    candidate_id: str
    subject: EvidenceBackedEconomicState
    activity: EvidenceBackedEconomicState
    state: RichSubjectState
    as_of: datetime
    temporal_policy: TemporalCurrentnessPolicy

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "candidate": self.candidate_id,
                "subject": self.subject.fingerprint,
                "activity": self.activity.fingerprint,
                "state": self.state.fingerprint,
                "as_of": self.as_of.isoformat(),
                "temporal_policy": (
                    self.temporal_policy.policy_id,
                    self.temporal_policy.version,
                    self.temporal_policy.stale_after.total_seconds(),
                    self.temporal_policy.historical_after.total_seconds(),
                ),
            }
        )

    def observation(self, field: str) -> EconomicObservation | None:
        scope, name = field.split(".", 1)
        return (self.subject if scope == "subject" else self.activity).get(name)

    def material(self, fields: tuple[str, ...]) -> tuple[EconomicObservation, ...]:
        return tuple(
            item
            for scope, source in (("subject", self.subject), ("activity", self.activity))
            for item in source.observations
            if f"{scope}.{item.datum.name}" in fields
            or any(f"{scope}.{target}" in fields for target in item.contradicts_fields)
        )


@dataclass(frozen=True, slots=True)
class EconomicEvaluationRequest(StructuredEvaluationRequest):
    """Compatible Choice request carrying semantics, not only opaque hashes."""

    candidate: EconomicCandidate
    dimension: TypingDimensionContract
    choice_space: ChoiceSpaceContract

    def __post_init__(self) -> None:
        super(EconomicEvaluationRequest, self).__post_init__()
        if (
            self.decision_contract_id != f"{self.dimension.dimension_id}:{self.dimension.version}"
            or self.state_fingerprint != self.candidate.fingerprint
            or self.question_fingerprint != self.dimension.fingerprint
            or self.choice_space_fingerprint != self.choice_space.fingerprint
            or self.option_ids != tuple(option.option_id for option in self.choice_space.options)
        ):
            raise ValueError("economic evaluation request must bind actual state/question/options")


@dataclass(frozen=True, slots=True)
class EconomicInterpretation:
    epistemic_state: XignalEpistemicState
    attention: AttentionDisposition
    reason_codes: tuple[str, ...]
    policy_version: str = POLICY_VERSION

    def __post_init__(self) -> None:
        if self.epistemic_state not in (
            XignalEpistemicState.POTENTIAL,
            XignalEpistemicState.UNKNOWN,
        ):
            raise ValueError("economic interpretation can never assert OBSERVED truth")
        if not self.policy_version.strip() or not self.reason_codes:
            raise ValueError("economic interpretation requires versioned policy reasons")


@dataclass(frozen=True, slots=True)
class EconomicReasoningResult:
    candidate: EconomicCandidate
    vector: TypedJudgmentVector
    raw_judgments: tuple[StructuredJudgment, ...]
    interpretation: EconomicInterpretation
    basis: ExplainableBasis
    dimension_bases: tuple[ExplainableBasis, ...]


def _gate(candidate: EconomicCandidate, contract: TypingDimensionContract) -> tuple[str, ...]:
    issues: list[str] = []
    for field in contract.state_requirements:
        item = candidate.observation(field)
        if item is None:
            issues.append(f"MISSING:{field}")
        elif item.basis.contribution is not BasisContribution.SUPPORTS:
            issues.append(f"UNSUPPORTED:{field}")
        elif item.epistemic_state not in (
            EpistemicState.OBSERVED,
            EpistemicState.CORROBORATED,
            EpistemicState.DECLARED,
        ):
            issues.append(f"UNRESOLVED:{field}:{item.epistemic_state.value}")
        elif (
            item.effective_currentness(as_of=candidate.as_of, policy=candidate.temporal_policy)
            is not Currentness.CURRENT
        ):
            issues.append(f"NON_CURRENT:{field}")
    for item in candidate.material(contract.state_requirements):
        if item.contradicts_fields or (
            item.canonical_support and item.canonical_support.contradictions
        ):
            issues.append(f"CONTRADICTION:{item.basis.datum_id}")
    return tuple(issues)


def _deterministic(candidate: EconomicCandidate, dimension_id: str) -> tuple[str, str]:
    def value(field: str) -> str:
        item = candidate.state.get(field)
        if item is None:
            raise ValueError("deterministic interpretation requires answerable inputs")
        return item.value

    if dimension_id == "delivery_reach":
        compatible = value("subject.reach_region") == value("activity.region") and value(
            "subject.delivery_mode"
        ) == value("activity.delivery_mode")
        # A region outside observed reach is unverified, not the whole market excluded.
        return (
            ("YES", "EXPLICIT_DELIVERY_SCOPE_MATCH")
            if compatible
            else ("UNKNOWN", "REACH_UNVERIFIED")
        )
    if dimension_id == "eligibility":
        if value("subject.certification") == value("activity.required_certification"):
            return "YES", "EXPLICIT_QUALIFICATION_MATCH"
        return "UNKNOWN", "QUALIFICATION_UNVERIFIED"
    try:
        until = datetime.fromisoformat(value("activity.action_until"))
    except ValueError:
        return "UNKNOWN", "WINDOW_UNRESOLVED"
    if until.tzinfo is None:
        return "UNKNOWN", "WINDOW_TIMEZONE_MISSING"
    return (
        ("YES", "EXPLICIT_WINDOW_OPEN")
        if candidate.as_of < until
        else ("NO", "EXPLICIT_WINDOW_CLOSED")
    )


def _basis(
    candidate: EconomicCandidate,
    *,
    target: str,
    contract_fingerprint: str,
    material: tuple[EconomicObservation, ...],
    interpretation: str,
    uncertainty: str,
) -> ExplainableBasis:
    digest = fingerprint(
        (candidate.fingerprint, target, contract_fingerprint, interpretation, uncertainty)
    )
    return ExplainableBasis(
        basis_id=f"basis:{digest}",
        subject_id=candidate.subject.state.subject_id,
        candidate_id=candidate.candidate_id,
        semantic_target=target,
        state_fingerprint=candidate.fingerprint,
        contract_fingerprint=contract_fingerprint,
        evaluated_at=candidate.as_of,
        data=tuple(item.basis for item in material),
        interpretation=interpretation,
        uncertainty=uncertainty,
    )


def run_economic_vertical(
    *,
    subject: EvidenceBackedEconomicState,
    activity: EvidenceBackedEconomicState,
    evaluator: StructuredEvaluatorPort,
    as_of: datetime,
    temporal_policy: TemporalCurrentnessPolicy,
) -> EconomicReasoningResult:
    """Derive a candidate, gate each axis, judge eligible semantics, then compose."""
    if as_of.tzinfo is None:
        raise ValueError("economic reasoning time must be timezone-aware")
    if subject.state.subject_id == activity.state.subject_id:
        raise ValueError("this vertical requires distinct capability and activity subjects")
    material = (*subject.observations, *activity.observations)
    if not material or len({item.basis.datum_id for item in material}) != len(material):
        raise ValueError("candidate requires evidence with globally unique basis datum ids")
    # Validate every timestamp, including contradictions and contextual observations.
    for item in material:
        item.effective_currentness(as_of=as_of, policy=temporal_policy)
    state = compile_rich_subject_state(
        subject_id=subject.state.subject_id,
        contributions=tuple(
            replace(item.datum, name=f"{scope}.{item.datum.name}")
            for scope, source in (("subject", subject), ("activity", activity))
            for item in source.observations
        ),
    )
    candidate = EconomicCandidate(
        candidate_id="candidate:"
        + fingerprint((subject.state.subject_id, activity.state.subject_id)),
        subject=subject,
        activity=activity,
        state=state,
        as_of=as_of,
        temporal_policy=temporal_policy,
    )
    evaluations: list[DimensionEvaluation] = []
    raw: list[StructuredJudgment] = []
    bases: list[ExplainableBasis] = []
    for contract in DIMENSIONS:
        issues = _gate(candidate, contract)
        no_certification = candidate.observation("activity.required_certification")
        not_applicable = (
            contract.dimension_id == "eligibility"
            and no_certification is not None
            and no_certification.datum.value == "NONE"
            and _gate(
                candidate,
                replace(contract, state_requirements=("activity.required_certification",)),
            )
            == ()
        )
        if not_applicable or issues:
            evaluation = DimensionEvaluation(
                dimension_id=contract.dimension_id,
                contract_fingerprint=contract.fingerprint,
                disposition=(
                    DimensionDisposition.NOT_APPLICABLE
                    if not_applicable
                    else DimensionDisposition.NOT_ANSWERABLE
                ),
                reason="EXPLICIT_NO_CERTIFICATION_REQUIREMENT"
                if not_applicable
                else ";".join(issues),
            )
        elif contract.dimension_id in _SEMANTIC:
            choice = _choice_space(contract)
            request = EconomicEvaluationRequest(
                decision_contract_id=f"{contract.dimension_id}:{contract.version}",
                state_fingerprint=candidate.fingerprint,
                question_fingerprint=contract.fingerprint,
                choice_space_fingerprint=choice.fingerprint,
                option_ids=tuple(option.option_id for option in choice.options),
                candidate=candidate,
                dimension=contract,
                choice_space=choice,
            )
            try:
                judgment = evaluate_structured(evaluator, request)
            except Exception as exc:
                # Failure is operational uncertainty; do not retain exception payloads/secrets.
                evaluation = DimensionEvaluation(
                    dimension_id=contract.dimension_id,
                    contract_fingerprint=contract.fingerprint,
                    disposition=DimensionDisposition.NOT_ANSWERABLE,
                    reason=f"EVALUATOR_FAILURE:{type(exc).__name__}",
                )
            else:
                raw.append(judgment)
                evaluation = DimensionEvaluation(
                    dimension_id=contract.dimension_id,
                    contract_fingerprint=contract.fingerprint,
                    disposition=DimensionDisposition.ANSWERABLE,
                    evaluator=judgment.evaluator,
                    evaluator_version=judgment.evaluator_version,
                    distribution=judgment.distribution,
                    confidence=judgment.confidence,
                    selected_option=judgment.selected_option,
                    replay_reference=judgment.replay_reference,
                    reason="BOUNDED_SOURCE_CONTEXT_JUDGMENT",
                )
        else:
            selected, reason = _deterministic(candidate, contract.dimension_id)
            evaluation = DimensionEvaluation(
                dimension_id=contract.dimension_id,
                contract_fingerprint=contract.fingerprint,
                disposition=DimensionDisposition.ANSWERABLE,
                evaluator="python",
                evaluator_version=POLICY_VERSION,
                selected_option=selected,
                reason=reason,
            )
        evaluations.append(evaluation)
        axis_material = candidate.material(contract.state_requirements)
        if any(item.basis.contribution is BasisContribution.SUPPORTS for item in axis_material):
            bases.append(
                _basis(
                    candidate,
                    target=contract.dimension_id,
                    contract_fingerprint=contract.fingerprint,
                    material=axis_material,
                    interpretation=f"{contract.question} Result: {evaluation.selected_option or evaluation.disposition.value}.",
                    uncertainty=evaluation.reason
                    or "Classification is non-canonical and scoped to the supplied evidence.",
                )
            )
    vector = TypedJudgmentVector(
        subject_id=subject.state.subject_id,
        candidate_id=candidate.candidate_id,
        state_fingerprint=candidate.fingerprint,
        evaluated_at=as_of,
        evaluations=tuple(evaluations),
    )
    core_blockers = tuple(
        item
        for item in evaluations
        if item.dimension_id in _CORE
        and item.disposition is not DimensionDisposition.NOT_APPLICABLE
        and (
            item.disposition is not DimensionDisposition.ANSWERABLE or item.selected_option != "YES"
        )
    )
    supplier_role = next(item for item in evaluations if item.dimension_id == "supplier_role")
    supplier_material_block = supplier_role.selected_option == "NO" or (
        supplier_role.disposition is DimensionDisposition.NOT_ANSWERABLE
        and "CONTRADICTION:" in (supplier_role.reason or "")
    )
    blockers = (
        *core_blockers,
        *((supplier_role,) if supplier_material_block else ()),
    )
    interpretation = EconomicInterpretation(
        epistemic_state=XignalEpistemicState.UNKNOWN
        if blockers
        else XignalEpistemicState.POTENTIAL,
        attention=(
            AttentionDisposition.RETAIN
            if any(item.selected_option == "NO" for item in blockers)
            else AttentionDisposition.INVESTIGATE
        )
        if blockers
        else AttentionDisposition.WARRANTED_ATTENTION,
        reason_codes=tuple(
            f"{item.dimension_id}:{item.reason}:{item.selected_option or 'UNKNOWN'}"
            for item in blockers
        )
        if blockers
        else ("ALIGNED_CAPABILITY_NEED_WITH_REACH_WINDOW_AND_ELIGIBILITY",),
    )
    basis = _basis(
        candidate,
        target="capability_need_opportunity",
        contract_fingerprint=fingerprint(
            (POLICY_VERSION, tuple(item.fingerprint for item in DIMENSIONS))
        ),
        material=material,
        interpretation=(
            "Potential functional relevance warrants attention; no relationship or commercial fit is established."
            if not blockers
            else "Opportunity relevance is unresolved or withheld within this scope."
        ),
        uncertainty="; ".join(
            (
                *interpretation.reason_codes,
                "Price, capacity, incumbent and commercial access are unassessed.",
            )
        ),
    )
    return EconomicReasoningResult(
        candidate, vector, tuple(raw), interpretation, basis, tuple(bases)
    )
