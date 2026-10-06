from __future__ import annotations

import pytest

from cognition.jobs.model import CognitiveJob, JobKind, StructuredResult
from cognition.providers.luna_batch import LunaBatchProvider


class _Transport:
    def __init__(self) -> None:
        self.calls = []

    def complete_batch(self, *, model, jobs):
        jobs = tuple(jobs)
        self.calls.append((model, jobs))
        return tuple(
            StructuredResult(job_id=job.id, provider="luna-fixture", payload={})
            for job in reversed(jobs)
        )


def _job(identifier: str) -> CognitiveJob:
    return CognitiveJob(
        id=identifier,
        kind=JobKind.DOCUMENT_SEMANTIC_EXTRACTION,
        instruction="extract grounded candidates",
        context={"subject_id": identifier},
    )


def test_luna_binding_requires_explicit_authorized_model() -> None:
    with pytest.raises(ValueError, match="authorized Luna model"):
        LunaBatchProvider(_Transport(), authorized_model=" ")


def test_luna_binding_forwards_exact_model_and_jobs_without_claiming_truth() -> None:
    transport = _Transport()
    provider = LunaBatchProvider(transport, authorized_model="authorized-luna")
    jobs = (_job("a"), _job("b"))

    results = tuple(provider.complete_batch(jobs))

    assert provider.authorized_model == "authorized-luna"
    assert transport.calls == [("authorized-luna", jobs)]
    assert tuple(result.job_id for result in results) == ("b", "a")
    assert all(result.is_canonical_truth is False for result in results)


def test_empty_batch_does_not_call_transport() -> None:
    transport = _Transport()
    provider = LunaBatchProvider(transport, authorized_model="authorized-luna")

    assert tuple(provider.complete_batch(())) == ()
    assert transport.calls == []
