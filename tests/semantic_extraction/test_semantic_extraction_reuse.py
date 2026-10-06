"""Content-addressed semantic extraction reuse across reobservations.

The benchmark drives the real HTTP sensor, HTML representation and fail-closed
payload normalizer; only the model provider is a fixture that counts calls.
"""

from __future__ import annotations

import socket
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery.learning_memory import LearningEventKind
from application.economic_discovery.prime import DimensionRoutingPolicy, PrimeRoute
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    execute_prime_source_slice,
)
from application.semantic_extraction import (
    ContentAddressedSemanticExtractor,
    InMemorySemanticExtractionRecordStore,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticTarget,
)
from application.source_representation import compile_rich_subject_state
from cognition.jobs.model import StructuredResult
from cognition.router.router import ModelRouter
from cognition.semantic_extraction_adapter import CognitiveSemanticExtractionAdapter
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PublicSourcePolicyGate,
    RawHttpResponse,
    ResolvedTarget,
)
from pipeline.source_representation import HtmlDocumentRepresentationAdapter
from tests.economic_discovery.test_prime_execution import (
    NOW,
    _authorized_seed,
    _budget,
    _contract,
    _Executor,
    _public_dns,
    _request,
    _source_policy,
)

CONTRACT = SemanticExtractionContract(
    contract_id="semantic:market-mode",
    version="1",
    targets=(SemanticTarget("market-mode", "economic market mode"),),
)
PUMPS = "ACME manufactures industrial pumps for food factories."
VALVES = "ACME manufactures sanitary valves for dairy plants."


def _page(sentence: str) -> bytes:
    return (
        "<html lang='en'><head><title>ACME</title></head>"
        f"<body><p>Since 1990.</p><p>{sentence}</p></body></html>"
    ).encode()


class _MutablePage:
    instrument_ref = "reuse-fixture-http/1"

    def __init__(self) -> None:
        self.body = _page(PUMPS)

    def fetch(
        self, target: ResolvedTarget, *, timeout_ms: int, max_response_bytes: int
    ) -> RawHttpResponse:
        del timeout_ms, max_response_bytes
        return RawHttpResponse(
            status=200,
            headers=(("Content-Type", "text/html; charset=utf-8"),),
            body=self.body,
            peer_ip=target.addresses[0],
        )


class _CountingProvider:
    """Returns the grounded 'manufactures' sentence it actually sees."""

    name = "fixture-semantic"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, job):  # type: ignore[no-untyped-def]
        self.calls += 1
        text = str(job.context["visible_text"])
        excerpt = next(item for item in (PUMPS, VALVES) if item in text)
        return StructuredResult(
            job_id=job.id,
            provider=self.name,
            payload={
                "provider_version": "1",
                "candidates": [
                    {
                        "semantic_target": "market-mode",
                        "statement": excerpt.removeprefix("ACME ").rstrip("."),
                        "excerpt": excerpt,
                        "grounding_surface": "VISIBLE_TEXT",
                    }
                ],
            },
        )


class _Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        return self.now


def _pipeline(tmp_path: Path):  # type: ignore[no-untyped-def]
    page, clock = _MutablePage(), _Clock()
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=page,  # type: ignore[arg-type]
        artifacts=artifacts,
        clock=clock,
    )
    return page, clock, sensor, HtmlDocumentRepresentationAdapter(artifacts)


def _reobserve(tmp_path: Path, extractor_factory, days: int, change_on: int):  # type: ignore[no-untyped-def]
    page, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    extractor = extractor_factory(CognitiveSemanticExtractionAdapter(ModelRouter((provider,))))
    policy = _source_policy()
    request = _request(policy)
    results: list[SemanticCandidateSet] = []
    for day in range(days):
        clock.now = NOW + timedelta(days=day)
        if day == change_on:
            page.body = _page(VALVES)
        observation = sensor.observe(request, policy)
        representation = representer.represent(request=request, observation=observation)
        results.append(extractor.extract(representation=representation, contract=CONTRACT))
    return provider.calls, results


def _with_reuse(max_age: timedelta = timedelta(days=30)):  # type: ignore[no-untyped-def]
    store = InMemorySemanticExtractionRecordStore()
    return lambda inner: ContentAddressedSemanticExtractor(
        inner, store, extractor_identity="fixture-semantic@1", max_reuse_age=max_age
    )


def test_reobservation_benchmark_reuses_unchanged_content_and_reextracts_changes(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    baseline_calls, baseline = _reobserve(tmp_path / "a", lambda inner: inner, 10, 7)
    reuse_calls, reused = _reobserve(tmp_path / "b", _with_reuse(), 10, 7)

    # 10 daily reobservations, content changes once: one provider call per distinct content.
    assert (baseline_calls, reuse_calls) == (10, 2)

    def semantics(item: SemanticCandidateSet):  # type: ignore[no-untyped-def]
        return [(c.semantic_target, c.statement, c.excerpt) for c in item.candidates]

    # Same grounded proposals, each bound to its own observation and time.
    assert [semantics(item) for item in reused] == [semantics(item) for item in baseline]
    for fresh, cached in zip(baseline, reused, strict=True):
        assert cached.representation_id == fresh.representation_id
        assert [c.observation_id for c in cached.candidates] == [
            c.observation_id for c in fresh.candidates
        ]
        assert [c.observed_at for c in cached.candidates] == [
            c.observed_at for c in fresh.candidates
        ]
        assert cached.provider == "fixture-semantic"
        assert not cached.is_canonical_truth
    assert [item.reused_from_extraction_id is None for item in reused] == [
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
    ]
    assert {item.reused_from_extraction_id for item in reused[1:7]} == {reused[0].extraction_id}
    assert {item.reused_from_extraction_id for item in reused[8:]} == {reused[7].extraction_id}


def test_reuse_is_bounded_by_age_from_the_original_provider_extraction(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    calls, results = _reobserve(tmp_path, _with_reuse(timedelta(days=3)), 8, 99)

    # Reuse never refreshes its own anchor: days 0 and 4 call the provider.
    assert calls == 2
    assert [item.reused_from_extraction_id is None for item in results] == [
        True,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ]


def test_contract_or_extractor_identity_change_forces_fresh_extraction(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    inner = CognitiveSemanticExtractionAdapter(ModelRouter((provider,)))
    store = InMemorySemanticExtractionRecordStore()
    policy = _source_policy()
    request = _request(policy)

    def represent(day: int):  # type: ignore[no-untyped-def]
        clock.now = NOW + timedelta(days=day)
        return representer.represent(request=request, observation=sensor.observe(request, policy))

    first = ContentAddressedSemanticExtractor(
        inner, store, extractor_identity="fixture-semantic@1", max_reuse_age=timedelta(days=30)
    )
    first.extract(representation=represent(0), contract=CONTRACT)
    changed_contract = replace(CONTRACT, version="2")
    first.extract(representation=represent(1), contract=changed_contract)
    swapped = ContentAddressedSemanticExtractor(
        inner, store, extractor_identity="other-provider@7", max_reuse_age=timedelta(days=30)
    )
    swapped.extract(representation=represent(2), contract=CONTRACT)

    assert provider.calls == 3


def test_ungroundable_reuse_fails_closed_to_fresh_extraction(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    store = InMemorySemanticExtractionRecordStore()
    extractor = ContentAddressedSemanticExtractor(
        CognitiveSemanticExtractionAdapter(ModelRouter((provider,))),
        store,
        extractor_identity="fixture-semantic@1",
        max_reuse_age=timedelta(days=30),
    )
    policy = _source_policy()
    request = _request(policy)
    first = representer.represent(request=request, observation=sensor.observe(request, policy))
    extractor.extract(representation=first, contract=CONTRACT)
    # Corrupt the stored anchor so its excerpt is no longer the text under its span.
    ((key, record),) = store._records.items()  # adversarial fixture
    store._records[key] = replace(
        record, candidates=(replace(record.candidates[0], excerpt="ACME builds robots."),)
    )

    clock.now = NOW + timedelta(days=1)
    second = representer.represent(request=request, observation=sensor.observe(request, policy))
    result = extractor.extract(representation=second, contract=CONTRACT)

    assert provider.calls == 2
    assert result.reused_from_extraction_id is None
    assert result.candidates[0].excerpt == PUMPS


def test_reused_set_must_reference_another_extraction() -> None:
    with pytest.raises(ValueError, match="earlier extraction"):
        SemanticCandidateSet(
            extraction_id="extraction:a",
            subject_id="org:acme",
            representation_id="rep:a",
            contract_fingerprint="contract",
            provider="fixture",
            provider_version="1",
            result_fingerprint="result",
            candidates=(),
            reused_from_extraction_id="extraction:a",
        )


def test_prime_accounts_reused_extraction_as_zero_provider_requests(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    extractor = ContentAddressedSemanticExtractor(
        CognitiveSemanticExtractionAdapter(ModelRouter((provider,))),
        InMemorySemanticExtractionRecordStore(),
        extractor_identity="fixture-semantic@1",
        max_reuse_age=timedelta(days=30),
    )
    seed = _authorized_seed()
    policy = _source_policy()
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    controllers = []

    for day in (0, 1):
        clock.now = NOW + timedelta(days=day)
        controller = _budget()
        controllers.append(controller)
        execute_prime_source_slice(
            execution_id=f"run:{day}",
            seed=seed,
            code_sha="abc123",
            occurred_at=clock.now,
            observation_memory=SqliteObservationMemory(tmp_path / f"obs-{day}.sqlite3"),
            learning_memory=learning,
            request=_request(policy),
            source_policy=policy,
            source_acquirer=sensor,
            representation_port=representer,
            prior_rich_state=compile_rich_subject_state(subject_id="org:acme", contributions=()),
            contracts=(_contract("market-mode"),),
            routing_policies=(
                DimensionRoutingPolicy(
                    "market-mode", "routing-v1", PrimeRoute.STRUCTURED_EVALUATOR
                ),
            ),
            research_decisions=(),
            execution_controller=controller,
            ports=PrimeExecutionPorts(
                deterministic=_Executor("deterministic"),
                structured_evaluator=_Executor("structured"),
                adaptive_research=_Executor("adaptive"),
            ),
            semantic_extractor=extractor,
            semantic_contract=CONTRACT,
        )

    assert provider.calls == 1
    semantic = [
        event
        for event in learning.for_xeed("xeed:1")
        if event.kind is LearningEventKind.SEMANTIC_EXTRACTION
    ]
    assert [event.reason_code for event in semantic] == [
        "GROUNDED_CANDIDATES_NORMALIZED",
        "GROUNDED_CANDIDATES_REUSED",
    ]
    assert semantic[1].provider == "fixture-semantic"
    assert semantic[1].replay.get("reused_from_extraction_id") == semantic[0].activity_ref
    # Structured evaluator still costs one request per run; extraction cost drops to zero.
    assert controllers[1].state.requests == controllers[0].state.requests - 1


def test_sqlite_store_carries_reuse_across_independent_runs(monkeypatch, tmp_path: Path) -> None:
    from pipeline.semantic_extraction import SqliteSemanticExtractionRecordStore

    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    _, clock, sensor, representer = _pipeline(tmp_path)
    provider = _CountingProvider()
    policy = _source_policy()
    request = _request(policy)
    results = []
    for day in (0, 1):
        clock.now = NOW + timedelta(days=day)
        extractor = ContentAddressedSemanticExtractor(  # a fresh process-equivalent each run
            CognitiveSemanticExtractionAdapter(ModelRouter((provider,))),
            SqliteSemanticExtractionRecordStore(tmp_path / "semantic-reuse.sqlite3"),
            extractor_identity="fixture-semantic@1",
            max_reuse_age=timedelta(days=30),
        )
        representation = representer.represent(
            request=request, observation=sensor.observe(request, policy)
        )
        results.append(extractor.extract(representation=representation, contract=CONTRACT))

    assert provider.calls == 1
    assert results[1].reused_from_extraction_id == results[0].extraction_id
    assert results[1].candidates[0].excerpt == results[0].candidates[0].excerpt == PUMPS
