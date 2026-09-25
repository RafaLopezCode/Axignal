"""Deterministic fail-closed pre-provider checks for V-next decision requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from experiments.decision_lab.contracts_vnext import (
    DECISION_CONTRACTS,
    STATE_CONTRACTS,
    DecisionContract,
    DecisionFamily,
    Missingness,
    RequirementCheck,
    contract_errors,
    missingness,
    path_value,
)


@dataclass(frozen=True)
class AnswerabilityResult:
    status: str
    reasons: tuple[str, ...]
    contract_version: str
    state_contract_version: str
    authority: str = "AXIGNAL_PRE_PROVIDER_INFORMATION_CONTROL"

    @property
    def answerable(self) -> bool:
        return self.status == "ANSWERABLE"


def _semantic_content(value: Any, item: Any) -> bool:
    """Reject empty text and reference-only values; do not infer truth or relevance."""
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = value.strip()
    if isinstance(item, dict):
        references = {str(item.get(key, "")).strip() for key in ("evidence_id", "source_ref")}
        if candidate in references:
            return False
    return not candidate.lower().startswith(("http://", "https://", "synthetic://"))


def validate_answerability(
    contract: DecisionContract,
    state: dict[str, Any],
) -> AnswerabilityResult:
    """Return information sufficiency only; this is not a truth/quality score."""
    errors = contract_errors(contract)
    reasons = set(errors)
    state_contract = STATE_CONTRACTS.get(contract.family)
    if state_contract is None:
        reasons.add("INVALID_STATE_CONTRACT")
    else:
        for requirement in state_contract.requirements:
            value = path_value(state, requirement.path)
            classification = missingness(value)
            if classification is Missingness.ABSENT:
                reasons.add("MISSING_REQUIRED_INFORMATION")
                continue
            if classification is Missingness.EMPTY:
                reasons.add("EMPTY_REQUIRED_INFORMATION")
                continue
            if classification in {Missingness.UNKNOWN, Missingness.UNAVAILABLE}:
                if not requirement.unknown_allowed:
                    reasons.add("MISSING_REQUIRED_INFORMATION")
                continue
            if classification is Missingness.NOT_APPLICABLE:
                if not requirement.not_applicable_allowed:
                    reasons.add("MISSING_REQUIRED_INFORMATION")
                continue
            if RequirementCheck.CARDINALITY in requirement.checks:
                count = len(value) if isinstance(value, (list, tuple, dict, str)) else 0
                if count < requirement.minimum_cardinality:
                    reasons.add("INSUFFICIENT_CARDINALITY")
            if RequirementCheck.PAIRWISE_ARGUMENTS in requirement.checks:
                entities = value
                if not isinstance(entities, dict) or not all(
                    isinstance(entities.get(key), dict) and entities[key] for key in ("a", "b")
                ):
                    reasons.add("INSUFFICIENT_CARDINALITY")
            if RequirementCheck.SEMANTIC_CONTENT in requirement.checks:
                items = value if isinstance(value, list) else [value]
                if not items or any(
                    not isinstance(item, dict) or not _semantic_content(item.get("content"), item)
                    for item in items
                ):
                    reasons.add("MISSING_SEMANTIC_CONTENT")
            if RequirementCheck.PROVENANCE in requirement.checks:
                items = value if isinstance(value, list) else [value]
                if not items or any(
                    not isinstance(item, str) or not item.strip() for item in items
                ):
                    reasons.add("MISSING_PROVENANCE")
            if RequirementCheck.DIRECTION in requirement.checks and (
                not isinstance(value, str)
                or value not in {"A_TO_B", "B_TO_A", "BIDIRECTIONAL", "UNDIRECTED"}
            ):
                reasons.add("INVALID_DIRECTION")
        if contract.family is DecisionFamily.ECONOMIC_RELATIONSHIP:
            endpoints = state.get("relationship", {}).get("endpoints", [])
            if isinstance(endpoints, list) and len(endpoints) >= 2 and endpoints[0] == endpoints[1]:
                reasons.add("PAIRWISE_ARGUMENTS_NOT_DISTINCT")
            temporal_required = (
                state.get("requirements", {}).get("temporal_context_required") is True
            )
            if (
                temporal_required
                and missingness(state.get("temporal_context")) is not Missingness.PRESENT
            ):
                reasons.add("MISSING_TEMPORAL_REFERENCE")
        if contract.family is DecisionFamily.CLAIM_EVIDENCE_SUPPORT:
            temporal_required = state.get("claim", {}).get("temporal_scope") == "CURRENT_AS_OF"
            if (
                temporal_required
                and missingness(state.get("temporal_context")) is not Missingness.PRESENT
            ):
                reasons.add("MISSING_TEMPORAL_REFERENCE")

    ordered = tuple(sorted(reasons))
    return AnswerabilityResult(
        "ANSWERABLE" if not ordered else "NOT_ANSWERABLE",
        ordered,
        contract.version,
        state_contract.version if state_contract else "UNKNOWN",
    )


def validate_decision_request(
    contract_id: str,
    state: dict[str, Any],
) -> AnswerabilityResult:
    """Resolve only registered experimental contracts; unknown versions fail closed."""
    contract = DECISION_CONTRACTS.get(contract_id)
    if contract is None:
        return AnswerabilityResult(
            "NOT_ANSWERABLE",
            ("INVALID_DECISION_CONTRACT",),
            "UNKNOWN",
            str(state.get("state_contract_version", "UNKNOWN")),
        )
    if state.get("state_contract_version") != contract.state_contract_version:
        return AnswerabilityResult(
            "NOT_ANSWERABLE",
            ("STATE_CONTRACT_VERSION_MISMATCH",),
            contract.version,
            str(state.get("state_contract_version", "ABSENT")),
        )
    return validate_answerability(contract, state)
