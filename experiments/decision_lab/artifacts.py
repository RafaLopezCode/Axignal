"""Reproducible, create-only result artifact storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.decision_lab.experiment import manifest_digest
from experiments.decision_lab.models import LabError
from experiments.decision_lab.outcomes import object_digest


def write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)


def read_result(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("artifact_type") != "decision-lab-result":
        raise ValueError("not a decision lab result artifact")
    result_id = value.get("result_id")
    if isinstance(result_id, str) and result_id:
        unhashed = dict(value)
        unhashed.pop("result_id", None)
        if manifest_digest(unhashed) != result_id:
            raise LabError("immutable result digest does not match artifact content")
    criteria = value.get("predeclared_evaluation_criteria")
    criteria_hash = value.get("evaluation_criteria_sha256")
    if criteria is not None and (
        not isinstance(criteria, dict)
        or not isinstance(criteria_hash, str)
        or object_digest(criteria) != criteria_hash
    ):
        raise LabError("immutable result evaluation criteria digest does not match")
    definition = value.get("experiment_definition")
    manifest = value.get("reproducibility_manifest")
    if isinstance(definition, dict) and isinstance(manifest, dict):
        if manifest.get("experiment_definition_digest") != object_digest(definition):
            raise LabError("experiment definition digest does not match result manifest")
        if criteria is not None and criteria != definition.get("evaluation_criteria"):
            raise LabError("result criteria differ from immutable experiment definition")
    return value
