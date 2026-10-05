from __future__ import annotations

from typing import cast

import pytest

from application.economic_discovery.contracts import (
    ConfidenceCapability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredJudgment,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetReservation,
    ExecutionBudgetState,
    ExecutionReservationRejected,
    GovernedExecutionController,
)
from application.economic_discovery.governed_dispatch import (
    DispatchCost,
    GovernedDispatchRecorder,
    GovernedSemanticExtractor,
    GovernedSourceAcquirer,
    GovernedStructuredEvaluator,
)
from application.semantic_extraction import (
    SemanticCandidateSet,
    SemanticExtractionContract,
)
from application.source_acquisition import (
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
)
from application.source_representation import DocumentRepresentation


def _policy(**changes: object) -> ExecutionBudgetPolicy:
    values: dict[str, object] = {
        "policy_id": "governed-dispatch-test",
        "version": "1",
        "max_requests": 8,
        "max_sources": 4,
        "max_loops": 4,
        "max_elapsed_ms": 10_000,
    }
    values.update(changes)
    return ExecutionBudgetPolicy(**values)  # type: ignore[arg-type]


def _ticks(*values: int):
    iterator = iter(values)
    return lambda: next(iterator)


class _SourcePort:
    def __init__(self, result: SourceObservation, *, fail: bool = False) -> None:
        self.result = result
        self.fail = fail
        self.calls = 0

    def observe(
        self,
        request: SourceRequest,
        policy: SourceDispatchPolicy,
    ) -> SourceObservation:
        del request, policy
        self.calls += 1
        if self.fail:
            raise TimeoutError("synthetic source failure")
        return self.result


class _SemanticPort:
    def __init__(self, result: SemanticCandidateSet, *, fail: bool = False) -> None:
        self.result = result
        self.fail = fail
        self.calls = 0

    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet:
        del representation, contract
        self.calls += 1
        if self.fail:
            raise TimeoutError("synthetic semantic failure")
        return self.result


class _EvaluatorPort:
    capability_profile = EvaluatorCapabilityProfile(
        "governed-dispatch-evaluator",
        "1",
        DistributionCapability.NEVER,
        ConfidenceCapability.NEVER,
        replay_reference_supported=True,
    )

    def __init__(self, result: StructuredJudgment, *, fail: bool = False) -> None:
        self.result = result
        self.fail = fail
        self.calls = 0

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        del request
        self.calls += 1
        if self.fail:
            raise TimeoutError("synthetic evaluator failure")
        return self.result


def _source_result(*, failure_state: str | None = None) -> SourceObservation:
    return cast(SourceObservation, type("SourceResult", (), {"failure_state": failure_state})())


def _semantic_result() -> SemanticCandidateSet:
    return cast(SemanticCandidateSet, object())


def _judgment() -> StructuredJudgment:
    return cast(StructuredJudgment, object())


def _source_args() -> tuple[SourceRequest, SourceDispatchPolicy]:
    return cast(SourceRequest, object()), cast(SourceDispatchPolicy, object())


def _semantic_args() -> tuple[DocumentRepresentation, SemanticExtractionContract]:
    return cast(DocumentRepresentation, object()), cast(SemanticExtractionContract, object())


def _evaluation_request() -> StructuredEvaluationRequest:
    return cast(StructuredEvaluationRequest, object())


def test_source_dispatch_is_blocked_before_underlying_port_when_source_budget_is_exhausted() -> (
    None
):
    controller = GovernedExecutionController(
        _policy(max_sources=1),
        ExecutionBudgetState(sources=1),
    )
    port = _SourcePort(_source_result())
    wrapper = GovernedSourceAcquirer(port, GovernedDispatchRecorder(controller))
    request, policy = _source_args()

    with pytest.raises(ExecutionReservationRejected):
        wrapper.observe(request, policy)

    assert port.calls == 0
    assert controller.active_reservation_ids == ()


def test_source_success_reconciles_request_source_latency_and_passthrough() -> None:
    controller = GovernedExecutionController(_policy())
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(1_000_000, 6_000_000),
    )
    result = _source_result()
    port = _SourcePort(result)
    wrapper = GovernedSourceAcquirer(port, recorder)
    request, policy = _source_args()

    actual = wrapper.observe(request, policy)

    assert actual is result
    assert controller.state.requests == 1
    assert controller.state.sources == 1
    assert controller.state.elapsed_ms == 5
    assert controller.state.cost_complete is False
    assert controller.state.amount_microunits is None
    assert controller.active_reservation_ids == ()
    assert len(recorder.records) == 1
    assert recorder.records[0].succeeded is True


def test_source_failure_is_accounted_and_leaves_no_active_reservation() -> None:
    controller = GovernedExecutionController(_policy())
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(10_000_000, 17_000_000),
    )
    port = _SourcePort(_source_result(), fail=True)
    wrapper = GovernedSourceAcquirer(port, recorder)
    request, policy = _source_args()

    with pytest.raises(TimeoutError, match="synthetic source failure"):
        wrapper.observe(request, policy)

    assert controller.state.requests == 1
    assert controller.state.sources == 1
    assert controller.state.elapsed_ms == 7
    assert controller.active_reservation_ids == ()
    assert recorder.records[0].succeeded is False


@pytest.mark.parametrize("fail", [False, True])
def test_semantic_dispatch_reconciles_request_latency_on_success_and_failure(fail: bool) -> None:
    controller = GovernedExecutionController(_policy())
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(20_000_000, 29_000_000),
    )
    result = _semantic_result()
    port = _SemanticPort(result, fail=fail)
    wrapper = GovernedSemanticExtractor(port, recorder)
    representation, contract = _semantic_args()

    if fail:
        with pytest.raises(TimeoutError, match="synthetic semantic failure"):
            wrapper.extract(representation=representation, contract=contract)
    else:
        assert wrapper.extract(representation=representation, contract=contract) is result

    assert controller.state.requests == 1
    assert controller.state.sources == 0
    assert controller.state.loops == 0
    assert controller.state.elapsed_ms == 9
    assert controller.active_reservation_ids == ()
    assert recorder.records[0].succeeded is (not fail)


@pytest.mark.parametrize("fail", [False, True])
def test_structured_evaluator_reconciles_request_loop_latency_and_passthrough(
    fail: bool,
) -> None:
    controller = GovernedExecutionController(_policy())
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(30_000_000, 41_000_000),
    )
    result = _judgment()
    port = _EvaluatorPort(result, fail=fail)
    wrapper = GovernedStructuredEvaluator(port, recorder)

    assert wrapper.capability_profile is port.capability_profile
    if fail:
        with pytest.raises(TimeoutError, match="synthetic evaluator failure"):
            wrapper.evaluate(_evaluation_request())
    else:
        assert wrapper.evaluate(_evaluation_request()) is result

    assert controller.state.requests == 1
    assert controller.state.sources == 0
    assert controller.state.loops == 1
    assert controller.state.elapsed_ms == 11
    assert controller.active_reservation_ids == ()
    assert recorder.records[0].succeeded is (not fail)


def test_unknown_cost_preserves_known_lower_bound_and_never_becomes_zero() -> None:
    controller = GovernedExecutionController(
        _policy(),
        ExecutionBudgetState(amount_microunits=7, currency="USD"),
    )
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(0, 1_000_000),
    )
    wrapper = GovernedSemanticExtractor(
        _SemanticPort(_semantic_result()),
        recorder,
    )
    representation, contract = _semantic_args()

    wrapper.extract(representation=representation, contract=contract)

    assert controller.state.amount_microunits == 7
    assert controller.state.currency == "USD"
    assert controller.state.cost_complete is False
    assert recorder.records[0].cost_known is False


def test_known_cost_accumulates_when_caller_can_state_it_contractually() -> None:
    controller = GovernedExecutionController(
        _policy(),
        ExecutionBudgetState(amount_microunits=7, currency="USD"),
    )
    recorder = GovernedDispatchRecorder(
        controller,
        monotonic_ns=_ticks(0, 2_000_000),
    )
    wrapper = GovernedSemanticExtractor(
        _SemanticPort(_semantic_result()),
        recorder,
        cost=DispatchCost(3, "usd"),
    )
    representation, contract = _semantic_args()

    wrapper.extract(representation=representation, contract=contract)

    assert controller.state.amount_microunits == 10
    assert controller.state.currency == "USD"
    assert controller.state.cost_complete is True
    assert recorder.records[0].amount_microunits == 3
    assert recorder.records[0].currency == "USD"


def test_repeated_reservation_id_fails_closed_before_port_call() -> None:
    controller = GovernedExecutionController(_policy())
    controller.reserve(
        ExecutionBudgetReservation(
            reservation_id="dispatch:0001:source",
            requests=1,
            sources=1,
        )
    )
    recorder = GovernedDispatchRecorder(controller)
    port = _SourcePort(_source_result())
    wrapper = GovernedSourceAcquirer(port, recorder)
    request, policy = _source_args()

    with pytest.raises(ValueError, match="already active"):
        wrapper.observe(request, policy)

    assert port.calls == 0
    assert controller.active_reservation_ids == ("dispatch:0001:source",)
    controller.release("dispatch:0001:source")
