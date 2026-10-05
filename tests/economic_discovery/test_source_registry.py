from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from application.economic_discovery.observation_memory import (
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
    observation_reuse_authority_from_payload,
    observation_reuse_authority_payload,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.source_registry import (
    RobotsDecision,
    RobotsRequirement,
    SourceRatePolicy,
    SourceRegistryEntry,
    SourceRegistryReason,
    SourceRegistryRejected,
    SourceRetentionPolicy,
    StaticSourceRegistry,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.source_acquisition import SourceTargetRule
from domain.evidence import Currentness

TEMPORAL = TemporalCurrentnessPolicy(
    policy_id="registry-currentness",
    version="1",
    stale_after=timedelta(days=30),
    historical_after=timedelta(days=90),
)


def _entry(**changes: object) -> SourceRegistryEntry:
    base = SourceRegistryEntry(
        source_id="official-homepage",
        version="2026-10-05",
        source_type="OFFICIAL_WEB",
        instrument_ref="stdlib-pinned-http/0.2",
        decision_basis="bounded public corporate homepage observation",
        targets=(SourceTargetRule("example.test", "/", ("https",)),),
        allowed_purposes=(ReusePurpose.CURRENT_STATE, ReusePurpose.HISTORICAL_REFERENCE),
        rights_status=ObservationRightsStatus.PERMITTED,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        reuse_scope=ObservationReuseScope.GLOBAL_PUBLIC,
        reuse_reason="registered public observation may be reused with provenance/currentness",
        temporal_policy=TEMPORAL,
        retention_policy=SourceRetentionPolicy(
            policy_id="public-evidence-retention",
            version="1",
            raw_retention_days=90,
            metadata_retention_days=365,
        ),
        rate_policy=SourceRatePolicy(
            policy_id="public-root-rate",
            version="1",
            max_requests=6,
            window_seconds=60,
        ),
        robots_requirement=RobotsRequirement.NOT_REQUIRED_SINGLE_DOCUMENT,
        robots_decision=RobotsDecision.NOT_APPLICABLE,
        robots_policy_ref="robots:single-document:v1",
        currentness=Currentness.CURRENT,
        timeout_ms=8_000,
    )
    return replace(base, **changes)


def _authorize(entry: SourceRegistryEntry):
    return StaticSourceRegistry((entry,)).authorize(
        source_id=entry.source_id,
        request_id="request:1",
        subject_id="org:example",
        observation_slot="website",
        target_uri="https://example.test/",
        source_type="OFFICIAL_WEB",
        purpose=ReusePurpose.CURRENT_STATE,
        instrument_ref="stdlib-pinned-http/0.2",
    )


def test_registry_binds_dispatch_reuse_currentness_rate_and_retention() -> None:
    entry = _entry()

    authorized = _authorize(entry)

    assert authorized.source_fingerprint == entry.fingerprint
    assert authorized.dispatch_policy.policy_id == "source-registry:official-homepage"
    assert authorized.dispatch_policy.policy_version == entry.version
    assert authorized.request.policy_version == entry.version
    assert authorized.request.policy_fingerprint == authorized.dispatch_policy.fingerprint
    assert authorized.reuse_authority.authority_id == entry.source_id
    assert authorized.reuse_authority.authority_version == entry.version
    assert authorized.reuse_authority.scope is ObservationReuseScope.GLOBAL_PUBLIC
    assert authorized.reuse_authority.applicable_subject_ids == ("org:example",)
    assert authorized.reuse_authority.applicable_purposes == (ReusePurpose.CURRENT_STATE.value,)
    assert authorized.reuse_authority.provenance_ref == (
        f"source-registry:{entry.source_id}@{entry.version}:{entry.fingerprint}"
    )
    assert authorized.reuse_authority.retention_policy_ref == "public-evidence-retention@1"
    assert authorized.reuse_authority.rate_policy_ref == "public-root-rate@1"
    assert authorized.reuse_authority.robots_policy_ref == "robots:single-document:v1"
    assert authorized.temporal_policy is TEMPORAL


@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        (
            _entry(rights_status=ObservationRightsStatus.UNKNOWN),
            SourceRegistryReason.RIGHTS_UNKNOWN,
        ),
        (
            _entry(rights_status=ObservationRightsStatus.PROHIBITED),
            SourceRegistryReason.RIGHTS_PROHIBITED,
        ),
        (
            _entry(access_status=ObservationAccessStatus.INACCESSIBLE),
            SourceRegistryReason.SOURCE_INACCESSIBLE,
        ),
    ],
)
def test_registry_fails_closed_when_rights_or_access_do_not_authorize(
    entry: SourceRegistryEntry,
    reason: SourceRegistryReason,
) -> None:
    with pytest.raises(SourceRegistryRejected) as exc_info:
        _authorize(entry)

    assert exc_info.value.reason is reason


@pytest.mark.parametrize(
    ("robots_decision", "reason"),
    [
        (RobotsDecision.UNKNOWN, SourceRegistryReason.ROBOTS_UNKNOWN),
        (RobotsDecision.PROHIBITED, SourceRegistryReason.ROBOTS_PROHIBITED),
    ],
)
def test_required_robots_metadata_fails_closed_without_permission(
    robots_decision: RobotsDecision,
    reason: SourceRegistryReason,
) -> None:
    entry = _entry(
        robots_requirement=RobotsRequirement.REQUIRED,
        robots_decision=robots_decision,
        robots_policy_ref="robots:required:v1",
    )

    with pytest.raises(SourceRegistryRejected) as exc_info:
        _authorize(entry)

    assert exc_info.value.reason is reason


def test_registry_rejects_unregistered_purpose_before_dispatch() -> None:
    entry = _entry(allowed_purposes=(ReusePurpose.HISTORICAL_REFERENCE,))
    registry = StaticSourceRegistry((entry,))

    with pytest.raises(SourceRegistryRejected) as exc_info:
        registry.authorize(
            source_id=entry.source_id,
            request_id="request:purpose",
            subject_id="org:example",
            observation_slot="website",
            target_uri="https://example.test/",
            source_type=entry.source_type,
            purpose=ReusePurpose.CURRENT_STATE,
            instrument_ref=entry.instrument_ref,
        )

    assert exc_info.value.reason is SourceRegistryReason.PURPOSE_NOT_ALLOWED


def test_registry_rejects_unregistered_instrument_before_dispatch() -> None:
    entry = _entry()

    with pytest.raises(SourceRegistryRejected) as exc_info:
        StaticSourceRegistry((entry,)).authorize(
            source_id=entry.source_id,
            request_id="request:instrument",
            subject_id="org:example",
            observation_slot="website",
            target_uri="https://example.test/",
            source_type=entry.source_type,
            purpose=ReusePurpose.CURRENT_STATE,
            instrument_ref="other-http/9",
        )

    assert exc_info.value.reason is SourceRegistryReason.INSTRUMENT_NOT_AUTHORIZED


def test_registry_authority_metadata_round_trips_without_losing_scope_or_policy_refs() -> None:
    authority = _authorize(_entry()).reuse_authority

    restored = observation_reuse_authority_from_payload(
        observation_reuse_authority_payload(authority)
    )

    assert restored == authority
