from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    ObservationMode,
    ObservationRecord,
)
from application.economic_discovery.continuous_observation import schedule_prime_research
from application.economic_discovery.observation_memory import GovernedObservation, ObservedField
from application.economic_discovery.prime import PrimeControlPlan, PrimeRoute, PrimeWorkItem
from application.economic_discovery.research_revalidation import (
    PrimeCurrentnessResearchRevalidator,
)
from application.economic_discovery.research_value import ResearchValueDisposition
from pipeline.continuous_observation.sqlite_store import SqliteSharedObservationWorkMemory
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory

NOW = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)
VALID_UNTIL = NOW + timedelta(days=30)


def _observation(observation_id: str, *, minute: int = 0, value: str = "Spain"):
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id="org:acme",
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=NOW + timedelta(minutes=minute),
            content_fingerprint=f"sha256:{observation_id}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=f"snapshot:{observation_id}",
        fields=(ObservedField("markets", value),),
    )


def _plan(*, include_research: bool = True, fingerprint: str = "rich-state:1") -> PrimeControlPlan:
    items = ()
    if include_research:
        items = (
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
        )
    return PrimeControlPlan(
        subject_id="org:acme",
        state_fingerprint=fingerprint,
        items=items,
    )


def _schedule(memory, plan):
    return schedule_prime_research(
        memory,
        plan=plan,
        requester_ref="prime:1",
        observation_watermark_at=NOW,
        observation_watermark_id="obs:1",
        valid_until=VALID_UNTIL,
        temporal_policy_id="currentness",
        temporal_policy_version="1",
    )


def test_current_prime_authority_survives_restart_and_authorizes_exact_intent(tmp_path) -> None:
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    observations.append(_observation("obs:1"))

    path = tmp_path / "research.sqlite3"
    memory = SqliteSharedObservationWorkMemory(path)
    intent = _schedule(memory, _plan())[0]

    reopened = SqliteSharedObservationWorkMemory(path)
    authority = reopened.prime_authority("org:acme")
    assert authority is not None
    assert authority.state_fingerprint == "rich-state:1"
    assert intent.work_key in authority.authorized_work_keys
    work = reopened.get(intent.work_key)
    assert work is not None
    assert PrimeCurrentnessResearchRevalidator(
        observation_memory=observations,
        research_memory=reopened,
    ).may_run(work, now=NOW + timedelta(minutes=1))


def test_rich_state_fingerprint_is_not_compared_to_observation_state_fingerprint(tmp_path) -> None:
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    observations.append(_observation("obs:1"))
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    intent = _schedule(memory, _plan(fingerprint="definitely-not-observation-fingerprint"))[0]
    work = memory.get(intent.work_key)
    assert work is not None

    assert PrimeCurrentnessResearchRevalidator(
        observation_memory=observations,
        research_memory=memory,
    ).may_run(work, now=NOW + timedelta(minutes=1))


def test_reobservation_invalidates_old_work_even_when_value_is_unchanged(tmp_path) -> None:
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    observations.append(_observation("obs:1"))
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    intent = _schedule(memory, _plan())[0]
    work = memory.get(intent.work_key)
    assert work is not None

    observations.append(_observation("obs:2", minute=5, value="Spain"))
    assert not PrimeCurrentnessResearchRevalidator(
        observation_memory=observations,
        research_memory=memory,
    ).may_run(work, now=NOW + timedelta(minutes=6))


def test_temporal_expiry_invalidates_authority_without_new_observation(tmp_path) -> None:
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    observations.append(_observation("obs:1"))
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    intent = _schedule(memory, _plan())[0]
    work = memory.get(intent.work_key)
    assert work is not None

    revalidator = PrimeCurrentnessResearchRevalidator(
        observation_memory=observations,
        research_memory=memory,
    )
    assert revalidator.may_run(work, now=VALID_UNTIL - timedelta(seconds=1))
    assert not revalidator.may_run(work, now=VALID_UNTIL)


def test_legacy_prime_authority_without_temporal_metadata_fails_closed(tmp_path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute(
            """
            CREATE TABLE prime_research_authority (
                subject_id TEXT PRIMARY KEY,
                state_fingerprint TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            INSERT INTO prime_research_authority(subject_id, state_fingerprint)
            VALUES ('org:acme', 'rich-state:legacy')
            """
        )

    memory = SqliteSharedObservationWorkMemory(path)
    assert memory.prime_authority("org:acme") is None


def test_new_prime_snapshot_without_dimension_revokes_old_research_authority(tmp_path) -> None:
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    observations.append(_observation("obs:1"))
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    intent = _schedule(memory, _plan())[0]
    work = memory.get(intent.work_key)
    assert work is not None

    _schedule(memory, _plan(include_research=False))
    authority = memory.prime_authority("org:acme")
    assert authority is not None
    assert authority.authorized_work_keys == frozenset()
    assert not PrimeCurrentnessResearchRevalidator(
        observation_memory=observations,
        research_memory=memory,
    ).may_run(work, now=NOW + timedelta(minutes=1))
