from __future__ import annotations

from datetime import UTC, datetime

from application.economic_discovery.continuous_observation import SharedObservationIntent
from cognition.async_research_canary import AsyncGovernedCanaryCoordinator
from cognition.jobs.model import StructuredResult
from cognition.providers.openai_batch import BatchPoll, BatchState, DurableBatchTransport
from pipeline.continuous_observation.async_canary_store import SqliteDurableCanaryExecutionStore
from pipeline.continuous_observation.sqlite_store import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


def _intent(dimension: str) -> SharedObservationIntent:
    return SharedObservationIntent(
        subject_id="org:axignal",
        state_fingerprint="state:1",
        dimension_id=dimension,
        missing_requirements=(f"{dimension} public evidence",),
        research_policy_id="research-value",
        research_policy_version="1",
        research_context_fingerprint="ctx:1",
    )


class _Client:
    def __init__(self):
        self.submits = []
        self.next_poll = BatchPoll("batch:1", BatchState.PENDING)

    def submit(self, *, model, jobs):
        self.submits.append((model, jobs))
        return "batch:1"

    def poll(self, batch_id):
        return self.next_poll


class _Admission:
    def admit(self, *, work, result):
        return work.work.intent.dimension_id == "seo"


def _setup(tmp_path):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intents = (_intent("seo"), _intent("geo"))
    for item in intents:
        memory.enqueue(item, "prime:test")
    client = _Client()
    coordinator = AsyncGovernedCanaryCoordinator(
        memory=memory,
        store=SqliteDurableCanaryExecutionStore(tmp_path / "canary.sqlite3"),
        transport=DurableBatchTransport(client),
        admission=_Admission(),
        authorized_model="gpt-5.6-luna",
    )
    return memory, intents, client, coordinator


def test_submit_persists_exact_claims_and_restart_does_not_resubmit(tmp_path) -> None:
    memory, intents, client, coordinator = _setup(tmp_path)
    keys = tuple(item.work_key for item in intents)
    first = coordinator.tick(
        subject_id="org:axignal", execution_id="canary:1", work_keys=keys, now=NOW
    )
    assert first.action == "submitted"
    assert len(client.submits) == 1
    restarted = AsyncGovernedCanaryCoordinator(
        memory=memory,
        store=SqliteDurableCanaryExecutionStore(tmp_path / "canary.sqlite3"),
        transport=DurableBatchTransport(client),
        admission=_Admission(),
        authorized_model="gpt-5.6-luna",
    )
    second = restarted.tick(
        subject_id="org:axignal", execution_id="canary:2", work_keys=keys, now=NOW
    )
    assert second.action == "pending"
    assert len(client.submits) == 1


def test_collect_completes_only_admitted_dimension_and_releases_other(tmp_path) -> None:
    memory, intents, client, coordinator = _setup(tmp_path)
    keys = tuple(item.work_key for item in intents)
    coordinator.tick(subject_id="org:axignal", execution_id="canary:1", work_keys=keys, now=NOW)
    jobs = client.submits[0][1]
    client.next_poll = BatchPoll(
        "batch:1",
        BatchState.COMPLETED,
        tuple(
            StructuredResult(
                job_id=job.id,
                provider="openai-batch",
                payload={"provider_version": "gpt-5.6-luna"},
            )
            for job in reversed(jobs)
        ),
    )
    settled = coordinator.tick(
        subject_id="org:axignal", execution_id="ignored", work_keys=keys, now=NOW
    )
    assert settled.action == "completed"
    assert memory.get(intents[0].work_key).state.value == "COMPLETE"
    assert memory.get(intents[1].work_key).state.value == "PENDING"


def test_provider_failure_releases_owned_work_without_marking_complete(tmp_path) -> None:
    memory, intents, client, coordinator = _setup(tmp_path)
    keys = tuple(item.work_key for item in intents)
    coordinator.tick(subject_id="org:axignal", execution_id="canary:1", work_keys=keys, now=NOW)
    client.next_poll = BatchPoll("batch:1", BatchState.FAILED, error_code="BATCH_EXPIRED")
    failed = coordinator.tick(
        subject_id="org:axignal", execution_id="ignored", work_keys=keys, now=NOW
    )
    assert failed.action == "failed"
    assert all(memory.get(key).state.value == "PENDING" for key in keys)
