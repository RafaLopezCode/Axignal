"""Cognition adapter implementing AXENT's grounded reasoner port through the router."""

from __future__ import annotations

import time

from application.axent.grounded.answer import ReasoningRequest, ReasoningResult
from cognition.jobs.model import CognitiveJob, JobKind
from cognition.router.router import ModelRouter


class CognitiveGroundedReasoner:
    """Provider-neutral: any registered provider serving GROUNDED_ANSWER jobs fits."""

    def __init__(
        self, router: ModelRouter, *, model: str, provider_name: str | None = None
    ) -> None:
        self._router = router
        self._provider_name = provider_name
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        started = time.monotonic()
        job = CognitiveJob(
            id=request.request_id,
            kind=JobKind.GROUNDED_ANSWER,
            instruction=request.system,
            context={
                "user": request.user,
                "schema": dict(request.schema),
                "max_output_tokens": request.max_output_tokens,
            },
        )
        try:
            result = self._router.route(job, self._provider_name)
        except Exception:
            # A provider failure is not an answer: AXENT falls back to showing evidence.
            return ReasoningResult(
                {}, self._model, None, None, int((time.monotonic() - started) * 1000)
            )
        payload = result.payload
        answer = payload.get("answer")

        def count(name: str) -> int | None:
            value = payload.get(name)
            return value if isinstance(value, int) else None

        latency = payload.get("latency_ms")
        return ReasoningResult(
            payload=answer if isinstance(answer, dict) else {},
            model=str(payload.get("model") or self._model),
            input_tokens=count("input_tokens"),
            output_tokens=count("output_tokens"),
            latency_ms=latency
            if isinstance(latency, int)
            else int((time.monotonic() - started) * 1000),
        )
