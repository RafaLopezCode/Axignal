"""Offline, synthetic-only invariants for the P0-JEV-02 laboratory."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from experiments.decision_lab.artifacts import read_result, write_result
from experiments.decision_lab.cli import ROOT, main, validate
from experiments.decision_lab.evaluator import RecordedEvaluator, failure_for_exception
from experiments.decision_lab.experiment import estimate_budget
from experiments.decision_lab.judgments import compose_support, normalize_judgment
from experiments.decision_lab.metrics import (
    calibration_metrics,
    classification_metrics,
    detect_critical_regressions,
)
from experiments.decision_lab.models import LabError
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator
from experiments.decision_lab.state import compile_state
from experiments.decision_lab.validation import validate_corpus, validate_grammar


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_committed_corpus_grammar_and_experiments_validate() -> None:
    corpus_count, question_count, experiment_count = validate()
    assert corpus_count == 42
    assert question_count >= 10
    assert experiment_count == 3
    assert main(["validate"]) == 0


def test_corpus_labels_have_independent_synthetic_authority() -> None:
    corpus = _load("corpus/v0.1/cases.json")
    cases = validate_corpus(corpus)
    assert all(case["label_authority"] == "SYNTHETIC_CONSTRUCTION" for case in cases)
    assert all(case["privacy_class"] == "SYNTHETIC" for case in cases)
    assert all(
        case["expected_outcome"] is None
        for case in cases
        if case["label_status"]
        in {"AMBIGUOUS_BY_DESIGN", "CONTRADICTORY_BY_DESIGN", "NO_EXPECTED_SINGLE_ANSWER"}
    )


def test_model_output_cannot_become_label_authority() -> None:
    corpus = _load("corpus/v0.1/cases.json")
    corpus["cases"][0]["label_authority"] = "JEV"
    with pytest.raises(LabError, match="label authority"):
        validate_corpus(corpus)


def test_duplicate_case_identity_rejected() -> None:
    corpus = _load("corpus/v0.1/cases.json")
    corpus["cases"][1]["case_id"] = corpus["cases"][0]["case_id"]
    with pytest.raises(LabError, match="unique"):
        validate_corpus(corpus)


def test_question_content_is_locked_to_version() -> None:
    grammar = _load("grammar/v0.1/grammar.json")
    lock = _load("grammar/v0.1/question-lock.json")
    assert len(validate_grammar(grammar, lock)) >= 10
    grammar["questions"][0]["instructions"] += " Changed in place."
    with pytest.raises(LabError, match="content changed"):
        validate_grammar(grammar, lock)


def test_same_state_has_same_fingerprint_and_semantic_change_changes_it() -> None:
    first = compile_state({"candidate": {"id": "SYN-1"}, "evidence": ["x"]})
    second = compile_state({"evidence": ["x"], "candidate": {"id": "SYN-1"}})
    changed = compile_state({"candidate": {"id": "SYN-1"}, "evidence": ["y"]})
    assert first.canonical_json == second.canonical_json
    assert first.fingerprint == second.fingerprint
    assert first.fingerprint != changed.fingerprint
    exposed = first.payload
    exposed["candidate"]["id"] = "MUTATED"
    assert first.payload["candidate"]["id"] == "SYN-1"


@pytest.mark.parametrize("field", ["api_key", "request_id", "trace_id"])
def test_state_excludes_secret_or_volatile_metadata(field: str) -> None:
    with pytest.raises(ValueError, match="forbidden"):
        compile_state({field: "not retained"})


def test_state_rejects_non_finite_numbers() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        compile_state({"value": float("nan")})


def test_missing_false_and_zero_remain_distinct() -> None:
    missing = normalize_judgment("q", "NOUL", {}, evaluator="fixture")
    false_value = normalize_judgment("q", "CHOICE", {"selected": "NO"}, evaluator="fixture")
    zero = normalize_judgment("q", "SCORE", {"value": 0}, evaluator="fixture")
    assert missing.status == "MISSING" and missing.value is None
    assert false_value.status == "ANSWERED" and false_value.value == "NO"
    assert zero.status == "ANSWERED" and zero.value == 0


def test_choice_score_and_noul_normalization_preserves_raw_typed_values() -> None:
    choice = normalize_judgment(
        "c",
        "CHOICE",
        {"selected": "A", "distribution": {"A": 0.7, "B": 0.3}, "confidence": 0.7},
        evaluator="fixture",
    )
    score = normalize_judgment(
        "s",
        "SCORE",
        {
            "value": 2,
            "distribution": {"1": 0.2, "2": 0.8},
            "confidence": 0.8,
            "legend": {1: "weak", 2: "strong"},
        },
        evaluator="fixture",
    )
    noul = normalize_judgment("n", "NOUL", {"probability_yes": 0.41}, evaluator="fixture")
    assert choice.value == "A" and choice.distribution == {"A": 0.7, "B": 0.3}
    assert score.value == 2 and score.confidence == 0.8
    assert score.legend == {"1": "weak", "2": "strong"}
    assert noul.value == 0.41 and noul.confidence is None
    assert compose_support(noul)["outcome"] == {"probability_yes": 0.41}


def test_malformed_answer_and_unknown_metadata_remain_nonsemantic() -> None:
    judgment = normalize_judgment(
        "q", "NOUL", {"probability_yes": 1.5}, evaluator="unknown", resolved_model=None
    )
    assert judgment.status == "MALFORMED"
    assert judgment.resolved_model is None
    assert compose_support(judgment)["outcome"] is None


def test_failure_is_not_composed_as_negative_and_text_is_not_retained() -> None:
    class AuthenticationError(Exception):
        pass

    failure = failure_for_exception(AuthenticationError("secret body must not persist"))
    assert failure.category == "AUTHENTICATION"
    assert "secret" not in repr(failure)


def test_recorded_fixture_replay_is_explicitly_not_jev() -> None:
    fixture = _load("fixtures/recorded/contract-fixture.json")
    evaluator = RecordedEvaluator({fixture["question_id"]: fixture["answer"]})
    rows = evaluator.evaluate({}, {fixture["question_id"]: fixture["primitive"]}, "fixture-only")
    assert rows[0].evaluator == "recorded-fixture"
    assert rows[0].requested_model == "fixture-only"
    assert rows[0].usage is None


def test_experiment_budget_preflight_enforces_request_question_and_state_limits() -> None:
    plan = _load("experiments/v0.1/claim-wording-ab.json")
    states = [{"candidate": "x"} for _ in plan["case_ids"]]
    estimate = estimate_budget(plan, states)
    assert estimate["expected_request_count"] == 10
    assert estimate["expected_question_count"] == 10
    plan["budget"]["max_requests"] = 1
    with pytest.raises(LabError, match="exceeds"):
        estimate_budget(plan, states)


def test_live_cli_requires_explicit_flag_and_key_absence_does_not_call_provider(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert (
        main(["run", "--experiment", "claim-wording-ab", "--output", str(tmp_path / "r.json")]) == 2
    )
    assert (
        main(
            [
                "run",
                "--experiment",
                "claim-wording-ab",
                "--live",
                "--output",
                str(tmp_path / "r.json"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "r.json").exists()


def test_typesafe_adapter_pins_model_disables_retries_and_preserves_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict = {}

    class FakeClient:
        def __init__(self, **kwargs):
            observed["client"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, **kwargs):
            observed["request"] = kwargs
            answer = SimpleNamespace(
                choice="SUPPORTED", probabilities={"SUPPORTED": 0.9}, confidence=0.9
            )
            return SimpleNamespace(
                choices={"CES.SUPPORT.v1": answer},
                model="jev-1.13.0",
                usage=SimpleNamespace(input_tokens=21, output_tokens=0, total_tokens=21),
            )

    fake = ModuleType("typesafe_sdk")
    fake.Choice = lambda **kwargs: kwargs
    fake.Noul = lambda **kwargs: kwargs
    fake.Score = lambda **kwargs: kwargs
    fake.RetryPolicy = lambda **kwargs: SimpleNamespace(**kwargs)
    fake.TypeSafeClient = FakeClient
    monkeypatch.setitem(sys.modules, "typesafe_sdk", fake)
    monkeypatch.setenv("TYPESAFE_API_KEY", "unit-test-secret")
    evaluator = TypeSafeLabEvaluator()
    question = {
        "question_id": "CES.SUPPORT.v1",
        "primitive": "CHOICE",
        "instructions": "Synthetic contract test",
        "criteria": {"SUPPORTED": None, "NO": None},
    }
    judgments, failure, metadata = evaluator.evaluate({"synthetic": True}, [question])
    assert failure is None
    assert metadata["resolved_model"] == "jev-1.13.0"
    assert metadata["usage"] == {"input_tokens": 21, "output_tokens": 0, "total_tokens": 21}
    assert metadata["sdk_version"] == "0.7.1"
    assert metadata["latency_seconds"] >= 0
    assert judgments[0].value == "SUPPORTED"
    assert judgments[0].usage == {"input_tokens": 21, "output_tokens": 0, "total_tokens": 21}
    assert observed["client"]["timeout"] == 30
    assert observed["request"]["model"] == "jev-1.13.0"
    assert observed["request"]["retry"].max_retries == 0
    assert "unit-test-secret" not in repr(judgments)


def test_result_artifact_is_create_only_and_readable(tmp_path: Path) -> None:
    path = tmp_path / "results" / "one.json"
    payload = {"artifact_type": "decision-lab-result", "result_id": "fixed"}
    write_result(path, payload)
    assert read_result(path) == payload
    with pytest.raises(FileExistsError):
        write_result(path, payload)


def test_metrics_are_class_scoped_and_calibration_unvalidated() -> None:
    metrics = classification_metrics(["yes", "no", "yes"], ["yes", "yes", "yes"])
    assert metrics["n"] == 3
    assert metrics["accuracy"] == pytest.approx(2 / 3)
    assert metrics["confusion_matrix"]["no"]["yes"] == 1
    assert metrics["calibration_status"] == "NOT_VALIDATED"
    calibration = calibration_metrics([0.9, 0.1], [True, False])
    assert calibration["brier_score"] == pytest.approx(0.01)
    assert calibration["status"] == "INFRASTRUCTURE_ONLY_NOT_VALIDATED"


def test_critical_regression_remains_visible_despite_aggregate_metrics() -> None:
    regressions = detect_critical_regressions(
        {"safe": "DISTINCT"}, {"safe": "SAME_ENTITY"}, {"safe"}
    )
    assert regressions == ["safe"]


def test_comparison_detects_case_level_critical_regression() -> None:
    from experiments.decision_lab.comparison import compare_records

    baseline = {
        "result_id": "a",
        "records": [
            {"case_id": "ENT-03", "variant_id": "v1", "compositions": [{"outcome": "DISTINCT"}]}
        ],
    }
    candidate = {
        "result_id": "b",
        "records": [
            {"case_id": "ENT-03", "variant_id": "v1", "compositions": [{"outcome": "SAME_ENTITY"}]}
        ],
    }
    comparison = compare_records(baseline, candidate, {"ENT-03"})
    assert comparison["critical_regressions"] == ["ENT-03::v1::1"]


def test_recorded_result_replay_recomposes_without_provider(tmp_path: Path) -> None:
    from experiments.decision_lab.judgments import normalize_judgment

    source = tmp_path / "source.json"
    output = tmp_path / "replayed.json"
    fixture = _load("fixtures/recorded/contract-fixture.json")
    judgment = normalize_judgment(
        fixture["question_id"],
        fixture["primitive"],
        fixture["answer"],
        evaluator="contract-fixture",
    )
    write_result(
        source,
        {
            "artifact_type": "decision-lab-result",
            "result_id": "source-id",
            "data_mode": "RECORDED_FIXTURE_NOT_OBSERVATION",
            "judgments": [judgment.to_dict()],
        },
    )
    assert main(["replay", "--result", str(source), "--output", str(output)]) == 0
    result = read_result(output)
    assert result["data_mode"] == "RECORDED_RESULT_REPLAY_NO_PROVIDER_CALL"
    assert result["records"][0]["judgments"][0]["value"] == "PARTIAL"


def test_no_grammar_self_promotion_or_cache_claim() -> None:
    grammar = _load("grammar/v0.1/grammar.json")
    assert all(
        item["experimental_status"] == "EXPERIMENTAL_CANDIDATE" for item in grammar["questions"]
    )
    assert not any(
        "cache" in path.name.lower() for path in (ROOT / "experiments/v0.1").glob("*.json")
    )
