"""Persistent daily observation budget: checked before every acquisition.

Global limits stop the tick. Scoped limits (one Xeed, one family, one source,
depth) only skip the lead that would exceed them. A conservative reservation is persisted before dispatch. A received acquisition
settles it to actual consumption; an interrupted one remains UNKNOWN and cannot
be dispatched again that day. Counters include unsettled reservations, not a
claim that their worst-case cost was actually spent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from application.observation_runtime.families import FamilyObservationPolicy, ObservationFamily

BUDGET_POLICY_VERSION = "aor-daily-budget-2026-10-10.2"


class BudgetScope(StrEnum):
    GLOBAL = "GLOBAL"
    XEED = "XEED"
    FAMILY = "FAMILY"
    SOURCE = "SOURCE"
    DEPTH = "DEPTH"


@dataclass(frozen=True, slots=True)
class BudgetDenial:
    scope: BudgetScope
    limit: str
    detail: str

    @property
    def stops_tick(self) -> bool:
        return self.scope is BudgetScope.GLOBAL

    def __str__(self) -> str:
        return f"{self.scope.value}:{self.limit}:{self.detail}"


@dataclass(frozen=True, slots=True)
class DailyObservationBudget:
    """Safe defaults; deployments set their own limits, the runtime never invents them."""

    policy_id: str = "aor-daily-budget"
    version: str = BUDGET_POLICY_VERSION
    max_runs_per_xeed: int = 12
    max_http_requests: int = 60
    max_paid_cost_microunits: int = 0
    max_runtime_seconds: float = 900.0
    max_actions: int = 40
    max_follow_up_depth: int = 3
    max_source_failures: int = 3
    source_request_caps: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if min(self.max_runs_per_xeed, self.max_http_requests, self.max_actions) < 0:
            raise ValueError("daily budget limits cannot be negative")
        if min(self.max_paid_cost_microunits, self.max_follow_up_depth) < 0:
            raise ValueError("daily budget limits cannot be negative")
        if self.max_runtime_seconds < 0 or self.max_source_failures < 1:
            raise ValueError("daily budget limits are invalid")

    def source_cap(self, source_id: str) -> int | None:
        return dict(self.source_request_caps).get(source_id)


@dataclass
class BudgetUsage:
    """What one day has consumed so far; operational state, never truth."""

    day: str
    requests: int = 0
    paid_cost_microunits: int = 0
    actions: int = 0
    runtime_seconds: float = 0.0
    xeed_actions: dict[str, int] = field(default_factory=dict)
    family_actions: dict[str, int] = field(default_factory=dict)
    family_requests: dict[str, int] = field(default_factory=dict)
    source_requests: dict[str, int] = field(default_factory=dict)
    source_failures: dict[str, int] = field(default_factory=dict)
    pending_acquisitions: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "day": self.day,
            "requests": self.requests,
            "paid_cost_microunits": self.paid_cost_microunits,
            "actions": self.actions,
            "runtime_seconds": self.runtime_seconds,
            "xeed_actions": dict(sorted(self.xeed_actions.items())),
            "family_actions": dict(sorted(self.family_actions.items())),
            "family_requests": dict(sorted(self.family_requests.items())),
            "source_requests": dict(sorted(self.source_requests.items())),
            "source_failures": dict(sorted(self.source_failures.items())),
            "pending_acquisitions": {
                key: dict(value) for key, value in sorted(self.pending_acquisitions.items())
            },
        }

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> BudgetUsage:
        def counts(key: str) -> dict[str, int]:
            raw = payload.get(key, {})
            if not isinstance(raw, dict):
                raise ValueError(f"budget usage {key} must be a mapping")
            return {str(k): int(v) for k, v in raw.items()}

        raw_pending = payload.get("pending_acquisitions", {})
        if not isinstance(raw_pending, dict):
            raise ValueError("pending acquisitions must be a mapping")
        pending: dict[str, dict[str, int]] = {}
        for key, value in raw_pending.items():
            if (
                not isinstance(value, dict)
                or set(value) != {"requests", "paid_cost_microunits"}
                or any(type(v) is not int or v < 0 for v in value.values())
            ):
                raise ValueError("pending acquisition bounds must be non-negative integers")
            pending[str(key)] = dict(value)
        requests, cost, actions = (
            payload[k] for k in ("requests", "paid_cost_microunits", "actions")
        )
        runtime = payload["runtime_seconds"]
        if not all(isinstance(v, int) for v in (requests, cost, actions)):
            raise ValueError("budget usage counters must be integers")
        if not isinstance(runtime, int | float):
            raise ValueError("budget runtime must be numeric")
        assert isinstance(requests, int) and isinstance(cost, int) and isinstance(actions, int)
        return cls(
            day=str(payload["day"]),
            requests=requests,
            paid_cost_microunits=cost,
            actions=actions,
            runtime_seconds=float(runtime),
            xeed_actions=counts("xeed_actions"),
            family_actions=counts("family_actions"),
            family_requests=counts("family_requests"),
            source_requests=counts("source_requests"),
            source_failures=counts("source_failures"),
            pending_acquisitions=pending,
        )


def global_denial(
    budget: DailyObservationBudget, usage: BudgetUsage, *, elapsed_seconds: float
) -> BudgetDenial | None:
    """A limit that ends the whole tick, whatever lead would run next."""

    if usage.actions >= budget.max_actions:
        return BudgetDenial(BudgetScope.GLOBAL, "max_actions", f"{usage.actions}")
    if usage.requests >= budget.max_http_requests:
        return BudgetDenial(BudgetScope.GLOBAL, "max_http_requests", f"{usage.requests}")
    if usage.runtime_seconds + elapsed_seconds >= budget.max_runtime_seconds:
        return BudgetDenial(
            BudgetScope.GLOBAL,
            "max_runtime_seconds",
            f"{usage.runtime_seconds + elapsed_seconds:.1f}",
        )
    return None


def reserve(
    budget: DailyObservationBudget,
    usage: BudgetUsage,
    *,
    xeed_id: str,
    family: FamilyObservationPolicy,
    source_id: str,
    depth: int,
    requests: int,
    cost_per_request_microunits: int,
    elapsed_seconds: float,
) -> BudgetDenial | None:
    """Can this acquisition start without breaking any limit? Checked before spending."""

    stop = global_denial(budget, usage, elapsed_seconds=elapsed_seconds)
    if stop is not None:
        return stop
    if usage.requests + requests > budget.max_http_requests:
        return BudgetDenial(BudgetScope.GLOBAL, "max_http_requests", f"{usage.requests}+{requests}")
    cost = cost_per_request_microunits * requests
    if cost and usage.paid_cost_microunits + cost > budget.max_paid_cost_microunits:
        return BudgetDenial(
            BudgetScope.SOURCE,
            "max_paid_cost_microunits",
            f"{source_id}:{usage.paid_cost_microunits}+{cost}",
        )
    if depth > budget.max_follow_up_depth:
        return BudgetDenial(BudgetScope.DEPTH, "max_follow_up_depth", f"{depth}")
    if usage.xeed_actions.get(xeed_id, 0) >= budget.max_runs_per_xeed:
        return BudgetDenial(BudgetScope.XEED, "max_runs_per_xeed", xeed_id)
    name = family.family.value
    if usage.family_actions.get(name, 0) >= family.max_actions_per_tick:
        return BudgetDenial(BudgetScope.FAMILY, "max_actions_per_tick", name)
    if usage.family_requests.get(name, 0) + requests > family.max_requests_per_tick:
        return BudgetDenial(BudgetScope.FAMILY, "max_requests_per_tick", name)
    if usage.source_failures.get(source_id, 0) >= budget.max_source_failures:
        return BudgetDenial(BudgetScope.SOURCE, "max_source_failures", source_id)
    cap = budget.source_cap(source_id)
    if cap is not None and usage.source_requests.get(source_id, 0) + requests > cap:
        return BudgetDenial(BudgetScope.SOURCE, "source_request_cap", source_id)
    return None


def charge(
    usage: BudgetUsage,
    *,
    xeed_id: str,
    family: ObservationFamily,
    source_id: str,
    requests: int,
    paid_cost_microunits: int,
    failed: bool,
) -> None:
    usage.actions += 1
    usage.requests += requests
    usage.paid_cost_microunits += paid_cost_microunits
    usage.xeed_actions[xeed_id] = usage.xeed_actions.get(xeed_id, 0) + 1
    usage.family_actions[family.value] = usage.family_actions.get(family.value, 0) + 1
    usage.family_requests[family.value] = usage.family_requests.get(family.value, 0) + requests
    usage.source_requests[source_id] = usage.source_requests.get(source_id, 0) + requests
    if failed:
        usage.source_failures[source_id] = usage.source_failures.get(source_id, 0) + 1


def settle_acquisition(
    usage: BudgetUsage,
    *,
    acquisition_key: str,
    family: ObservationFamily,
    source_id: str,
    requests: int,
    paid_cost_microunits: int,
    failed: bool,
) -> None:
    """Settle a reservation only after a bounded result has actually arrived."""
    reserved = usage.pending_acquisitions[acquisition_key]
    if not 0 <= requests <= reserved["requests"]:
        raise RuntimeError(f"{source_id} exceeded its request allowance")
    if not 0 <= paid_cost_microunits <= reserved["paid_cost_microunits"]:
        raise RuntimeError(f"{source_id} exceeded its registered cost bound")
    unused = reserved["requests"] - requests
    usage.requests -= unused
    usage.paid_cost_microunits -= reserved["paid_cost_microunits"] - paid_cost_microunits
    usage.family_requests[family.value] -= unused
    usage.source_requests[source_id] -= unused
    if failed:
        usage.source_failures[source_id] = usage.source_failures.get(source_id, 0) + 1
    del usage.pending_acquisitions[acquisition_key]
