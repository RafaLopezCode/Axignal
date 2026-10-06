"""OpenAI SDK implementation of the PB-10 narrow Batch client."""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from cognition.jobs.model import CognitiveJob, StructuredResult
from cognition.providers.openai_batch import BatchPoll, BatchState


class OpenAISdkBatchClient:
    def __init__(self, client: OpenAI | None = None) -> None:
        self._client = client or OpenAI()

    def submit(self, *, model: str, jobs: Sequence[CognitiveJob]) -> str:
        content = self._jsonl(model=model, jobs=jobs)
        uploaded = self._client.files.create(
            file=("axignal-pb10.jsonl", io.BytesIO(content)),
            purpose="batch",
        )
        batch = self._client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/responses",
            completion_window="24h",
        )
        return str(batch.id)

    def poll(self, batch_id: str) -> BatchPoll:
        batch = self._client.batches.retrieve(batch_id)
        status = str(batch.status)
        if status in {"validating", "in_progress", "finalizing", "cancelling"}:
            return BatchPoll(batch_id, BatchState.PENDING)
        if status != "completed":
            return BatchPoll(batch_id, BatchState.FAILED, error_code=f"BATCH_{status.upper()}")
        if not batch.output_file_id:
            return BatchPoll(batch_id, BatchState.FAILED, error_code="BATCH_OUTPUT_MISSING")
        response = self._client.files.content(batch.output_file_id)
        raw = response.read()
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        return BatchPoll(batch_id, BatchState.COMPLETED, self._parse_results(text))

    @staticmethod
    def _jsonl(*, model: str, jobs: Sequence[CognitiveJob]) -> bytes:
        lines = []
        seen: set[str] = set()
        for job in jobs:
            if job.id in seen:
                raise ValueError("batch custom ids must be unique")
            seen.add(job.id)
            body = {
                "model": model,
                "reasoning": {"effort": "high"},
                "tools": [{"type": "web_search"}],
                "input": (
                    f"{job.instruction}\n\nGoverned context JSON:\n"
                    + json.dumps(job.context, sort_keys=True, ensure_ascii=False)
                    + "\n\nReturn only structured research evidence. Every evidence candidate "
                    "must bind exactly one governed missing requirement to a public source URL "
                    "and a short supporting excerpt. Do not invent evidence."
                ),
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "axignal_research_evidence",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["EVIDENCE_FOUND", "NO_EVIDENCE"],
                                },
                                "evidence_candidates": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "requirement": {"type": "string"},
                                            "source_url": {"type": "string"},
                                            "excerpt": {"type": "string"},
                                        },
                                        "required": ["requirement", "source_url", "excerpt"],
                                    },
                                },
                                "unresolved_requirements": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "status",
                                "evidence_candidates",
                                "unresolved_requirements",
                            ],
                        },
                    }
                },
            }
            lines.append(
                json.dumps(
                    {"custom_id": job.id, "method": "POST", "url": "/v1/responses", "body": body},
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        return (("\n".join(lines) + "\n") if lines else "").encode()

    @classmethod
    def _parse_results(cls, text: str) -> tuple[StructuredResult, ...]:
        results = []
        for line in text.splitlines():
            if not line.strip():
                continue
            record: dict[str, Any] = json.loads(line)
            custom_id = str(record.get("custom_id", ""))
            response = record.get("response")
            if (
                not custom_id
                or not isinstance(response, dict)
                or response.get("status_code") != 200
            ):
                raise ValueError("batch output contains failed or malformed response")
            body = response.get("body")
            if not isinstance(body, dict):
                raise ValueError("batch output response body is missing")
            research = cls._research_payload(body)
            results.append(
                StructuredResult(
                    job_id=custom_id,
                    provider="openai-batch",
                    payload={
                        "provider_version": str(body.get("model", "unknown")),
                        "response_id": str(body.get("id", "")),
                        "research": research,
                        "usage": body.get("usage", {}),
                    },
                )
            )
        return tuple(results)

    @staticmethod
    def _research_payload(body: dict[str, Any]) -> dict[str, Any]:
        output = body.get("output")
        if not isinstance(output, list):
            raise ValueError("batch response output is missing")
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                raw = part.get("text")
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError("batch structured output text is missing")
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("batch structured output must be an object")
                return parsed
        raise ValueError("batch structured research output is missing")
