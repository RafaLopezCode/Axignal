"""Reproducible, create-only result artifact storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)


def read_result(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("artifact_type") != "decision-lab-result":
        raise ValueError("not a decision lab result artifact")
    return value
