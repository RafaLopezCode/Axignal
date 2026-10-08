"""Synchronous Luna binding over the OpenAI Responses API for grounded answers.

The call carries no tools (no browsing, no retrieval): the model reasons only
over the instructions and the bounded context pack it is handed, and must
return the strict JSON schema of the job. Responses are not stored. Usage is
reported as measured by the provider. The SDK is optional and loaded lazily.
"""

from __future__ import annotations

import json
import time
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from cognition.jobs.model import CognitiveJob, JobKind, StructuredResult

DEFAULT_LUNA_MODEL = "gpt-6-luna"

_SCHEMA_NAMES = {
    JobKind.GROUNDED_ANSWER: "axent_grounded_answer",
    JobKind.SEMANTIC_DECISION: "axignal_semantic_decision",
}


class _ResponsesSdk(Protocol):
    responses: Any


def _default_sdk(key_file: Path | None = None) -> _ResponsesSdk:
    try:
        module = import_module("openai")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Luna requires the optional research-canary-live dependency group"
        ) from exc
    factory = vars(module).get("OpenAI")
    if factory is None:
        raise RuntimeError("installed OpenAI package does not expose OpenAI")
    options: dict[str, object] = {
        "timeout": 15.0,
        "max_retries": 0,
        "base_url": "https://api.openai.com/v1",
    }
    if key_file is not None:
        if not key_file.is_absolute() or not 0 < key_file.stat().st_size <= 8192:
            raise RuntimeError("Luna credential unavailable")
        options["api_key"] = key_file.read_text(encoding="utf-8").strip()
    return cast(_ResponsesSdk, factory(**options))


class LunaResponsesProvider:
    """CognitiveProvider for GROUNDED_ANSWER and SEMANTIC_DECISION jobs on an explicitly
    authorized model."""

    name = "luna-responses"

    def __init__(
        self,
        *,
        authorized_model: str = DEFAULT_LUNA_MODEL,
        client: _ResponsesSdk | None = None,
        reasoning_effort: str = "low",
        key_file: Path | None = None,
    ) -> None:
        if not authorized_model.strip():
            raise ValueError("authorized Luna model binding is required")
        self.model = authorized_model
        self._client = client
        self._effort = reasoning_effort
        self._key_file = key_file

    def complete(self, job: CognitiveJob) -> StructuredResult:
        if job.kind not in _SCHEMA_NAMES:
            raise ValueError("the Luna responses binding serves grounded answers and decisions")
        context = job.context
        schema, user = context.get("schema"), context.get("user")
        limit = context.get("max_output_tokens")
        if not isinstance(schema, dict) or not isinstance(user, str) or not isinstance(limit, int):
            raise ValueError("grounded answer job context is malformed")
        client = self._client or _default_sdk(self._key_file)
        self._client = client
        started = time.monotonic()
        response = client.responses.create(
            model=self.model,
            instructions=job.instruction,
            input=user,
            max_output_tokens=limit,
            reasoning={"effort": self._effort},
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": _SCHEMA_NAMES[job.kind],
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        try:
            answer = json.loads(str(response.output_text))
        except (json.JSONDecodeError, AttributeError):
            answer = {}
        usage = getattr(response, "usage", None)
        return StructuredResult(
            job_id=job.id,
            provider=self.name,
            payload={
                "answer": answer if isinstance(answer, dict) else {},
                "model": self.model,
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "latency_ms": latency_ms,
            },
        )
