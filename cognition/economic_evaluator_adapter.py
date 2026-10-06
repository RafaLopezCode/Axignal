"""Provider-neutral adapter from the cognitive router to EB-04 judgments."""

from __future__ import annotations

import hashlib
import json

from application.economic_discovery.contracts import (
    ConfidenceCapability,
    ConfidenceSemantics,
    DistributionAvailability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredEvaluatorPort,
    StructuredJudgment,
)
from application.economic_discovery.first_vertical import (
    EconomicEvaluationRequest,
)
from cognition.jobs.model import CognitiveJob, JobKind
from cognition.router.router import ModelRouter


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CognitiveEconomicEvaluatorAdapter(StructuredEvaluatorPort):
    """Route exact, evidence-grounded EB-04 questions and accept one typed choice.

    Provider output remains a non-authoritative judgment. The operator must
    inject a router and explicitly selected provider/version; credentials or
    installed SDKs never create this adapter or authorize a call.
    """

    def __init__(
        self,
        router: ModelRouter,
        *,
        provider_name: str,
        provider_version: str,
    ) -> None:
        if not provider_name.strip() or not provider_version.strip():
            raise ValueError("economic evaluator provider identity must be explicit")
        if provider_name not in router.registered():
            raise ValueError("configured economic evaluator provider is not registered")
        self._router = router
        self._provider_name = provider_name
        self._provider_version = provider_version
        self._profile = EvaluatorCapabilityProfile(
            profile_id=f"cognitive-economic-choice:{provider_name}",
            version=provider_version,
            distribution=DistributionCapability.NEVER,
            confidence=ConfidenceCapability.NEVER,
            replay_reference_supported=True,
        )

    @property
    def capability_profile(self) -> EvaluatorCapabilityProfile:
        return self._profile

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        if not isinstance(request, EconomicEvaluationRequest):
            raise TypeError("economic evaluator accepts only the typed EB-04 request")
        candidate = request.candidate
        material = candidate.material(request.dimension.state_requirements)
        evidence = [
            {
                "field": f"{scope}.{item.datum.name}",
                "value": item.datum.value,
                "epistemicState": item.epistemic_state.value,
                "currentness": item.currentness.value,
                "sourceType": item.basis.source_type,
                "sourceRef": item.basis.source_ref,
                "observedAt": item.basis.observed_at.isoformat(),
                "support": item.basis.excerpt_or_summary,
            }
            for scope, source in (("subject", candidate.subject), ("activity", candidate.activity))
            for item in source.observations
            if item in material
        ]
        job = CognitiveJob(
            id=(
                "economic-judgment:"
                + _digest(
                    (
                        request.decision_contract_id,
                        request.state_fingerprint,
                        request.question_fingerprint,
                        request.choice_space_fingerprint,
                    )
                )
            ),
            kind=JobKind.RELATIONSHIP_VERIFICATION,
            instruction=(
                f"Evaluate this bounded proposition: {request.dimension.question} "
                "Choose only an option justified by the supplied source material. "
                "Return exactly one JSON property selected_option, whose value is one of the listed options. "
                "Use UNKNOWN when evidence is missing, indirect, conflicting, or outside the stated scope. "
                "Do not assert commercial fit, a customer relationship, or canonical truth."
            ),
            context={
                "decisionContract": request.decision_contract_id,
                "dimension": request.dimension.dimension_id,
                "stateFingerprint": request.state_fingerprint,
                "questionFingerprint": request.question_fingerprint,
                "choiceSpaceFingerprint": request.choice_space_fingerprint,
                "scope": request.choice_space.scope,
                "options": [
                    {"id": item.option_id, "meaning": item.meaning}
                    for item in request.choice_space.options
                ],
                "evidence": evidence,
            },
        )
        result = self._router.route(job, provider_name=self._provider_name)
        if result.job_id != job.id or result.provider != self._provider_name:
            raise ValueError("economic evaluator response identity does not match routed job")
        if set(result.payload) != {"selected_option"}:
            raise ValueError("economic evaluator response must contain only selected_option")
        selected_option = result.payload["selected_option"]
        if not isinstance(selected_option, str) or selected_option not in request.option_ids:
            raise ValueError(
                "economic evaluator selected an option outside the declared choice set"
            )
        replay_reference = f"cognitive-result:{job.id}:{_digest(result.payload)}"
        return StructuredJudgment(
            selected_option=selected_option,
            evaluator=self._provider_name,
            evaluator_version=self._provider_version,
            decision_contract_id=request.decision_contract_id,
            state_fingerprint=request.state_fingerprint,
            question_fingerprint=request.question_fingerprint,
            choice_space_fingerprint=request.choice_space_fingerprint,
            capability_profile=self._profile,
            distribution_availability=DistributionAvailability.UNAVAILABLE,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference=replay_reference,
        )
