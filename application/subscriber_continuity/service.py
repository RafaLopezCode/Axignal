"""Subscriber Brain continuity: checkpoints, declared-dependency invalidation, delta.

Authorities are reused, not duplicated:

* temporal authority — Observation Memory (EB-06) through ``evaluate_dependencies``;
* recomputation — the T12 runtime's persisted owed work and its ``RecomputationPort``;
  this service only *owes* work (``RecomputeOwedPort``), it never schedules or runs it;
* shared work — EB-07 completes work into global Observation Memory; ``subject_changed``
  fans out to dependent Foci through an index, never a scan of every Focus.

Checkpoints and invalidations are append-only. A Tenant reads only its own Focus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from application.subscriber_continuity.delta import invalidation_delta, state_delta
from application.subscriber_continuity.dependencies import (
    DependencyEvaluation,
    evaluate_dependencies,
)
from application.subscriber_continuity.derive import derive_continuity_state
from application.subscriber_continuity.model import (
    ContinuityCheckpoint,
    ContinuityState,
    InvalidationAction,
)
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId


class ContinuityStore(Protocol):
    def append(
        self, tenant_id: str, xeed_id: str, state: ContinuityState
    ) -> tuple[ContinuityCheckpoint, bool]:
        """Append unless the latest checkpoint already has the same meaning."""

    def latest(
        self, tenant_id: str, xeed_id: str, *, as_of: datetime | None = None
    ) -> ContinuityCheckpoint | None: ...

    def get(
        self, tenant_id: str, xeed_id: str, checkpoint_id: str
    ) -> ContinuityCheckpoint | None: ...

    def history(self, tenant_id: str, xeed_id: str) -> tuple[ContinuityCheckpoint, ...]: ...

    def dependents(self, subject_id: str) -> tuple[tuple[str, str], ...]: ...

    def record_invalidations(
        self,
        checkpoint: ContinuityCheckpoint,
        evaluations: tuple[DependencyEvaluation, ...],
        *,
        evaluated_at: datetime,
    ) -> int: ...

    def invalidations(
        self, tenant_id: str, xeed_id: str, checkpoint_id: str
    ) -> tuple[dict[str, str], ...]: ...

    def owe(
        self,
        checkpoint: ContinuityCheckpoint,
        family: str,
        dependency_keys: tuple[str, ...],
        *,
        owed_at: datetime,
    ) -> bool: ...

    def undelivered(
        self, tenant_id: str, xeed_id: str
    ) -> tuple[tuple[str, str, tuple[str, ...]], ...]: ...

    def mark_delivered(
        self, tenant_id: str, xeed_id: str, checkpoint_id: str, family: str, *, at: datetime
    ) -> None: ...

    def recompute_ledger(self, tenant_id: str, xeed_id: str) -> tuple[dict[str, object], ...]: ...


class RecomputeOwedPort(Protocol):
    """The T12 runtime's owed-work queue. False means a live tick holds it; retry later."""

    def owe_recompute(
        self, *, xeed_id: str, family: str, evidence_keys: tuple[str, ...], now: datetime
    ) -> bool: ...


class BrainRuntime(Protocol):
    """The parts of ``SubscriberEconomicRuntime`` continuity relies on."""

    observation_memory: Any
    output_store: Any
    opportunity_store: Any
    reuse_policy: Any
    temporal_policy: Any

    def authorize(self, authorized_context: TrustedRequestContext, xeed_id: XeedId) -> Any: ...

    def read(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, as_of: datetime
    ) -> Any: ...

    def deliver_content(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        projection: dict[str, object],
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class ReconcileReport:
    tenant_id: str
    xeed_id: str
    checkpoint_id: str | None
    statuses: dict[str, str] = field(default_factory=dict)
    new_invalidations: int = 0
    owed: tuple[str, ...] = ()
    delivered: tuple[str, ...] = ()

    def to_wire(self) -> dict[str, object]:
        return {
            "checkpointId": self.checkpoint_id,
            "statuses": self.statuses,
            "newInvalidations": self.new_invalidations,
            "owedFamilies": list(self.owed),
            "deliveredFamilies": list(self.delivered),
        }


@dataclass(slots=True)
class ContinuityService:
    runtime: BrainRuntime
    store: ContinuityStore

    def record(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, *, as_of: datetime
    ) -> tuple[ContinuityCheckpoint, bool]:
        """Checkpoint what the Brain holds for this Focus at ``as_of`` (authorized read)."""

        read = self.runtime.read(authorized_context, xeed_id, as_of)
        authorized = self.runtime.authorize(authorized_context, xeed_id)
        xeed = authorized.authorized_xeed.xeed
        organization = authorized.organization
        scope = {
            "tenant_id": xeed.tenant_id,
            "xeed_id": xeed.id,
            "organization_id": organization.id,
            "as_of": as_of,
        }
        output = self.runtime.output_store.latest(**scope)
        opportunities = self.runtime.opportunity_store.latest(**scope)
        refs = tuple(
            ref
            for ref in (
                None if output is None else output.output_id,
                None if opportunities is None else opportunities.projection_id,
            )
            if ref is not None
        )
        trace = None if output is None else output.runtime_signal.get("executionTrace")
        state = derive_continuity_state(
            read.projection,
            organization_id=organization.id,
            snapshot_refs=refs,
            execution_trace=trace if isinstance(trace, dict) else None,
            memory=self.runtime.observation_memory,
            temporal_cut=as_of,
        )
        return self.store.append(xeed.tenant_id, xeed.id, state)

    def reconcile(
        self,
        tenant_id: str,
        xeed_id: str,
        *,
        now: datetime,
        owe: RecomputeOwedPort | None = None,
    ) -> ReconcileReport:
        """Evaluate the latest checkpoint's declared dependencies; owe only what moved."""

        latest = self.store.latest(tenant_id, xeed_id)
        if latest is None:
            return ReconcileReport(tenant_id, xeed_id, None)
        evaluations = evaluate_dependencies(
            latest.state.dependencies,
            memory=self.runtime.observation_memory,
            tenant_id=tenant_id,
            xeed_id=xeed_id,
            as_of=now,
            reuse_policy=self.runtime.reuse_policy,
            temporal_policy=self.runtime.temporal_policy,
        )
        moved = tuple(
            item for item in evaluations.values() if item.action is not InvalidationAction.NONE
        )
        new = self.store.record_invalidations(latest, moved, evaluated_at=now)
        owed: dict[str, set[str]] = {}
        for item in latest.state.items:
            keys = {
                key
                for key in item.dependency_keys
                if key in evaluations and evaluations[key].action is InvalidationAction.RECOMPUTE
            }
            if keys and item.family is not None:
                owed.setdefault(item.family, set()).update(keys)
        for family, family_keys in sorted(owed.items()):
            self.store.owe(latest, family, tuple(sorted(family_keys)), owed_at=now)
        delivered: list[str] = []
        if owe is not None:
            for checkpoint_id, family, owed_keys in self.store.undelivered(tenant_id, xeed_id):
                if checkpoint_id != latest.checkpoint_id:
                    continue  # superseded: the newer checkpoint carries its own debt
                if owe.owe_recompute(
                    xeed_id=xeed_id, family=family, evidence_keys=owed_keys, now=now
                ):
                    self.store.mark_delivered(tenant_id, xeed_id, checkpoint_id, family, at=now)
                    delivered.append(family)
        return ReconcileReport(
            tenant_id,
            xeed_id,
            latest.checkpoint_id,
            {key: item.status.value for key, item in sorted(evaluations.items())},
            new,
            tuple(sorted(owed)),
            tuple(delivered),
        )

    def subject_changed(
        self, subject_id: str, *, now: datetime, owe: RecomputeOwedPort | None = None
    ) -> tuple[ReconcileReport, ...]:
        """Fan out to Foci whose latest checkpoint depends on this subject (indexed)."""

        return tuple(
            self.reconcile(tenant_id, xeed_id, now=now, owe=owe)
            for tenant_id, xeed_id in self.store.dependents(subject_id)
        )

    def read(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, *, as_of: datetime
    ) -> dict[str, object]:
        """This Focus's continuity only: origin, checkpoint, delta, invalidation, debt."""

        authorized = self.runtime.authorize(authorized_context, xeed_id)
        xeed = authorized.authorized_xeed.xeed
        latest = self.store.latest(xeed.tenant_id, xeed.id, as_of=as_of)
        if latest is None:
            return {"state": "NO_CHECKPOINT", "xeedId": xeed.id}
        previous = (
            None
            if latest.origin.previous_checkpoint_id is None
            else self.store.get(xeed.tenant_id, xeed.id, latest.origin.previous_checkpoint_id)
        )
        evaluations = evaluate_dependencies(
            latest.state.dependencies,
            memory=self.runtime.observation_memory,
            tenant_id=xeed.tenant_id,
            xeed_id=xeed.id,
            as_of=as_of,
            reuse_policy=self.runtime.reuse_policy,
            temporal_policy=self.runtime.temporal_policy,
        )
        pending = invalidation_delta(latest.state, evaluations)
        view: dict[str, object] = {
            "state": "CHECKPOINTED",
            "xeedId": xeed.id,
            "checkpoint": latest.summary(),
            "deltaFromPrevious": state_delta(
                None if previous is None else previous.state, latest.state
            ).to_wire(),
            "currentSupport": {
                "asOf": as_of.isoformat(),
                "isCurrent": not pending.changed,
                "delta": pending.to_wire(),
                "dependencies": {
                    key: {"status": item.status.value, "reason": item.reason}
                    for key, item in sorted(evaluations.items())
                },
            },
            "invalidations": list(
                self.store.invalidations(xeed.tenant_id, xeed.id, latest.checkpoint_id)
            ),
            "recompute": list(self.store.recompute_ledger(xeed.tenant_id, xeed.id)),
        }

        # Old checkpoints can contain source copies in dependency fields/questions.
        # Feed lineage to the same authorized runtime boundary; never expose the
        # historical dependency material or mutate the immutable checkpoint.
        delivered = self.runtime.deliver_content(
            authorized_context,
            xeed_id,
            {
                "continuity": view,
                "evidenceDependencies": [
                    {
                        "observationId": dependency.key.removeprefix("obs:"),
                        "source_ref": dependency.source_ref,
                        "observed_at": dependency.observed_at.isoformat(),
                        "fields": [
                            {"name": name, "value": value} for name, value, _ in dependency.fields
                        ],
                    }
                    for dependency in latest.state.dependencies
                    if dependency.key.startswith("obs:")
                ],
            },
        )
        continuity = delivered["continuity"]
        assert isinstance(continuity, dict)
        return continuity
