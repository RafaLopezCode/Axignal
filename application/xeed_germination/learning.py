"""Learning-Memory bridge for completed Xeed bootstrap attempts."""

from __future__ import annotations

from datetime import datetime

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.xeed_germination.bootstrap import BootstrapDisposition, BootstrapPlan


def bootstrap_learning_event(
    *,
    event_id: str,
    plan: BootstrapPlan,
    occurred_at: datetime,
    code_sha: str,
    outcome: LearningOutcome,
    after_state_fingerprint: str,
    reason_code: str,
    cost: LearningCost | None = None,
    yield_: LearningYield | None = None,
    output_fingerprint: str | None = None,
    replay: LearningReplayReference | None = None,
) -> LearningEvent:
    """Record observed bootstrap outcome without changing bootstrap policy."""

    if cost is None:
        cost = LearningCost()
    if yield_ is None:
        yield_ = LearningYield()

    if plan.disposition is BootstrapDisposition.ADAPTIVE_RESEARCH:
        mechanism = LearningMechanism.ADAPTIVE_RESEARCH
    else:
        mechanism = LearningMechanism.DETERMINISTIC

    return LearningEvent(
        event_id=event_id,
        kind=LearningEventKind.BOOTSTRAP,
        outcome=outcome,
        occurred_at=occurred_at,
        subject_id=plan.subject_id,
        xeed_id=plan.xeed_id,
        activity_ref=plan.plan_fingerprint,
        policy_id=plan.policy_id,
        policy_version=plan.policy_version,
        code_sha=code_sha,
        mechanism=mechanism,
        input_fingerprint=plan.plan_fingerprint,
        output_fingerprint=output_fingerprint,
        reason_code=reason_code,
        before_state_fingerprint=plan.state_fingerprint,
        after_state_fingerprint=after_state_fingerprint,
        replay=(
            LearningReplayReference.non_replayable("BOOTSTRAP_PLAN_PAYLOAD_NOT_RETAINED")
            if replay is None
            else replay
        ),
        cost=cost,
        yield_=yield_,
    )
