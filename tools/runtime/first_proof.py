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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
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
from application.economic_discovery.prime import DimensionRoutingPolicy, PrimeRoute, PrimeWorkItem
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    PrimeMechanismResult,
    execute_prime_source_slice,
)
from application.semantic_extraction import SemanticCandidateSet
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
    SourceTargetRule,
    source_observation_id,
)
from application.source_representation import RichSubjectState, compile_rich_subject_state
from application.subscriber_projection import (
    TodayCandidate,
    TodayPolicy,
    build_evidence_narrative,
    project_explainable_xignal,
    project_today,
)
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
from domain.xignal import XignalEpistemicState, XignalKind
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PinnedHttpTransport,
    PublicSourcePolicyGate,
)
from pipeline.source_representation import HtmlDocumentRepresentationAdapter


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


class _FixedSourceAcquirer:
    def __init__(self, observation: SourceObservation) -> None:
        self._observation = observation

    def observe(self, request: SourceRequest, policy: SourceDispatchPolicy) -> SourceObservation:
        del request, policy
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

    def next_sequence(self) -> int:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM first_proof_sessions"
            ).fetchone()
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


@dataclass(slots=True)
class FirstProofService:
    code_sha: str
    allowed_host: str
    store: FirstProofStore
    observation_memory: SqliteObservationMemory
    learning_memory: SqliteLearningMemory
    artifacts: ContentAddressedArtifactStore

    def current_projection(self) -> dict[str, object] | None:
        return self.store.latest()

    def _validate_target(self, target_uri: str) -> str:
        parsed = urlsplit(target_uri.strip())
        host = (parsed.hostname or "").rstrip(".").lower()
        if parsed.scheme != "https" or host != self.allowed_host:
            raise ValueError("FR-30 first proof permits only the configured HTTPS host")
        if parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError(
                "FR-30 target must use canonical HTTPS without credentials/custom port"
            )
        return parsed.geturl()

    def plant(self, *, label: str, target_uri: str) -> dict[str, object]:
        label = label.strip()
        if not label:
            raise ValueError("Xeed label is required")
        target_uri = self._validate_target(target_uri)
        now = datetime.now(UTC)
        sequence = self.store.next_sequence()
        xeed_id = XeedId(f"xeed:production-first-proof:{sequence}")
        xeed = Xeed(xeed_id, TENANT_ID, ORGANIZATION_ID, label)
        organization = Organization(ORGANIZATION_ID, "AXIGNAL")
        authority = _SingleSeedAuthority(xeed, organization)
        authorized = AuthorizedXeedReader(authority, authority, authority).read(
            TrustedRequestContext(PRINCIPAL_ID, TENANT_ID), xeed_id
        )
        seed = AuthorizedXeedOrganizationReader(authority).read(authorized)

        lifecycle = plant_xeed_runtime(seed=seed, initiated_by=PRINCIPAL_ID, created_at=now)
        begin_resolution(seed=seed, state=lifecycle, occurred_at=now)

        contract = TypingDimensionContract(
            dimension_id="public-web-representation",
            version="fr30-v1",
            semantic_target="condition-bound public website representation",
            primitive=SemanticPrimitive.CHOICE,
            question="Is a public website representation observable at the authorized target?",
            state_requirements=("document.website.visible_text",),
            dependencies=("document.website.visible_text",),
            mutually_exclusive=True,
            abstention_policy="preserve UNKNOWN outside the observed surface",
        )
        routing = (
            DimensionRoutingPolicy(
                dimension_id=contract.dimension_id,
                version="fr30-routing-v1",
                answerable_route=PrimeRoute.DETERMINISTIC,
            ),
        )
        prior = compile_rich_subject_state(subject_id=ORGANIZATION_ID, contributions=())
        bootstrap = build_bootstrap_plan(
            seed=seed,
            rich_state=prior,
            policy=BootstrapPolicy("xeed-bootstrap", "fr30-v1", max_known_sources=1),
            known_sources=(
                BootstrapSourceCandidate(
                    candidate_id="source:official-homepage",
                    subject_id=ORGANIZATION_ID,
                    observation_slot="website",
                    source_ref=target_uri,
                    source_type="OFFICIAL_WEB",
                    provides_fields=frozenset({"document.website.visible_text"}),
                    priority=1,
                ),
            ),
            contracts=(contract,),
            routing_policies=routing,
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

        host = self.allowed_host
        source_policy = SourceDispatchPolicy(
            policy_id="source:fr30-official-web:v1",
            disposition=DispatchDisposition.ALLOW,
            decision_basis="FR-30 operator-authorized official AXIGNAL public homepage",
            targets=(
                SourceTargetRule(host, "/", ("https",)),
                SourceTargetRule(f"www.{host}", "/", ("https",)),
            ),
            timeout_ms=8_000,
            max_redirects=3,
        )
        request = SourceRequest(
            request_id=f"request:fr30:{sequence}:official-homepage",
            subject_id=ORGANIZATION_ID,
            observation_slot="website",
            target_uri=target_uri,
            source_type="OFFICIAL_WEB",
            policy_id=source_policy.policy_id,
            policy_fingerprint=source_policy.fingerprint,
        )
        sensor = HttpSourceSensor(
            policy_gate=PublicSourcePolicyGate(),
            transport=PinnedHttpTransport(),
            artifacts=self.artifacts,
        )
        observation = sensor.observe(request, source_policy)
        if observation.failure_state is not None or observation.body_artifact_ref is None:
            raise FirstProofInsufficientEvidence(
                f"SOURCE_NOT_EVALUABLE:{observation.failure_state or 'NO_BODY'}"
            )
        representation_adapter = HtmlDocumentRepresentationAdapter(self.artifacts)
        executor = _AnswerabilityExecutor()
        trace = execute_prime_source_slice(
            execution_id=execution_id,
            seed=seed,
            code_sha=self.code_sha,
            occurred_at=now,
            observation_memory=self.observation_memory,
            learning_memory=self.learning_memory,
            request=request,
            source_policy=source_policy,
            source_acquirer=_FixedSourceAcquirer(observation),
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
        )
        apply_prime_trace(seed=seed, state=lifecycle, trace=trace, occurred_at=now)
        representation = representation_adapter.represent(request=request, observation=observation)
        observation_id = source_observation_id(request, observation)
        excerpt = (
            representation.title or representation.description or representation.visible_text[:240]
        )
        uncertainty = (
            "This observation covers only the authorized public homepage at this observation time. "
            "Search, generative, social, reputation and other public surfaces remain UNKNOWN."
        )
        basis = ExplainableBasis(
            basis_id=f"basis:fr30:{sequence}:{_digest(trace.rich_state_fingerprint)[:16]}",
            subject_id=ORGANIZATION_ID,
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
            evaluated_at=now,
            data=(
                BasisDatum(
                    datum_id=f"datum:fr30:{sequence}:homepage",
                    observation_id=observation_id,
                    source_ref=observation.final_uri,
                    source_type=request.source_type,
                    observed_at=observation.retrieved_at,
                    excerpt_or_summary=excerpt,
                    contribution=BasisContribution.SUPPORTS,
                ),
            ),
            interpretation="The authorized public homepage was reachable and contained visible text when AXIGNAL observed it.",
            uncertainty=uncertainty,
        )
        xignal_projection = project_explainable_xignal(
            organization_context=seed,
            candidate_id=basis.candidate_id,
            kind=XignalKind.REPRESENTATION,
            epistemic_state=XignalEpistemicState.OBSERVED,
            title="AXIGNAL's public homepage is observable from the outside",
            why_attention=(
                "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation."
            ),
            basis=basis,
            emitted_at=now,
            policy_version="fr30-xignal-v1",
            observation_support_refs=(observation_id,),
            currentness=Currentness.CURRENT,
            unknowns=(uncertainty,),
        )
        apply_first_xignal(
            seed=seed, state=lifecycle, projection=xignal_projection, occurred_at=now
        )
        narrative = build_evidence_narrative(
            organization_context=seed,
            projection=xignal_projection,
            basis=basis,
            observation_memory=self.observation_memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(self.artifacts),
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
            occurred_at=now,
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
            occurred_at=now,
            subject_id=ORGANIZATION_ID,
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
                "id": str(ORGANIZATION_ID),
                "name": organization.canonical_name,
                "capabilities": [],
                "markets": [],
            },
            "nodes": [node],
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
        self.store.append(
            xeed_id=str(xeed_id), created_at=now, target_uri=target_uri, projection=projection
        )
        return projection
