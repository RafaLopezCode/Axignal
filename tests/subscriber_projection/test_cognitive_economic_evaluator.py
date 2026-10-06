from __future__ import annotations

from pathlib import Path

import pytest

from cognition.economic_evaluator_adapter import CognitiveEconomicEvaluatorAdapter
from cognition.jobs.model import CognitiveJob, StructuredResult
from cognition.router.router import ModelRouter
from tests.economic_discovery.test_first_vertical_e2e import _run_fixture


class _Provider:
    name = "offline-structured-test"

    def __init__(self, selected_option: str = "UNKNOWN") -> None:
        self.selected_option = selected_option
        self.calls = 0
        self.job: CognitiveJob | None = None

    def complete(self, job: CognitiveJob) -> StructuredResult:
        self.calls += 1
        self.job = job
        return StructuredResult(
            job_id=job.id,
            provider=self.name,
            payload={"selected_option": self.selected_option},
        )


def test_router_adapter_binds_exact_eb04_contract_and_reports_no_fake_confidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _result, _transport, _extractor, fixture_evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path
    )
    request = fixture_evaluator.requests[0]
    provider = _Provider()
    adapter = CognitiveEconomicEvaluatorAdapter(
        ModelRouter((provider,)),
        provider_name=provider.name,
        provider_version="deployment-manifest-v1",
    )

    judgment = adapter.evaluate(request)

    assert provider.calls == 1
    assert provider.job is not None
    assert provider.job.context["stateFingerprint"] == request.state_fingerprint
    assert judgment.selected_option == "UNKNOWN"
    assert judgment.distribution == ()
    assert judgment.confidence is None
    assert judgment.evaluator_version == "deployment-manifest-v1"
    assert judgment.replay_reference.startswith("cognitive-result:")


def test_router_adapter_requires_explicit_provider_and_rejects_untyped_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _result, _transport, _extractor, fixture_evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path
    )
    request = fixture_evaluator.requests[0]
    provider = _Provider("NOT_AN_OPTION")
    router = ModelRouter((provider,))
    with pytest.raises(ValueError, match="not registered"):
        CognitiveEconomicEvaluatorAdapter(
            router,
            provider_name="missing-provider",
            provider_version="1",
        )

    adapter = CognitiveEconomicEvaluatorAdapter(
        router,
        provider_name=provider.name,
        provider_version="1",
    )
    with pytest.raises(ValueError, match="outside the declared choice set"):
        adapter.evaluate(request)
