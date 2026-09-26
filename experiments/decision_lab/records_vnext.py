"""Required audit fields for V-next experimental cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from experiments.decision_lab.failure_attribution_vnext import FailureAttribution
from experiments.decision_lab.models import NormalizedJudgment


@dataclass(frozen=True)
class DecisionCaseRecord:
    case_id: str
    golden_target: str | None
    golden_provenance: str
    decision_contract_version: str
    question_version: str
    state_contract_version: str
    state_compiler_version: str
    answerability_status: str
    answerability_reasons: tuple[str, ...]
    primitive: str
    requested_model: str
    sdk_version: str
    composition_policy_version: str
    raw_judgment: NormalizedJudgment | None
    composed_result: dict[str, Any] | None
    metrics: dict[str, Any]
    failure_attribution: FailureAttribution | None
    result_source: str = "PROVIDER_JUDGMENT"

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.case_id or not self.golden_provenance:
            errors.append("CASE_ID_OR_GOLDEN_PROVENANCE_MISSING")
        if not all(
            (
                self.decision_contract_version,
                self.question_version,
                self.state_contract_version,
                self.state_compiler_version,
                self.composition_policy_version,
            )
        ):
            errors.append("VERSION_BINDING_MISSING")
        if self.answerability_status not in {"ANSWERABLE", "NOT_ANSWERABLE"}:
            errors.append("INVALID_ANSWERABILITY_STATUS")
        if self.result_source not in {"PROVIDER_JUDGMENT", "DETERMINISTIC_RESULT"}:
            errors.append("INVALID_RESULT_SOURCE")
        if self.result_source == "DETERMINISTIC_RESULT" and self.raw_judgment is not None:
            errors.append("DETERMINISTIC_RESULT_MUST_NOT_BE_PROVIDER_JUDGMENT")
        if self.result_source == "DETERMINISTIC_RESULT" and self.metrics:
            errors.append("DETERMINISTIC_RESULT_EXCLUDED_FROM_PROVIDER_METRICS")
        if self.answerability_status == "NOT_ANSWERABLE" and (
            self.raw_judgment is not None or self.composed_result is not None
        ):
            errors.append("UNANSWERABLE_CASE_HAS_PROVIDER_RESULT")
        if (
            self.answerability_status == "ANSWERABLE"
            and self.raw_judgment is not None
            and self.composed_result is not None
            and self.composed_result.get("canonical_authority") is not False
        ):
            errors.append("COMPOSED_RESULT_AUTHORITY_INVALID")
        return tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
