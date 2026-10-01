from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationMode,
    ObservationRecord,
    ObservationReuseAuthority,
    ObservationReuseContext,
    ObservationReusePolicy,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
    ReuseDisposition,
    ReusePurpose,
    ReuseReason,
    ReuseTargetScope,
    evaluate_observation_reuse,
    select_reusable_observations,
)
from domain.evidence.epistemics import Currentness
from pipeline.observation_memory import SqliteObservationMemory

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
POLICY = ObservationReusePolicy("observation-reuse", "1")


def _authority(
    *,
    rights: ObservationRightsStatus = ObservationRightsStatus.PERMITTED,
    access: ObservationAccessStatus = ObservationAccessStatus.ACCESSIBLE,
    scope: ObservationReuseScope = ObservationReuseScope.GLOBAL_PUBLIC,
    owner: str | None = None,
    provenance: str | None = "provenance:source-policy:1",
    currentness: Currentness = Currentness.CURRENT,
    subjects: tuple[str, ...] = ("org:acme",),
    purposes: tuple[str, ...] = (
        ReusePurpose.CURRENT_STATE.value,
        ReusePurpose.HISTORICAL_REFERENCE.value,
    ),
) -> ObservationReuseAuthority:
    return ObservationReuseAuthority(
        rights_status=rights,
        access_status=access,
        scope=scope,
        scope_owner_id=owner,
        provenance_ref=provenance,
        currentness=currentness,
        applicable_subject_ids=subjects,
        applicable_purposes=purposes,
    )


def _observation(
    *,
    observation_id: str = "obs:1",
    subject_id: str = "org:acme",
    authority: ObservationReuseAuthority | None = None,
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id=subject_id,
            source_ref="https://public.example/acme",
            source_type="PUBLIC_WEB",
            observed_at=NOW,
            content_fingerprint="sha256:content",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_artifact_ref="artifact:obs:1",
        fields=(ObservedField("document.home.visible_text", "ACME industrial pumps"),),
        reuse_authority=_authority() if authority is None else authority,
    )


def _context(
    *,
    tenant_id: str = "tenant:1",
    target_scope: ReuseTargetScope = ReuseTargetScope.TENANT_PRIVATE,
    purpose: ReusePurpose = ReusePurpose.CURRENT_STATE,
    subject_id: str = "org:acme",
) -> ObservationReuseContext:
    return ObservationReuseContext(
        subject_id=subject_id,
        xeed_id="xeed:1",
        tenant_id=tenant_id,
        target_scope=target_scope,
        purpose=purpose,
    )


def test_public_observation_is_not_reusable_without_explicit_rights() -> None:
    observation = _observation(authority=_authority(rights=ObservationRightsStatus.UNKNOWN))

    decision = evaluate_observation_reuse(
        observation,
        context=_context(),
        policy=POLICY,
    )

    assert decision.disposition is ReuseDisposition.REJECT
    assert decision.reason is ReuseReason.RIGHTS_UNKNOWN


def test_prohibited_rights_and_inaccessible_are_distinct_from_false() -> None:
    prohibited = evaluate_observation_reuse(
        _observation(authority=_authority(rights=ObservationRightsStatus.PROHIBITED)),
        context=_context(),
        policy=POLICY,
    )
    inaccessible = evaluate_observation_reuse(
        _observation(authority=_authority(access=ObservationAccessStatus.INACCESSIBLE)),
        context=_context(),
        policy=POLICY,
    )

    assert prohibited.reason is ReuseReason.RIGHTS_PROHIBITED
    assert inaccessible.reason is ReuseReason.INACCESSIBLE
    assert prohibited.disposition is ReuseDisposition.REJECT
    assert inaccessible.disposition is ReuseDisposition.REJECT


def test_private_observation_can_stay_private_but_cannot_leak_global() -> None:
    private = _observation(
        authority=_authority(
            scope=ObservationReuseScope.TENANT_PRIVATE,
            owner="tenant:1",
        )
    )

    same_tenant = evaluate_observation_reuse(
        private,
        context=_context(tenant_id="tenant:1"),
        policy=POLICY,
    )
    other_tenant = evaluate_observation_reuse(
        private,
        context=_context(tenant_id="tenant:2"),
        policy=POLICY,
    )
    global_world = evaluate_observation_reuse(
        private,
        context=_context(target_scope=ReuseTargetScope.GLOBAL_WORLD),
        policy=POLICY,
    )

    assert same_tenant.disposition is ReuseDisposition.ALLOW
    assert other_tenant.reason is ReuseReason.PRIVATE_SCOPE_MISMATCH
    assert global_world.reason is ReuseReason.PRIVATE_SCOPE_GLOBAL_LEAK


def test_stale_is_rejected_for_current_state_but_can_support_historical_reference() -> None:
    stale = _observation(authority=_authority(currentness=Currentness.STALE))

    current = evaluate_observation_reuse(
        stale,
        context=_context(purpose=ReusePurpose.CURRENT_STATE),
        policy=POLICY,
    )
    historical = evaluate_observation_reuse(
        stale,
        context=_context(purpose=ReusePurpose.HISTORICAL_REFERENCE),
        policy=POLICY,
    )

    assert current.disposition is ReuseDisposition.REJECT
    assert current.reason is ReuseReason.STALE_FOR_CURRENT_USE
    assert historical.disposition is ReuseDisposition.ALLOW


def test_unknown_currentness_is_not_silently_treated_as_current_or_historical() -> None:
    unknown = _observation(authority=_authority(currentness=Currentness.UNKNOWN))

    for purpose in (ReusePurpose.CURRENT_STATE, ReusePurpose.HISTORICAL_REFERENCE):
        decision = evaluate_observation_reuse(
            unknown,
            context=_context(purpose=purpose),
            policy=POLICY,
        )
        assert decision.disposition is ReuseDisposition.REJECT
        assert decision.reason is ReuseReason.CURRENTNESS_UNKNOWN


def test_subject_and_purpose_applicability_are_exact() -> None:
    wrong_subject = evaluate_observation_reuse(
        _observation(authority=_authority(subjects=("org:other",))),
        context=_context(),
        policy=POLICY,
    )
    wrong_purpose = evaluate_observation_reuse(
        _observation(authority=_authority(purposes=(ReusePurpose.HISTORICAL_REFERENCE.value,))),
        context=_context(),
        policy=POLICY,
    )

    assert wrong_subject.reason is ReuseReason.SUBJECT_NOT_APPLICABLE
    assert wrong_purpose.reason is ReuseReason.PURPOSE_NOT_APPLICABLE


def test_selection_keeps_rejected_observation_in_memory_but_out_of_reuse(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    allowed = _observation(observation_id="obs:allowed")
    rejected = _observation(
        observation_id="obs:blocked",
        authority=_authority(rights=ObservationRightsStatus.UNKNOWN),
    )
    memory.append(allowed)
    memory.append(rejected)

    selection = select_reusable_observations(
        memory,
        context=_context(),
        policy=POLICY,
    )

    assert selection.observation_ids == frozenset({"obs:allowed"})
    assert {item.record.observation_id for item in memory.for_subject("org:acme")} == {
        "obs:allowed",
        "obs:blocked",
    }
    assert {decision.reason for decision in selection.decisions} == {
        ReuseReason.ALLOWED,
        ReuseReason.RIGHTS_UNKNOWN,
    }


def test_reuse_authority_round_trips_durably(tmp_path: Path) -> None:
    database = tmp_path / "observations.sqlite3"
    observation = _observation(
        authority=_authority(
            scope=ObservationReuseScope.TENANT_PRIVATE,
            owner="tenant:1",
        )
    )
    memory = SqliteObservationMemory(database)
    assert memory.append(observation) is True

    reopened = SqliteObservationMemory(database)
    assert reopened.for_subject("org:acme") == (observation,)


def test_legacy_observation_rows_migrate_to_restricted_unknown_reuse(tmp_path: Path) -> None:
    database = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE observations (
                observation_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                source_type TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                content_fingerprint TEXT NOT NULL,
                mode TEXT NOT NULL,
                raw_content TEXT,
                raw_artifact_ref TEXT,
                CHECK (raw_content IS NOT NULL OR raw_artifact_ref IS NOT NULL)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE observation_fields (
                observation_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                field_value TEXT NOT NULL,
                field_position INTEGER NOT NULL,
                PRIMARY KEY (observation_id, field_name)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "obs:legacy",
                "org:acme",
                "https://public.example/acme",
                "PUBLIC_WEB",
                NOW.isoformat(),
                "sha256:legacy",
                ObservationMode.DETERMINISTIC_SENSOR.value,
                None,
                "artifact:legacy",
            ),
        )

    reopened = SqliteObservationMemory(database)
    observation = reopened.for_subject("org:acme")[0]

    assert observation.reuse_authority.rights_status is ObservationRightsStatus.UNKNOWN
    assert observation.reuse_authority.scope is ObservationReuseScope.RESTRICTED
    assert observation.reuse_authority.currentness is Currentness.UNKNOWN

    decision = evaluate_observation_reuse(
        observation,
        context=_context(),
        policy=POLICY,
    )
    assert decision.disposition is ReuseDisposition.REJECT


def test_missing_provenance_blocks_reuse_even_when_rights_are_permitted() -> None:
    observation = _observation(authority=replace(_authority(), provenance_ref=None))

    decision = evaluate_observation_reuse(
        observation,
        context=_context(),
        policy=POLICY,
    )

    assert decision.reason is ReuseReason.PROVENANCE_MISSING


def test_historical_currentness_is_not_current_but_remains_historical_evidence() -> None:
    historical = _observation(authority=_authority(currentness=Currentness.HISTORICAL))

    current = evaluate_observation_reuse(
        historical,
        context=_context(purpose=ReusePurpose.CURRENT_STATE),
        policy=POLICY,
    )
    reference = evaluate_observation_reuse(
        historical,
        context=_context(purpose=ReusePurpose.HISTORICAL_REFERENCE),
        policy=POLICY,
    )

    assert current.disposition is ReuseDisposition.REJECT
    assert current.reason is ReuseReason.HISTORICAL_FOR_CURRENT_USE
    assert reference.disposition is ReuseDisposition.ALLOW
