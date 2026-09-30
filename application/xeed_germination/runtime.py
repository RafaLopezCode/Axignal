"""First-Xeed runtime lifecycle composed from existing governed outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.learning_memory import (
    LearningMemory,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.prime_execution import PrimeExecutionTrace
from application.subscriber_projection.xignal import ExplainableXignalProjection
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from application.xeed_germination.bootstrap import BootstrapDisposition, BootstrapPlan
from application.xeed_germination.learning import bootstrap_learning_event
from domain.xeed.germination import XeedGerminationState, XeedGerminationStatus


@dataclass(frozen=True, slots=True)
class FirstXeedReadinessDecision:
    xeed_id: str
    first_xignal_id: str
    observation_depth: int
    lifecycle_revision: int
    ready: bool
    policy_id: str
    policy_version: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.xeed_id,
                self.first_xignal_id,
                self.policy_id,
                self.policy_version,
            )
        ):
            raise ValueError("first-Xeed readiness decision identity is required")
        if self.observation_depth < 0 or self.lifecycle_revision < 0:
            raise ValueError("first-Xeed readiness decision counters cannot be negative")
        if not self.reason_codes:
            raise ValueError("first-Xeed readiness decision requires reasons")


def _require_context(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
) -> None:
    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("first-Xeed runtime requires AuthorizedXeedOrganization")
    if state.xeed_id != seed.authorized_xeed.xeed.id:
        raise ValueError("Xeed runtime state does not match authorized Xeed")


def plant_xeed_runtime(
    *,
    seed: AuthorizedXeedOrganization,
    initiated_by: str,
    created_at: datetime,
) -> XeedGerminationState:
    """Create runtime lifecycle state only for an already-authorized planted Xeed."""

    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("first-Xeed runtime requires AuthorizedXeedOrganization")
    return XeedGerminationState(
        xeed_id=seed.authorized_xeed.xeed.id,
        initiated_by=initiated_by,
        created_at=created_at,
    )


def begin_resolution(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    occurred_at: datetime,
) -> None:
    _require_context(seed=seed, state=state)
    state.transition(
        XeedGerminationStatus.RESOLVING,
        occurred_at=occurred_at,
        reason_code="AUTHORIZED_XEED_RESOLUTION_STARTED",
    )


def apply_bootstrap_plan(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    plan: BootstrapPlan,
    occurred_at: datetime,
    learning_memory: LearningMemory,
    execution_id: str,
    code_sha: str,
) -> None:
    """Map governed bootstrap outcome to lifecycle without inventing readiness."""

    _require_context(seed=seed, state=state)
    if not execution_id.strip():
        raise ValueError("bootstrap execution identity is required")
    if not code_sha.strip():
        raise ValueError("bootstrap code SHA is required")
    if plan.xeed_id != state.xeed_id or plan.subject_id != seed.organization.id:
        raise ValueError("bootstrap plan does not match first-Xeed runtime context")
    if state.status is not XeedGerminationStatus.RESOLVING:
        raise ValueError("bootstrap outcome requires RESOLVING lifecycle state")

    if plan.disposition is BootstrapDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS:
        target = XeedGerminationStatus.BLOCKED
        reason = "BOOTSTRAP_BLOCKED_BY_BUDGET_OR_RIGHTS"
    elif plan.disposition in {
        BootstrapDisposition.RETAIN_UNKNOWN,
        BootstrapDisposition.DEFER,
    }:
        target = XeedGerminationStatus.INSUFFICIENT_EVIDENCE
        reason = f"BOOTSTRAP_{plan.disposition.value}"
    else:
        target = XeedGerminationStatus.OBSERVING
        reason = f"BOOTSTRAP_{plan.disposition.value}"

    state.transition(target, occurred_at=occurred_at, reason_code=reason)

    outcome = (
        LearningOutcome.PARTIAL
        if plan.disposition
        in {
            BootstrapDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS,
            BootstrapDisposition.RETAIN_UNKNOWN,
            BootstrapDisposition.DEFER,
        }
        else LearningOutcome.COMPLETED
    )
    event = bootstrap_learning_event(
        event_id=(
            f"learn:{execution_id}:00-bootstrap:{state.xeed_id}:{plan.plan_fingerprint[:16]}"
        ),
        plan=plan,
        occurred_at=occurred_at,
        code_sha=code_sha,
        outcome=outcome,
        after_state_fingerprint=plan.state_fingerprint,
        reason_code=reason,
        yield_=LearningYield(observations_reused=plan.reused_observation_count),
        output_fingerprint=plan.plan_fingerprint,
        replay=LearningReplayReference.non_replayable(
            "BOOTSTRAP_PLAN_PAYLOAD_NOT_RETAINED",
            code_sha=code_sha,
            plan_fingerprint=plan.plan_fingerprint,
            policy_id=plan.policy_id,
            policy_version=plan.policy_version,
            state_fingerprint=plan.state_fingerprint,
        ),
    )
    learning_memory.append(event)


def apply_prime_trace(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    trace: PrimeExecutionTrace,
    occurred_at: datetime,
) -> None:
    """Record real observation progress from Prime without claiming a Xignal exists."""

    _require_context(seed=seed, state=state)
    if trace.xeed_id != state.xeed_id or trace.subject_id != seed.organization.id:
        raise ValueError("Prime trace does not match first-Xeed runtime context")
    if state.status not in {
        XeedGerminationStatus.OBSERVING,
        XeedGerminationStatus.PARTIAL_READY,
        XeedGerminationStatus.LIVE,
    }:
        raise ValueError("Prime trace requires an observing/partial/live Xeed")

    state.note_observation(observed_at=occurred_at)
    if state.status is XeedGerminationStatus.LIVE:
        return

    reason = (
        f"PRIME_PARTIAL_STOP:{trace.budget_stop_reason}"
        if trace.budget_stop_reason is not None
        else "PRIME_OBSERVATION_AVAILABLE_NO_XIGNAL_YET"
    )
    if state.status is XeedGerminationStatus.OBSERVING:
        state.transition(
            XeedGerminationStatus.PARTIAL_READY,
            occurred_at=occurred_at,
            reason_code=reason,
        )


def apply_first_xignal(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    projection: ExplainableXignalProjection,
    occurred_at: datetime,
) -> None:
    """Advance only when a real explainable Xignal has been produced."""

    _require_context(seed=seed, state=state)
    xignal = projection.xignal
    if xignal.xeed_id != state.xeed_id or xignal.subject_id != seed.organization.id:
        raise ValueError("Xignal projection does not match first-Xeed runtime context")
    if state.status not in {
        XeedGerminationStatus.OBSERVING,
        XeedGerminationStatus.PARTIAL_READY,
        XeedGerminationStatus.FIRST_XIGNAL_READY,
    }:
        raise ValueError("first Xignal requires observing or partial lifecycle state")

    state.note_first_xignal(xignal.xignal_id)
    if state.status is not XeedGerminationStatus.FIRST_XIGNAL_READY:
        state.transition(
            XeedGerminationStatus.FIRST_XIGNAL_READY,
            occurred_at=occurred_at,
            reason_code="FIRST_EXPLAINABLE_XIGNAL_AVAILABLE",
        )


def apply_readiness_decision(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    decision: FirstXeedReadinessDecision,
    occurred_at: datetime,
) -> None:
    """Transition FIRST_XIGNAL_READY to LIVE only through explicit readiness."""

    _require_context(seed=seed, state=state)
    if state.status not in {
        XeedGerminationStatus.FIRST_XIGNAL_READY,
        XeedGerminationStatus.PARTIAL_READY,
    }:
        raise ValueError("LIVE readiness requires first-Xignal or partial-ready state")
    if state.first_xignal_id is None:
        raise ValueError("LIVE readiness cannot proceed without a recorded first Xignal")
    if (
        decision.xeed_id != state.xeed_id
        or decision.first_xignal_id != state.first_xignal_id
        or decision.observation_depth != state.observation_depth
        or decision.lifecycle_revision != len(state.transitions)
    ):
        raise ValueError("readiness decision does not match current Xeed lifecycle state")

    if decision.ready:
        if state.status is XeedGerminationStatus.PARTIAL_READY:
            state.transition(
                XeedGerminationStatus.FIRST_XIGNAL_READY,
                occurred_at=occurred_at,
                reason_code="FIRST_XIGNAL_ALREADY_AVAILABLE_FOR_READINESS",
            )
        state.transition(
            XeedGerminationStatus.LIVE,
            occurred_at=occurred_at,
            reason_code=f"READINESS:{decision.policy_id}:{decision.policy_version}",
        )
        return

    if state.status is XeedGerminationStatus.FIRST_XIGNAL_READY:
        state.transition(
            XeedGerminationStatus.PARTIAL_READY,
            occurred_at=occurred_at,
            reason_code="READINESS_NOT_YET_SATISFIED:" + ",".join(decision.reason_codes),
        )


def mark_runtime_failed(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    occurred_at: datetime,
    reason_code: str,
) -> None:
    _require_context(seed=seed, state=state)
    state.transition(
        XeedGerminationStatus.FAILED,
        occurred_at=occurred_at,
        reason_code=reason_code,
    )


def mark_runtime_blocked(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    occurred_at: datetime,
    reason_code: str,
) -> None:
    _require_context(seed=seed, state=state)
    state.transition(
        XeedGerminationStatus.BLOCKED,
        occurred_at=occurred_at,
        reason_code=reason_code,
    )
