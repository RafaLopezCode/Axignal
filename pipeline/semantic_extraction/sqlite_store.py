"""SQLite adapter for content-addressed semantic extraction reuse records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from application.semantic_extraction import (
    GroundingSurface,
    ReusableCandidate,
    SemanticExtractionRecord,
)


class SqliteSemanticExtractionRecordStore:
    """Durable reuse anchors; one original provider extraction per content key."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS semantic_extraction_records (
                    content_key TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def get(self, content_key: str) -> SemanticExtractionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM semantic_extraction_records WHERE content_key = ?",
                (content_key,),
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return SemanticExtractionRecord(
            content_key=data["content_key"],
            extracted_for_observed_at=datetime.fromisoformat(data["extracted_for_observed_at"]),
            extraction_id=data["extraction_id"],
            provider=data["provider"],
            provider_version=data["provider_version"],
            candidates=tuple(
                ReusableCandidate(
                    semantic_target=item["semantic_target"],
                    statement=item["statement"],
                    excerpt=item["excerpt"],
                    grounding_surface=GroundingSurface(item["grounding_surface"]),
                    start=item["start"],
                    end=item["end"],
                    structured_index=item["structured_index"],
                )
                for item in data["candidates"]
            ),
        )

    def put(self, record: SemanticExtractionRecord) -> None:
        payload = {
            "content_key": record.content_key,
            "extracted_for_observed_at": record.extracted_for_observed_at.isoformat(),
            "extraction_id": record.extraction_id,
            "provider": record.provider,
            "provider_version": record.provider_version,
            "candidates": [
                {
                    "semantic_target": item.semantic_target,
                    "statement": item.statement,
                    "excerpt": item.excerpt,
                    "grounding_surface": item.grounding_surface.value,
                    "start": item.start,
                    "end": item.end,
                    "structured_index": item.structured_index,
                }
                for item in record.candidates
            ],
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO semantic_extraction_records VALUES (?, ?)",
                (record.content_key, json.dumps(payload, sort_keys=True, ensure_ascii=False)),
            )
