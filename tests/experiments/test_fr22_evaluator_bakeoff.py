from __future__ import annotations

import json
from pathlib import Path

from experiments.decision_lab.artifacts import read_result, write_result
from experiments.decision_lab.bakeoff_vnext import (
    CandidateExecutionStatus,
    CostKnowledge,
    build_bakeoff_artifact,
    default_candidates,
    frozen_input_manifest,
    load_compiled_cases,
)


def test_fr22_compiles_same_frozen_inputs_for_every_candidate() -> None:
    cases = load_compiled_cases()
    manifest = frozen_input_manifest(cases)
    artifact = build_bakeoff_artifact()

    assert manifest["case_count"] == 14
    assert artifact["same_input_contract"] is True
    assert {row["input_manifest_sha256"] for row in artifact["candidates"]} == {
        manifest["manifest_sha256"]
    }


def test_fr22_provider_state_excludes_evaluator_only_labels() -> None:
    cases = load_compiled_cases()

    for case in cases:
        serialized = json.dumps(case.provider_state, sort_keys=True)
        assert "expected_outcome" not in serialized
        assert "label_provenance" not in serialized
        assert "DETERMINISTIC_GROUND_TRUTH" not in serialized


def test_fr22_preflight_blocks_or_marks_unavailable_instead_of_simulating_providers() -> None:
    candidates = {item.candidate_id: item for item in default_candidates()}

    assert candidates["deterministic-baseline"].status is CandidateExecutionStatus.EXECUTED
    assert candidates["typesafe-jev"].status is CandidateExecutionStatus.BLOCKED
    assert candidates["typesafe-jev"].reason_code == "P0_JEV_04A_BLOCKED_NO_VALID_CORPUS"
    assert candidates["luna-structured"].status is CandidateExecutionStatus.UNAVAILABLE
    assert candidates["openai-decisions"].status is CandidateExecutionStatus.UNAVAILABLE


def test_fr22_unknown_provider_cost_never_becomes_zero() -> None:
    candidates = default_candidates()

    for candidate in candidates:
        if candidate.cost_knowledge is CostKnowledge.UNKNOWN:
            assert candidate.amount_microunits is None
            assert candidate.currency is None

    artifact = build_bakeoff_artifact()
    for row in artifact["candidates"]:
        cost = row["metrics"]["cost"]
        if cost["knowledge"] == CostKnowledge.UNKNOWN.value:
            assert cost["amount_microunits"] is None
            assert cost["currency"] is None


def test_fr22_has_no_vendor_winner_without_comparable_provider_evidence() -> None:
    artifact = build_bakeoff_artifact()

    assert artifact["winner_status"] == "NOT_DECLARED"
    assert artifact["provider_quality_claim"] == "NOT_ESTABLISHED"
    assert (
        artifact["disagreement_error_correlation"]
        == "NOT_AVAILABLE_FEWER_THAN_TWO_EXECUTED_PROVIDER_EVALUATORS"
    )


def test_fr22_deterministic_baseline_abstains_when_no_deterministic_rule_applies() -> None:
    artifact = build_bakeoff_artifact()
    baseline = next(
        row
        for row in artifact["candidates"]
        if row["candidate"]["candidate_id"] == "deterministic-baseline"
    )

    assert baseline["metrics"]["status"] == "EXECUTED"
    assert baseline["metrics"]["answered_cases"] == 0
    assert baseline["metrics"]["coverage"] == 0
    assert baseline["metrics"]["abstention"] > 0
    assert baseline["metrics"]["calibration"] == "NOT_AVAILABLE_NO_PROVIDER_DISTRIBUTION"


def test_fr22_artifact_round_trips_with_immutable_digest(tmp_path: Path) -> None:
    artifact = build_bakeoff_artifact()
    path = tmp_path / "fr22.json"

    write_result(path, artifact)
    loaded = read_result(path)

    assert loaded["result_id"] == artifact["result_id"]
    assert loaded["frozen_input_manifest"] == artifact["frozen_input_manifest"]
    assert loaded["winner_status"] == "NOT_DECLARED"


def test_fr22_metrics_surface_every_predeclared_measurement_family() -> None:
    artifact = build_bakeoff_artifact()
    baseline = next(
        row
        for row in artifact["candidates"]
        if row["candidate"]["candidate_id"] == "deterministic-baseline"
    )
    metrics = baseline["metrics"]

    for key in (
        "class_errors",
        "false_observed_potential",
        "coverage",
        "abstention",
        "calibration",
        "schema_failures",
        "latency_ms",
        "retries",
        "cost",
        "language_context_sensitivity",
    ):
        assert key in metrics
    assert "disagreement_error_correlation" in artifact


def test_fr22_runner_does_not_import_or_simulate_provider_sdks() -> None:
    source = (
        (Path(__file__).resolve().parents[2] / "experiments" / "decision_lab" / "bakeoff_vnext.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    for forbidden in ("typesafe_sdk", "openai import", "requests.", "httpx.", "urllib.request"):
        assert forbidden not in source


def test_fr22_tracked_artifact_matches_current_deterministic_runner() -> None:
    root = Path(__file__).resolve().parents[2]
    tracked = read_result(
        root / "experiments" / "decision_lab" / "artifacts" / "fr22-evaluator-bakeoff-v1.json"
    )
    regenerated = build_bakeoff_artifact()

    assert tracked == regenerated
