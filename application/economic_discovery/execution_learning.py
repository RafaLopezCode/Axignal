"""Learning Memory bridge for governed execution stops."""

from __future__ import annotations

from datetime import datetime

from application.economic_discovery.execution_budget import (
    ExecutionBudgetDecision,
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
)
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
)


def execution_stop_learning_event(
    *,
    event_id: str,
    occurred_at: datetime,
    subject_id: str,
    activity_ref: str,
    code_sha: str,
    kind: LearningEventKind,
    mechanism: LearningMechanism,
    policy: ExecutionBudgetPolicy,
    state: ExecutionBudgetState,
    decision: ExecutionBudgetDecision,
    xeed_id: str | None = None,
    before_state_fingerprint: str | None = None,
    after_state_fingerprint: str | None = None,
) -> LearningEvent:
    """Record a governed stop as partial operational evidence, never as success."""

    if decision.may_continue or decision.stop_reason is None:
        raise ValueError("execution stop learning event requires a stopped decision")
    if decision.policy_fingerprint != policy.fingerprint:
        raise ValueError("execution stop decision/policy mismatch")
    if decision.state_fingerprint != state.fingerprint:
        raise ValueError("execution stop decision/state mismatch")

    cost = LearningCost(
        amount_microunits=state.amount_microunits,
        currency=state.currency,
        latency_ms=state.elapsed_ms,
    )
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=LearningOutcome.PARTIAL,
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref=activity_ref,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        code_sha=code_sha,
        mechanism=mechanism,
        input_fingerprint=state.fingerprint,
        reason_code=decision.stop_reason.value,
        before_state_fingerprint=before_state_fingerprint,
        after_state_fingerprint=after_state_fingerprint,
        cost=cost,
        yield_=LearningYield(),
    )
