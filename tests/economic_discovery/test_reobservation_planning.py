"""Reobservation planning: content change vs evidence refresh vs currentness transition."""

from __future__ import annotations

import socket
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.economic_discovery.continuous_observation import (
    PrimeResearchAuthority,
    refresh_prime_research_authority,
)
from application.economic_discovery.observation_reuse import ObservationReuseRejected
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    execute_prime_source_slice,
)
from application.source_representation import (
    RichStateDatum,
    compile_rich_subject_state,
    representation_state_data,
    rich_state_delta,
)
from domain.evidence.epistemics import Currentness
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from tests.economic_discovery.reobservation_benchmark import (
    CONTRACTS,
    ROUTING,
    _CountingExecutor,
    run_reobservation_benchmark,
)
from tests.economic_discovery.test_prime_execution import (
    NOW,
    _authorized_seed,
    _budget,
    _public_dns,
    _request,
    _reuse_authority,
    _reuse_policy,
    _source_policy,
    _temporal_policy,
)
from tests.semantic_extraction.test_semantic_extraction_reuse import _pipeline


def test_reobservation_benchmark_reruns_only_what_changed(tmp_path: Path) -> None:
    full = run_reobservation_benchmark(tmp_path / "full", incremental=False)
    incremental = run_reobservation_benchmark(tmp_path / "incremental", incremental=True)

    assert incremental["plans"] == [
        (0, ("market-mode", "market-currentness", "reputation")),  # initial state
        (1, ()),  # identical refresh, still CURRENT
        (2, ()),
        (3, ("market-mode", "market-currentness", "reputation")),  # real content change
        (4, ()),
        (40, ("market-currentness",)),  # refresh after aging: STALE -> CURRENT only
        (41, ()),
    ]
    measured = ("structured_calls", "dimensions_reevaluated", "research_items_created")
    assert {key: full[key] for key in measured} == {
        "structured_calls": 14,
        "dimensions_reevaluated": 21,
        "research_items_created": 7,
    }
    assert {key: incremental[key] for key in measured} == {
        "structured_calls": 5,
        "dimensions_reevaluated": 7,
        "research_items_created": 3,
    }
    assert (full["total_requests"], incremental["total_requests"]) == (24, 15)
    assert full["semantic_provider_calls"] == incremental["semantic_provider_calls"] == 3
    assert incremental["full_fallbacks"] == 0
    # Same conclusions and same final state; the open research gap stays runnable.
    assert incremental["final_answers"] == full["final_answers"]
    assert incremental["final_state"] == full["final_state"]
    assert incremental["research_runnable_at_end"] == full["research_runnable_at_end"] == 1


def _datum(name: str, value: str, observation: str, day: int, source: str = "src:a"):  # type: ignore[no-untyped-def]
    return RichStateDatum(
        name=name,
        value=value,
        observation_id=observation,
        representation_id=f"rep:{observation}",
        source_ref=source,
        observed_at=NOW + timedelta(days=day),
    )


def test_delta_separates_content_change_from_refresh() -> None:
    before = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=(
            _datum("same", "x", "o1", 0),
            _datum("value", "x", "o1", 0),
            _datum("source", "x", "o1", 0),
            _datum("removed", "x", "o1", 0),
        ),
    )
    after = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=(
            _datum("same", "x", "o2", 1),
            _datum("value", "y", "o2", 1),
            _datum("source", "x", "o2", 1, source="src:b"),
            _datum("added", "x", "o2", 1),
        ),
    )

    delta = rich_state_delta(before, after)

    assert delta.refreshed_fields == {"same"}
    assert delta.semantic_fields == {"value", "source", "removed", "added"}
    assert rich_state_delta(before, before).refreshed_fields == frozenset()


def _empty():  # type: ignore[no-untyped-def]
    return compile_rich_subject_state(subject_id="org:acme", contributions=())


def _run(tmp_path, sensor, representer, observations, *, day, prior, request=None):  # type: ignore[no-untyped-def]
    policy = _source_policy()
    return execute_prime_source_slice(
        execution_id=f"run:{day}:{id(prior)}",
        seed=_authorized_seed(),
        code_sha="abc123",
        occurred_at=NOW + timedelta(days=day),
        observation_memory=observations,
        learning_memory=SqliteLearningMemory(tmp_path / "learning.sqlite3"),
        request=request or _request(policy),
        source_policy=policy,
        source_acquirer=sensor,
        representation_port=representer,
        prior_rich_state=prior,
        contracts=CONTRACTS[:2],
        routing_policies=ROUTING[:2],
        research_decisions=(),
        execution_controller=_budget(),
        ports=PrimeExecutionPorts(_CountingExecutor(), _CountingExecutor(), _CountingExecutor()),
        reuse_policy=_reuse_policy(),
        temporal_currentness_policy=_temporal_policy(),
        ingested_observation_reuse_authority=_reuse_authority(),
    )


def test_refresh_trace_keeps_new_provenance_and_names_the_transition(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    policy = _source_policy()
    request = _request(policy)
    _run(tmp_path, sensor, representer, observations, day=0, prior=_empty())
    prior = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=representation_state_data(
            representer.represent(request=request, observation=sensor.observe(request, policy)),
            observation_slot="website",
        ),
    )
    clock.now = NOW + timedelta(days=1)
    refresh = _run(tmp_path, sensor, representer, observations, day=1, prior=prior)
    clock.now = NOW + timedelta(days=45)
    aged = _run(tmp_path, sensor, representer, observations, day=45, prior=prior)

    assert refresh.prime_plan is None
    assert refresh.semantic_change_fields == frozenset()
    assert refresh.refreshed_fields and refresh.currentness_transition is None
    assert refresh.rich_state_fingerprint != aged.rich_state_fingerprint
    assert aged.currentness_transition == (Currentness.STALE, Currentness.CURRENT)
    assert aged.prime_plan is not None
    assert [item.dimension_id for item in aged.prime_plan.items] == ["market-currentness"]


def test_stale_data_of_another_slot_is_still_refused_as_current_state(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    policy = _source_policy()
    request = _request(policy)
    _run(tmp_path, sensor, representer, observations, day=0, prior=_empty())
    website = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=representation_state_data(
            representer.represent(request=request, observation=sensor.observe(request, policy)),
            observation_slot="website",
        ),
    )
    careers = replace(request, request_id="request:acme:careers:1", observation_slot="careers")

    clock.now = NOW + timedelta(days=45)
    with pytest.raises(ObservationReuseRejected) as rejected:
        _run(
            tmp_path,
            sensor,
            representer,
            observations,
            day=45,
            prior=website,
            request=careers,
        )

    assert rejected.value.decision.reason.value == "STALE_FOR_CURRENT_USE"


def test_authority_refresh_requires_lineage_and_keeps_the_same_work(tmp_path: Path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    authority = PrimeResearchAuthority(
        subject_id="org:acme",
        state_fingerprint="state:planned",
        authorized_work_keys=frozenset({"observe-work:a"}),
        observation_watermark_at=NOW,
        observation_watermark_id="obs:1",
        valid_until=NOW + timedelta(days=30),
        temporal_policy_id="prime-currentness",
        temporal_policy_version="aud06-v1",
    )
    memory.replace_prime_authority(authority)
    refresh = {
        "subject_id": "org:acme",
        "observation_watermark_at": NOW + timedelta(days=1),
        "observation_watermark_id": "obs:2",
        "valid_until": NOW + timedelta(days=31),
        "temporal_policy_id": "prime-currentness",
        "temporal_policy_version": "aud06-v1",
    }

    assert not refresh_prime_research_authority(
        memory, prior_observation_ids=frozenset({"obs:unrelated"}), **refresh
    )
    assert memory.prime_authority("org:acme") == authority
    assert refresh_prime_research_authority(
        memory, prior_observation_ids=frozenset({"obs:1"}), **refresh
    )
    refreshed = memory.prime_authority("org:acme")
    assert refreshed is not None
    assert refreshed.authorized_work_keys == authority.authorized_work_keys
    assert refreshed.state_fingerprint == authority.state_fingerprint
    assert (refreshed.observation_watermark_id, refreshed.valid_until) == (
        "obs:2",
        NOW + timedelta(days=31),
    )
    # Never moves backwards.
    assert not refresh_prime_research_authority(
        memory, prior_observation_ids=frozenset({"obs:2"}), **refresh
    )
