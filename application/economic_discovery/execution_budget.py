"""Provider-neutral execution budget and stop contracts for AXIGNAL.

This module governs whether another unit of research/observation work may start.
It does not choose sources, providers, truth, or canonical writes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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
        and state.amount_microunits is None
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

    if state.amount_microunits is not None and delta.amount_microunits is None:
        next_amount: int | None = None
        next_currency: str | None = None
    elif state.amount_microunits is None and delta.amount_microunits is None:
        next_amount = None
        next_currency = None
    else:
        known_currency = state.currency or delta.currency
        if (
            state.currency is not None
            and delta.currency is not None
            and state.currency != delta.currency
        ):
            raise ValueError("execution delta currency does not match accumulated currency")
        next_amount = (state.amount_microunits or 0) + (delta.amount_microunits or 0)
        next_currency = known_currency

    return ExecutionBudgetState(
        amount_microunits=next_amount,
        currency=next_currency,
        elapsed_ms=state.elapsed_ms + delta.elapsed_ms,
        requests=state.requests + delta.requests,
        sources=state.sources + delta.sources,
        retries=state.retries + delta.retries,
        loops=state.loops + delta.loops,
        no_progress_streak=0 if delta.made_progress else state.no_progress_streak + 1,
    )


@dataclass(slots=True)
class GovernedExecutionController:
    """Small stateful guard used by executors to prevent unbounded work."""

    policy: ExecutionBudgetPolicy
    state: ExecutionBudgetState = ExecutionBudgetState()

    def authorize_next(self) -> ExecutionBudgetDecision:
        return evaluate_execution_budget(policy=self.policy, state=self.state)

    def record(self, delta: ExecutionBudgetDelta) -> ExecutionBudgetState:
        self.state = advance_execution_budget(
            policy=self.policy,
            state=self.state,
            delta=delta,
        )
        return self.state
