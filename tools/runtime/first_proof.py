"""Production first-Xeed -> first-proof vertical for FR-30.

This module is deliberately narrow: it plants an operator-only Xeed for an
explicitly allowlisted public HTTPS surface, runs the governed bootstrap/source
observation path, emits an observation-backed representation Xignal, builds its
evidence narrative and persists a subscriber-safe read model for reload.
It never creates a canonical FAXT from subscriber input.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from application.economic_discovery.brain_contracts import (
    SemanticPrimitive,
    TypingDimensionContract,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    GovernedExecutionController,
)
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
    normalized_field_change,
)
from application.economic_discovery.observation_reuse import (
    ObservationReuseContext,
    ObservationReusePolicy,
    ReuseDisposition,
    ReusePurpose,
    ReuseTargetScope,
    evaluate_observation_reuse,
)
from application.economic_discovery.prime import DimensionRoutingPolicy, PrimeRoute, PrimeWorkItem
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    PrimeMechanismResult,
    execute_prime_source_slice,
)
from application.economic_discovery.source_registry import (
    RobotsDecision,
    RobotsRequirement,
    SourceRatePolicy,
    SourceRegistryEntry,
    SourceRetentionPolicy,
    StaticSourceRegistry,
)
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_currentness,
)
from application.semantic_extraction import SemanticCandidateSet
from application.source_acquisition import (
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
    SourceTargetRule,
    public_acquisition_rejection_reason,
    public_source_reference,
    source_observation_id,
)
from application.source_representation import RichSubjectState, compile_rich_subject_state
from application.subscriber_projection import (
    NarrativeAccessContext,
    NarrativeMaterial,
    NarrativeMaterialContribution,
    NarrativeMaterialMapResolver,
    ObservationPhenomenon,
    ObservationSupport,
    ObservationSupportMapResolver,
    TodayCandidate,
    TodayPolicy,
    build_evidence_narrative,
    project_explainable_xignal,
    project_today,
)
from application.subscriber_projection.cognitive_projection import observation_cognition
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination import (
    BootstrapPolicy,
    BootstrapSourceCandidate,
    FirstMapReadinessPolicy,
    apply_bootstrap_plan,
    apply_first_xignal,
    apply_prime_trace,
    apply_readiness_decision,
    begin_resolution,
    build_bootstrap_plan,
    evaluate_first_map_readiness,
    plant_xeed_runtime,
)
from domain.evidence import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal
from domain.xeed import Xeed
from domain.xeed.germination import XeedGerminationState
from domain.xignal import XignalEpistemicState, XignalKind
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PinnedHttpTransport,
    PublicSourcePolicyGate,
)
from pipeline.source_representation import (
    DocumentRepresentationError,
    HtmlDocumentRepresentationAdapter,
)

FIRST_PROOF_TEMPORAL_POLICY = TemporalCurrentnessPolicy(
    policy_id="first-proof-currentness",
    version="aud06-v1",
    stale_after=timedelta(days=30),
    historical_after=timedelta(days=90),
)

# These failures mean the governed source bytes were acquired, but this bounded
# HTML adapter cannot establish visibility. Other representation failures can
# indicate integrity, authorization, or unusable-source problems and must keep
# their existing failure behavior.
_VISIBILITY_REPRESENTATION_LIMITS = frozenset(
    {
        "stylesheet visibility comment is unresolved",
        "inline stylesheet visibility is unresolved",
        "computed stylesheet visibility is unresolved",
        "layout stylesheet visibility is unresolved",
        "stylesheet visibility declaration is unresolved",
        "stylesheet visibility is unresolved",
        "stylesheet visibility selector is unresolved",
        "malformed hidden ancestry visibility is unresolved",
    }
)


class FirstProofInsufficientEvidence(RuntimeError):
    """The governed observation completed without enough evidence for first proof."""


PRINCIPAL_ID = PrincipalId("principal:production-first-proof")
TENANT_ID = TenantId("tenant:production-first-proof")
ORGANIZATION_ID = OrganizationId("org:axignal")


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class _SingleSeedAuthority:
    def __init__(self, xeed: Xeed, organization: Organization) -> None:
        self._principal = Principal(PRINCIPAL_ID)
        self._xeed = xeed
        self._organization = organization

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        return self._principal if principal_id == self._principal.id else None

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        return principal_id == PRINCIPAL_ID and tenant_id == TENANT_ID

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None:
        return self._xeed if xeed_id == self._xeed.id else None

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self._organization if organization_id == self._organization.id else None


class _RecordingSourceAcquirer:
    """Composition adapter that exposes the exact observation Prime acquired."""

    def __init__(self, delegate: HttpSourceSensor) -> None:
        self._delegate = delegate
        self._observation: SourceObservation | None = None

    def observe(self, request: SourceRequest, policy: SourceDispatchPolicy) -> SourceObservation:
        observation = self._delegate.observe(request, policy)
        self._observation = observation
        if observation.failure_state is not None or observation.body_artifact_ref is None:
            raise FirstProofInsufficientEvidence(
                f"SOURCE_NOT_EVALUABLE:{observation.failure_state or 'NO_BODY'}"
            )
        return observation

    def require_observation(self) -> SourceObservation:
        if self._observation is None:
            raise RuntimeError("governed source acquisition did not produce an observation")
        return self._observation


class _AnswerabilityExecutor:
    def execute(
        self,
        *,
        item: PrimeWorkItem,
        state: RichSubjectState,
        semantic_candidates: SemanticCandidateSet | None,
    ) -> PrimeMechanismResult:
        del semantic_candidates
        fingerprint = _digest(
            {
                "dimension": item.dimension_id,
                "route": None if item.route is None else item.route.value,
                "state": state.fingerprint,
            }
        )
        return PrimeMechanismResult(
            output_fingerprint=f"deterministic:{fingerprint}",
            made_progress=True,
            cost=LearningCost(amount_microunits=0, currency="EUR", latency_ms=0),
        )


class FirstProofStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS first_proof_sessions (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    xeed_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    target_uri TEXT NOT NULL,
                    projection_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS first_proof_sequence (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO first_proof_sequence SELECT 1, COALESCE(MAX(sequence),0) FROM first_proof_sessions"
            )

    def next_sequence(self) -> int:
        with sqlite3.connect(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("UPDATE first_proof_sequence SET value=value+1 WHERE id=1")
            row = connection.execute("SELECT value FROM first_proof_sequence WHERE id=1").fetchone()
        return int(row[0])

    def append(
        self, *, xeed_id: str, created_at: datetime, target_uri: str, projection: dict[str, object]
    ) -> None:
        payload = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO first_proof_sessions (xeed_id, created_at, target_uri, projection_json) VALUES (?, ?, ?, ?)",
                (xeed_id, created_at.astimezone(UTC).isoformat(), target_uri, payload),
            )

    def latest(self) -> dict[str, object] | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT projection_json FROM first_proof_sessions ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        return None if row is None else json.loads(str(row[0]))

    def get(self, xeed_id: str) -> dict[str, object] | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT projection_json FROM first_proof_sessions WHERE xeed_id=?", (xeed_id,)
            ).fetchone()
        return None if row is None else json.loads(str(row[0]))


@dataclass(slots=True)
class FirstProofService:
    code_sha: str
    allowed_host: str
    store: FirstProofStore
    observation_memory: SqliteObservationMemory
    research_work_memory: SqliteSharedObservationWorkMemory
    learning_memory: SqliteLearningMemory
    artifacts: ContentAddressedArtifactStore
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def _authorized_history(
        self, *, subject_id: str, xeed_id: str, as_of: datetime
    ) -> tuple[GovernedObservation, ...]:
        context = ObservationReuseContext(
            subject_id=subject_id,
            xeed_id=xeed_id,
            tenant_id=str(TENANT_ID),
            target_scope=ReuseTargetScope.GLOBAL_WORLD,
            purpose=ReusePurpose.HISTORICAL_REFERENCE,
            as_of=as_of,
        )
        return tuple(
            item
            for item in self.observation_memory.for_subject(subject_id)
            if item.record.observed_at <= as_of
            and evaluate_observation_reuse(
                item,
                context=context,
                policy=ObservationReusePolicy("first-proof-history", "2"),
                temporal_policy=FIRST_PROOF_TEMPORAL_POLICY,
            ).disposition
            is ReuseDisposition.ALLOW
        )

    def _temporal_history_payload(
        self, *, subject_id: str, xeed_id: str, as_of: datetime
    ) -> dict[str, object]:
        history = self._authorized_history(subject_id=subject_id, xeed_id=xeed_id, as_of=as_of)
        ordered_history = sorted(
            history,
            key=lambda item: (item.record.observed_at, item.record.observation_id),
        )
        temporal_items: list[dict[str, object]] = []
        previous_fields: tuple[tuple[str, str], ...] | None = None
        for observation in ordered_history:
            if observation.record.observed_at > as_of:
                continue
            effective_currentness = evaluate_currentness(
                observation,
                as_of=as_of,
                policy=FIRST_PROOF_TEMPORAL_POLICY,
            ).current
            normalized_fields = tuple(
                sorted((field.name, field.value) for field in observation.fields)
            )
            temporal_items.append(
                {
                    "observationId": observation.record.observation_id,
                    "sourceRef": observation.record.source_ref,
                    "sourceType": observation.record.source_type,
                    "observedAt": observation.record.observed_at.astimezone(UTC).isoformat(),
                    "currentness": effective_currentness.value,
                    "normalizedStateChanged": normalized_field_change(
                        previous_fields, normalized_fields
                    ),
                }
            )
            previous_fields = normalized_fields
        return {
            "disposition": (
                "EMPTY"
                if not temporal_items
                else "SINGLE_OBSERVATION"
                if len(temporal_items) == 1
                else "MULTIPLE_OBSERVATIONS"
            ),
            "items": temporal_items,
        }

    def _cognition_payload(
        self,
        *,
        subject_id: str,
        xeed_id: str,
        as_of: datetime,
        signals: tuple[tuple[str, str], ...],
    ) -> dict[str, object]:
        observations = tuple(
            (
                item,
                evaluate_currentness(item, as_of=as_of, policy=FIRST_PROOF_TEMPORAL_POLICY).current,
            )
            for item in self._authorized_history(
                subject_id=subject_id, xeed_id=xeed_id, as_of=as_of
            )
            if item.record.observed_at <= as_of
            and item.reuse_authority.scope is ObservationReuseScope.GLOBAL_PUBLIC
            and item.reuse_authority.rights_status is ObservationRightsStatus.PERMITTED
            and item.reuse_authority.access_status is ObservationAccessStatus.ACCESSIBLE
        )
        return observation_cognition(observations, as_of=as_of, signals=signals)

    def _persist_visibility_limited_projection(
        self,
        *,
        xeed_id: XeedId,
        label: str,
        organization: Organization,
        target_uri: str,
        created_at: datetime,
        lifecycle: XeedGerminationState,
        as_of: datetime,
        error: DocumentRepresentationError,
    ) -> dict[str, object]:
        """Persist admitted evidence when deterministic page visibility is unresolved."""
        if str(error) not in _VISIBILITY_REPRESENTATION_LIMITS:
            raise error

        organization_id = str(organization.id)
        projection: dict[str, object] = {
            "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF",
            "runtimeCodeSha": self.code_sha,
            "lifecycleStatus": lifecycle.status.value,
            "context": {"id": str(xeed_id), "label": label},
            "organization": {"id": organization_id, "name": organization.canonical_name},
            "nodes": [],
            "temporalHistory": self._temporal_history_payload(
                subject_id=organization_id,
                xeed_id=str(xeed_id),
                as_of=as_of,
            ),
            "memberships": [],
            "today": {"disposition": "EMPTY", "items": []},
            "digitalRepresentation": {
                "state": "NOT_MEASURED",
                "reason": {
                    "code": "REPRESENTATION_VISIBILITY_UNRESOLVED",
                    "explanation": (
                        "AXIGNAL acquired and retained the authorized public source, but its "
                        "deterministic HTML adapter could not resolve stylesheet visibility. "
                        "No page representation or Xignal was emitted."
                    ),
                    "detailCode": str(error),
                },
                "scopeLimit": (
                    "Source acquisition and provenance are available; rendered-page visibility "
                    "remains UNKNOWN under this representation limit."
                ),
            },
            "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
        }
        projection["cognition"] = self._cognition_payload(
            subject_id=organization_id,
            xeed_id=str(xeed_id),
            as_of=as_of,
            signals=(),
        )
        self.store.append(
            xeed_id=str(xeed_id),
            created_at=created_at,
            target_uri=target_uri,
            projection=projection,
        )
        return projection

    def current_projection(
        self, *, as_of: datetime | None = None, xeed_id: str | None = None
    ) -> dict[str, object] | None:
        stored = self.store.latest() if xeed_id is None else self.store.get(xeed_id)
        if stored is None:
            return None
        evaluated_at = self.clock() if as_of is None else as_of
        if evaluated_at.tzinfo is None:
            raise ValueError("first-proof projection as_of must be timezone-aware")

        projection = cast(dict[str, object], json.loads(json.dumps(stored)))
        organization_data = projection.get("organization")
        if isinstance(organization_data, dict) and isinstance(organization_data.get("id"), str):
            projection["temporalHistory"] = self._temporal_history_payload(
                subject_id=str(organization_data["id"]),
                xeed_id=str(cast(dict[str, object], projection["context"])["id"]),
                as_of=evaluated_at,
            )

        nodes = projection.get("nodes")
        if not isinstance(nodes, list):
            return projection

        nodes[:] = [
            node
            for node in nodes
            if isinstance(node, dict)
            and isinstance(node.get("observedAt"), str)
            and datetime.fromisoformat(str(node["observedAt"])) <= evaluated_at
        ]
        today = projection.get("today")
        if isinstance(today, dict) and isinstance(today.get("items"), list):
            visible = {str(node["id"]) for node in nodes}
            today["items"] = [
                item
                for item in today["items"]
                if isinstance(item, dict) and item.get("xignalId") in visible
            ]
            if not today["items"]:
                today["disposition"] = "EMPTY"
        if isinstance(organization_data, dict):
            projection["cognition"] = self._cognition_payload(
                subject_id=str(organization_data["id"]),
                xeed_id=str(cast(dict[str, object], projection["context"])["id"]),
                as_of=evaluated_at,
                signals=tuple((str(node["id"]), "presence") for node in nodes),
            )

        any_non_current = False
        for node in nodes:
            if not isinstance(node, dict):
                continue
            refs = node.get("observationSupportRefs")
            if not isinstance(refs, list) or not refs:
                continue

            effective: list[Currentness] = []
            for observation_id in refs:
                if not isinstance(observation_id, str):
                    continue
                if not isinstance(organization_data, dict):
                    return None
                observation = self.observation_memory.get_observation(
                    str(organization_data["id"]),
                    observation_id,
                )
                if observation is None:
                    effective.append(Currentness.UNKNOWN)
                    continue
                decision = evaluate_currentness(
                    observation,
                    as_of=evaluated_at,
                    policy=FIRST_PROOF_TEMPORAL_POLICY,
                )
                effective.append(decision.current)

            if not effective:
                continue
            if Currentness.UNKNOWN in effective:
                node_currentness = Currentness.UNKNOWN
            elif Currentness.HISTORICAL in effective:
                node_currentness = Currentness.HISTORICAL
            elif Currentness.STALE in effective:
                node_currentness = Currentness.STALE
            else:
                node_currentness = Currentness.CURRENT

            node["currentness"] = node_currentness.value
            any_non_current = any_non_current or node_currentness is not Currentness.CURRENT

            narrative = node.get("evidenceNarrative")
            if isinstance(narrative, dict):
                steps = narrative.get("steps")
                if isinstance(steps, list):
                    for step in steps:
                        if not isinstance(step, dict):
                            continue
                        if step.get("kind") in {
                            "XIGNAL",
                            "OBSERVATION",
                            "SOURCE",
                            "CONTRADICTION",
                        }:
                            step["currentness"] = node_currentness.value

        if any_non_current:
            today = projection.get("today")
            if isinstance(today, dict):
                today["disposition"] = "EMPTY"
                today["items"] = []

        return projection

    def _validate_target(self, target_uri: str) -> str:
        parsed = urlsplit(target_uri.strip())
        host = (parsed.hostname or "").rstrip(".").lower()
        if parsed.scheme != "https" or host != self.allowed_host:
            raise ValueError("FR-30 first proof permits only the configured HTTPS host")
        privacy_rejection = public_acquisition_rejection_reason(target_uri)
        if privacy_rejection is not None:
            raise ValueError("FR-30 target contains private credential material")
        if parsed.port not in (None, 443):
            raise ValueError("FR-30 target must use canonical HTTPS without custom port")
        return public_source_reference(parsed.geturl())

    def plant(self, *, label: str, target_uri: str) -> dict[str, object]:
        label = label.strip()
        if not label:
            raise ValueError("Xeed label is required")
        target_uri = self._validate_target(target_uri)
        return self.observe_resolved(
            label=label,
            target_uri=target_uri,
            organization=Organization(ORGANIZATION_ID, "AXIGNAL"),
        )

    def observe_resolved(
        self, *, label: str, target_uri: str, organization: Organization
    ) -> dict[str, object]:
        """Composition-only entry: caller supplies already-resolved canonical authority.

        Public HTTP must never forward user name/id here; attention resolution
        binds a server-owned catalog target before using this same FR-30 path.
        """
        organization_id = organization.id
        now = self.clock()
        sequence = self.store.next_sequence()
        xeed_id = XeedId(f"xeed:production-first-proof:{sequence}")
        xeed = Xeed(xeed_id, TENANT_ID, organization_id, label)
        authority = _SingleSeedAuthority(xeed, organization)
        authorized = AuthorizedXeedReader(authority, authority, authority).read(
            TrustedRequestContext(PRINCIPAL_ID, TENANT_ID), xeed_id
        )
        seed = AuthorizedXeedOrganizationReader(authority).read(authorized)

        lifecycle = plant_xeed_runtime(seed=seed, initiated_by=PRINCIPAL_ID, created_at=now)
        begin_resolution(seed=seed, state=lifecycle, occurred_at=now)

        contract = TypingDimensionContract(
            dimension_id="public-web-representation",
            version="fr30-v2",
            semantic_target="condition-bound public website representation",
            primitive=SemanticPrimitive.CHOICE,
            question="Is a public website representation observable at the authorized target?",
            state_requirements=("document.website.extracted_text",),
            dependencies=("document.website.extracted_text",),
            mutually_exclusive=True,
            abstention_policy="preserve UNKNOWN outside the observed surface",
        )
        routing = (
            DimensionRoutingPolicy(
                dimension_id=contract.dimension_id,
                version="fr30-routing-v2",
                answerable_route=PrimeRoute.DETERMINISTIC,
            ),
        )
        prior = compile_rich_subject_state(subject_id=organization_id, contributions=())
        bootstrap = build_bootstrap_plan(
            seed=seed,
            rich_state=prior,
            policy=BootstrapPolicy("xeed-bootstrap", "fr30-v1", max_known_sources=1),
            known_sources=(
                BootstrapSourceCandidate(
                    candidate_id="source:official-homepage",
                    subject_id=organization_id,
                    observation_slot="website",
                    source_ref=public_source_reference(target_uri),
                    source_type="OFFICIAL_WEB",
                    provides_fields=frozenset({"document.website.extracted_text"}),
                    priority=1,
                ),
            ),
            contracts=(contract,),
            routing_policies=routing,
            temporal_policy=FIRST_PROOF_TEMPORAL_POLICY,
            as_of=now,
        )
        execution_id = f"run:fr30:{sequence}"
        apply_bootstrap_plan(
            seed=seed,
            state=lifecycle,
            plan=bootstrap,
            occurred_at=now,
            learning_memory=self.learning_memory,
            execution_id=execution_id,
            code_sha=self.code_sha,
        )

        host = urlsplit(target_uri).hostname or ""
        transport = PinnedHttpTransport()
        registry = StaticSourceRegistry(
            (
                SourceRegistryEntry(
                    source_id="fr30-official-homepage",
                    version="2",
                    source_type="OFFICIAL_WEB",
                    instrument_ref=transport.instrument_ref,
                    decision_basis=(
                        "Operator-authorized canonical organization public homepage; "
                        "single root document only, no crawl/subresource authority"
                    ),
                    targets=(
                        SourceTargetRule(host, "/", ("https",)),
                        SourceTargetRule(f"www.{host}", "/", ("https",)),
                    ),
                    allowed_purposes=(
                        ReusePurpose.CURRENT_STATE,
                        ReusePurpose.HISTORICAL_REFERENCE,
                    ),
                    rights_status=ObservationRightsStatus.PERMITTED,
                    access_status=ObservationAccessStatus.ACCESSIBLE,
                    reuse_scope=ObservationReuseScope.GLOBAL_PUBLIC,
                    reuse_reason=(
                        "registered public homepage observation may be reused for current "
                        "state and historical evidence reference while provenance/currentness "
                        "and retention remain valid"
                    ),
                    temporal_policy=FIRST_PROOF_TEMPORAL_POLICY,
                    retention_policy=SourceRetentionPolicy(
                        policy_id="fr30-public-evidence-retention",
                        version="1",
                        raw_retention_days=90,
                        metadata_retention_days=365,
                    ),
                    rate_policy=SourceRatePolicy(
                        policy_id="fr30-public-root-rate",
                        version="1",
                        max_requests=6,
                        window_seconds=60,
                    ),
                    robots_requirement=RobotsRequirement.NOT_REQUIRED_SINGLE_DOCUMENT,
                    robots_decision=RobotsDecision.NOT_APPLICABLE,
                    robots_policy_ref="robots:single-public-root-document:v1",
                    currentness=Currentness.CURRENT,
                    timeout_ms=8_000,
                    max_redirects=3,
                ),
            )
        )
        authorization = registry.authorize(
            source_id="fr30-official-homepage",
            request_id=f"request:fr30:{sequence}:official-homepage",
            subject_id=organization_id,
            observation_slot="website",
            target_uri=target_uri,
            source_type="OFFICIAL_WEB",
            purpose=ReusePurpose.CURRENT_STATE,
            instrument_ref=transport.instrument_ref,
        )
        # Authorize historical evidence reuse separately. The registry's single
        # acquisition grant intentionally covers only its requested purpose.
        historical_authorization = registry.authorize(
            source_id="fr30-official-homepage",
            request_id=f"request:fr30:{sequence}:historical-reference",
            subject_id=organization_id,
            observation_slot="website",
            target_uri=target_uri,
            source_type="OFFICIAL_WEB",
            purpose=ReusePurpose.HISTORICAL_REFERENCE,
            instrument_ref=transport.instrument_ref,
        )
        reuse_authority = replace(
            authorization.reuse_authority,
            applicable_purposes=(
                authorization.purpose.value,
                historical_authorization.purpose.value,
            ),
        )
        source_policy = authorization.dispatch_policy
        request = authorization.request
        sensor = HttpSourceSensor(
            policy_gate=PublicSourcePolicyGate(),
            transport=transport,
            artifacts=self.artifacts,
        )
        source_acquirer = _RecordingSourceAcquirer(sensor)
        representation_adapter = HtmlDocumentRepresentationAdapter(self.artifacts)
        executor = _AnswerabilityExecutor()
        try:
            trace = execute_prime_source_slice(
                execution_id=execution_id,
                seed=seed,
                code_sha=self.code_sha,
                occurred_at=now,
                observation_memory=self.observation_memory,
                learning_memory=self.learning_memory,
                request=request,
                source_policy=source_policy,
                source_acquirer=source_acquirer,
                representation_port=representation_adapter,
                prior_rich_state=prior,
                contracts=(contract,),
                routing_policies=routing,
                research_decisions=(),
                execution_controller=GovernedExecutionController(
                    policy=ExecutionBudgetPolicy(
                        policy_id="fr30-first-proof-budget",
                        version="1",
                        currency="EUR",
                        max_amount_microunits=1,
                        max_requests=4,
                        max_sources=2,
                        max_elapsed_ms=15_000,
                        max_retries=1,
                        max_loops=2,
                        max_no_progress_streak=1,
                    ),
                    state=ExecutionBudgetState(amount_microunits=0, currency="EUR"),
                ),
                ports=PrimeExecutionPorts(executor, executor, executor),
                temporal_currentness_policy=authorization.temporal_policy,
                ingested_observation_reuse_authority=reuse_authority,
                research_work_memory=self.research_work_memory,
            )
        except DocumentRepresentationError as error:
            if str(error) not in _VISIBILITY_REPRESENTATION_LIMITS:
                raise
            observation = source_acquirer.require_observation()
            return self._persist_visibility_limited_projection(
                xeed_id=xeed_id,
                label=label,
                organization=organization,
                target_uri=target_uri,
                created_at=now,
                lifecycle=lifecycle,
                as_of=max(now, observation.retrieved_at),
                error=error,
            )
        observation = source_acquirer.require_observation()
        projection_as_of = max(now, observation.retrieved_at)
        apply_prime_trace(seed=seed, state=lifecycle, trace=trace, occurred_at=projection_as_of)
        representation = representation_adapter.represent(request=request, observation=observation)
        observation_id = source_observation_id(request, observation)
        excerpt = (
            representation.title or representation.description or representation.document_text[:240]
        )
        uncertainty = (
            "This observation covers only the authorized public homepage at this observation time. "
            "Search, generative, social, reputation and other public surfaces remain UNKNOWN."
        )
        basis = ExplainableBasis(
            basis_id=f"basis:fr30:{sequence}:{_digest(trace.rich_state_fingerprint)[:16]}",
            subject_id=organization_id,
            candidate_id="candidate:public-homepage-representation",
            semantic_target="condition-bound public website representation",
            state_fingerprint=trace.rich_state_fingerprint,
            contract_fingerprint=_digest(
                {
                    "dimension": contract.dimension_id,
                    "version": contract.version,
                    "routing": routing[0].version,
                }
            ),
            evaluated_at=projection_as_of,
            data=(
                BasisDatum(
                    datum_id=f"datum:fr30:{sequence}:homepage",
                    observation_id=observation_id,
                    source_ref=public_source_reference(observation.final_uri),
                    source_type=request.source_type,
                    observed_at=observation.retrieved_at,
                    excerpt_or_summary=excerpt,
                    contribution=BasisContribution.SUPPORTS,
                    representation_fingerprint=representation.fingerprint,
                    extraction_fingerprint=None,
                ),
            ),
            interpretation=(
                "The authorized public homepage was reachable and contained deterministic "
                "document text when AXIGNAL observed it. Visual visibility remains UNKNOWN "
                "when external stylesheet effects are unresolved."
            ),
            uncertainty=uncertainty,
        )
        xignal_projection = project_explainable_xignal(
            organization_context=seed,
            candidate_id=basis.candidate_id,
            kind=XignalKind.REPRESENTATION,
            epistemic_state=XignalEpistemicState.OBSERVED,
            title=f"{organization.canonical_name}'s public homepage is observable from the outside",
            why_attention=(
                "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation."
            ),
            basis=basis,
            emitted_at=projection_as_of,
            policy_version="fr30-xignal-v1",
            observation_support_refs=(observation_id,),
            observation_support_resolver=ObservationSupportMapResolver(
                {
                    observation_id: ObservationSupport(
                        observation_id=observation_id,
                        subject_id=organization_id,
                        phenomenon=ObservationPhenomenon.PUBLIC_REPRESENTATION,
                        instrument_ref=observation.instrument_ref,
                        instrument_version=observation.instrument_ref.rsplit("/", 1)[-1],
                        scope_ref=request.observation_slot,
                        provenance_ref=observation.raw_observation_ref,
                        source_ref=public_source_reference(observation.final_uri),
                        observed_at=observation.retrieved_at,
                        currentness=Currentness.CURRENT,
                    )
                }
            ),
            currentness=Currentness.CURRENT,
            unknowns=(uncertainty,),
        )
        apply_first_xignal(
            seed=seed, state=lifecycle, projection=xignal_projection, occurred_at=projection_as_of
        )
        narrative = build_evidence_narrative(
            organization_context=seed,
            projection=xignal_projection,
            basis=basis,
            observation_memory=self.observation_memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(self.artifacts),
            material_resolver=NarrativeMaterialMapResolver(
                (
                    NarrativeMaterial(
                        observation_id=observation_id,
                        subject_id=organization_id,
                        candidate_id=basis.candidate_id,
                        source_ref=public_source_reference(observation.final_uri),
                        source_type=request.source_type,
                        observed_at=observation.retrieved_at,
                        excerpt_or_summary=excerpt,
                        contribution=NarrativeMaterialContribution.SUPPORTS,
                        representation_fingerprint=representation.fingerprint,
                        extraction_fingerprint=None,
                    ),
                )
            ),
            access_context=NarrativeAccessContext(
                subject_id=str(organization_id),
                xeed_id=str(seed.authorized_xeed.xeed.id),
                tenant_id=str(seed.authorized_xeed.xeed.tenant_id),
                target_scope=ReuseTargetScope.TENANT_PRIVATE,
                purpose=ReusePurpose.CURRENT_STATE,
                as_of=projection_as_of,
            ),
            reuse_policy=ObservationReusePolicy(
                "subscriber-evidence-narrative",
                "1",
            ),
            temporal_policy=FIRST_PROOF_TEMPORAL_POLICY,
        )
        readiness = evaluate_first_map_readiness(
            seed=seed,
            state=lifecycle,
            policy=FirstMapReadinessPolicy("first-map-readiness", "fr30-v1"),
            projection=xignal_projection,
            narrative=narrative,
        )
        if readiness.decision is None or not readiness.decision.ready:
            raise FirstProofInsufficientEvidence(
                "FIRST_MAP_NOT_READY:" + ",".join(item.value for item in readiness.reason_codes)
            )
        apply_readiness_decision(
            seed=seed,
            state=lifecycle,
            decision=readiness.decision,
            occurred_at=projection_as_of,
        )
        today = project_today(
            candidates=(
                TodayCandidate(
                    projection=xignal_projection,
                    focus_ref=xignal_projection.xignal.xignal_id,
                    changed_at=observation.retrieved_at,
                    material=True,
                ),
            ),
            policy=TodayPolicy("today", "fr30-v1"),
        )
        emission_event = LearningEvent(
            event_id=f"learn:{execution_id}:06-xignal:{xignal_projection.xignal.xignal_id}",
            kind=LearningEventKind.DETERMINISTIC_EVALUATION,
            outcome=LearningOutcome.COMPLETED,
            occurred_at=projection_as_of,
            subject_id=organization_id,
            xeed_id=xeed_id,
            activity_ref=xignal_projection.xignal.xignal_id,
            policy_id="xignal-projection",
            policy_version="fr30-v1",
            code_sha=self.code_sha,
            mechanism=LearningMechanism.DETERMINISTIC,
            input_fingerprint=basis.basis_id,
            output_fingerprint=xignal_projection.xignal.xignal_id,
            reason_code="XIGNAL_EMITTED_FROM_GOVERNED_OBSERVATION",
            replay=LearningReplayReference.replayable(
                basis_id=basis.basis_id,
                observation_id=observation_id,
                source_artifact_ref=observation.raw_observation_ref,
            ),
            cost=LearningCost(amount_microunits=0, currency="EUR", latency_ms=0),
            yield_=LearningYield(xignals_emitted=1),
        )
        self.learning_memory.append(emission_event)
        learning_ids = tuple(
            event.event_id for event in self.learning_memory.for_xeed(str(xeed_id))
        )

        node = {
            "id": xignal_projection.xignal.xignal_id,
            "nodeKind": "XIGNAL",
            "title": xignal_projection.xignal.title,
            "whyAttention": xignal_projection.xignal.why_attention,
            "interpretation": xignal_projection.interpretation,
            "uncertainty": xignal_projection.uncertainty,
            "epistemicState": xignal_projection.xignal.epistemic_state.value,
            "currentness": xignal_projection.xignal.currentness.value,
            "observedAt": xignal_projection.last_observed_at.astimezone(UTC).isoformat(),
            "evidenceAccess": "AVAILABLE",
            "sourceRefs": list(xignal_projection.source_refs),
            "observationSupportRefs": list(xignal_projection.xignal.observation_support_refs),
            "unknowns": list(xignal_projection.xignal.unknowns),
            "evidenceNarrative": {
                "xignalId": narrative.xignal_id,
                "focusStepId": narrative.focus_step_id,
                "steps": [
                    {
                        "id": step.step_id,
                        "kind": step.kind.value,
                        "label": step.label,
                        "sourceRef": step.source_ref,
                        "observedAt": None
                        if step.observed_at is None
                        else step.observed_at.astimezone(UTC).isoformat(),
                        "currentness": step.currentness,
                        "artifactVerified": step.artifact_verified,
                    }
                    for step in narrative.steps
                ],
            },
            "learningEventIds": list(learning_ids),
        }
        projection: dict[str, object] = {
            "realityLevel": "LIVE_PRODUCTION_FIRST_PROOF",
            "runtimeCodeSha": self.code_sha,
            "lifecycleStatus": lifecycle.status.value,
            "context": {"id": str(xeed_id), "label": label},
            "organization": {
                "id": str(organization_id),
                "name": organization.canonical_name,
                "capabilities": [],
                "markets": [],
            },
            "nodes": [node],
            "temporalHistory": self._temporal_history_payload(
                subject_id=str(organization_id),
                xeed_id=str(xeed_id),
                as_of=projection_as_of,
            ),
            "memberships": [
                {"from": str(xeed_id), "to": node["id"], "meaning": "Xeed observes Xignal"}
            ],
            "today": {
                "disposition": today.disposition.value,
                "items": [
                    {
                        "xignalId": item.xignal_id,
                        "whatChanged": item.what_changed,
                        "whyItMatters": item.why_it_matters,
                        "observedAt": item.observed_at.astimezone(UTC).isoformat(),
                        "showHowRef": item.show_how_ref,
                    }
                    for item in today.items
                ],
            },
            "learning": {
                "eventIds": list(learning_ids),
                "linkedXignalEventId": emission_event.event_id,
            },
            "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
        }
        projection["cognition"] = self._cognition_payload(
            subject_id=str(organization_id),
            xeed_id=str(xeed_id),
            as_of=projection_as_of,
            signals=((str(node["id"]), "presence"),),
        )
        self.store.append(
            xeed_id=str(xeed_id), created_at=now, target_uri=target_uri, projection=projection
        )
        return projection
