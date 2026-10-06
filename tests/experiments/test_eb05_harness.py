from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from experiments.decision_lab.artifacts import read_result, write_result
from experiments.decision_lab.bakeoff_vnext import load_compiled_cases
from experiments.decision_lab.contracts_vnext import DECISION_CONTRACTS
from experiments.decision_lab.eb05_preflight import build_eb05_preflight_artifact
from experiments.decision_lab.harness_vnext import (
    HarnessMode,
    compare_fixture_modes,
    live_eligibility,
    run_fixture_mode,
)
from experiments.decision_lab.models import NormalizedJudgment


class FixtureEvaluator:
    execution_scope = "OFFLINE_FIXTURE_ONLY"
    evaluator_id = "synthetic-fixture"
    evaluator_version = "1"

    def __init__(self) -> None:
        self.single_calls = 0
        self.batch_calls = 0
        self.input_cases: list[dict[str, object]] = []

    def _evaluate(self, case) -> NormalizedJudgment:
        self.input_cases.append(asdict(case))
        contract = DECISION_CONTRACTS[case.contract_id]
        value: str | float = (
            contract.answer_space[0] if contract.primitive.value == "CHOICE" else 0.5
        )
        return NormalizedJudgment(
            question_id=case.contract_id,
            primitive=contract.primitive.value,
            value=value,
            evaluator=self.evaluator_id,
            usage={"input_tokens": 3, "output_tokens": 1},
        )

    def evaluate_one(self, case) -> NormalizedJudgment:
        self.single_calls += 1
        return self._evaluate(case)

    def evaluate_batch(self, cases) -> tuple[NormalizedJudgment, ...]:
        self.batch_calls += 1
        return tuple(self._evaluate(case) for case in cases)


def test_eb05_fixture_modes_use_same_sanitized_inputs_and_preserve_dimensions() -> None:
    evaluator = FixtureEvaluator()
    comparison = compare_fixture_modes(evaluator=evaluator)

    assert comparison["same_inputs"] is True
    assert comparison["same_request_population"] is True
    assert comparison["outputs_equivalent"] is True
    assert evaluator.single_calls == 11
    assert evaluator.batch_calls == 1
    assert all(
        "expected_outcome" not in item and "label_provenance" not in item
        for item in evaluator.input_cases
    )
    singles = comparison["single"]
    assert singles["execution_scope"] == "OFFLINE_FIXTURE_ADAPTER_ONLY"
    assert singles["metrics"]["usage"] == {
        "knowledge": "KNOWN",
        "counters": {"input_tokens": 33, "output_tokens": 11},
    }
    assert set(singles["metrics"]["dimensions"]) == {
        "CES.SUPPORT.vNext",
        "ENT.ALIGN.vNext",
        "REL.EXISTENCE.vNext",
    }
    assert singles["metrics"]["dimensions"]["REL.EXISTENCE.vNext"]["risk"] is None
    assert singles["metrics"]["severe_errors"] == 2


def test_eb05_nonanswerable_cases_are_not_dispatched_and_live_gate_is_explicit() -> None:
    evaluator = FixtureEvaluator()
    run = run_fixture_mode(evaluator=evaluator, mode=HarnessMode.SINGLES)

    assert evaluator.single_calls == 11
    assert sum(row["status"] == "NOT_ANSWERABLE" for row in run["records"]) == 3
    eligibility = {row["candidate_id"]: row for row in live_eligibility()}
    assert eligibility["typesafe-jev"]["eligibility"] == "BLOCKED"
    assert eligibility["typesafe-jev"]["reason_code"] == "P0_JEV_04A_BLOCKED_NO_VALID_CORPUS"
    assert eligibility["luna-structured"]["eligibility"] == "UNAVAILABLE"
    assert eligibility["openai-decisions"]["eligibility"] == "UNAVAILABLE"


def test_eb05_batch_failure_is_preserved_without_single_fallback_or_exception_text() -> None:
    class AuthenticationFailure(Exception):
        pass

    class BrokenBatch(FixtureEvaluator):
        def evaluate_batch(self, cases):
            self.batch_calls += 1
            raise AuthenticationFailure("sensitive token value")

    evaluator = BrokenBatch()
    result = run_fixture_mode(evaluator=evaluator, mode=HarnessMode.BATCH)

    assert result["execution"]["status"] == "FAILED"
    assert result["execution"]["failure_categories"] == ["AUTHENTICATION"]
    assert result["execution"]["batch_fallback"] == "NOT_ATTEMPTED"
    assert evaluator.single_calls == 0
    assert all("sensitive token value" not in repr(row) for row in result["records"])
    assert result["metrics"]["failures"] == 11


def test_eb05_batch_latency_is_aggregate_and_missing_usage_stays_unknown() -> None:
    class MissingUsage(FixtureEvaluator):
        def _evaluate(self, case) -> NormalizedJudgment:
            result = super()._evaluate(case)
            return NormalizedJudgment(
                question_id=result.question_id,
                primitive=result.primitive,
                value=result.value,
                evaluator=result.evaluator,
                usage=None,
            )

    result = run_fixture_mode(evaluator=MissingUsage(), mode=HarnessMode.BATCH)

    assert result["execution"]["batch_elapsed_ms"] is not None
    assert all(row["latency_ms"] is None for row in result["records"])
    assert all(
        row["latency_scope"] in {"BATCH_AGGREGATE", "NOT_MEASURED"} for row in result["records"]
    )
    assert result["metrics"]["usage"] == {"knowledge": "UNKNOWN", "counters": None}


def test_eb05_fixture_runner_rejects_unmarked_adapter_before_dispatch() -> None:
    class Unmarked(FixtureEvaluator):
        execution_scope = "LIVE_PROVIDER"

    evaluator = Unmarked()
    with pytest.raises(ValueError, match="offline fixture adapters only"):
        run_fixture_mode(evaluator=evaluator, mode=HarnessMode.SINGLES)
    assert evaluator.single_calls == 0


def test_eb05_replay_identity_binds_mode_evaluator_and_same_compiled_inputs() -> None:
    cases = load_compiled_cases()
    evaluator = FixtureEvaluator()
    singles = run_fixture_mode(evaluator=evaluator, mode=HarnessMode.SINGLES, cases=cases)
    repeated = run_fixture_mode(evaluator=FixtureEvaluator(), mode=HarnessMode.SINGLES, cases=cases)
    batch = run_fixture_mode(evaluator=FixtureEvaluator(), mode=HarnessMode.BATCH, cases=cases)

    assert singles["input_manifest_sha256"] == repeated["input_manifest_sha256"]
    assert singles["request_identity"] == repeated["request_identity"]
    assert singles["request_identity"] != batch["request_identity"]


def test_eb05_preflight_artifact_is_reproducible_and_keeps_provider_gates(tmp_path: Path) -> None:
    artifact = build_eb05_preflight_artifact()
    path = tmp_path / "eb05.json"
    write_result(path, artifact)
    loaded = read_result(path)
    repeated = build_eb05_preflight_artifact()

    assert loaded == repeated
    assert loaded["batch_vs_singles"]["status"] == "LIVE_COMPARISON_BLOCKED"
    assert loaded["winner_status"] == "NOT_DECLARED"
    assert loaded["live_provider_eligibility"] == list(live_eligibility())
    assert loaded["dimension_measurement_basis"]["labels_visible_to_evaluator"] is False
    root_artifact = Path(__file__).resolve().parents[2] / (
        "experiments/decision_lab/artifacts/eb05-harness-preflight-v1.json"
    )
    assert read_result(root_artifact) == repeated


def _harness_case(contract_id: str):  # type: ignore[no-untyped-def]
    return next(item for item in load_compiled_cases() if item.contract_id == contract_id)


def _judged(case, primitive: str, answer: dict) -> tuple[str, str | None]:  # type: ignore[no-untyped-def]
    from experiments.decision_lab.harness_vnext import _validated_judgment
    from experiments.decision_lab.judgments import normalize_judgment

    return _validated_judgment(
        case, normalize_judgment(case.contract_id, primitive, answer, evaluator="fixture")
    )


@pytest.mark.parametrize(
    ("primitive", "answer", "expected"),
    [
        ("CHOICE", {"selected": "SAME_LEGAL_ENTITY"}, ("ANSWERED", None)),
        (
            "CHOICE",
            {"selected": "CUSTOMER"},
            ("SCHEMA_FAILURE", "CHOICE_OUTSIDE_DECLARED_CONTRACT"),
        ),
        (
            "CHOICE",
            {
                "selected": "SAME_LEGAL_ENTITY",
                "distribution": {"SAME_LEGAL_ENTITY": 0.6, "UNRESOLVED": 0.4},
            },
            ("ANSWERED", None),
        ),
        (
            "CHOICE",
            {
                "selected": "SAME_LEGAL_ENTITY",
                "distribution": {"SAME_LEGAL_ENTITY": 0.5, "CUSTOMER": 0.5},
            },
            ("SCHEMA_FAILURE", "DISTRIBUTION_OUTSIDE_DECLARED_CONTRACT"),
        ),
        ("CHOICE", {}, ("ABSTAINED", None)),
        ("SCORE", {"value": 3}, ("SCHEMA_FAILURE", "PRIMITIVE_OUTSIDE_DECLARED_CONTRACT")),
        (
            "NOUL",
            {"probability_yes": 0.9},
            ("SCHEMA_FAILURE", "PRIMITIVE_OUTSIDE_DECLARED_CONTRACT"),
        ),
    ],
)
def test_choice_contract_validation_is_discriminative(
    primitive: str, answer: dict, expected: tuple[str, str | None]
) -> None:
    assert _judged(_harness_case("ENT.ALIGN.vNext"), primitive, answer) == expected


@pytest.mark.parametrize(
    ("primitive", "answer", "expected"),
    [
        ("NOUL", {"probability_yes": 0.0}, ("ANSWERED", None)),
        ("NOUL", {"probability_yes": 1.0}, ("ANSWERED", None)),
        ("NOUL", {"probability_yes": 1.2}, ("SCHEMA_FAILURE", "MALFORMED_TYPED_JUDGMENT")),
        (
            "CHOICE",
            {"selected": "probability_yes"},
            ("SCHEMA_FAILURE", "PRIMITIVE_OUTSIDE_DECLARED_CONTRACT"),
        ),
    ],
)
def test_noul_contract_validation_is_discriminative(
    primitive: str, answer: dict, expected: tuple[str, str | None]
) -> None:
    assert _judged(_harness_case("REL.EXISTENCE.vNext"), primitive, answer) == expected


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ({"value": 2}, ("ANSWERED", None)),
        ({"value": 2.0, "distribution": {"1": 0.2, "2": 0.8}}, ("ANSWERED", None)),
        ({"value": 7}, ("SCHEMA_FAILURE", "SCORE_VALUE_OUTSIDE_CONTRACT")),
        (
            {"value": 2, "distribution": {"2": 0.5, "9": 0.5}},
            ("SCHEMA_FAILURE", "DISTRIBUTION_OUTSIDE_DECLARED_CONTRACT"),
        ),
        ({"value": True}, ("SCHEMA_FAILURE", "MALFORMED_TYPED_JUDGMENT")),
    ],
)
def test_score_contract_validation_is_discriminative(
    monkeypatch: pytest.MonkeyPatch, answer: dict, expected: tuple[str, str | None]
) -> None:
    from dataclasses import replace

    from experiments.decision_lab import contracts_vnext
    from experiments.decision_lab.contracts_vnext import Primitive

    case = _harness_case("ENT.ALIGN.vNext")
    score_contract = replace(
        DECISION_CONTRACTS[case.contract_id],
        primitive=Primitive.SCORE,
        answer_space=("1", "2", "3"),
    )
    monkeypatch.setitem(contracts_vnext.DECISION_CONTRACTS, case.contract_id, score_contract)

    assert _judged(case, "SCORE", answer) == expected
