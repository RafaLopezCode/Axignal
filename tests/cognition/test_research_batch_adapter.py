from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.batch_research import claim_research_batch
from application.economic_discovery.continuous_observation import SharedObservationIntent
from cognition.jobs.model import StructuredResult
from cognition.research_batch_adapter import CognitiveResearchBatchExecutor
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 6, 30, tzinfo=UTC)


def _claimed(tmp_path):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intents = tuple(
        SharedObservationIntent(
            subject_id="org:acme",
            state_fingerprint="state:1",
            dimension_id=dimension,
            missing_requirements=(f"{dimension}.missing",),
            research_policy_id="research:value",
            research_policy_version="1",
            research_context_fingerprint=f"context:{dimension}",
        )
        for dimension in ("seo", "geo")
    )
    for intent in intents:
        memory.enqueue(intent, "prime:test")
    return claim_research_batch(
        memory,
        work_keys=tuple(intent.work_key for intent in intents),
        now=NOW,
        lease_for=timedelta(minutes=5),
        max_batch_size=2,
    )


class _Provider:
    name = "luna-batch"

    def __init__(self, invalid=False):
        self.invalid = invalid
        self.jobs = ()

    def complete_batch(self, jobs):
        self.jobs = tuple(jobs)
        results = tuple(
            StructuredResult(
                job_id=job.id,
                provider=self.name,
                payload={
                    "provider_version": "fixture/1",
                    "evidence_candidates": [job.context["dimension_id"]],
                },
            )
            for job in reversed(self.jobs)
        )
        return results[:-1] if self.invalid else results


class _Admission:
    def __init__(self):
        self.calls = []

    def admit(self, *, work, result):
        self.calls.append((work, result))
        return work.work.intent.dimension_id == "seo"


def test_cognitive_batch_preserves_governed_context_and_requires_admission(tmp_path) -> None:
    claimed = _claimed(tmp_path)
    provider = _Provider()
    admission = _Admission()

    results = CognitiveResearchBatchExecutor(provider, admission).execute_batch(claimed)

    assert tuple(job.kind.value for job in provider.jobs) == ("GAP_ENRICHMENT",) * 2
    assert provider.jobs[0].context["missing_requirements"] == ("seo.missing",)
    assert tuple(result.work_key for result in results) == tuple(
        item.lease.work_key for item in claimed
    )
    assert tuple(result.objective_resolved for result in results) == (True, False)
    assert len(admission.calls) == 2


def test_invalid_provider_population_fails_before_admission(tmp_path) -> None:
    admission = _Admission()
    with pytest.raises(ValueError, match="population"):
        CognitiveResearchBatchExecutor(_Provider(invalid=True), admission).execute_batch(
            _claimed(tmp_path)
        )
    assert admission.calls == []


def test_empty_batch_is_noop(tmp_path) -> None:
    provider = _Provider()
    admission = _Admission()
    assert CognitiveResearchBatchExecutor(provider, admission).execute_batch(()) == ()
    assert provider.jobs == ()
    assert admission.calls == []
