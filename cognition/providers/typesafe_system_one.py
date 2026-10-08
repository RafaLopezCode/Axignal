"""TypeSafe System One (Jev) as a replaceable semantic judge.

One request carries every question of a batch over one state: Jev reads the state
once and answers the questions in parallel (speculative fan-out), and only input
tokens are billed. Retries follow the SDK's bounded backoff, honouring ``Retry-After``
on 429. The SDK is optional and imported lazily; no request, response body,
exception text or credential is ever stored or logged.

Licence boundary (MCA §2.1 to §2.3): AXIGNAL integrates the API into its own application.
Outputs must never be used to distil, imitate or train another model (§2.3(b)).
"""

from __future__ import annotations

import time
from importlib import import_module
from pathlib import Path
from typing import Any

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.contracts import (
    NOUL_LABELS,
    BatchResult,
    JudgmentSource,
    SemanticAnswer,
    SemanticBatch,
    SemanticJudgeError,
    SemanticQuestion,
    Usage,
)

DEFAULT_JEV_MODEL = "jev-1.13.0"


def _sdk() -> Any:
    try:
        return import_module("typesafe_sdk")
    except ModuleNotFoundError as exc:
        raise SemanticJudgeError("SDK_UNAVAILABLE") from exc


def _read_key(key_file: Path) -> str:
    if not key_file.is_absolute() or not 0 < key_file.stat().st_size <= 4096:
        raise SemanticJudgeError("CREDENTIAL_UNAVAILABLE")
    return key_file.read_text(encoding="utf-8").strip()


def _question(sdk: Any, question: SemanticQuestion) -> Any:
    meanings = dict(question.criteria)
    if question.primitive is SemanticPrimitive.CHOICE:
        return sdk.Choice(instructions=question.instructions, criteria=meanings)
    if question.primitive is SemanticPrimitive.SCORE:
        # Ordered levels; the API answers by level index.
        return sdk.Score(
            instructions=question.instructions,
            criteria=[meaning for _, meaning in question.criteria],
        )
    return sdk.Noul(
        instructions=question.instructions,
        criteria={"true": meanings["true"], "false": meanings["false"]},
    )


def _normalized(pairs: list[tuple[str, float]]) -> tuple[tuple[str, float], ...]:
    total = sum(p for _, p in pairs)
    if total <= 0:
        raise SemanticJudgeError("EMPTY_DISTRIBUTION")
    return tuple((label, p / total) for label, p in pairs)


def _answer(question: SemanticQuestion, raw: Any, model: str) -> SemanticAnswer:
    common: dict[str, Any] = {
        "question_id": question.question_id,
        "primitive": question.primitive,
        "source": JudgmentSource.SYSTEM_ONE,
        "evaluator": TypeSafeSystemOneJudge.name,
        "model": model,
    }
    if question.primitive is SemanticPrimitive.NOUL:
        p = float(raw.noul)
        return SemanticAnswer(**common, distribution=((NOUL_LABELS[0], p), (NOUL_LABELS[1], 1 - p)))
    probabilities = dict(raw.probabilities)
    if question.primitive is SemanticPrimitive.SCORE:
        pairs = [
            (label, float(probabilities.get(i, 0.0))) for i, label in enumerate(question.labels)
        ]
    else:
        pairs = [(label, float(probabilities.get(label, 0.0))) for label in question.labels]
    distribution = _normalized(pairs)
    return SemanticAnswer(
        **common,
        distribution=distribution,
        selected=max(distribution, key=lambda item: item[1])[0],
        confidence=float(raw.confidence) if raw.confidence is not None else None,
    )


class TypeSafeSystemOneJudge:
    """``SemanticJudgePort`` over TypeSafe's ``POST /v1/systemone``."""

    name = "typesafe-system-one"

    def __init__(
        self,
        *,
        model: str = DEFAULT_JEV_MODEL,
        key_file: Path | None = None,
        client: Any | None = None,
        sdk: Any | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        if not model.strip():
            raise ValueError("an explicit Jev model binding is required")
        self.model = model
        self._key_file = key_file
        self._client = client
        self._sdk = sdk
        self._timeout = timeout
        self._max_retries = max_retries

    def _connected(self, sdk: Any) -> Any:
        if self._client is None:
            if self._key_file is None:
                raise SemanticJudgeError("CREDENTIAL_UNAVAILABLE")
            self._client = sdk.TypeSafeClient(
                api_key=_read_key(self._key_file),
                timeout=self._timeout,
                retry=sdk.RetryPolicy(max_retries=self._max_retries),
            )
        return self._client

    def judge(self, batch: SemanticBatch) -> BatchResult:
        sdk = self._sdk or _sdk()
        client = self._connected(sdk)
        questions = {q.question_id: _question(sdk, q) for q in batch.questions}
        started = time.monotonic()
        try:
            response = client.system_one(
                state=dict(batch.state), questions=questions, model=self.model
            )
        except Exception as exc:  # categories only: payloads and messages are never kept
            raise SemanticJudgeError(_category(sdk, exc)) from None
        latency_ms = int((time.monotonic() - started) * 1000)
        resolved_model = getattr(response, "model", None) or self.model
        raw_answers = getattr(response, "answers", {}) or {}
        answers = []
        for question in batch.questions:
            raw = raw_answers.get(question.question_id)
            if raw is None:
                continue
            try:
                answers.append(_answer(question, raw, str(resolved_model)))
            except (AttributeError, TypeError, ValueError):
                continue  # an answer outside the contract is dropped, never repaired
        usage = getattr(response, "usage", None)
        return BatchResult(
            batch_id=batch.batch_id,
            evaluator=self.name,
            model=str(resolved_model),
            answers=tuple(answers),
            usage=Usage(
                input_tokens=getattr(usage, "input_tokens", None),
                output_tokens=getattr(usage, "output_tokens", None),
            ),
            latency_ms=latency_ms,
        )


def _category(sdk: Any, exc: Exception) -> str:
    for name, category in (
        ("TypeSafeRateLimitError", "RATE_LIMITED"),
        ("TypeSafeAuthenticationError", "AUTHENTICATION"),
        ("TypeSafePermissionDeniedError", "PERMISSION_DENIED"),
        ("TypeSafeAPITimeoutError", "TIMEOUT"),
        ("TypeSafeAPIConnectionError", "CONNECTION"),
        ("TypeSafeBadRequestError", "BAD_REQUEST"),
        ("TypeSafeUnprocessableEntityError", "UNPROCESSABLE"),
        ("TypeSafeInternalServerError", "PROVIDER_ERROR"),
    ):
        error_type = getattr(sdk, name, None)
        if isinstance(error_type, type) and isinstance(exc, error_type):
            return category
    return "UNEXPECTED"
