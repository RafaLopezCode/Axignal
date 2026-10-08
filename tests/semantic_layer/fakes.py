"""Deterministic stand-ins for System One and reasoning providers (no network)."""

from __future__ import annotations

from collections.abc import Callable

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.contracts import (
    NOUL_LABELS,
    BatchResult,
    JudgmentSource,
    SemanticAnswer,
    SemanticBatch,
    SemanticJudgeError,
    SemanticQuestion,
    Usage,
)

Rule = Callable[[SemanticBatch, SemanticQuestion], tuple[str, float]]


def answer(question: SemanticQuestion, label: str, confidence: float, evaluator: str, model: str):
    if question.primitive is SemanticPrimitive.NOUL:
        p = confidence if label == "true" else 1 - confidence
        return SemanticAnswer(
            question.question_id,
            question.primitive,
            JudgmentSource.SYSTEM_ONE,
            evaluator,
            model,
            distribution=((NOUL_LABELS[0], p), (NOUL_LABELS[1], 1 - p)),
        )
    rest = (1 - confidence) / (len(question.labels) - 1)
    return SemanticAnswer(
        question.question_id,
        question.primitive,
        JudgmentSource.SYSTEM_ONE,
        evaluator,
        model,
        distribution=tuple((lb, confidence if lb == label else rest) for lb in question.labels),
        selected=label,
        confidence=confidence,
    )


class FakeSystemOne:
    name = "typesafe-system-one"
    model = "jev-1.13.0"

    def __init__(self, rule: Rule, *, fail: str | None = None) -> None:
        self.rule = rule
        self.fail = fail
        self.calls: list[SemanticBatch] = []

    def judge(self, batch: SemanticBatch) -> BatchResult:
        self.calls.append(batch)
        if self.fail:
            raise SemanticJudgeError(self.fail)
        answers = tuple(
            answer(q, *self.rule(batch, q), self.name, self.model) for q in batch.questions
        )
        return BatchResult(
            batch.batch_id,
            self.name,
            self.model,
            answers,
            Usage(input_tokens=batch.estimated_input_tokens(), output_tokens=0),
            latency_ms=150,
        )


class FakeReasoning:
    name = "luna-responses"
    model = "gpt-6-luna"

    def __init__(self, choose: Callable[[SemanticQuestion], str]) -> None:
        self.choose = choose
        self.calls: list[SemanticBatch] = []

    def decide(self, batch: SemanticBatch) -> BatchResult:
        self.calls.append(batch)
        answers = tuple(
            SemanticAnswer(
                q.question_id,
                q.primitive,
                JudgmentSource.REASONING,
                self.name,
                self.model,
                selected=self.choose(q),
            )
            for q in batch.questions
            if self.choose(q) in q.labels
        )
        return BatchResult(
            batch.batch_id,
            self.name,
            self.model,
            answers,
            Usage(input_tokens=900, output_tokens=40),
        )
