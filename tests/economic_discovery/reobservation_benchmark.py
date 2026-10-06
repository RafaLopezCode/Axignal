"""Reobservation benchmark harness over the real Prime source slice.

Real: HTTP sensor (fixture transport), HTML representation, governed observation
memory, reuse gate, Prime routing, durable research memory and content-addressed
semantic extraction. Fixtures: the page transport, the semantic provider and the
mechanism executors, which only count calls and answer from state content.

``incremental=True`` chains each run's rich state into the next run as prior;
``incremental=False`` passes an empty prior every time (the FirstProof shape).
If Prime refuses an aged prior, the caller falls back to an empty prior, as a
caller without incremental support has to.
"""

from __future__ import annotations

import hashlib
import socket
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from application.economic_discovery.brain_contracts import (
    SemanticPrimitive,
    TypingDimensionContract,
)
from application.economic_discovery.observation_reuse import ObservationReuseRejected
from application.economic_discovery.prime import DimensionRoutingPolicy, PrimeRoute
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    PrimeMechanismResult,
    execute_prime_source_slice,
)
from application.economic_discovery.research_revalidation import (
    PrimeCurrentnessResearchRevalidator,
)
from application.economic_discovery.research_value import (
    ResearchValueContext,
    ResearchValuePolicy,
    ResearchValueSignal,
    decide_research_value,
)
from application.semantic_extraction import (
    ContentAddressedSemanticExtractor,
    InMemorySemanticExtractionRecordStore,
)
from application.source_representation import (
    compile_rich_subject_state,
    representation_state_data,
)
from cognition.router.router import ModelRouter
from cognition.semantic_extraction_adapter import CognitiveSemanticExtractionAdapter
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from tests.economic_discovery.test_prime_execution import (
    NOW,
    _authorized_seed,
    _budget,
    _request,
    _reuse_authority,
    _reuse_policy,
    _source_policy,
    _temporal_policy,
)
from tests.semantic_extraction.test_semantic_extraction_reuse import (
    CONTRACT,
    PUMPS,
    VALVES,
    _CountingProvider,
    _page,
    _pipeline,
)

TEXT = "document.website.visible_text"
# (day, sentence): refreshes, one real content change, then a gap past stale_after.
TIMELINE: tuple[tuple[int, str], ...] = (
    (0, PUMPS),
    (1, PUMPS),
    (2, PUMPS),
    (3, VALVES),
    (4, VALVES),
    (40, VALVES),
    (41, VALVES),
)


def _contract(dimension_id: str, requirement: str, *extra: str) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.CHOICE,
        question=f"What is {dimension_id}?",
        state_requirements=(requirement,),
        dependencies=(TEXT, *extra),
        mutually_exclusive=True,
        abstention_policy="preserve UNKNOWN",
    )


CONTRACTS = (
    _contract("market-mode", TEXT),
    _contract("market-currentness", TEXT, "source.currentness"),
    _contract("reputation", "document.reviews.visible_text"),
)
ROUTING = tuple(
    DimensionRoutingPolicy(item.dimension_id, "routing-v1", PrimeRoute.STRUCTURED_EVALUATOR)
    for item in CONTRACTS
)


@dataclass
class _CountingExecutor:
    calls: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)

    def execute(self, *, item, state, semantic_candidates):  # type: ignore[no-untyped-def]
        self.calls.append(item.dimension_id)
        datum = state.get(TEXT)
        answer = hashlib.sha256(f"{item.dimension_id}|{datum.value}".encode()).hexdigest()
        self.answers[item.dimension_id] = answer
        return PrimeMechanismResult(output_fingerprint=answer, made_progress=True, requests=1)


def run_reobservation_benchmark(tmp_path: Path, *, incremental: bool) -> dict[str, Any]:
    resolve = socket.getaddrinfo
    socket.getaddrinfo = lambda *_a, **_k: [  # type: ignore[assignment]
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 443))
    ]
    try:
        return _run(tmp_path, incremental=incremental)
    finally:
        socket.getaddrinfo = resolve


def _run(tmp_path: Path, *, incremental: bool) -> dict[str, Any]:
    page, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    extractor = ContentAddressedSemanticExtractor(
        CognitiveSemanticExtractionAdapter(ModelRouter((provider,))),
        InMemorySemanticExtractionRecordStore(),
        extractor_identity="fixture-semantic@1",
        max_reuse_age=timedelta(days=30),
    )
    structured, research_executor = _CountingExecutor(), _CountingExecutor()
    observations = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    research = SqliteSharedObservationWorkMemory(tmp_path / "research.sqlite3")
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    seed, policy = _authorized_seed(), _source_policy()
    request = _request(policy)
    prior = compile_rich_subject_state(subject_id="org:acme", contributions=())
    metrics: dict[str, Any] = {
        "structured_calls": 0,
        "dimensions_reevaluated": 0,
        "research_items_created": 0,
        "semantic_provider_calls": 0,
        "total_requests": 0,
        "full_fallbacks": 0,
        "plans": [],
    }
    research_keys: set[str] = set()

    for day, sentence in TIMELINE:
        clock.now = NOW + timedelta(days=day)
        page.body = _page(sentence)
        preview = representer.represent(
            request=request, observation=sensor.observe(request, policy)
        )
        expected = compile_rich_subject_state(
            subject_id="org:acme",
            contributions=representation_state_data(preview, observation_slot="website"),
        )
        decision = decide_research_value(
            context=ResearchValueContext(
                subject_id="org:acme",
                state_fingerprint=expected.fingerprint,
                dimension_id="reputation",
                missing_requirements=("document.reviews.visible_text",),
                value_signals=frozenset({ResearchValueSignal.MATERIALITY}),
                rights_permit=True,
                capability_available=True,
                budget_permits=True,
                known_source_available=False,
            ),
            policy=ResearchValuePolicy(
                policy_id="research-value",
                version="fr17-v1",
                research_signals=frozenset({ResearchValueSignal.MATERIALITY}),
            ),
        )
        attempts = [prior if incremental else expected_empty(prior)]
        if incremental and prior.data:
            attempts.append(expected_empty(prior))
        for attempt_index, attempt_prior in enumerate(attempts):
            controller = _budget(max_loops=20)
            try:
                trace = execute_prime_source_slice(
                    execution_id=f"run:{day}:{attempt_index}",
                    seed=seed,
                    code_sha="bench",
                    occurred_at=clock.now,
                    observation_memory=observations,
                    learning_memory=learning,
                    request=request,
                    source_policy=policy,
                    source_acquirer=sensor,
                    representation_port=representer,
                    prior_rich_state=attempt_prior,
                    contracts=CONTRACTS,
                    routing_policies=ROUTING,
                    research_decisions=(decision,),
                    execution_controller=controller,
                    ports=PrimeExecutionPorts(
                        deterministic=structured,
                        structured_evaluator=structured,
                        adaptive_research=research_executor,
                    ),
                    semantic_extractor=extractor,
                    semantic_contract=CONTRACT,
                    reuse_policy=_reuse_policy(),
                    temporal_currentness_policy=_temporal_policy(),
                    ingested_observation_reuse_authority=_reuse_authority(),
                    research_work_memory=research,
                )
            except ObservationReuseRejected:
                metrics["full_fallbacks"] += 1
                continue
            break
        metrics["total_requests"] += controller.state.requests
        plan = trace.prime_plan
        planned = () if plan is None else tuple(item.dimension_id for item in plan.items)
        metrics["plans"].append((day, planned))
        metrics["dimensions_reevaluated"] += len(planned)
        research_keys |= set(research.pending_work_keys())
        prior = expected

    metrics["structured_calls"] = len(structured.calls)
    metrics["research_items_created"] = len(research_keys)
    metrics["semantic_provider_calls"] = provider.calls
    revalidator = PrimeCurrentnessResearchRevalidator(
        observation_memory=observations, research_memory=research
    )
    runnable = [
        key
        for key in research.pending_work_keys()
        if revalidator.may_run(research.get(key), now=clock.now)  # type: ignore[arg-type]
    ]
    metrics["research_runnable_at_end"] = len(runnable)
    metrics["final_answers"] = dict(sorted(structured.answers.items()))
    metrics["final_state"] = {item.name: item.value for item in prior.data}
    return metrics


def expected_empty(prior):  # type: ignore[no-untyped-def]
    return compile_rich_subject_state(subject_id=prior.subject_id, contributions=())
