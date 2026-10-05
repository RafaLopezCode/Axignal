"""Provider-neutral execution budget and stop contracts for AXIGNAL.

This module governs whether another unit of research/observation work may start.
It does not choose sources, providers, truth, or canonical writes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ExecutionStopReason(StrEnum):
    MONETARY_BUDGET_EXHAUSTED = "MONETARY_BUDGET_EXHAUSTED"
    REQUEST_BUDGET_EXHAUSTED = "REQUEST_BUDGET_EXHAUSTED"
    SOURCE_BUDGET_EXHAUSTED = "SOURCE_BUDGET_EXHAUSTED"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"
    LOOP_LIMIT_REACHED = "LOOP_LIMIT_REACHED"
    NO_PROGRESS = "NO_PROGRESS"
    COST_UNKNOWN = "COST_UNKNOWN"


@dataclass(frozen=True, slots=True)
class ExecutionBudgetPolicy:
    policy_id: str
    version: str
    currency: str | None = None
    max_amount_microunits: int | None = None
    max_requests: int | None = None
    max_sources: int | None = None
    max_elapsed_ms: int | None = None
    max_retries: int | None = None
    max_loops: int | None = None
    max_no_progress_streak: int | None = None
    stop_on_unknown_cost: bool = False

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("execution budget policy identity is required")
        if (self.currency is None) != (self.max_amount_microunits is None):
            raise ValueError("monetary budget amount and currency must coexist")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("execution budget currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        for value in (
            self.max_amount_microunits,
            self.max_requests,
            self.max_sources,
            self.max_elapsed_ms,
            self.max_retries,
            self.max_loops,
            self.max_no_progress_streak,
        ):
            if value is not None and value < 1:
                raise ValueError("execution budget limits must be positive")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "version": self.version,
                "currency": self.currency,
                "max_amount_microunits": self.max_amount_microunits,
                "max_requests": self.max_requests,
                "max_sources": self.max_sources,
                "max_elapsed_ms": self.max_elapsed_ms,
                "max_retries": self.max_retries,
                "max_loops": self.max_loops,
                "max_no_progress_streak": self.max_no_progress_streak,
                "stop_on_unknown_cost": self.stop_on_unknown_cost,
            }
        )


@dataclass(frozen=True, slots=True)
class ExecutionBudgetState:
    amount_microunits: int | None = None
    currency: str | None = None
    cost_complete: bool | None = None
    elapsed_ms: int = 0
    requests: int = 0
    sources: int = 0
    retries: int = 0
    loops: int = 0
    no_progress_streak: int = 0

    def __post_init__(self) -> None:
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("execution cost amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("execution cost cannot be negative")
        inferred_complete = self.amount_microunits is not None
        if self.cost_complete is None:
            object.__setattr__(self, "cost_complete", inferred_complete)
        elif not isinstance(self.cost_complete, bool):
            raise ValueError("execution cost completeness must be boolean")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("execution state currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        for value in (
            self.elapsed_ms,
            self.requests,
            self.sources,
            self.retries,
            self.loops,
            self.no_progress_streak,
        ):
            if value < 0:
                raise ValueError("execution counters cannot be negative")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "amount_microunits": self.amount_microunits,
                "currency": self.currency,
                "cost_complete": self.cost_complete,
                "elapsed_ms": self.elapsed_ms,
                "requests": self.requests,
                "sources": self.sources,
                "retries": self.retries,
                "loops": self.loops,
                "no_progress_streak": self.no_progress_streak,
            }
        )


@dataclass(frozen=True, slots=True)
class ExecutionBudgetDelta:
    amount_microunits: int | None = None
    currency: str | None = None
    elapsed_ms: int = 0
    requests: int = 0
    sources: int = 0
    retries: int = 0
    loops: int = 1
    made_progress: bool = True

    def __post_init__(self) -> None:
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("execution delta cost amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("execution delta cost cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("execution delta currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        for value in (
            self.elapsed_ms,
            self.requests,
            self.sources,
            self.retries,
            self.loops,
        ):
            if value < 0:
                raise ValueError("execution delta counters cannot be negative")


@dataclass(frozen=True, slots=True)
class ExecutionBudgetReservation:
    """Capacity held before a costly dispatch and reconciled afterward."""

    reservation_id: str
    amount_microunits: int | None = None
    currency: str | None = None
    elapsed_ms: int = 0
    requests: int = 0
    sources: int = 0
    retries: int = 0
    loops: int = 0

    def __post_init__(self) -> None:
        if not self.reservation_id.strip():
            raise ValueError("execution reservation identity is required")
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("reserved monetary amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("reserved execution cost cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("reservation currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        for value in (
            self.elapsed_ms,
            self.requests,
            self.sources,
            self.retries,
            self.loops,
        ):
            if value < 0:
                raise ValueError("execution reservation counters cannot be negative")


class ExecutionReservationRejected(RuntimeError):
    """Raised when a pre-dispatch reservation would exceed governed capacity."""

    def __init__(self, decision: ExecutionBudgetDecision) -> None:
        self.decision = decision
        super().__init__(f"execution reservation rejected: {decision.stop_reason}")


@dataclass(frozen=True, slots=True)
class ExecutionBudgetDecision:
    may_continue: bool
    policy_id: str
    policy_version: str
    policy_fingerprint: str
    state_fingerprint: str
    stop_reason: ExecutionStopReason | None = None

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.policy_id,
                self.policy_version,
                self.policy_fingerprint,
                self.state_fingerprint,
            )
        ):
            raise ValueError("execution budget decision identity is required")
        if self.may_continue and self.stop_reason is not None:
            raise ValueError("continuing execution cannot carry a stop reason")
        if not self.may_continue and self.stop_reason is None:
            raise ValueError("stopped execution requires a stop reason")


def evaluate_execution_budget(
    *,
    policy: ExecutionBudgetPolicy,
    state: ExecutionBudgetState,
) -> ExecutionBudgetDecision:
    """Authorize or stop the next unit of work from current measured usage."""

    reason: ExecutionStopReason | None = None

    if (
        policy.stop_on_unknown_cost
        and policy.max_amount_microunits is not None
        and not state.cost_complete
    ):
        reason = ExecutionStopReason.COST_UNKNOWN

    if (
        reason is None
        and policy.max_amount_microunits is not None
        and state.amount_microunits is not None
    ):
        if state.currency != policy.currency:
            raise ValueError("execution cost currency does not match budget currency")
        if state.amount_microunits >= policy.max_amount_microunits:
            reason = ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED

    checks = (
        (policy.max_requests, state.requests, ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED),
        (policy.max_sources, state.sources, ExecutionStopReason.SOURCE_BUDGET_EXHAUSTED),
        (policy.max_elapsed_ms, state.elapsed_ms, ExecutionStopReason.DEADLINE_EXCEEDED),
        (policy.max_retries, state.retries, ExecutionStopReason.RETRY_LIMIT_REACHED),
        (policy.max_loops, state.loops, ExecutionStopReason.LOOP_LIMIT_REACHED),
        (
            policy.max_no_progress_streak,
            state.no_progress_streak,
            ExecutionStopReason.NO_PROGRESS,
        ),
    )
    if reason is None:
        for limit, used, candidate in checks:
            if limit is not None and used >= limit:
                reason = candidate
                break

    return ExecutionBudgetDecision(
        may_continue=reason is None,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        policy_fingerprint=policy.fingerprint,
        state_fingerprint=state.fingerprint,
        stop_reason=reason,
    )


def _accumulate_execution_delta(
    *,
    state: ExecutionBudgetState,
    delta: ExecutionBudgetDelta,
) -> ExecutionBudgetState:
    """Accumulate measured usage without deciding whether dispatch was allowed."""

    if (
        state.currency is not None
        and delta.currency is not None
        and state.currency != delta.currency
    ):
        raise ValueError("execution delta currency does not match accumulated currency")

    if delta.amount_microunits is None:
        next_amount = state.amount_microunits
        next_currency = state.currency
        next_complete = False
    else:
        next_currency = state.currency or delta.currency
        next_amount = (state.amount_microunits or 0) + delta.amount_microunits
        next_complete = bool(state.cost_complete)

    return ExecutionBudgetState(
        amount_microunits=next_amount,
        currency=next_currency,
        cost_complete=next_complete,
        elapsed_ms=state.elapsed_ms + delta.elapsed_ms,
        requests=state.requests + delta.requests,
        sources=state.sources + delta.sources,
        retries=state.retries + delta.retries,
        loops=state.loops + delta.loops,
        no_progress_streak=0 if delta.made_progress else state.no_progress_streak + 1,
    )


def advance_execution_budget(
    *,
    policy: ExecutionBudgetPolicy,
    state: ExecutionBudgetState,
    delta: ExecutionBudgetDelta,
) -> ExecutionBudgetState:
    """Record one completed unit of work after pre-dispatch authorization."""

    before = evaluate_execution_budget(policy=policy, state=state)
    if not before.may_continue:
        raise RuntimeError(f"execution already stopped: {before.stop_reason}")
    return _accumulate_execution_delta(state=state, delta=delta)


def _reserved_projection(
    state: ExecutionBudgetState,
    reservations: tuple[ExecutionBudgetReservation, ...],
) -> ExecutionBudgetState:
    amount = state.amount_microunits
    currency = state.currency
    complete = bool(state.cost_complete)
    elapsed_ms = state.elapsed_ms
    requests = state.requests
    sources = state.sources
    retries = state.retries
    loops = state.loops

    for reservation in reservations:
        if (
            currency is not None
            and reservation.currency is not None
            and currency != reservation.currency
        ):
            raise ValueError("reservation currency does not match accumulated currency")
        if reservation.amount_microunits is None:
            complete = False
        else:
            currency = currency or reservation.currency
            amount = (amount or 0) + reservation.amount_microunits
        elapsed_ms += reservation.elapsed_ms
        requests += reservation.requests
        sources += reservation.sources
        retries += reservation.retries
        loops += reservation.loops

    return ExecutionBudgetState(
        amount_microunits=amount,
        currency=currency,
        cost_complete=complete,
        elapsed_ms=elapsed_ms,
        requests=requests,
        sources=sources,
        retries=retries,
        loops=loops,
        no_progress_streak=state.no_progress_streak,
    )


def _pre_reservation_global_stop_reason(
    *,
    policy: ExecutionBudgetPolicy,
    state: ExecutionBudgetState,
) -> ExecutionStopReason | None:
    """Stop every dispatch only for constraints that are globally exhausted."""

    if (
        policy.stop_on_unknown_cost
        and policy.max_amount_microunits is not None
        and not state.cost_complete
    ):
        return ExecutionStopReason.COST_UNKNOWN
    if (
        policy.max_amount_microunits is not None
        and state.amount_microunits is not None
        and state.amount_microunits >= policy.max_amount_microunits
    ):
        return ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED
    if policy.max_elapsed_ms is not None and state.elapsed_ms >= policy.max_elapsed_ms:
        return ExecutionStopReason.DEADLINE_EXCEEDED
    if (
        policy.max_no_progress_streak is not None
        and state.no_progress_streak >= policy.max_no_progress_streak
    ):
        return ExecutionStopReason.NO_PROGRESS
    return None


def _reservation_stop_reason(
    *,
    policy: ExecutionBudgetPolicy,
    projected: ExecutionBudgetState,
) -> ExecutionStopReason | None:
    if (
        policy.stop_on_unknown_cost
        and policy.max_amount_microunits is not None
        and not projected.cost_complete
    ):
        return ExecutionStopReason.COST_UNKNOWN
    if (
        policy.max_amount_microunits is not None
        and projected.amount_microunits is not None
        and projected.amount_microunits > policy.max_amount_microunits
    ):
        return ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED

    checks = (
        (policy.max_requests, projected.requests, ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED),
        (policy.max_sources, projected.sources, ExecutionStopReason.SOURCE_BUDGET_EXHAUSTED),
        (policy.max_elapsed_ms, projected.elapsed_ms, ExecutionStopReason.DEADLINE_EXCEEDED),
        (policy.max_retries, projected.retries, ExecutionStopReason.RETRY_LIMIT_REACHED),
        (policy.max_loops, projected.loops, ExecutionStopReason.LOOP_LIMIT_REACHED),
    )
    for limit, reserved, reason in checks:
        if limit is not None and reserved > limit:
            return reason
    return None


@dataclass(slots=True)
class GovernedExecutionController:
    """Stateful pre-dispatch reservation and post-dispatch accounting guard."""

    policy: ExecutionBudgetPolicy
    state: ExecutionBudgetState = ExecutionBudgetState()
    _reservations: dict[str, ExecutionBudgetReservation] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def authorize_next(self) -> ExecutionBudgetDecision:
        return evaluate_execution_budget(policy=self.policy, state=self.state)

    @property
    def active_reservation_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._reservations))

    def reserve(self, reservation: ExecutionBudgetReservation) -> ExecutionBudgetReservation:
        if reservation.reservation_id in self._reservations:
            raise ValueError("execution reservation id is already active")
        global_reason = _pre_reservation_global_stop_reason(
            policy=self.policy,
            state=self.state,
        )
        if global_reason is not None:
            raise ExecutionReservationRejected(
                ExecutionBudgetDecision(
                    may_continue=False,
                    policy_id=self.policy.policy_id,
                    policy_version=self.policy.version,
                    policy_fingerprint=self.policy.fingerprint,
                    state_fingerprint=self.state.fingerprint,
                    stop_reason=global_reason,
                )
            )

        projected = _reserved_projection(
            self.state,
            (*self._reservations.values(), reservation),
        )
        reason = _reservation_stop_reason(policy=self.policy, projected=projected)
        if reason is not None:
            raise ExecutionReservationRejected(
                ExecutionBudgetDecision(
                    may_continue=False,
                    policy_id=self.policy.policy_id,
                    policy_version=self.policy.version,
                    policy_fingerprint=self.policy.fingerprint,
                    state_fingerprint=self.state.fingerprint,
                    stop_reason=reason,
                )
            )
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def reconcile(
        self,
        reservation_id: str,
        delta: ExecutionBudgetDelta,
    ) -> ExecutionBudgetState:
        if reservation_id not in self._reservations:
            raise ValueError("execution reservation is not active")
        next_state = _accumulate_execution_delta(state=self.state, delta=delta)
        self._reservations.pop(reservation_id)
        self.state = next_state
        return self.state

    def release(self, reservation_id: str) -> None:
        if self._reservations.pop(reservation_id, None) is None:
            raise ValueError("execution reservation is not active")

    def record(self, delta: ExecutionBudgetDelta) -> ExecutionBudgetState:
        self.state = advance_execution_budget(
            policy=self.policy,
            state=self.state,
            delta=delta,
        )
        return self.state
