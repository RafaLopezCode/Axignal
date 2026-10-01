"""FR-22 governed evaluator bakeoff over the frozen AXIGNAL vNext corpus.

The runner executes only candidates that are actually governed/available. Blocked or
unavailable providers remain first-class rows with UNKNOWN cost; they are never
simulated and never replaced by marketing claims or fixture outputs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from experiments.decision_lab.compiler_vnext import compile_from_sources
from experiments.decision_lab.contracts_vnext import deterministic_entity_identifier_result
from experiments.decision_lab.experiment import manifest_digest
from experiments.decision_lab.metrics import classification_metrics

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = ROOT / "experiments" / "decision_lab" / "corpus" / "vnext" / "cases.json"

FAMILY_CONTRACT = {
    "CLAIM_EVIDENCE_SUPPORT": "CES.SUPPORT.vNext",
    "ENTITY_ALIGNMENT": "ENT.ALIGN.vNext",
    "ECONOMIC_RELATIONSHIP": "REL.EXISTENCE.vNext",
}


class CandidateExecutionStatus(StrEnum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class CostKnowledge(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    status: CandidateExecutionStatus
    reason_code: str
    evidence_ref: str
    cost_knowledge: CostKnowledge
    amount_microunits: int | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.candidate_id, self.reason_code, self.evidence_ref)
        ):
            raise ValueError("bakeoff candidate identity/provenance is required")
        if self.cost_knowledge is CostKnowledge.KNOWN:
            if self.amount_microunits is None or self.amount_microunits < 0:
                raise ValueError("known cost requires non-negative amount")
            if self.currency is None or not self.currency.strip():
                raise ValueError("known cost requires currency")
        elif self.amount_microunits is not None or self.currency is not None:
            raise ValueError("unknown/not-applicable cost cannot carry a fabricated amount")


@dataclass(frozen=True)
class CompiledBakeoffCase:
    case_id: str
    family: str
    contract_id: str
    state_contract_version: str
    compiler_version: str
    state_fingerprint: str
    answerability_status: str
    expected_outcome: str | None
    label_provenance: str
    tags: tuple[str, ...]
    provider_state: dict[str, Any]


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_compiled_cases(path: Path = DEFAULT_CORPUS) -> tuple[CompiledBakeoffCase, ...]:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("cases")
    if not isinstance(rows, list):
        raise ValueError("FR-22 corpus cases are missing")

    compiled_cases: list[CompiledBakeoffCase] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("FR-22 corpus case must be an object")
        family = str(row["family"])
        contract_id = FAMILY_CONTRACT.get(family)
        if contract_id is None:
            raise ValueError(f"FR-22 has no contract mapping for family {family!r}")
        source_state = row["state"]
        evidence_catalog = row["evidence_catalog"]
        if not isinstance(source_state, dict) or not isinstance(evidence_catalog, dict):
            raise ValueError("FR-22 case state/evidence catalog must be objects")
        compiled = compile_from_sources(contract_id, source_state, evidence_catalog)
        expected_answerability = str(row["expected_answerability"])
        if compiled.answerability.status != expected_answerability:
            raise ValueError(
                f"FR-22 corpus answerability drift for {row['case_id']}: "
                f"{compiled.answerability.status} != {expected_answerability}"
            )
        compiled_cases.append(
            CompiledBakeoffCase(
                case_id=str(row["case_id"]),
                family=family,
                contract_id=contract_id,
                state_contract_version=compiled.state_contract_version,
                compiler_version=compiled.compiler_version,
                state_fingerprint=compiled.fingerprint,
                answerability_status=compiled.answerability.status,
                expected_outcome=(
                    None if row.get("expected_outcome") is None else str(row["expected_outcome"])
                ),
                label_provenance=str(row["label_provenance"]),
                tags=tuple(str(tag) for tag in row.get("tags", ())),
                provider_state=compiled.payload,
            )
        )
    return tuple(compiled_cases)


def frozen_input_manifest(cases: tuple[CompiledBakeoffCase, ...]) -> dict[str, Any]:
    rows = [
        {
            "case_id": case.case_id,
            "family": case.family,
            "contract_id": case.contract_id,
            "state_contract_version": case.state_contract_version,
            "compiler_version": case.compiler_version,
            "state_fingerprint": case.state_fingerprint,
            "answerability_status": case.answerability_status,
        }
        for case in cases
    ]
    return {
        "corpus_ref": "experiments/decision_lab/corpus/vnext/cases.json@vNext.1",
        "case_count": len(rows),
        "cases": rows,
        "manifest_sha256": _digest(rows),
        "provider_view_rule": (
            "provider receives compiled state/contracts only; expected_outcome, "
            "label_provenance and evaluator-only notes are excluded"
        ),
    }


def default_candidates() -> tuple[CandidateSpec, ...]:
    return (
        CandidateSpec(
            candidate_id="deterministic-baseline",
            status=CandidateExecutionStatus.EXECUTED,
            reason_code="LOCAL_DETERMINISTIC_RULES_ONLY",
            evidence_ref="ADR-0024; experiments/decision_lab/contracts_vnext.py",
            cost_knowledge=CostKnowledge.NOT_APPLICABLE,
        ),
        CandidateSpec(
            candidate_id="luna-structured",
            status=CandidateExecutionStatus.UNAVAILABLE,
            reason_code="NO_GOVERNED_API_ADAPTER_OR_AUTHORIZED_MODEL_BINDING",
            evidence_ref="FR-22 execution preflight 2026-10-01",
            cost_knowledge=CostKnowledge.UNKNOWN,
        ),
        CandidateSpec(
            candidate_id="openai-decisions",
            status=CandidateExecutionStatus.UNAVAILABLE,
            reason_code="ACCESS_AND_API_TERMS_NOT_ESTABLISHED",
            evidence_ref="FR-22 execution preflight 2026-10-01",
            cost_knowledge=CostKnowledge.UNKNOWN,
        ),
        CandidateSpec(
            candidate_id="typesafe-jev",
            status=CandidateExecutionStatus.BLOCKED,
            reason_code="P0_JEV_04A_BLOCKED_NO_VALID_CORPUS",
            evidence_ref="GitHub PR #18 research/p0-jev-04a-golden-corpus-authority",
            cost_knowledge=CostKnowledge.UNKNOWN,
        ),
    )


def _deterministic_prediction(case: CompiledBakeoffCase) -> tuple[str | None, str]:
    if case.answerability_status != "ANSWERABLE":
        return None, "ABSTAIN_NOT_ANSWERABLE"
    if case.family == "ENTITY_ALIGNMENT":
        result = deterministic_entity_identifier_result(case.provider_state)
        if result is not None:
            return result, "DETERMINISTIC_VERIFIED_IDENTIFIER"
    return None, "ABSTAIN_NO_APPLICABLE_DETERMINISTIC_RULE"


def _deterministic_records(
    cases: tuple[CompiledBakeoffCase, ...],
) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for case in cases:
        selected, reason = _deterministic_prediction(case)
        records.append(
            {
                "case_id": case.case_id,
                "state_fingerprint": case.state_fingerprint,
                "answerability_status": case.answerability_status,
                "selected_option": selected,
                "reason_code": reason,
                "distribution_availability": "UNAVAILABLE",
                "distribution": None,
                "confidence_semantics": "UNAVAILABLE",
                "confidence": None,
                "schema_failure": False,
                "latency_ms": None,
                "retries": 0,
                "cost_knowledge": CostKnowledge.NOT_APPLICABLE.value,
                "amount_microunits": None,
                "currency": None,
            }
        )
    return tuple(records)


def _candidate_metrics(
    spec: CandidateSpec,
    cases: tuple[CompiledBakeoffCase, ...],
    records: tuple[dict[str, Any], ...] | None,
) -> dict[str, Any]:
    if spec.status is not CandidateExecutionStatus.EXECUTED:
        return {
            "status": spec.status.value,
            "reason_code": spec.reason_code,
            "class_errors": "NOT_MEASURED",
            "false_observed_potential": "NOT_MEASURED",
            "coverage": "NOT_MEASURED",
            "abstention": "NOT_MEASURED",
            "calibration": "NOT_MEASURED",
            "schema_failures": "NOT_MEASURED",
            "latency_ms": "UNKNOWN",
            "retries": "NOT_MEASURED",
            "cost": {
                "knowledge": spec.cost_knowledge.value,
                "amount_microunits": None,
                "currency": None,
            },
            "language_context_sensitivity": "NOT_MEASURED",
        }

    assert records is not None
    answerable = [case for case in cases if case.answerability_status == "ANSWERABLE"]
    record_by_id = {str(record["case_id"]): record for record in records}
    answered = [
        case for case in answerable if record_by_id[case.case_id]["selected_option"] is not None
    ]
    scoreable_answered = [case for case in answered if case.expected_outcome is not None]
    expected = [str(case.expected_outcome) for case in scoreable_answered]
    predicted = [str(record_by_id[case.case_id]["selected_option"]) for case in scoreable_answered]
    classification = classification_metrics(expected, predicted)
    class_errors = (
        None
        if classification["n"] == 0
        else classification["n"]
        - sum(
            classification["confusion_matrix"][label][label]
            for label in classification["confusion_matrix"]
        )
    )
    return {
        "status": spec.status.value,
        "reason_code": spec.reason_code,
        "answerable_cases": len(answerable),
        "answered_cases": len(answered),
        "scoreable_answered_cases": len(scoreable_answered),
        "class_errors": class_errors,
        "classification": classification,
        "false_observed_potential": ("NOT_APPLICABLE_NO_OBSERVED_POTENTIAL_PROJECTION_IN_FR22_LAB"),
        "coverage": len(answered) / len(answerable) if answerable else None,
        "abstention": len(answerable) - len(answered),
        "calibration": "NOT_AVAILABLE_NO_PROVIDER_DISTRIBUTION",
        "schema_failures": sum(bool(record["schema_failure"]) for record in records),
        "latency_ms": "UNKNOWN_NOT_INSTRUMENTED_FOR_LOCAL_DETERMINISTIC_RULE",
        "retries": sum(int(record["retries"]) for record in records),
        "cost": {
            "knowledge": spec.cost_knowledge.value,
            "amount_microunits": spec.amount_microunits,
            "currency": spec.currency,
        },
        "language_context_sensitivity": "NOT_MEASURED_NO_PAIRED_VARIANTS",
    }


def build_bakeoff_artifact(
    *,
    corpus_path: Path = DEFAULT_CORPUS,
    candidates: tuple[CandidateSpec, ...] | None = None,
) -> dict[str, Any]:
    cases = load_compiled_cases(corpus_path)
    manifest = frozen_input_manifest(cases)
    specs = default_candidates() if candidates is None else candidates
    candidate_rows: list[dict[str, Any]] = []

    for spec in specs:
        records = (
            _deterministic_records(cases)
            if spec.candidate_id == "deterministic-baseline"
            and spec.status is CandidateExecutionStatus.EXECUTED
            else None
        )
        candidate_rows.append(
            {
                "candidate": asdict(spec),
                "input_manifest_sha256": manifest["manifest_sha256"],
                "records": records,
                "metrics": _candidate_metrics(spec, cases, records),
            }
        )

    executed = [
        row
        for row in candidate_rows
        if row["candidate"]["status"] == CandidateExecutionStatus.EXECUTED.value
    ]
    provider_executed = [
        row for row in executed if row["candidate"]["candidate_id"] != "deterministic-baseline"
    ]
    payload: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "experiment_id": "FR-22-evaluator-decision-lab-bakeoff-v1",
        "data_mode": "SYNTHETIC_AXIGNAL_STRUCTURAL_FIXTURES",
        "frozen_input_manifest": manifest,
        "candidates": candidate_rows,
        "same_input_contract": len({str(row["input_manifest_sha256"]) for row in candidate_rows})
        == 1,
        "provider_quality_claim": (
            "NOT_ESTABLISHED"
            if not provider_executed
            else "DESCRIPTIVE_ONLY_REQUIRES_GOVERNED_DATASET_REVIEW"
        ),
        "winner_status": "NOT_DECLARED",
        "winner_reason": (
            "INSUFFICIENT_COMPARABLE_PROVIDER_EVIDENCE; blocked/unavailable candidates "
            "are not simulated and synthetic fixtures are not statistical evidence"
        ),
        "disagreement_error_correlation": (
            "NOT_AVAILABLE_FEWER_THAN_TWO_EXECUTED_PROVIDER_EVALUATORS"
        ),
        "calibration_rule": ("CALCULATE_ONLY_WHEN_REAL_PROVIDER_DISTRIBUTION_HAS_VALID_SEMANTICS"),
        "cost_rule": "MISSING_OR_UNMEASURED_COST_REMAINS_UNKNOWN_NEVER_ZERO",
        "authority": (
            "EXPERIMENTAL_ONLY; no policy promotion, EvidenceAdmission or AXIGLAND write"
        ),
        "limitations": [
            "The vNext corpus is synthetic structural evidence, not real-world model-quality evidence.",
            "TypeSafe Jev is blocked by P0-JEV-04A authority/rights gates in open PR #18.",
            "Luna structured has no governed adapter/authorized model binding in this repository.",
            "OpenAI Decisions access and API terms are not established in this repository.",
            "No vendor ranking or winner is authorized from this artifact.",
        ],
    }
    normalized = json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    normalized["result_id"] = manifest_digest(dict(normalized))
    return normalized
