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
from experiments.decision_lab.experiment import estimate_budget, manifest_digest
from experiments.decision_lab.judgments import (
    compose_relationship_decomposition,
    compose_support,
    normalize_judgment,
)
from experiments.decision_lab.metrics import (
    calibration_metrics,
    classification_metrics,
    detect_critical_regressions,
)
from experiments.decision_lab.models import LabError
from experiments.decision_lab.outcomes import evaluate_experiment_outcome, object_digest
from experiments.decision_lab.pricing import estimate_cost_from_usage, load_pricing_policy
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator
from experiments.decision_lab.state import apply_state_variant, compile_state
from experiments.decision_lab.validation import (
    validate_corpus,
    validate_experiment,
    validate_grammar,
)


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
    assert estimate["preflight_request_bytes"] > 0
    assert estimate["preflight_token_count"] == "UNKNOWN"
    assert estimate["preflight_monetary_cost"] == "UNKNOWN"
    assert "input_token_upper_bound" not in estimate
    assert "estimated_cost_usd" not in estimate
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
    judgments, failure, metadata = evaluator.evaluate(
        {"synthetic": True}, [question], model="jev-1.13.0"
    )
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
    payload = {"artifact_type": "decision-lab-result", "result_id": ""}
    payload["result_id"] = manifest_digest(
        {key: value for key, value in payload.items() if key != "result_id"}
    )
    write_result(path, payload)
    assert read_result(path) == payload
    with pytest.raises(FileExistsError):
        write_result(path, payload)


def test_completed_result_rejects_changed_predeclared_criteria(tmp_path: Path) -> None:
    path = tmp_path / "criteria.json"
    criteria = {"minimum_effect": 0.1, "minimum_answered_cases": 3}
    payload = {
        "artifact_type": "decision-lab-result",
        "result_id": "",
        "predeclared_evaluation_criteria": criteria,
        "evaluation_criteria_sha256": object_digest(criteria),
    }
    payload["result_id"] = manifest_digest(
        {key: value for key, value in payload.items() if key != "result_id"}
    )
    write_result(path, payload)
    assert read_result(path)["predeclared_evaluation_criteria"] == criteria
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["predeclared_evaluation_criteria"]["minimum_effect"] = 0.01
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(LabError, match="digest"):
        read_result(path)


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
            "result_id": "",
            "data_mode": "RECORDED_FIXTURE_NOT_OBSERVATION",
            "judgments": [judgment.to_dict()],
        },
    )
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    source_payload["result_id"] = manifest_digest(
        {key: value for key, value in source_payload.items() if key != "result_id"}
    )
    source.write_text(json.dumps(source_payload), encoding="utf-8")
    assert main(["replay", "--result", str(source), "--output", str(output)]) == 0
    result = read_result(output)
    assert result["data_mode"] == "RECORDED_RESULT_REPLAY_NO_PROVIDER_CALL"
    assert result["records"][0]["judgments"][0]["value"] == "PARTIAL"


def test_fixture_replay_result_digest_is_valid(tmp_path: Path) -> None:
    output = tmp_path / "fixture-replay.json"
    fixture = ROOT / "fixtures/recorded/contract-fixture.json"
    assert main(["replay", "--fixture", str(fixture), "--output", str(output)]) == 0
    assert read_result(output)["data_mode"] == "RECORDED_FIXTURE_NOT_OBSERVATION"


def test_no_grammar_self_promotion_or_cache_claim() -> None:
    grammar = _load("grammar/v0.1/grammar.json")
    assert all(
        item["experimental_status"] == "EXPERIMENTAL_CANDIDATE" for item in grammar["questions"]
    )
    assert not any(
        "cache" in path.name.lower() for path in (ROOT / "experiments/v0.1").glob("*.json")
    )


def _definition(name: str) -> tuple[dict, dict[str, dict]]:
    definition = _load(f"experiments/v0.1/{name}.json")
    grammar = _load("grammar/v0.1/grammar.json")
    return definition, {item["question_id"]: item for item in grammar["questions"]}


def test_question_wording_rejects_state_variant_drift() -> None:
    definition, grammar = _definition("claim-wording-ab")
    definition["variants"][1]["state_variant"] = "full_context"
    with pytest.raises(LabError, match="state or model"):
        validate_experiment(definition, grammar)


def test_question_wording_rejects_primitive_drift() -> None:
    definition, grammar = _definition("claim-wording-ab")
    grammar["CES.SUPPORT.v2"]["primitive"] = "SCORE"
    with pytest.raises(LabError, match="primitive"):
        validate_experiment(definition, grammar)


def test_state_ablation_rejects_question_version_drift() -> None:
    definition, grammar = _definition("minimal-state-ablation")
    definition["variants"][1]["question_ids"] = ["CES.SUPPORT.v2"]
    with pytest.raises(LabError, match="question versions"):
        validate_experiment(definition, grammar)


def test_atomic_decomposition_rejects_state_variant_drift() -> None:
    definition, grammar = _definition("relationship-atomic-decomposition")
    definition["variants"][1]["state_variant"] = "full_context"
    with pytest.raises(LabError, match="state and model"):
        validate_experiment(definition, grammar)


def test_model_comparison_and_repeatability_contracts_are_supported() -> None:
    definition, grammar = _definition("claim-wording-ab")
    base_variant = definition["variants"][0]
    model_comparison = json.loads(json.dumps(definition))
    model_comparison["experiment_type"] = "MODEL_COMPARISON"
    model_comparison["independent_variable"] = "requested_model"
    model_comparison["controlled_dimensions"] = [
        "case_ids",
        "question_versions",
        "state_variant",
        "repetitions",
        "policy_version",
        "budget",
    ]
    model_comparison["variants"] = [
        {**base_variant, "variant_id": "m1", "requested_model": "jev-1.13.0"},
        {**base_variant, "variant_id": "m2", "requested_model": "jev-1.12.0"},
    ]
    validate_experiment(model_comparison, grammar)

    repeatability = json.loads(json.dumps(definition))
    repeatability["experiment_type"] = "REPEATABILITY"
    repeatability["independent_variable"] = "repetition_count"
    repeatability["controlled_dimensions"] = [
        "case_ids",
        "question_versions",
        "state_variant",
        "requested_model",
        "policy_version",
        "budget",
    ]
    repeatability["variants"] = [base_variant]
    repeatability["repetitions"] = 3
    validate_experiment(repeatability, grammar)


def test_unknown_state_variant_fails_closed_and_ablation_is_deterministic() -> None:
    state = {
        "candidate": {"id": "SYN-1"},
        "temporal_context": {"status": "known"},
        "provenance": {"seed": "x"},
    }
    first, version = apply_state_variant(state, "minimal")
    second, second_version = apply_state_variant(state, "minimal")
    assert first == second
    assert version == second_version == "0.1.0"
    assert "temporal_context" not in first and "provenance" not in first
    assert compile_state(first).fingerprint == compile_state(second).fingerprint
    with pytest.raises(LabError, match="unknown state variant"):
        apply_state_variant(state, "silent-fallthrough")


def test_relationship_atomic_composer_produces_comparable_and_unresolved_states() -> None:
    atomic = [
        normalize_judgment(
            "REL.PRESENCE.v1", "NOUL", {"probability_yes": 0.9}, evaluator="fixture"
        ),
        normalize_judgment("REL.TYPE.v1", "CHOICE", {"selected": "CUSTOMER"}, evaluator="fixture"),
        normalize_judgment("REL.TIME.v1", "CHOICE", {"selected": "CURRENT"}, evaluator="fixture"),
        normalize_judgment(
            "REL.CONTRADICTION.v1", "NOUL", {"probability_yes": 0.1}, evaluator="fixture"
        ),
    ]
    composed = compose_relationship_decomposition(atomic)
    compound = normalize_judgment(
        "REL.COMPOUND.v1", "CHOICE", {"selected": "CURRENT"}, evaluator="fixture"
    )
    assert composed["outcome"] == compose_support(compound)["outcome"] == "CURRENT"
    assert composed["signals"]["presence_probability"] == 0.9
    assert composed["canonical_authority"] is False
    contradictory = [
        *atomic[:-1],
        normalize_judgment(
            "REL.CONTRADICTION.v1", "NOUL", {"probability_yes": 0.8}, evaluator="fixture"
        ),
    ]
    preserved = compose_relationship_decomposition(contradictory)
    assert preserved["outcome"] == "UNRESOLVED"
    assert preserved["resolution_state"] == "CONTRADICTORY"
    assert (
        compose_relationship_decomposition(atomic[:-1])["resolution_state"]
        == "INCOMPLETE_ATOMIC_SET"
    )


def _outcome_definition(minimum_effect: float | None = 0.1) -> dict:
    return {
        "evaluation_criteria": {
            "primary_metric": "exact_outcome_accuracy",
            "direction": "HIGHER_IS_BETTER",
            "minimum_effect": minimum_effect,
            "minimum_answered_cases": 3,
            "critical_regression_policy": "BLOCK",
            "invalidation_conditions": ["OPERATIONAL_FAILURE"],
            **(
                {"no_threshold_reason": "No justified threshold."} if minimum_effect is None else {}
            ),
        }
    }


def _outcome_metrics(first: float, second: float, n: int = 3) -> dict:
    return {
        "baseline": {"exact_outcome_accuracy": first, "unique_answered_cases": n},
        "candidate": {"exact_outcome_accuracy": second, "unique_answered_cases": n},
    }


def test_predeclared_outcomes_support_not_support_and_inconclusive() -> None:
    assert (
        evaluate_experiment_outcome(_outcome_definition(), _outcome_metrics(0.5, 0.8))["outcome"]
        == "SUPPORTED"
    )
    assert (
        evaluate_experiment_outcome(_outcome_definition(), _outcome_metrics(0.8, 0.5))["outcome"]
        == "NOT_SUPPORTED"
    )
    assert (
        evaluate_experiment_outcome(_outcome_definition(None), _outcome_metrics(0.5, 0.8))[
            "outcome"
        ]
        == "INCONCLUSIVE"
    )


def test_inadequate_evidence_failures_and_critical_regression_are_inconclusive() -> None:
    definition = _outcome_definition()
    assert evaluate_experiment_outcome(definition, _outcome_metrics(0.5, 0.8, 2))["reasons"] == [
        "INSUFFICIENT_ANSWERED_CASES"
    ]
    assert (
        evaluate_experiment_outcome(definition, _outcome_metrics(0.5, 0.8), operational_failures=1)[
            "outcome"
        ]
        == "INCONCLUSIVE"
    )
    assert (
        evaluate_experiment_outcome(
            definition, _outcome_metrics(0.5, 0.8), critical_regressions=["critical-case"]
        )["outcome"]
        == "INCONCLUSIVE"
    )


def test_usage_pricing_requires_versioned_policy_and_provider_token_usage() -> None:
    policy = load_pricing_policy()
    priced = estimate_cost_from_usage(policy, {"input_tokens": 100}, model="jev-1.13.0")
    assert priced["estimated_cost"] == pytest.approx(0.0000042)
    assert priced["invoice_cost"] == "UNKNOWN"
    assert priced["pricing_policy_version"] == policy["policy_version"]
    assert estimate_cost_from_usage(policy, None, model="jev-1.13.0")["estimated_cost"] == "UNKNOWN"
    assert (
        estimate_cost_from_usage(policy, {"input_tokens": 100}, model="jev-1.12.0")[
            "estimated_cost"
        ]
        == "UNKNOWN"
    )
