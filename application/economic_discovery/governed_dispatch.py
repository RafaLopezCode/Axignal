"""Reusable governed dispatch wrappers for costly Economic Brain ports.

These adapters only enforce execution budget, attempt accounting and monotonic
latency measurement. They have no authority over truth, semantics, admission or
provider output.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from application.economic_discovery.contracts import (
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredEvaluatorPort,
    StructuredJudgment,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    ExecutionBudgetReservation,
    GovernedExecutionController,
)
from application.economic_discovery.prime_execution import (
    SemanticExtractionPort,
    SourceAcquisitionPort,
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

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class DispatchCost:
    """Known per-dispatch monetary cost, or explicit UNKNOWN when omitted."""

    amount_microunits: int | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("dispatch cost amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("dispatch cost cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("dispatch cost currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)

    @property
    def known(self) -> bool:
        return self.amount_microunits is not None


@dataclass(frozen=True, slots=True)
class ExecutionAttemptRecord:
    attempt_kind: str
    reservation_id: str
    elapsed_ms: int
    succeeded: bool
    requests: int
    sources: int
    loops: int
    amount_microunits: int | None
    currency: str | None

    def __post_init__(self) -> None:
        if not self.attempt_kind.strip() or not self.reservation_id.strip():
            raise ValueError("execution attempt record identity is required")
        if self.elapsed_ms < 0:
            raise ValueError("execution attempt elapsed time cannot be negative")
        for value in (self.requests, self.sources, self.loops):
            if value < 0:
                raise ValueError("execution attempt counters cannot be negative")
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("execution attempt cost amount and currency must coexist")

    @property
    def cost_known(self) -> bool:
        return self.amount_microunits is not None


@dataclass(slots=True)
class GovernedDispatchRecorder:
    controller: GovernedExecutionController
    records: list[ExecutionAttemptRecord] = field(default_factory=list)
    sequence: int = 0
    monotonic_ns: Callable[[], int] = time.monotonic_ns

    def next_id(self, kind: str) -> str:
        if not kind.strip():
            raise ValueError("governed dispatch kind is required")
        self.sequence += 1
        return f"dispatch:{self.sequence:04d}:{kind}"

    def execute(
        self,
        *,
        kind: str,
        reservation_id: str,
        requests: int,
        sources: int,
        loops: int,
        cost: DispatchCost,
        call: Callable[[], T],
        success: Callable[[T], bool] | None = None,
        reported_cost: Callable[[T], DispatchCost] | None = None,
    ) -> T:
        self.controller.reserve(
            ExecutionBudgetReservation(
                reservation_id=reservation_id,
                amount_microunits=cost.amount_microunits,
                currency=cost.currency,
                requests=requests,
                sources=sources,
                loops=loops,
            )
        )
        started_ns = self.monotonic_ns()
        succeeded = False
        # A reservation estimate is not measured spend. With dynamic reporting,
        # a failed transport may have incurred an unknown charge.
        actual_cost = cost if reported_cost is None else DispatchCost()
        try:
            result = call()
            if reported_cost is not None:
                actual_cost = reported_cost(result)
            succeeded = True if success is None else success(result)
        except Exception:
            elapsed_ms = max(0, (self.monotonic_ns() - started_ns) // 1_000_000)
            self.controller.reconcile(
                reservation_id,
                ExecutionBudgetDelta(
                    amount_microunits=actual_cost.amount_microunits,
                    currency=actual_cost.currency,
                    elapsed_ms=elapsed_ms,
                    requests=requests,
                    sources=sources,
                    loops=loops,
                    made_progress=False,
                ),
            )
            self.records.append(
                ExecutionAttemptRecord(
                    attempt_kind=kind,
                    reservation_id=reservation_id,
                    elapsed_ms=elapsed_ms,
                    succeeded=False,
                    requests=requests,
                    sources=sources,
                    loops=loops,
                    amount_microunits=actual_cost.amount_microunits,
                    currency=actual_cost.currency,
                )
            )
            raise

        elapsed_ms = max(0, (self.monotonic_ns() - started_ns) // 1_000_000)
        self.controller.reconcile(
            reservation_id,
            ExecutionBudgetDelta(
                amount_microunits=actual_cost.amount_microunits,
                currency=actual_cost.currency,
                elapsed_ms=elapsed_ms,
                requests=requests,
                sources=sources,
                loops=loops,
                made_progress=succeeded,
            ),
        )
        self.records.append(
            ExecutionAttemptRecord(
                attempt_kind=kind,
                reservation_id=reservation_id,
                elapsed_ms=elapsed_ms,
                succeeded=succeeded,
                requests=requests,
                sources=sources,
                loops=loops,
                amount_microunits=actual_cost.amount_microunits,
                currency=actual_cost.currency,
            )
        )
        return result


@dataclass(slots=True)
class GovernedSourceAcquirer:
    inner: SourceAcquisitionPort
    recorder: GovernedDispatchRecorder
    cost: DispatchCost = DispatchCost()

    def observe(
        self,
        request: SourceRequest,
        policy: SourceDispatchPolicy,
    ) -> SourceObservation:
        reservation_id = self.recorder.next_id("source")
        return self.recorder.execute(
            kind="source",
            reservation_id=reservation_id,
            requests=1,
            sources=1,
            loops=0,
            cost=self.cost,
            call=lambda: self.inner.observe(request, policy),
            success=lambda observation: observation.failure_state is None,
        )


@dataclass(slots=True)
class GovernedSemanticExtractor:
    inner: SemanticExtractionPort
    recorder: GovernedDispatchRecorder
    cost: DispatchCost = DispatchCost()

    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet:
        reservation_id = self.recorder.next_id("semantic")
        return self.recorder.execute(
            kind="semantic",
            reservation_id=reservation_id,
            requests=1,
            sources=0,
            loops=0,
            cost=self.cost,
            call=lambda: self.inner.extract(
                representation=representation,
                contract=contract,
            ),
        )


@dataclass(slots=True)
class GovernedStructuredEvaluator:
    inner: StructuredEvaluatorPort
    recorder: GovernedDispatchRecorder
    cost: DispatchCost = DispatchCost()

    @property
    def capability_profile(self) -> EvaluatorCapabilityProfile:
        return self.inner.capability_profile

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        reservation_id = self.recorder.next_id("structured-evaluate")
        return self.recorder.execute(
            kind="structured-evaluate",
            reservation_id=reservation_id,
            requests=1,
            sources=0,
            loops=1,
            cost=self.cost,
            call=lambda: self.inner.evaluate(request),
        )
