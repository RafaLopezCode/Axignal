from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_projection.subscriber_runtime import (
    SubscriberEconomicRuntime,
    SubscriberRuntimeStatus,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    TrustedRequestContext,
    XeedReadError,
)
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal
from domain.xeed.model import Xeed
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.subscriber_projection.opportunity_store import (
    SqliteSubscriberOpportunityProjectionStore,
)
from pipeline.subscriber_projection.sqlite_store import SqliteSubscriberEconomicOutputStore
from tests.economic_discovery.test_first_vertical_e2e import _run_fixture


class _Auth:
    def __init__(self, *, principals: dict[str, Principal], xeeds: dict[str, Xeed]) -> None:
        self.principals = principals
        self.xeeds = xeeds
        self.memberships: set[tuple[str, str]] = set()

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        return self.principals.get(principal_id)

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        return (principal_id, tenant_id) in self.memberships

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None:
        return self.xeeds.get(xeed_id)


class _Organizations:
    def __init__(self, organizations: dict[str, Organization]) -> None:
        self.organizations = organizations

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organizations.get(organization_id)


def _real_result(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    result, *_ = _run_fixture(monkeypatch, tmp_path)
    return result


def _runtime(
    tmp_path: Path, result: Any
) -> tuple[SubscriberEconomicRuntime, TrustedRequestContext, Xeed]:
    wire = result.human_output.to_wire()
    organization_id = str(wire["subject_ref"])
    org = Organization(OrganizationId(organization_id), "Arbor Cooling")
    xeed = Xeed(XeedId("xeed:subscriber:1"), TenantId("tenant:one"), org.id, "Arbor Cooling")
    auth = _Auth(
        principals={"principal:one": Principal(PrincipalId("principal:one"))}, xeeds={xeed.id: xeed}
    )
    auth.memberships.add(("principal:one", "tenant:one"))
    context = TrustedRequestContext(PrincipalId("principal:one"), TenantId("tenant:one"))

    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    subject_refs = {
        str(item.datum.observation_id) for item in result.subject_source.state.observations
    }
    activity_id = str(wire["activity_subject_ref"])
    appended: set[str] = set()
    for item in wire["evidence"]:
        assert isinstance(item, dict)
        observation_id = str(item["observation_ref"])
        if observation_id in appended:
            continue
        appended.add(observation_id)
        subject_id = organization_id if observation_id in subject_refs else activity_id
        source_ref = str(item["source_ref"])
        observed_at = datetime.fromisoformat(str(item["observed_at"]))
        authority = ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.PERMITTED,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.GLOBAL_PUBLIC,
            provenance_ref=f"provenance:{observation_id}",
            currentness=Currentness.CURRENT,
            applicable_subject_ids=(subject_id,),
            applicable_purposes=("CURRENT_STATE", "HISTORICAL_REFERENCE"),
            authority_id="test-source-policy",
            authority_version="1",
        )
        memory.append(
            GovernedObservation(
                record=ObservationRecord(
                    observation_id=observation_id,
                    subject_id=subject_id,
                    source_ref=source_ref,
                    source_type=str(item["source_type"]),
                    observed_at=observed_at,
                    content_fingerprint=f"fingerprint:{observation_id}",
                    mode=ObservationMode.DETERMINISTIC_SENSOR,
                ),
                raw_content=str(item["excerpt"]),
                reuse_authority=authority,
            )
        )
    runtime = SubscriberEconomicRuntime(
        authorized_xeeds=AuthorizedXeedReader(auth, auth, auth),
        organization_reader=AuthorizedXeedOrganizationReader(_Organizations({org.id: org})),
        observation_memory=memory,
        output_store=SqliteSubscriberEconomicOutputStore(tmp_path / "subscriber-output.sqlite3"),
        opportunity_store=SqliteSubscriberOpportunityProjectionStore(
            tmp_path / "subscriber-output.sqlite3"
        ),
        reuse_policy=ObservationReusePolicy("subscriber-read", "1"),
        temporal_policy=TemporalCurrentnessPolicy(
            "subscriber-currentness", "1", timedelta(days=7), timedelta(days=30)
        ),
        code_sha="test-sha",
    )
    return runtime, context, xeed


def test_runtime_persists_and_reads_real_eb04_output_with_memory_lineage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = _real_result(monkeypatch, tmp_path)
    runtime, context, xeed = _runtime(tmp_path, result)

    assert runtime.publish(context, xeed.id, result) is True
    assert runtime.publish(context, xeed.id, result) is False
    read = runtime.read(context, xeed.id, result.reasoning.vector.evaluated_at)

    assert read.status is SubscriberRuntimeStatus.SUCCESS
    assert read.reason is None
    assert read.projection["organization"] == {
        "id": result.human_output.to_wire()["subject_ref"],
        "name": "Arbor Cooling",
    }
    nodes = read.projection["nodes"]
    assert isinstance(nodes, list) and len(nodes) == 1
    signal = nodes[0]
    assert isinstance(signal, dict)
    assert (
        signal["epistemicState"] == result.human_output.result.interpretation.epistemic_state.value
    )
    assert signal["currentness"] == "CURRENT"
    assert signal["sourceRefs"]
    assert read.projection["economicOutput"]["output_id"] == result.human_output.output_id
    temporal = read.projection["temporalHistory"]
    assert temporal["disposition"] == "SINGLE_OBSERVATION"


def test_runtime_keeps_memory_measurements_visible_when_economic_output_is_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = _real_result(monkeypatch, tmp_path)
    runtime, context, xeed = _runtime(tmp_path, result)

    read = runtime.read(context, xeed.id, result.reasoning.vector.evaluated_at)

    assert read.status is SubscriberRuntimeStatus.INSUFFICIENT_EVIDENCE
    assert "No persisted evidence-backed economic output" in (read.reason or "")
    assert read.projection["nodes"] == []
    assert read.projection["digitalRepresentation"]["state"] == "NOT_MEASURED"
    assert "No condition-bound" in read.projection["digitalRepresentation"]["reason"]
    temporal = read.projection["temporalHistory"]
    assert temporal["disposition"] == "SINGLE_OBSERVATION"
    assert temporal["items"][0]["sourceRef"]


def test_runtime_downgrades_output_when_observation_memory_is_not_current(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = _real_result(monkeypatch, tmp_path)
    runtime, context, xeed = _runtime(tmp_path, result)
    runtime.publish(context, xeed.id, result)

    read = runtime.read(context, xeed.id, result.reasoning.vector.evaluated_at + timedelta(days=8))

    assert read.status is SubscriberRuntimeStatus.SUCCESS
    assert read.reason is not None
    signal = read.projection["nodes"][0]
    assert signal["epistemicState"] == "UNKNOWN"
    assert signal["currentness"] == "STALE"
    assert read.projection["today"]["disposition"] == "EMPTY"
    assert read.projection["economicOutput"]["epistemic_state"] == "UNKNOWN"


def test_runtime_rechecks_membership_before_loading_private_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result = _real_result(monkeypatch, tmp_path)
    runtime, context, xeed = _runtime(tmp_path, result)
    runtime.publish(context, xeed.id, result)
    unauthorized = TrustedRequestContext(PrincipalId("principal:other"), context.tenant_id)

    with pytest.raises(XeedReadError):
        runtime.read(unauthorized, xeed.id, result.reasoning.vector.evaluated_at)
