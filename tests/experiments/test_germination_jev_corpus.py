from __future__ import annotations

import json

import pytest

from experiments.decision_lab.germination_corpus import (
    ALLOWED_GOLD,
    build_all_cases,
    build_case,
    load_corpus,
    load_question,
)
from experiments.decision_lab.germination_jev_runner import run_live
from experiments.decision_lab.models import LabError


def test_all_real_corpus_cases_are_answerable_and_sealed_without_label_leakage() -> None:
    cases = build_all_cases()

    assert len(cases) == 12
    assert {case.gold for case in cases} <= ALLOWED_GOLD
    for case in cases:
        state, question = case.request.provider_payload()
        serialized = json.dumps(state, sort_keys=True)
        assert case.gold not in serialized
        assert state["claim"]["proposition"]
        assert len(state["evidence"]) == 1
        assert state["evidence"][0]["content"]
        assert state["evidence"][0]["provenance"]["source_ref"] == case.source_url
        assert question["question_id"] == "CES.SUPPORT.vNext.2"


def test_gold_label_is_evaluator_only_even_when_mutated() -> None:
    raw = dict(load_corpus()["cases"][0])
    raw["gold"] = "UNRESOLVED"

    case = build_case(raw, load_question())
    state, _ = case.request.provider_payload()

    assert case.gold == "UNRESOLVED"
    assert "UNRESOLVED" not in json.dumps(state, sort_keys=True)


@pytest.mark.parametrize("field", ["claim", "gold", "source"])
def test_incomplete_real_corpus_case_fails_closed(field: str) -> None:
    raw = dict(load_corpus()["cases"][0])
    raw[field] = ""

    with pytest.raises(LabError):
        build_case(raw, load_question())


def test_live_runner_refuses_to_fabricate_result_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

    with pytest.raises(LabError, match="refusing a fake live result"):
        run_live()


def test_evidence_excerpt_mutation_is_detected_before_provider_boundary() -> None:
    raw = dict(load_corpus()["cases"][0])
    raw["source"] = dict(raw["source"])
    raw["source"]["excerpt"] += " mutated"

    with pytest.raises(LabError, match="hash mismatch"):
        build_case(raw, load_question())
