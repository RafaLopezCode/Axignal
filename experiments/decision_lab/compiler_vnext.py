"""Explicit V-next state assembly, normalization, validation and fingerprinting."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, cast

from experiments.decision_lab.answerability_vnext import (
    AnswerabilityResult,
    validate_decision_request,
)
from experiments.decision_lab.models import LabError

COMPILER_VERSION = "decision-state-compiler.vNext.1"


@dataclass(frozen=True)
class CompiledDecisionState:
    state_contract_version: str
    compiler_version: str
    canonical_json: str
    fingerprint: str
    answerability: AnswerabilityResult
    unresolved_references: tuple[str, ...]

    @property
    def payload(self) -> dict[str, Any]:
        payload = json.loads(self.canonical_json)
        if not isinstance(payload, dict):
            raise LabError("compiled decision state is not an object")
        return cast(dict[str, Any], payload)


def assemble_state(
    source_state: dict[str, Any], evidence_catalog: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Resolve explicit evidence references; missing records never become text."""
    source = json.loads(json.dumps(source_state, ensure_ascii=False))
    has_refs = "evidence_refs" in source
    has_legacy_ids = "evidence_ids" in source
    refs = source.pop("evidence_refs", None)
    legacy_ids = source.pop("evidence_ids", None)
    if has_refs and has_legacy_ids:
        raise LabError("evidence_ids and evidence_refs cannot both be declared")
    if has_legacy_ids:
        refs = legacy_ids
    if not has_refs and not has_legacy_ids:
        return source, ()
    if not isinstance(refs, list) or any(
        not isinstance(item, str) or not item.strip() for item in refs
    ):
        raise LabError("evidence_refs must be a list of non-empty identifiers")
    if len(refs) != len(set(refs)):
        raise LabError("evidence_refs cannot contain duplicate identifiers")
    assembled: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for evidence_id in refs:
        record = evidence_catalog.get(evidence_id)
        if record is None:
            unresolved.append(evidence_id)
            continue
        if not isinstance(record, dict):
            raise LabError(f"evidence catalog record must be an object: {evidence_id}")
        try:
            item = json.loads(json.dumps(record, ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise LabError(f"evidence catalog record is not JSON-safe: {evidence_id}") from exc
        item["evidence_id"] = evidence_id
        assembled.append(item)
    source["evidence"] = assembled
    return source, tuple(unresolved)


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Copy JSON-safe values and reject invalid numbers without inventing defaults."""
    candidate = json.loads(json.dumps(state, ensure_ascii=False, allow_nan=False))
    if not isinstance(candidate, dict):
        raise LabError("decision state must be an object")
    normalized = cast(dict[str, Any], candidate)

    def check(value: Any, path: str = "state") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise LabError(f"non-string object key at {path}")
                check(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check(child, f"{path}[{index}]")
        elif isinstance(value, float) and not math.isfinite(value):
            raise LabError(f"non-finite number at {path}")
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise LabError(f"unsupported value at {path}")

    check(normalized)
    return normalized


def canonical_serialize(state: dict[str, Any]) -> str:
    return json.dumps(
        state, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def compile_decision_state(
    contract_id: str,
    state: dict[str, Any],
    *,
    unresolved_references: tuple[str, ...] = (),
) -> CompiledDecisionState:
    """Compile deterministically and attach an independent answerability verdict."""
    normalized = normalize_state(state)
    if unresolved_references:
        normalized["unresolved_evidence_refs"] = list(unresolved_references)
    answerability = validate_decision_request(contract_id, normalized)
    if unresolved_references:
        answerability = AnswerabilityResult(
            "NOT_ANSWERABLE",
            tuple(sorted(set(answerability.reasons) | {"UNRESOLVED_REFERENCE"})),
            answerability.contract_version,
            answerability.state_contract_version,
        )
    serialized = canonical_serialize(normalized)
    return CompiledDecisionState(
        str(normalized.get("state_contract_version", "UNKNOWN")),
        COMPILER_VERSION,
        serialized,
        hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        answerability,
        unresolved_references,
    )


def compile_from_sources(
    contract_id: str,
    source_state: dict[str, Any],
    evidence_catalog: dict[str, dict[str, Any]],
) -> CompiledDecisionState:
    assembled, unresolved = assemble_state(source_state, evidence_catalog)
    return compile_decision_state(contract_id, assembled, unresolved_references=unresolved)
