"""SQLite judgment memory: append-only, first answer per key wins.

Keys bind world state, question version and evaluator model, so nothing tenant-private
is stored: the state itself is not kept, only its fingerprint and the typed answer.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.contracts import JudgmentSource, SemanticAnswer, canonical_json


class SqliteJudgmentMemory:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_judgments (
                    memory_key TEXT PRIMARY KEY,
                    answer_json TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Commit on success and always close: no connection outlives a call."""
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get(self, key: str) -> SemanticAnswer | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT answer_json FROM semantic_judgments WHERE memory_key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return SemanticAnswer(
            question_id=data["questionId"],
            primitive=SemanticPrimitive(data["primitive"]),
            source=JudgmentSource(data["source"]),
            evaluator=data["evaluator"],
            model=data["model"],
            distribution=tuple((label, float(p)) for label, p in data["distribution"]),
            selected=data["selected"],
            confidence=data["confidence"],
        )

    def put(self, key: str, answer: SemanticAnswer, *, recorded_at: datetime) -> None:
        if recorded_at.tzinfo is None:
            raise ValueError("judgment memory times must be timezone-aware")
        payload = canonical_json(
            {
                "questionId": answer.question_id,
                "primitive": answer.primitive.value,
                "source": answer.source.value,
                "evaluator": answer.evaluator,
                "model": answer.model,
                "distribution": [list(item) for item in answer.distribution],
                "selected": answer.selected,
                "confidence": answer.confidence,
            }
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO semantic_judgments VALUES (?, ?, ?)",
                (key, payload, recorded_at.isoformat()),
            )
