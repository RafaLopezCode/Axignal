"""Budget preflight and reproducibility manifest helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from experiments.decision_lab.models import LabError


def estimate_budget(
    definition: Mapping[str, Any],
    states: list[dict[str, Any]],
    questions_by_id: Mapping[str, dict[str, Any]] | None = None,
    variant_states: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    budget = definition["budget"]
    variants = definition["variants"]
    questions_per_variant = [len(variant["question_ids"]) for variant in variants]
    repetitions = int(definition.get("repetitions", 1))
    requests = len(states) * len(variants) * repetitions
    question_count = sum(questions_per_variant) * len(states) * repetitions
    max_bytes = max(
        (
            len(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            for variant in variants
            for state in (
                variant_states[variant["variant_id"]] if variant_states is not None else states
            )
        ),
        default=0,
    )
    total_request_bytes = 0
    max_request_bytes = 0
    for variant in variants:
        concrete_states = (
            variant_states[variant["variant_id"]] if variant_states is not None else states
        )
        if len(concrete_states) != len(states):
            raise LabError("state variant case count does not match experiment case count")
        for state in concrete_states:
            question_docs = (
                [questions_by_id[qid] for qid in variant["question_ids"]]
                if questions_by_id is not None
                else variant["question_ids"]
            )
            request_body = {
                "state": state,
                "questions": question_docs,
                "model": variant.get("requested_model", definition["requested_model"]),
            }
            request_bytes = len(json.dumps(request_body, ensure_ascii=False).encode("utf-8"))
            max_request_bytes = max(max_request_bytes, request_bytes)
            total_request_bytes += request_bytes * repetitions
    if (
        requests > budget["max_requests"]
        or question_count > budget["max_questions"]
        or max_bytes > budget["max_state_bytes"]
        or max_request_bytes > budget["max_request_bytes"]
        or total_request_bytes > budget["max_total_request_bytes"]
    ):
        raise LabError("experiment exceeds its predeclared request, question, or state-byte budget")
    return {
        "expected_request_count": requests,
        "expected_question_count": question_count,
        "max_state_bytes": max_bytes,
        "max_request_bytes": max_request_bytes,
        "preflight_request_bytes": total_request_bytes,
        "preflight_token_count": "UNKNOWN",
        "preflight_monetary_cost": "UNKNOWN",
        "invoice_cost": "UNKNOWN",
    }


def manifest_digest(value: dict[str, Any]) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
