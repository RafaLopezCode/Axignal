"""Explicitly invoked, optional TypeSafe adapter for experimental use only."""

from __future__ import annotations

import json
import math
import time
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from experiments.decision_lab.evaluator import failure_for_exception
from experiments.decision_lab.judgments import normalize_judgment
from experiments.decision_lab.models import LabError, NormalizedJudgment, OperationalFailure
from experiments.decision_lab.requests_vnext import ValidatedProviderRequest

ADAPTER_VERSION = "0.2.0"


def _question(primitive: str, definition: dict[str, Any]) -> Any:
    from typesafe_sdk import Choice, Noul, Score

    kwargs = {"instructions": definition["instructions"]}
    if primitive == "CHOICE":
        return Choice(**kwargs, criteria=definition["criteria"])
    if primitive == "SCORE":
        return Score(**kwargs, criteria=definition["criteria"])
    if primitive == "NOUL":
        noul_semantics = json.dumps(
            definition["criteria"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        kwargs["instructions"] += (
            "\n\nAXIGNAL proposition contract (data, not source instructions): " + noul_semantics
        )
        return Noul(**kwargs)
    raise LabError("unsupported TypeSafe primitive")


def _safe_raw_answer(typed: Any, primitive: str) -> dict[str, Any]:
    """Copy only replay-relevant typed answer fields from the SDK object."""
    field_names = {
        "CHOICE": ("choice", "probabilities", "confidence"),
        "SCORE": ("score", "probabilities", "confidence", "legend"),
        "NOUL": ("noul", "probability_yes", "probability"),
    }[primitive]
    answer: dict[str, Any] = {}
    for field_name in field_names:
        if not hasattr(typed, field_name):
            continue
        value = getattr(typed, field_name)
        scalar = (
            value is None
            or isinstance(value, (str, int, bool))
            or (isinstance(value, float) and math.isfinite(value))
        )
        mapping = isinstance(value, dict) and all(
            isinstance(key, (str, int))
            and (
                item is None
                or isinstance(item, (str, int, bool))
                or (isinstance(item, float) and math.isfinite(item))
            )
            for key, item in value.items()
        )
        if scalar or mapping:
            answer[field_name] = value
    return answer


class TypeSafeLabEvaluator:
    """Lazy SDK use; one call, no retries, no raw response/error serialization."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key
        if not self._api_key or not self._api_key.strip():
            raise LabError("TYPESAFE_API_KEY is unavailable")

    def evaluate(
        self,
        request: ValidatedProviderRequest,
        *,
        model: str,
    ) -> tuple[list[NormalizedJudgment], OperationalFailure | None, dict[str, Any]]:
        if type(request) is not ValidatedProviderRequest:
            raise LabError("provider boundary requires ValidatedProviderRequest")
        state, definition = request.provider_payload()
        question_definitions = [definition]
        from typesafe_sdk import RetryPolicy, TypeSafeClient

        questions = {
            item["question_id"]: _question(item["primitive"], item) for item in question_definitions
        }
        try:
            started = time.perf_counter()
            with TypeSafeClient(api_key=self._api_key, timeout=30) as client:
                response = client.system_one(
                    state=state,
                    questions=questions,
                    model=model,
                    retry=RetryPolicy(max_retries=0),
                )
            elapsed_seconds = time.perf_counter() - started
        except Exception as exc:  # SDK errors are reduced to safe categories only.
            return (
                [],
                failure_for_exception(exc),
                {"latency_seconds": time.perf_counter() - started},
            )

        usage_obj = getattr(response, "usage", None)
        usage: dict[str, int] = {}
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            value = getattr(usage_obj, key, None)
            if isinstance(value, int) and not isinstance(value, bool):
                usage[key] = value
        resolved = getattr(response, "model", None)
        judgments: list[NormalizedJudgment] = []
        raw_answers: dict[str, dict[str, Any]] = {}
        for definition in question_definitions:
            qid = definition["question_id"]
            primitive = definition["primitive"]
            typed_map = getattr(
                response, {"CHOICE": "choices", "SCORE": "scores", "NOUL": "nouls"}[primitive], None
            )
            if not isinstance(typed_map, dict):
                typed_map = getattr(response, "answers", {})
            typed = typed_map.get(qid) if isinstance(typed_map, dict) else None
            raw_answers[qid] = _safe_raw_answer(typed, primitive)
            if primitive == "CHOICE":
                answer = {
                    "selected": getattr(typed, "choice", None),
                    "distribution": getattr(typed, "probabilities", None),
                    "confidence": getattr(typed, "confidence", None),
                }
            elif primitive == "SCORE":
                answer = {
                    "value": getattr(typed, "score", None),
                    "distribution": getattr(typed, "probabilities", None),
                    "confidence": getattr(typed, "confidence", None),
                    "legend": getattr(typed, "legend", None),
                }
            else:
                answer = {
                    "probability_yes": getattr(
                        typed,
                        "noul",
                        getattr(typed, "probability_yes", getattr(typed, "probability", None)),
                    )
                }
            judgments.append(
                normalize_judgment(
                    qid,
                    primitive,
                    answer,
                    evaluator="typesafe-sdk",
                    requested_model=model,
                    resolved_model=resolved if isinstance(resolved, str) else None,
                    usage=usage or None,
                )
            )
        safe_meta: dict[str, Any] = (
            {"resolved_model": resolved} if isinstance(resolved, str) else {}
        )
        safe_meta["raw_answers"] = raw_answers
        safe_meta["latency_seconds"] = elapsed_seconds
        try:
            safe_meta["sdk_version"] = version("typesafe-sdk")
        except PackageNotFoundError:
            safe_meta["sdk_version"] = "0.7.1"
        if usage:
            safe_meta["usage"] = usage
        return judgments, None, safe_meta
