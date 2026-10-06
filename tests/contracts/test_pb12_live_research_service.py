from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    ObservationMode,
    ObservationRecord,
)
from application.economic_discovery.continuous_observation import schedule_prime_research
from application.economic_discovery.observation_memory import GovernedObservation, ObservedField
from application.economic_discovery.prime import PrimeControlPlan, PrimeRoute, PrimeWorkItem
from application.economic_discovery.research_value import ResearchValueDisposition
from cognition.providers.openai_batch import BatchPoll, BatchState, DurableBatchTransport
from pipeline.continuous_observation.runtime_store import SqliteResearchRuntimeStore
from tools.runtime.live_research import LiveResearchCanaryService, main

NOW = datetime(2026, 10, 6, 10, 30, tzinfo=UTC)


class _BatchClient:
    def __init__(self) -> None:
        self.submits = []
        self.polls = []

    def submit(self, *, model, jobs):
        self.submits.append((model, tuple(jobs)))
        return "batch:test"

    def poll(self, batch_id):
        self.polls.append(batch_id)
        return BatchPoll(batch_id, BatchState.PENDING)


def _observation(observation_id: str, *, minute: int = 0) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id="org:canary",
            source_ref="https://example.com/canary",
            source_type="OFFICIAL_WEB",
            observed_at=NOW + timedelta(minutes=minute),
            content_fingerprint=f"sha256:{observation_id}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=f"snapshot:{observation_id}",
        fields=(ObservedField("markets", "Spain"),),
    )


def _authority_args() -> dict[str, object]:
    return {
        "observation_watermark_at": NOW,
        "observation_watermark_id": "obs:1",
        "valid_until": NOW + timedelta(days=30),
        "temporal_policy_id": "currentness",
        "temporal_policy_version": "1",
    }


def _plan(fingerprint: str = "rich-state:fixture") -> PrimeControlPlan:
    return PrimeControlPlan(
        subject_id="org:canary",
        state_fingerprint=fingerprint,
        items=(
            PrimeWorkItem(
                dimension_id="reputation",
                disposition=DimensionDisposition.NOT_ANSWERABLE,
                route=PrimeRoute.ADAPTIVE_RESEARCH,
                policy_version="route:1",
                missing_requirements=("document.reviews.visible_text",),
                research_disposition=ResearchValueDisposition.RESEARCH_NOW,
                research_policy_id="research-value",
                research_policy_version="1",
                research_context_fingerprint="context:1",
                research_reason_codes=("MATERIALITY",),
            ),
        ),
    )


def _service(tmp_path, client: _BatchClient) -> LiveResearchCanaryService:
    return LiveResearchCanaryService(
        data_dir=tmp_path,
        subject_id="org:canary",
        model="fixture-model",
        transport=DurableBatchTransport(client),
    )


def test_service_dispatches_only_current_prime_authorized_work(tmp_path) -> None:
    client = _BatchClient()
    service = _service(tmp_path, client)
    service.observation_memory.append(_observation("obs:1"))
    schedule_prime_research(
        service.memory,
        plan=_plan(),
        requester_ref="prime:test",
        **_authority_args(),
    )

    payload = service.tick(now=NOW + timedelta(minutes=1), execution_id="pb12:1")
    assert payload["action"] == "submitted"
    assert payload["global_inflight"] == 1
    assert len(client.submits) == 1


def test_service_reobservation_blocks_stale_work_before_provider(tmp_path) -> None:
    client = _BatchClient()
    service = _service(tmp_path, client)
    service.observation_memory.append(_observation("obs:1"))
    schedule_prime_research(
        service.memory,
        plan=_plan(),
        requester_ref="prime:test",
        **_authority_args(),
    )

    service.observation_memory.append(_observation("obs:2", minute=5))
    payload = service.tick(now=NOW + timedelta(minutes=6), execution_id="pb12:stale")
    assert payload["action"] == "idle"
    assert payload["global_inflight"] == 0
    assert client.submits == []


def test_service_is_hard_limited_to_single_inflight_canary(tmp_path) -> None:
    client = _BatchClient()
    try:
        LiveResearchCanaryService(
            data_dir=tmp_path,
            subject_id="org:canary",
            model="fixture-model",
            max_global_inflight=2,
            transport=DurableBatchTransport(client),
        )
    except ValueError as exc:
        assert "exactly one inflight batch" in str(exc)
    else:
        raise AssertionError("PB12 must reject broader concurrency")


def test_control_only_kill_switch_does_not_require_provider_key(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "axignal-live-research-canary",
            "--data-dir",
            str(tmp_path),
            "--subject-id",
            "org:canary",
            "--set-kill-switch",
            "on",
            "--control-only",
        ],
    )
    assert main() == 0
    payload = capsys.readouterr().out
    assert '"kill_switch": true' in payload
    assert SqliteResearchRuntimeStore(tmp_path / "research-runtime.sqlite3").snapshot().kill_switch
