"""Fixture-only EB-05 execution mechanics for the governed FR-22 contracts.

This module deliberately has no live-provider mode. A later authority change can
attach an adapter only after the corpus, rights and provider eligibility gates
have been resolved without changing these measurement semantics.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Protocol

from experiments.decision_lab.bakeoff_vnext import (
    CompiledBakeoffCase,
    load_compiled_cases,
)
from experiments.decision_lab.evaluator import failure_for_exception
from experiments.decision_lab.models import NormalizedJudgment


class HarnessMode(StrEnum):
    SINGLES = "SINGLES"
    BATCH = "BATCH"


class LiveEligibility(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ProviderVisibleCase:
    """Minimal adapter view; it has no label, tag or provenance field."""

    case_id: str
    dimension_id: str
    contract_id: str
    primitive: str
    semantic_target: str
    question_version: str
    question_fingerprint: str
    answer_space: tuple[str, ...]
    uncertainty_semantics: str
    composition_policy: str
    state_contract_version: str
    compiler_version: str
    state_fingerprint: str
    answerability_status: str
    state_json: str


class FixtureEvaluator(Protocol):
    execution_scope: str
    evaluator_id: str
    evaluator_version: str

    def evaluate_one(self, case: ProviderVisibleCase) -> NormalizedJudgment: ...

    def evaluate_batch(
        self, cases: tuple[ProviderVisibleCase, ...]
    ) -> tuple[NormalizedJudgment, ...]: ...


def live_eligibility() -> tuple[dict[str, str], ...]:
    """Current dated execution state; this function never reads credentials."""

    return (
        {
            "candidate_id": "deterministic-baseline",
            "eligibility": LiveEligibility.ELIGIBLE.value,
            "reason_code": "LOCAL_RULES_NO_PROVIDER_CALL",
        },
        {
            "candidate_id": "typesafe-jev",
            "eligibility": LiveEligibility.BLOCKED.value,
            "reason_code": "P0_JEV_04A_BLOCKED_NO_VALID_CORPUS",
        },
        {
            "candidate_id": "luna-structured",
            "eligibility": LiveEligibility.UNAVAILABLE.value,
            "reason_code": "NO_GOVERNED_ADAPTER_OR_AUTHORIZED_MODEL_BINDING",
        },
        {
            "candidate_id": "openai-decisions",
            "eligibility": LiveEligibility.UNAVAILABLE.value,
            "reason_code": "ACCESS_AND_API_TERMS_NOT_ESTABLISHED",
        },
    )


def _visible(case: CompiledBakeoffCase) -> ProviderVisibleCase:
    from experiments.decision_lab.contracts_vnext import DECISION_CONTRACTS

    contract = DECISION_CONTRACTS[case.contract_id]
    state_json = json.dumps(case.provider_state, sort_keys=True, separators=(",", ":"))
    return ProviderVisibleCase(
        case_id=case.case_id,
        dimension_id=case.contract_id,
        contract_id=case.contract_id,
        primitive=contract.primitive.value,
        semantic_target=contract.semantic_target,
        question_version=contract.question_version,
        question_fingerprint=contract.question_semantic_fingerprint,
        answer_space=contract.answer_space,
        uncertainty_semantics=contract.uncertainty_semantics,
        composition_policy=contract.composition_policy,
        state_contract_version=case.state_contract_version,
        compiler_version=case.compiler_version,
        state_fingerprint=case.state_fingerprint,
        answerability_status=case.answerability_status,
        state_json=state_json,
    )


def _input_digest(inputs: tuple[ProviderVisibleCase, ...]) -> str:
    body = json.dumps([asdict(item) for item in inputs], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _empty_judgment(case: CompiledBakeoffCase, status: str) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "dimension_id": case.contract_id,
        "state_fingerprint": case.state_fingerprint,
        "answerability_status": case.answerability_status,
        "status": status,
        "judgment": None,
        "failure_category": None,
        "latency_ms": None,
        "usage": None,
        "cost": {"knowledge": "UNKNOWN", "amount_microunits": None, "currency": None},
        "latency_scope": "NOT_MEASURED",
    }


def _validated_judgment(
    case: CompiledBakeoffCase, judgment: NormalizedJudgment
) -> tuple[str, str | None]:
    if judgment.question_id != case.contract_id:
        return "SCHEMA_FAILURE", "QUESTION_ID_MISMATCH"
    if judgment.status == "MALFORMED":
        return "SCHEMA_FAILURE", "MALFORMED_TYPED_JUDGMENT"
    if judgment.status == "MISSING":
        return "ABSTAINED", None
    # Validate against the declared contract, never against what the evaluator claims to be.
    contract = _contract(case)
    primitive = str(contract.primitive.value)
    if judgment.primitive != primitive:
        return "SCHEMA_FAILURE", "PRIMITIVE_OUTSIDE_DECLARED_CONTRACT"
    answer_space = set(contract.answer_space)
    if primitive == "CHOICE" and (
        not isinstance(judgment.value, str) or judgment.value not in answer_space
    ):
        return "SCHEMA_FAILURE", "CHOICE_OUTSIDE_DECLARED_CONTRACT"
    if (
        primitive in {"CHOICE", "SCORE"}
        and judgment.distribution is not None
        and not set(judgment.distribution) <= answer_space
    ):
        return "SCHEMA_FAILURE", "DISTRIBUTION_OUTSIDE_DECLARED_CONTRACT"
    if primitive == "NOUL" and (
        not isinstance(judgment.value, (int, float))
        or isinstance(judgment.value, bool)
        or not 0 <= judgment.value <= 1
    ):
        return "SCHEMA_FAILURE", "NOUL_VALUE_OUTSIDE_CONTRACT"
    if primitive == "SCORE" and (
        not isinstance(judgment.value, (int, float))
        or isinstance(judgment.value, bool)
        or not any(_same_score(judgment.value, label) for label in answer_space)
    ):
        return "SCHEMA_FAILURE", "SCORE_VALUE_OUTSIDE_CONTRACT"
    return "ANSWERED", None


def _same_score(value: float, label: str) -> bool:
    try:
        return float(label) == float(value)
    except ValueError:
        return False


def _contract(case: CompiledBakeoffCase) -> Any:
    from experiments.decision_lab.contracts_vnext import DECISION_CONTRACTS

    return DECISION_CONTRACTS[case.contract_id]


def run_fixture_mode(
    *,
    evaluator: FixtureEvaluator,
    mode: HarnessMode,
    cases: tuple[CompiledBakeoffCase, ...] | None = None,
) -> dict[str, Any]:
    """Run only an explicitly supplied offline fixture adapter over answerable cases."""

    if getattr(evaluator, "execution_scope", None) != "OFFLINE_FIXTURE_ONLY":
        raise ValueError("EB-05 fixture runner accepts offline fixture adapters only")
    selected_cases = load_compiled_cases() if cases is None else cases
    inputs = tuple(_visible(case) for case in selected_cases)
    manifest_sha = _input_digest(inputs)
    rows = [_empty_judgment(case, "NOT_ANSWERABLE") for case in selected_cases]
    positions = {
        case.case_id: index
        for index, case in enumerate(selected_cases)
        if case.answerability_status == "ANSWERABLE"
    }
    eligible_cases = tuple(inputs[index] for index in positions.values())
    started = time.perf_counter()
    per_case_latency: dict[str, int] = {}
    per_case_failure: dict[str, str] = {}
    batch_latency: int | None = None
    paired: tuple[tuple[ProviderVisibleCase, NormalizedJudgment], ...] = ()
    if eligible_cases and mode is HarnessMode.BATCH:
        batch_started = time.perf_counter()
        try:
            judgments = evaluator.evaluate_batch(eligible_cases)
            if len(judgments) != len(eligible_cases):
                raise ValueError("batch result count does not match request count")
            paired = tuple(zip(eligible_cases, judgments, strict=True))
        except Exception as exc:  # safe category only; exception bodies may contain secrets
            category = failure_for_exception(exc).category
            per_case_failure.update({item.case_id: category for item in eligible_cases})
        batch_latency = max(0, round((time.perf_counter() - batch_started) * 1000))
    elif eligible_cases:
        singles: list[tuple[ProviderVisibleCase, NormalizedJudgment]] = []
        for item in eligible_cases:
            call_started = time.perf_counter()
            try:
                singles.append((item, evaluator.evaluate_one(item)))
            except Exception as exc:  # preserve per-call partial success safely
                per_case_failure[item.case_id] = failure_for_exception(exc).category
            per_case_latency[item.case_id] = max(
                0, round((time.perf_counter() - call_started) * 1000)
            )
        paired = tuple(singles)

    elapsed_ms = max(0, round((time.perf_counter() - started) * 1000))
    for case in selected_cases:
        category = per_case_failure.get(case.case_id)
        if category is not None:
            row = _empty_judgment(case, "FAILED")
            row["failure_category"] = category
            row["latency_ms"] = per_case_latency.get(case.case_id)
            row["latency_scope"] = "PER_CASE" if mode is HarnessMode.SINGLES else "BATCH_FAILURE"
            rows[positions[case.case_id]] = row
    for request, judgment in paired:
        case_index = positions[request.case_id]
        source_case = selected_cases[case_index]
        status, reason = _validated_judgment(source_case, judgment)
        row = _empty_judgment(source_case, status)
        row.update(
            {
                "judgment": judgment.to_dict() if status != "SCHEMA_FAILURE" else None,
                "failure_category": reason,
                "latency_ms": per_case_latency.get(request.case_id),
                "latency_scope": "PER_CASE" if mode is HarnessMode.SINGLES else "BATCH_AGGREGATE",
                "usage": judgment.usage,
            }
        )
        rows[case_index] = row

    metrics = _metrics(selected_cases, rows)
    payload: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "experiment_id": "EB-05-fixture-mechanics-v1",
        "data_mode": "SYNTHETIC_FIXTURE_ONLY_NOT_PROVIDER_EVIDENCE",
        "execution_scope": "OFFLINE_FIXTURE_ADAPTER_ONLY",
        "mode": mode.value,
        "evaluator": {
            "id": evaluator.evaluator_id,
            "version": evaluator.evaluator_version,
            "execution_scope": evaluator.execution_scope,
        },
        "input_manifest_sha256": manifest_sha,
        "request_identity": hashlib.sha256(
            f"EB-05-fixture-v1|{manifest_sha}|{evaluator.evaluator_id}|{evaluator.evaluator_version}|{mode.value}".encode()
        ).hexdigest(),
        "records": rows,
        "metrics": metrics,
        "execution": {
            "status": (
                "FAILED"
                if per_case_failure and not paired
                else "PARTIAL_FAILURE"
                if per_case_failure
                else "EXECUTED"
            ),
            "failure_categories": sorted(set(per_case_failure.values())),
            "elapsed_ms": elapsed_ms,
            "batch_elapsed_ms": batch_latency,
            "call_count": (
                1 if mode is HarnessMode.BATCH and eligible_cases else len(eligible_cases)
            ),
            "batch_fallback": "NOT_ATTEMPTED",
        },
        "live_provider_eligibility": live_eligibility(),
        "authority": "NO_POLICY_PROMOTION_NO_CANONICAL_WRITES",
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["result_id"] = hashlib.sha256(body.encode()).hexdigest()
    return payload


def compare_fixture_modes(
    *, evaluator: FixtureEvaluator, cases: tuple[CompiledBakeoffCase, ...] | None = None
) -> dict[str, Any]:
    singles = run_fixture_mode(evaluator=evaluator, mode=HarnessMode.SINGLES, cases=cases)
    batch = run_fixture_mode(evaluator=evaluator, mode=HarnessMode.BATCH, cases=cases)

    def by_id(result: dict[str, Any]) -> dict[str, Any]:
        return {item["case_id"]: item["judgment"] for item in result["records"]}

    single_results, batch_results = by_id(singles), by_id(batch)
    manifest_match = singles["input_manifest_sha256"] == batch["input_manifest_sha256"]
    return {
        "data_mode": "SYNTHETIC_FIXTURE_ONLY_NOT_PROVIDER_EVIDENCE",
        "same_inputs": manifest_match,
        "same_request_population": set(single_results) == set(batch_results),
        "outputs_equivalent": manifest_match and single_results == batch_results,
        "single_result_id": singles["result_id"],
        "batch_result_id": batch["result_id"],
        "single": singles,
        "batch": batch,
    }


def _metrics(cases: tuple[CompiledBakeoffCase, ...], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["case_id"]: row for row in rows}
    dimensions: dict[str, dict[str, Any]] = {}
    for case in cases:
        if case.answerability_status != "ANSWERABLE":
            continue
        dimension = dimensions.setdefault(
            case.contract_id,
            {"answerable": 0, "answered": 0, "scoreable": 0, "errors": 0, "severe_errors": 0},
        )
        dimension["answerable"] += 1
        row = by_id[case.case_id]
        judgment = row["judgment"]
        if row["status"] != "ANSWERED" or not isinstance(judgment, dict):
            continue
        dimension["answered"] += 1
        if judgment["primitive"] == "CHOICE" and case.expected_outcome is not None:
            dimension["scoreable"] += 1
            incorrect = judgment["value"] != case.expected_outcome
            dimension["errors"] += int(incorrect)
            severe = bool(set(case.tags) & {"contradictory", "wrong-entity-if-merged"})
            dimension["severe_errors"] += int(incorrect and severe)
    for values in dimensions.values():
        values["coverage"] = values["answered"] / values["answerable"]
        values["risk"] = values["errors"] / values["scoreable"] if values["scoreable"] else None
        values["risk_coverage_basis"] = "SCOREABLE_CHOICE_CASES_ONLY"
    answered_rows = [row for row in rows if row["status"] == "ANSWERED"]
    usage_rows = [row["usage"] for row in answered_rows]
    usage_known = bool(usage_rows) and all(isinstance(value, dict) for value in usage_rows)
    usage_totals: dict[str, int] = {}
    if usage_known:
        for usage in usage_rows:
            for key, value in usage.items():
                if (
                    not isinstance(key, str)
                    or not isinstance(value, int)
                    or isinstance(value, bool)
                    or value < 0
                ):
                    usage_known = False
                    usage_totals = {}
                    break
                usage_totals[key] = usage_totals.get(key, 0) + value
            if not usage_known:
                break
    return {
        "dimensions": dimensions,
        "abstentions": sum(row["status"] == "ABSTAINED" for row in rows),
        "failures": sum(row["status"] == "FAILED" for row in rows),
        "schema_failures": sum(row["status"] == "SCHEMA_FAILURE" for row in rows),
        "severe_errors": sum(value["severe_errors"] for value in dimensions.values()),
        "usage": (
            {"knowledge": "KNOWN", "counters": usage_totals}
            if usage_known
            else {"knowledge": "UNKNOWN", "counters": None}
        ),
        "cost": {"knowledge": "UNKNOWN", "amount_microunits": None, "currency": None},
        "calibration": "NOT_AVAILABLE_UNLESS_VALID_PROVIDER_DISTRIBUTION_EXISTS",
    }
