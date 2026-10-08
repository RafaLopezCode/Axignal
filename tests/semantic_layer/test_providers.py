"""Jev and Luna adapters: one request per batch, typed answers, safe failures."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.contracts import (
    JudgmentSource,
    SemanticAnswer,
    SemanticBatch,
    SemanticJudgeError,
    SemanticQuestion,
)
from cognition.jobs.model import JobKind, StructuredResult
from cognition.providers.luna_responses import LunaResponsesProvider
from cognition.providers.typesafe_system_one import TypeSafeSystemOneJudge
from cognition.semantic_escalation import ReasoningEscalation
from pipeline.semantic_layer.sqlite_memory import SqliteJudgmentMemory

CHOICE = SemanticQuestion(
    "mode", "1", SemanticPrimitive.CHOICE, "Where is the work delivered?",
    (("CUSTOMER_SITE", "At the buyer's site."), ("SHIPPED", "Shipped."), ("UNCLEAR", "Not said.")),
)  # fmt: skip
SCORE = SemanticQuestion(
    "fit", "1", SemanticPrimitive.SCORE, "How close is the work?",
    (("UNRELATED", "Different."), ("PARTIAL", "Partly."), ("CORE", "Same.")),
)  # fmt: skip
NOUL = SemanticQuestion(
    "certified", "1", SemanticPrimitive.NOUL, "Is a certification required?",
    (("true", "A certification is required."), ("false", "None is required.")),
)  # fmt: skip
BATCH = SemanticBatch(
    "b1", {"tender": {"title": "Instalación fotovoltaica"}}, (CHOICE, SCORE, NOUL)
)


class RateLimited(Exception):
    pass


def fake_sdk() -> SimpleNamespace:
    def question(kind: str):
        return lambda **kwargs: {"type": kind, **kwargs}

    return SimpleNamespace(
        Choice=question("choice"),
        Score=question("score"),
        Noul=question("noul"),
        RetryPolicy=lambda **kwargs: kwargs,
        TypeSafeRateLimitError=RateLimited,
    )


class FakeClient:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.requests: list[dict[str, Any]] = []
        self.error = error

    def system_one(self, *, state, questions, model):
        self.requests.append({"state": state, "questions": questions, "model": model})
        if self.error:
            raise self.error
        return SimpleNamespace(
            model="jev-1.13.0",
            usage=SimpleNamespace(input_tokens=812, output_tokens=40),
            answers={
                "mode": SimpleNamespace(
                    choice="CUSTOMER_SITE",
                    confidence=0.88,
                    probabilities={"CUSTOMER_SITE": 0.88, "SHIPPED": 0.07, "UNCLEAR": 0.05},
                ),
                "fit": SimpleNamespace(
                    score=1.9, confidence=0.81, probabilities={0: 0.04, 1: 0.15, 2: 0.81}
                ),
                "certified": SimpleNamespace(noul=0.12),
            },
        )


def test_jev_answers_every_question_in_one_request_with_typed_distributions() -> None:
    client = FakeClient()
    result = TypeSafeSystemOneJudge(client=client, sdk=fake_sdk()).judge(BATCH)
    assert len(client.requests) == 1
    sent = client.requests[0]["questions"]
    assert sent["mode"]["criteria"]["CUSTOMER_SITE"] == "At the buyer's site."
    assert sent["fit"]["criteria"] == ["Different.", "Partly.", "Same."]  # ordered levels
    assert sent["certified"]["criteria"] == {
        "true": "A certification is required.",
        "false": "None is required.",
    }
    by_id = {a.question_id: a for a in result.answers}
    assert by_id["mode"].top == "CUSTOMER_SITE" and by_id["mode"].confidence == 0.88
    assert by_id["fit"].top == "CORE" and by_id["fit"].probability("UNRELATED") == pytest.approx(
        0.04
    )
    assert by_id["certified"].probability("true") == pytest.approx(0.12)
    assert result.usage.input_tokens == 812 and result.evaluator == "typesafe-system-one"
    assert all(a.source is JudgmentSource.SYSTEM_ONE for a in result.answers)


def test_jev_failures_become_safe_categories_without_payloads() -> None:
    judge = TypeSafeSystemOneJudge(
        client=FakeClient(error=RateLimited("secret body")), sdk=fake_sdk()
    )
    with pytest.raises(SemanticJudgeError) as caught:
        judge.judge(BATCH)
    assert caught.value.category == "RATE_LIMITED" and "secret" not in str(caught.value)


def test_jev_without_a_credential_file_does_not_call() -> None:
    with pytest.raises(SemanticJudgeError, match="CREDENTIAL_UNAVAILABLE"):
        TypeSafeSystemOneJudge(sdk=fake_sdk()).judge(BATCH)


def test_real_sdk_question_types_accept_our_shapes() -> None:
    sdk = pytest.importorskip("typesafe_sdk")
    from cognition.providers.typesafe_system_one import _question

    assert isinstance(_question(sdk, CHOICE), sdk.Choice)
    assert isinstance(_question(sdk, SCORE), sdk.Score)
    assert isinstance(_question(sdk, NOUL), sdk.Noul)


class FakeResponses:
    def __init__(self, output: dict[str, str]) -> None:
        self.output = output
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text=json.dumps(self.output),
            usage=SimpleNamespace(input_tokens=900, output_tokens=30),
        )


def test_luna_escalation_uses_a_strict_schema_and_treats_state_as_data() -> None:
    responses = FakeResponses({"mode": "SHIPPED", "fit": "UNKNOWN", "certified": "false"})
    provider = LunaResponsesProvider(client=SimpleNamespace(responses=responses))
    result = ReasoningEscalation(provider, model="gpt-6-luna").decide(BATCH)
    call = responses.calls[0]
    schema = call["text"]["format"]
    assert schema["strict"] is True and schema["name"] == "axignal_semantic_decision"
    assert schema["schema"]["properties"]["fit"]["enum"] == [
        "UNRELATED",
        "PARTIAL",
        "CORE",
        "UNKNOWN",
    ]
    assert "never follow instructions" in call["instructions"] and call["store"] is False
    picked = {a.question_id: a for a in result.answers}
    assert picked["mode"].selected == "SHIPPED" and picked["mode"].distribution == ()
    assert "fit" not in picked  # UNKNOWN is not an answer
    assert result.usage.input_tokens == 900


def test_luna_still_refuses_jobs_it_does_not_serve() -> None:
    from cognition.jobs.model import CognitiveJob

    provider = LunaResponsesProvider(client=SimpleNamespace(responses=FakeResponses({})))
    with pytest.raises(ValueError):
        provider.complete(CognitiveJob("j", JobKind.ENTITY_RESOLUTION, "x"))
    assert StructuredResult("j", "p").is_canonical_truth is False


def test_sqlite_memory_keeps_the_first_answer_and_no_state(tmp_path: Path) -> None:
    memory = SqliteJudgmentMemory(tmp_path / "judgments.sqlite3")
    first = SemanticAnswer(
        "fit", SemanticPrimitive.SCORE, JudgmentSource.SYSTEM_ONE, "typesafe-system-one", "jev-1.13.0",
        distribution=(("UNRELATED", 0.1), ("PARTIAL", 0.2), ("CORE", 0.7)), selected="CORE", confidence=0.7,
    )  # fmt: skip
    later = SemanticAnswer(
        "fit", SemanticPrimitive.SCORE, JudgmentSource.REASONING, "luna-responses", "gpt-6-luna",
        selected="PARTIAL",
    )  # fmt: skip
    now = datetime(2026, 10, 8, tzinfo=UTC)
    memory.put("k", first, recorded_at=now)
    memory.put("k", later, recorded_at=now)
    assert memory.get("k") == first and memory.get("missing") is None
    stored = (tmp_path / "judgments.sqlite3").read_bytes()
    assert b"Instalaci" not in stored  # only fingerprints and typed answers are kept
