"""Provider-neutral contracts for typed semantic judgments.

A question is a narrow, versioned judgment over supplied state (ADR-0047 shapes:
Choice, Score, Noul). An answer is model output about that question: a distribution
over the declared labels, never canonical truth and never a probability of the world
(``JEV_DISTRIBUTION != SALE_PROBABILITY``, MASTER §53). Python decides what an answer
may change; providers only answer.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.brain_contracts import SemanticPrimitive

#: Noul questions always answer over these two labels.
NOUL_LABELS = ("true", "false")


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SemanticQuestion:
    """One governed judgment. ``criteria`` are (label, meaning) pairs; Score levels are
    ordered from lowest to highest; Noul criteria are exactly ``true`` and ``false``."""

    question_id: str
    version: str
    primitive: SemanticPrimitive
    instructions: str
    criteria: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.question_id.strip() or not self.version.strip():
            raise ValueError("semantic question identity and version are required")
        if not self.instructions.strip():
            raise ValueError("semantic question instructions are required")
        labels = self.labels
        if len(set(labels)) != len(labels) or any(not label.strip() for label in labels):
            raise ValueError("semantic question labels must be unique and non-empty")
        if any(not meaning.strip() for _, meaning in self.criteria):
            raise ValueError("every label needs a stated meaning")
        if self.primitive is SemanticPrimitive.NOUL and labels != NOUL_LABELS:
            raise ValueError("a Noul question declares exactly the true and false meanings")
        if self.primitive is not SemanticPrimitive.NOUL and len(labels) < 2:
            raise ValueError("Choice and Score questions need at least two labels")

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(label for label, _ in self.criteria)

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "id": self.question_id,
                "version": self.version,
                "primitive": self.primitive.value,
                "instructions": self.instructions,
                "criteria": self.criteria,
            }
        )


@dataclass(frozen=True, slots=True)
class SemanticBatch:
    """Independent questions over one state, answered together (speculative fan-out).

    State must be world-level and JSON-safe: public observations, never a tenant's
    private context, so the same judgment can be reused for every Focus that meets it.
    """

    batch_id: str
    state: Mapping[str, object]
    questions: tuple[SemanticQuestion, ...]

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("semantic batch identity is required")
        if not self.questions:
            raise ValueError("a semantic batch asks at least one question")
        ids = [question.question_id for question in self.questions]
        if len(set(ids)) != len(ids):
            raise ValueError("questions in one batch must have unique ids")
        canonical_json(self.state)  # raises on non-JSON state

    @property
    def state_fingerprint(self) -> str:
        return fingerprint(self.state)

    def question(self, question_id: str) -> SemanticQuestion:
        return next(q for q in self.questions if q.question_id == question_id)

    def only(self, question_ids: tuple[str, ...]) -> SemanticBatch:
        """The same state asking only ``question_ids`` (memory misses, escalations)."""
        return SemanticBatch(
            self.batch_id,
            self.state,
            tuple(q for q in self.questions if q.question_id in question_ids),
        )

    def estimated_input_tokens(self) -> int:
        """Conservative estimate (3 characters per token) for budgets and packing."""
        questions = [
            {"instructions": q.instructions, "criteria": q.criteria} for q in self.questions
        ]
        return math.ceil(len(canonical_json({"s": self.state, "q": questions})) / 3)


class JudgmentSource(StrEnum):
    SYSTEM_ONE = "SYSTEM_ONE"
    REASONING = "REASONING"


@dataclass(frozen=True, slots=True)
class SemanticAnswer:
    """Typed provider output for one question. Not canonical, not evidence.

    System One answers carry a full distribution over the declared labels. A reasoning
    answer may carry only ``selected``: an invented distribution would be false precision.
    """

    question_id: str
    primitive: SemanticPrimitive
    source: JudgmentSource
    evaluator: str
    model: str
    distribution: tuple[tuple[str, float], ...] = ()
    selected: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.question_id.strip() or not self.evaluator.strip() or not self.model.strip():
            raise ValueError("semantic answer identity is required")
        labels = [label for label, _ in self.distribution]
        if len(labels) != len(set(labels)):
            raise ValueError("distribution labels must be unique")
        if any(not math.isfinite(p) or p < 0.0 or p > 1.0 for _, p in self.distribution):
            raise ValueError("distribution values must be probabilities")
        if self.distribution and not math.isclose(
            sum(p for _, p in self.distribution), 1.0, abs_tol=1e-3
        ):
            raise ValueError("distribution must sum to one")
        if not self.distribution and self.selected is None:
            raise ValueError("an answer needs a distribution or a selected label")
        if self.selected is not None and self.distribution and self.selected not in labels:
            raise ValueError("selected label must belong to the distribution")
        if self.confidence is not None and not (
            math.isfinite(self.confidence) and 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError("confidence must be a probability")

    @property
    def is_canonical_truth(self) -> bool:
        return False

    def probability(self, label: str) -> float | None:
        return dict(self.distribution).get(label)

    @property
    def top(self) -> str:
        if self.selected is not None:
            return self.selected
        return max(self.distribution, key=lambda item: item[1])[0]

    def to_wire(self) -> dict[str, object]:
        return {
            "questionId": self.question_id,
            "primitive": self.primitive.value,
            "source": self.source.value,
            "evaluator": self.evaluator,
            "model": self.model,
            "selected": self.top,
            "distribution": {label: round(p, 4) for label, p in self.distribution},
            "confidence": None if self.confidence is None else round(self.confidence, 4),
            "nonAuthoritative": True,
        }


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class BatchResult:
    batch_id: str
    evaluator: str
    model: str
    answers: tuple[SemanticAnswer, ...]
    usage: Usage = Usage()
    latency_ms: int | None = None


class SemanticJudgeError(Exception):
    """A provider call failed. ``category`` is safe to log; payloads never are."""

    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


class SemanticJudgePort(Protocol):
    """Fast typed judgments over a batch (System One family, e.g. Jev)."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def judge(self, batch: SemanticBatch) -> BatchResult: ...


class ReasoningEscalationPort(Protocol):
    """A slower reasoning model consulted only for uncertain, material questions."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def decide(self, batch: SemanticBatch) -> BatchResult: ...
