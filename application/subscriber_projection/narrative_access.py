"""Tenant/reuse authorization boundary for evidence narrative presentation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessMetadata,
    ObservationReuseScope,
)
from application.economic_discovery.observation_reuse import (
    ObservationReuseContext,
    ObservationReuseDecision,
    ObservationReusePolicy,
    ReuseDisposition,
    ReusePurpose,
    ReuseTargetScope,
    evaluate_observation_reuse_metadata,
)


class NarrativeObservationMemory(Protocol):
    def access_metadata(
        self,
        subject_id: str,
        observation_id: str,
    ) -> ObservationAccessMetadata | None: ...

    def get_observation(
        self,
        subject_id: str,
        observation_id: str,
    ) -> GovernedObservation | None: ...


class NarrativeEvidenceScope(StrEnum):
    GLOBAL_PUBLIC = "GLOBAL_PUBLIC"
    TENANT_PRIVATE = "TENANT_PRIVATE"


@dataclass(frozen=True, slots=True)
class NarrativeAccessContext:
    subject_id: str
    xeed_id: str
    tenant_id: str
    target_scope: ReuseTargetScope
    purpose: ReusePurpose
    as_of: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.subject_id, "subject_id"),
            (self.xeed_id, "xeed_id"),
            (self.tenant_id, "tenant_id"),
        ):
            if not value.strip():
                raise ValueError(f"narrative access requires {name}")
        if self.as_of.tzinfo is None:
            raise ValueError("narrative access as_of must be timezone-aware")

    @property
    def reuse_context(self) -> ObservationReuseContext:
        return ObservationReuseContext(
            subject_id=self.subject_id,
            xeed_id=self.xeed_id,
            tenant_id=self.tenant_id,
            target_scope=self.target_scope,
            purpose=self.purpose,
        )


@dataclass(frozen=True, slots=True)
class AuthorizedNarrativeObservation:
    decision: ObservationReuseDecision
    evidence_scope: NarrativeEvidenceScope


class NarrativeObservationAuthorizationError(ValueError):
    def __init__(self, decision: ObservationReuseDecision) -> None:
        self.decision = decision
        super().__init__(f"narrative observation access rejected:{decision.reason.value}")


def authorize_narrative_observation(
    metadata: ObservationAccessMetadata,
    *,
    context: NarrativeAccessContext,
    policy: ObservationReusePolicy,
) -> AuthorizedNarrativeObservation:
    decision = evaluate_observation_reuse_metadata(
        metadata,
        context=context.reuse_context,
        policy=policy,
    )
    if decision.disposition is not ReuseDisposition.ALLOW:
        raise NarrativeObservationAuthorizationError(decision)

    if metadata.reuse_authority.scope is ObservationReuseScope.TENANT_PRIVATE:
        evidence_scope = NarrativeEvidenceScope.TENANT_PRIVATE
    elif metadata.reuse_authority.scope is ObservationReuseScope.GLOBAL_PUBLIC:
        evidence_scope = NarrativeEvidenceScope.GLOBAL_PUBLIC
    else:
        raise NarrativeObservationAuthorizationError(decision)

    return AuthorizedNarrativeObservation(
        decision=decision,
        evidence_scope=evidence_scope,
    )
