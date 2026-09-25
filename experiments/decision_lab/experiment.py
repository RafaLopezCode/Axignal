"""Budget preflight and reproducibility manifest helpers."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from experiments.decision_lab.models import LabError

PRICE_USD_PER_MILLION_INPUT_TOKENS = 0.042
PRICE_SOURCE = "https://docs.typesafe.ai/models (reviewed 2026-09-25)"


def estimate_budget(
    definition: Mapping[str, Any],
    states: list[dict[str, Any]],
    questions_by_id: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    budget = definition["budget"]
    variants = definition["variants"]
    questions_per_variant = [len(variant["question_ids"]) for variant in variants]
    requests = len(states) * len(variants) * int(definition.get("repetitions", 1))
    question_count = (
        sum(questions_per_variant) * len(states) * int(definition.get("repetitions", 1))
    )
    max_bytes = max(
        (len(json.dumps(state, ensure_ascii=False).encode("utf-8")) for state in states), default=0
    )
    byte_estimate = 0
    max_request_bytes = 0
    for state in states:
        for variant in variants:
            question_docs = (
                [questions_by_id[qid] for qid in variant["question_ids"]]
                if questions_by_id is not None
                else variant["question_ids"]
            )
            request_body = {
                "state": state,
                "questions": question_docs,
                "model": definition["requested_model"],
            }
            request_bytes = len(json.dumps(request_body, ensure_ascii=False).encode("utf-8"))
            max_request_bytes = max(max_request_bytes, request_bytes)
            byte_estimate += request_bytes * int(definition.get("repetitions", 1))
    if (
        requests > budget["max_requests"]
        or question_count > budget["max_questions"]
        or max_bytes > budget["max_state_bytes"]
        or max_request_bytes > budget["max_request_bytes"]
        or byte_estimate > budget["max_input_tokens_estimate"]
    ):
        raise LabError("experiment exceeds its predeclared request, question, or state-byte budget")
    estimated_cost = math.ceil(byte_estimate * PRICE_USD_PER_MILLION_INPUT_TOKENS) / 1_000_000
    max_cost = float(budget.get("max_cost_usd", 0))
    if estimated_cost > max_cost:
        raise LabError("conservative input-byte cost estimate exceeds declared cost budget")
    return {
        "expected_request_count": requests,
        "expected_question_count": question_count,
        "max_state_bytes": max_bytes,
        "max_request_bytes": max_request_bytes,
        "input_token_upper_bound": byte_estimate,
        "estimated_cost_usd": estimated_cost,
        "cost_source": PRICE_SOURCE,
        "estimate_is_invoice": False,
    }


def manifest_digest(value: dict[str, Any]) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
