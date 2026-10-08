"""Judgment memory: one judgment per (world state, question version, evaluator model).

Reuse is exact. A changed state, a new question version or a different model is a
miss and is judged again, so continuity and model upgrades re-evaluate instead of
inheriting stale answers. Because state is world-level, a judgment made for one
Focus is reused by every other Focus that meets the same tender and capability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from application.semantic_layer.contracts import SemanticAnswer, SemanticQuestion, fingerprint


def memory_key(
    state_fingerprint: str, question: SemanticQuestion, evaluator: str, model: str
) -> str:
    return fingerprint([state_fingerprint, question.fingerprint, evaluator, model])


class JudgmentMemoryPort(Protocol):
    def get(self, key: str) -> SemanticAnswer | None: ...

    def put(self, key: str, answer: SemanticAnswer, *, recorded_at: datetime) -> None: ...


class InMemoryJudgmentMemory:
    def __init__(self) -> None:
        self._items: dict[str, SemanticAnswer] = {}

    def get(self, key: str) -> SemanticAnswer | None:
        return self._items.get(key)

    def put(self, key: str, answer: SemanticAnswer, *, recorded_at: datetime) -> None:
        if recorded_at.tzinfo is None:
            raise ValueError("judgment memory times must be timezone-aware")
        self._items.setdefault(key, answer)
