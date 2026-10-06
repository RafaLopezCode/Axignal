"""Persistence and authorization contracts for opportunity subscriber output."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

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
from application.observation_intelligence import (
    ObservationBudget,
    OperationalLearning,
    SourceFindings,
    SourceRegistry,
    StopPolicy,
    build_strategy,
    run_observation_loop,
)
from application.observation_intelligence.loop import SourceObservationPort
from application.subscriber_projection.subscriber_runtime import (
    SubscriberEconomicRuntime,
    SubscriberOpportunityProjectionError,
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
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.subscriber_projection.opportunity_store import (
    SqliteSubscriberOpportunityProjectionStore,
)
from pipeline.subscriber_projection.sqlite_store import SqliteSubscriberEconomicOutputStore
from tests.observation_intelligence.scenarios import AS_OF, HOMEPAGES, context_for
from tests.observation_intelligence.ted_fixture import FixtureTedTransport


class _IdentityStore:
    def __init__(self, principal: Principal, xeed: Xeed) -> None:
        self.principal = principal
        self.xeed = xeed
        self.memberships = {(principal.id, xeed.tenant_id)}

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        return self.principal if principal_id == self.principal.id else None

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        return (principal_id, tenant_id) in self.memberships

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None:
        return self.xeed if xeed_id == self.xeed.id else None


class _WebsiteStub:
    def observe(self, action, source):  # type: ignore[no-untyped-def]
        return SourceFindings(source.source_id, AS_OF, 1, 0, 0)


class _Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


def _runtime(tmp_path: Path):
    organization = Organization(OrganizationId("org:solartec"), "Solartec Levante")
    xeed = Xeed(XeedId("xeed:solartec"), TenantId("tenant:solar"), organization.id)
    principal = Principal(PrincipalId("principal:solar"))
    identity = _IdentityStore(principal, xeed)
    request = TrustedRequestContext(principal.id, xeed.tenant_id)
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    runtime = SubscriberEconomicRuntime(
        authorized_xeeds=AuthorizedXeedReader(identity, identity, identity),
        organization_reader=AuthorizedXeedOrganizationReader(_Organizations(organization)),
        observation_memory=memory,
        output_store=SqliteSubscriberEconomicOutputStore(tmp_path / "subscriber.sqlite3"),
        opportunity_store=SqliteSubscriberOpportunityProjectionStore(
            tmp_path / "subscriber.sqlite3"
        ),
        reuse_policy=ObservationReusePolicy("opportunity-subscriber", "1"),
        temporal_policy=TemporalCurrentnessPolicy(
            "opportunity-subscriber-currentness", "1", timedelta(days=7), timedelta(days=30)
        ),
        code_sha="test-opportunity-runtime",
    )
    return runtime, memory, request, xeed, organization


def _append_capability_source(memory: SqliteObservationMemory, organization: Organization) -> None:
    observation_id = "obs:xeed:solartec:homepage"
    source_ref = "https://solartec.example/"
    observed_at = AS_OF - timedelta(hours=1)
    memory.append(
        GovernedObservation(
            record=ObservationRecord(
                observation_id=observation_id,
                subject_id=organization.id,
                source_ref=source_ref,
                source_type="PUBLIC_WEBSITE",
                observed_at=observed_at,
                content_fingerprint="homepage-fingerprint",
                mode=ObservationMode.DETERMINISTIC_SENSOR,
            ),
            raw_content=HOMEPAGES["xeed:solartec"],
            raw_artifact_ref="artifact:homepage:solar",
            reuse_authority=ObservationReuseAuthority(
                rights_status=ObservationRightsStatus.PERMITTED,
                access_status=ObservationAccessStatus.ACCESSIBLE,
                scope=ObservationReuseScope.GLOBAL_PUBLIC,
                provenance_ref="provenance:homepage:solar",
                currentness=Currentness.CURRENT,
                applicable_subject_ids=(organization.id,),
                applicable_purposes=("HISTORICAL_REFERENCE",),
                authority_id="public-homepage-rights",
                authority_version="1",
            ),
        )
    )


def _loop_seed(xeed_id: str = "xeed:solartec"):
    context, coverage = context_for(xeed_id)
    strategy = build_strategy(
        context,
        coverage=coverage,
        budget=ObservationBudget(
            max_requests=10, max_amount_microunits=0, max_depth=2, max_actions=10
        ),
        registry=SourceRegistry(),
        stop_policy=StopPolicy(sufficient_candidates=3, max_no_gain_streak=2),
    )
    transport = FixtureTedTransport()
    adapters: dict[str, SourceObservationPort] = {
        "ted-search-v3": TedSearchAdapter(transport, clock=lambda: AS_OF),
        "official-public-website": _WebsiteStub(),
    }
    return context, strategy, coverage, adapters, transport


def _loop_inputs(xeed_id: str = "xeed:solartec"):
    context, strategy, coverage, adapters, _transport = _loop_seed(xeed_id)
    result = run_observation_loop(
        strategy,
        context,
        adapters=adapters,
        coverage=coverage,
        learning=OperationalLearning(),
    )
    return context, strategy, result, coverage


def test_real_loop_candidate_is_persisted_and_read_in_its_authorized_scope(
    tmp_path: Path,
) -> None:
    runtime, memory, request, xeed, organization = _runtime(tmp_path)
    _append_capability_source(memory, organization)
    context, strategy, coverage, adapters, _transport = _loop_seed()
    result = runtime.execute_observation_loop(
        request,
        xeed.id,
        observation_context=context,
        strategy=strategy,
        adapters=adapters,
        coverage=coverage,
        learning=OperationalLearning(),
    )

    assert (
        runtime.publish_observation_loop(
            request,
            xeed.id,
            observation_context=context,
            strategy=strategy,
            result=result,
            coverage=coverage,
        )
        is False
    )

    # A new store instance proves the cognition payload survived serialization.
    runtime.opportunity_store = SqliteSubscriberOpportunityProjectionStore(
        tmp_path / "subscriber.sqlite3"
    )
    read = runtime.read(request, xeed.id, AS_OF)

    assert read.status is SubscriberRuntimeStatus.SUCCESS
    cognition = read.projection["cognition"]
    assert isinstance(cognition, dict)
    opportunities = cognition["opportunities"]
    assert isinstance(opportunities, list) and len(opportunities) == 3
    opportunity = next(
        item for item in opportunities if item["id"] == result.candidates[0].candidate_id
    )
    assert opportunity["familyId"] == "demand"
    assert opportunity["opportunityFamily"] == "PUBLIC_PROCUREMENT"
    assert opportunity["epistemic"] == "POTENTIAL"
    assert opportunity["currentness"] == "CURRENT"
    assert opportunity["market"] == result.candidates[0].market.code
    assert opportunity["matchBasis"] == list(result.candidates[0].match_basis)
    assert opportunity["unknown"] == list(result.candidates[0].missing_context)
    assert opportunity["buyer"] == result.candidates[0].record.buyer_name
    assert opportunity["whyPotential"]
    assert opportunity["whyLooked"]
    source_ids = {source["id"] for source in cognition["sources"]}
    assert opportunity["capability"]["sourceId"] in source_ids
    assert opportunity["demand"]["sourceId"] in source_ids
    demand_source = next(
        source
        for source in cognition["sources"]
        if source["id"] == opportunity["demand"]["sourceId"]
    )
    assert demand_source["provenanceRef"] == result.candidates[0].record.record_id
    assert not any("relationship" in key.lower() for key in opportunity)


def test_opportunity_degrades_to_unknown_when_its_evidence_ages(tmp_path: Path) -> None:
    runtime, memory, request, xeed, organization = _runtime(tmp_path)
    _append_capability_source(memory, organization)
    context, strategy, result, coverage = _loop_inputs()
    runtime.publish_observation_loop(
        request,
        xeed.id,
        observation_context=context,
        strategy=strategy,
        result=result,
        coverage=coverage,
    )

    read = runtime.read(request, xeed.id, AS_OF + timedelta(days=8))

    cognition = read.projection["cognition"]
    assert isinstance(cognition, dict)
    opportunity = cognition["opportunities"][0]
    assert opportunity["epistemic"] == "UNKNOWN"
    assert opportunity["currentness"] == "STALE"
    assert opportunity["currentnessEvaluatedAt"] == (AS_OF + timedelta(days=8)).isoformat()
    assert any("currentness" in item for item in opportunity["unknown"])


def test_private_evidence_absent_from_authorized_history_is_not_projected(
    tmp_path: Path,
) -> None:
    runtime, _memory, request, xeed, _organization = _runtime(tmp_path)
    context, strategy, result, coverage = _loop_inputs()

    assert (
        runtime.publish_observation_loop(
            request,
            xeed.id,
            observation_context=context,
            strategy=strategy,
            result=result,
            coverage=coverage,
        )
        is False
    )
    read = runtime.read(request, xeed.id, AS_OF)
    cognition = read.projection["cognition"]
    assert isinstance(cognition, dict)
    assert cognition["opportunities"] == []
    assert read.status is SubscriberRuntimeStatus.INSUFFICIENT_EVIDENCE


def test_unadmitted_capability_seed_is_rejected_before_adapter_dispatch(tmp_path: Path) -> None:
    runtime, _memory, request, xeed, _organization = _runtime(tmp_path)
    context, strategy, coverage, adapters, transport = _loop_seed()

    with pytest.raises(SubscriberOpportunityProjectionError, match="require evidence admitted"):
        runtime.execute_observation_loop(
            request,
            xeed.id,
            observation_context=context,
            strategy=strategy,
            adapters=adapters,
            coverage=coverage,
            learning=OperationalLearning(),
        )
    assert transport.bodies == []


def test_capability_excerpt_must_be_present_in_its_admitted_source(tmp_path: Path) -> None:
    runtime, memory, request, xeed, organization = _runtime(tmp_path)
    _append_capability_source(memory, organization)
    context, strategy, coverage, adapters, transport = _loop_seed()
    capabilities = tuple(
        replace(
            capability,
            basis=(replace(capability.basis[0], excerpt="A fabricated capability."),),
        )
        for capability in context.capabilities
    )
    context = replace(context, capabilities=capabilities)

    with pytest.raises(SubscriberOpportunityProjectionError, match="require evidence admitted"):
        runtime.execute_observation_loop(
            request,
            xeed.id,
            observation_context=context,
            strategy=strategy,
            adapters=adapters,
            coverage=coverage,
            learning=OperationalLearning(),
        )
    assert transport.bodies == []


def test_unauthorized_tenant_is_rejected_before_projection_read_or_write(
    tmp_path: Path,
) -> None:
    runtime, memory, request, xeed, organization = _runtime(tmp_path)
    _append_capability_source(memory, organization)
    context, strategy, result, coverage = _loop_inputs()
    runtime.publish_observation_loop(
        request,
        xeed.id,
        observation_context=context,
        strategy=strategy,
        result=result,
        coverage=coverage,
    )
    unauthorized = TrustedRequestContext(PrincipalId("principal:other"), xeed.tenant_id)
    seed_context, strategy, coverage, adapters, transport = _loop_seed()

    with pytest.raises(XeedReadError):
        runtime.read(unauthorized, xeed.id, AS_OF)
    with pytest.raises(XeedReadError):
        runtime.publish_observation_loop(
            unauthorized,
            xeed.id,
            observation_context=context,
            strategy=strategy,
            result=result,
            coverage=coverage,
        )
    with pytest.raises(XeedReadError):
        runtime.execute_observation_loop(
            unauthorized,
            xeed.id,
            observation_context=seed_context,
            strategy=strategy,
            adapters=adapters,
            coverage=coverage,
            learning=OperationalLearning(),
        )
    assert transport.bodies == []
