"""Offline-only contract tests for the first live-pilot boundary."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

from experiments.decision_lab.artifacts import read_result, write_result
from experiments.decision_lab.cli import _load, _run_result_replay
from experiments.decision_lab.experiment import manifest_digest
from experiments.decision_lab.judgments import normalize_judgment
from experiments.decision_lab.outcomes import object_digest
from experiments.decision_lab.pilot import _smoke_budget
from experiments.decision_lab.providers.typesafe import TypeSafeLabEvaluator, _safe_raw_answer
from experiments.decision_lab.state import apply_state_variant, compile_state
from experiments.decision_lab.validation import validate_corpus, validate_grammar

LAB_ROOT = Path(__file__).parents[2] / "experiments/decision_lab"


def test_smoke_budget_is_exactly_one_request_and_question() -> None:
    cases = validate_corpus(_load(LAB_ROOT / "corpus/v0.1/cases.json"))
    questions = validate_grammar(
        _load(LAB_ROOT / "grammar/v0.1/grammar.json"),
        _load(LAB_ROOT / "grammar/v0.1/question-lock.json"),
    )
    case = next(item for item in cases if item["case_id"] == "CES-01-clear-positive")
    question = next(item for item in questions if item["question_id"] == "CES.SUPPORT.v1")

    budget = _smoke_budget(case, question)

    assert budget["expected_request_count"] == 1
    assert budget["expected_question_count"] == 1
    assert budget["preflight_token_count"] == "UNKNOWN"
    assert budget["preflight_monetary_cost"] == "UNKNOWN"


def test_evidence_ids_alone_do_not_make_claim_support_state_answerable() -> None:
    """Characterize the recorded state; this is not a semantic sufficiency validator."""
    cases = validate_corpus(_load(LAB_ROOT / "corpus/v0.1/cases.json"))
    case = next(item for item in cases if item["case_id"] == "CES-01-clear-positive")
    question = next(
        item
        for item in validate_grammar(
            _load(LAB_ROOT / "grammar/v0.1/grammar.json"),
            _load(LAB_ROOT / "grammar/v0.1/question-lock.json"),
        )
        if item["question_id"] == "CES.SUPPORT.v1"
    )
    minimal, _version = apply_state_variant(dict(case["state"]), "minimal")
    serialized = compile_state(minimal).canonical_json

    assert case["evidence"][0]["text"]
    assert minimal["evidence_ids"] == [case["evidence"][0]["evidence_id"]]
    assert "claim" not in minimal
    assert "evidence" not in minimal
    assert "text" not in minimal
    assert "claim" not in question["relevant_state_paths"]
    assert "evidence_text" not in question["relevant_state_paths"]
    assert case["evidence"][0]["text"] not in serialized


def test_raw_answer_whitelist_preserves_only_replay_fields() -> None:
    answer = SimpleNamespace(
        choice="SUPPORTED",
        probabilities={"SUPPORTED": 0.91, "PARTIAL": 0.09},
        confidence=0.91,
        provider_internal=object(),
    )

    assert _safe_raw_answer(answer, "CHOICE") == {
        "choice": "SUPPORTED",
        "probabilities": {"SUPPORTED": 0.91, "PARTIAL": 0.09},
        "confidence": 0.91,
    }


def test_adapter_preserves_reported_usage_without_synthesizing_fields(
    monkeypatch: Any,
) -> None:
    qid = "CES.SUPPORT.v1"
    choice = SimpleNamespace(
        choice="SUPPORTED",
        probabilities={"SUPPORTED": 0.91, "PARTIAL": 0.09},
        confidence=0.91,
    )

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            assert kwargs["timeout"] == 30

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *_args: Any) -> None:
            return None

        def system_one(self, *, state: Any, questions: Any, model: str, retry: Any) -> Any:
            assert state == {"candidate": "synthetic"}
            assert set(questions) == {qid}
            assert model == "jev-1.13.0"
            assert retry.max_retries == 0
            return SimpleNamespace(
                choices={qid: choice},
                model="jev-1.13.0",
                usage=SimpleNamespace(input_tokens=13, output_tokens=None, total_tokens=None),
            )

    class FakeRetryPolicy:
        def __init__(self, *, max_retries: int) -> None:
            self.max_retries = max_retries

    class FakeChoice:
        def __init__(self, **_kwargs: Any) -> None:
            pass

    fake_sdk = ModuleType("typesafe_sdk")
    fake_sdk.Choice = FakeChoice  # type: ignore[attr-defined]
    fake_sdk.Noul = FakeChoice  # type: ignore[attr-defined]
    fake_sdk.Score = FakeChoice  # type: ignore[attr-defined]
    fake_sdk.RetryPolicy = FakeRetryPolicy  # type: ignore[attr-defined]
    fake_sdk.TypeSafeClient = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "typesafe_sdk", fake_sdk)

    judgments, failure, metadata = TypeSafeLabEvaluator(api_key="test-only").evaluate(
        {"candidate": "synthetic"},
        [
            {
                "question_id": qid,
                "primitive": "CHOICE",
                "instructions": "synthetic test question",
                "criteria": {"SUPPORTED": None, "PARTIAL": None},
            }
        ],
        model="jev-1.13.0",
    )

    assert failure is None
    assert judgments[0].usage == {"input_tokens": 13}
    assert metadata["usage"] == {"input_tokens": 13}
    assert "total_tokens" not in metadata["usage"]
    assert metadata["raw_answers"][qid] == {
        "choice": "SUPPORTED",
        "probabilities": {"SUPPORTED": 0.91, "PARTIAL": 0.09},
        "confidence": 0.91,
    }


def test_result_replay_recomputes_metrics_and_predeclared_outcome(tmp_path: Path) -> None:
    corpus = validate_corpus(_load(LAB_ROOT / "corpus/v0.1/cases.json"))
    cases = {item["case_id"]: item for item in corpus}
    grammar = {
        item["question_id"]: item
        for item in validate_grammar(
            _load(LAB_ROOT / "grammar/v0.1/grammar.json"),
            _load(LAB_ROOT / "grammar/v0.1/question-lock.json"),
        )
    }
    definition: dict[str, Any] = _load(LAB_ROOT / "experiments/v0.1/claim-wording-ab.json")
    records = []
    for case_id in definition["case_ids"]:
        case = cases[case_id]
        for variant in definition["variants"]:
            question_id = variant["question_ids"][0]
            judgment = normalize_judgment(
                question_id,
                grammar[question_id]["primitive"],
                {"selected": case["expected_outcome"]},
                evaluator="offline-fixture",
                requested_model=definition["requested_model"],
                resolved_model=None,
                usage=None,
            )
            records.append(
                {
                    "case_id": case_id,
                    "variant_id": variant["variant_id"],
                    "repetition": 1,
                    "expected_outcome": case["expected_outcome"],
                    "label_status": case["label_status"],
                    "state_fingerprint": "fixture-fingerprint",
                    "judgments": [judgment.to_dict()],
                    "failure": None,
                    "metadata": {},
                }
            )
    criteria = definition["evaluation_criteria"]
    source: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "experiment_id": definition["experiment_id"],
        "experiment_definition": definition,
        "data_mode": "OFFLINE_TEST_FIXTURE",
        "records": records,
        "predeclared_evaluation_criteria": criteria,
        "evaluation_criteria_sha256": object_digest(criteria),
    }
    source["result_id"] = manifest_digest(source)
    source_path = tmp_path / "source-result.json"
    write_result(source_path, source)
    replay_path = tmp_path / "replay-result.json"

    _run_result_replay(source_path, replay_path)

    replay = read_result(replay_path)
    assert replay["source_result_id"] == source["result_id"]
    assert set(replay["metrics_by_variant"]) == {"v1", "v2"}
    assert all(metric["n_answered"] == 5 for metric in replay["metrics_by_variant"].values())
    assert replay["result"] == "INCONCLUSIVE"
    assert replay["result_reasons"] == ["NO_PREDECLARED_MINIMUM_EFFECT"]


def test_smoke_replay_without_experiment_definition_is_digest_valid(tmp_path: Path) -> None:
    judgment = normalize_judgment(
        "CES.SUPPORT.v1",
        "CHOICE",
        {"selected": "NO_EVIDENCE", "distribution": {"NO_EVIDENCE": 1.0}},
        evaluator="offline-test",
        requested_model="jev-1.13.0",
        resolved_model="jev-1.13.0",
        usage=None,
    )
    source: dict[str, Any] = {
        "artifact_type": "decision-lab-result",
        "result_version": "0.1.0",
        "data_mode": "LIVE_PROVIDER_SMOKE",
        "experiment_id": "p0-jev-03-smoke",
        "records": [{"case_id": "CES-01-clear-positive", "judgments": [judgment.to_dict()]}],
        "reproducibility_manifest": {"git_revision": "offline-test-revision"},
    }
    source["result_id"] = manifest_digest(source)
    source_path = tmp_path / "smoke-source.json"
    write_result(source_path, source)
    replay_path = tmp_path / "smoke-replay.json"

    _run_result_replay(source_path, replay_path)

    replay = read_result(replay_path)
    assert replay["source_result_id"] == source["result_id"]
    assert replay["experiment_definition"] is None
    assert replay["records"][0]["judgments"] == [judgment.to_dict()]
