from __future__ import annotations

import json
from types import SimpleNamespace

from cognition.jobs.model import CognitiveJob, JobKind
from cognition.providers.openai_batch import BatchState
from cognition.providers.openai_sdk_batch import OpenAISdkBatchClient


def _job():
    return CognitiveJob(
        id="job:1",
        kind=JobKind.GAP_ENRICHMENT,
        instruction="research governed gap",
        context={"subject_id": "org:axignal"},
    )


class _Files:
    def __init__(self):
        self.created = []
        self.output = b""

    def create(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id="file:input")

    def content(self, file_id):
        return SimpleNamespace(read=lambda: self.output)


class _Batches:
    def __init__(self):
        self.created = []
        self.status = "in_progress"

    def create(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id="batch:1")

    def retrieve(self, batch_id):
        return SimpleNamespace(
            id=batch_id,
            status=self.status,
            output_file_id="file:output" if self.status == "completed" else None,
        )


class _Sdk:
    def __init__(self):
        self.files = _Files()
        self.batches = _Batches()


def test_submission_uses_responses_batch() -> None:
    sdk = _Sdk()
    client = OpenAISdkBatchClient(sdk)
    assert client.submit(model="authorized-luna", jobs=(_job(),)) == "batch:1"
    assert sdk.batches.created[0]["endpoint"] == "/v1/responses"
    record = json.loads(sdk.files.created[0]["file"][1].read().decode())
    assert record["custom_id"] == "job:1"
    assert record["body"]["reasoning"]["effort"] == "high"


def test_poll_is_non_blocking_while_pending() -> None:
    assert OpenAISdkBatchClient(_Sdk()).poll("batch:1").state is BatchState.PENDING


def test_completed_output_maps_identity_and_remains_noncanonical() -> None:
    sdk = _Sdk()
    sdk.batches.status = "completed"
    sdk.files.output = (
        json.dumps({
            "custom_id": "job:1",
            "response": {
                "status_code": 200,
                "body": {
                    "id": "resp:1",
                    "model": "authorized-luna",
                    "output": [{"type": "message"}],
                    "usage": {"input_tokens": 12, "output_tokens": 3},
                },
            },
        }).encode() + b"\n"
    )
    result = OpenAISdkBatchClient(sdk).poll("batch:1")
    assert result.state is BatchState.COMPLETED
    assert result.results[0].job_id == "job:1"
    assert result.results[0].is_canonical_truth is False


def test_terminal_failure_is_fail_closed() -> None:
    sdk = _Sdk()
    sdk.batches.status = "expired"
    result = OpenAISdkBatchClient(sdk).poll("batch:1")
    assert result.state is BatchState.FAILED
    assert result.error_code == "BATCH_EXPIRED"
