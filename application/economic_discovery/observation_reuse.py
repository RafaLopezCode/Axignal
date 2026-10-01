"""Deterministic observation reuse gate for FR-24."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationMemory,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from domain.evidence.epistemics import Currentness


class ReuseTargetScope(StrEnum):
    GLOBAL_WORLD = "GLOBAL_WORLD"
    TENANT_PRIVATE = "TENANT_PRIVATE"


class ReusePurpose(StrEnum):
    CURRENT_STATE = "CURRENT_STATE"
    HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"


class ReuseDisposition(StrEnum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"


class ReuseReason(StrEnum):
    ALLOWED = "ALLOWED"
    SUBJECT_MISMATCH = "SUBJECT_MISMATCH"
    RIGHTS_PROHIBITED = "RIGHTS_PROHIBITED"
    RIGHTS_UNKNOWN = "RIGHTS_UNKNOWN"
    INACCESSIBLE = "INACCESSIBLE"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    RESTRICTED_SCOPE = "RESTRICTED_SCOPE"
    PRIVATE_SCOPE_GLOBAL_LEAK = "PRIVATE_SCOPE_GLOBAL_LEAK"
    PRIVATE_SCOPE_MISMATCH = "PRIVATE_SCOPE_MISMATCH"
    SUBJECT_NOT_APPLICABLE = "SUBJECT_NOT_APPLICABLE"
    PURPOSE_NOT_APPLICABLE = "PURPOSE_NOT_APPLICABLE"
    STALE_FOR_CURRENT_USE = "STALE_FOR_CURRENT_USE"
    HISTORICAL_FOR_CURRENT_USE = "HISTORICAL_FOR_CURRENT_USE"
    CURRENTNESS_UNKNOWN = "CURRENTNESS_UNKNOWN"


@dataclass(frozen=True, slots=True)
class ObservationReusePolicy:
    policy_id: str
    version: str

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("observation reuse policy identity is required")


@dataclass(frozen=True, slots=True)
class ObservationReuseContext:
    subject_id: str
    xeed_id: str
    tenant_id: str
    target_scope: ReuseTargetScope
    purpose: ReusePurpose

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.xeed_id.strip() or not self.tenant_id.strip():
            raise ValueError("observation reuse context identity is required")

    @property
    def fingerprint(self) -> str:
        payload = {
            "subject_id": self.subject_id,
            "xeed_id": self.xeed_id,
            "tenant_id": self.tenant_id,
            "target_scope": self.target_scope.value,
            "purpose": self.purpose.value,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ObservationReuseDecision:
    observation_id: str
    disposition: ReuseDisposition
    reason: ReuseReason
    policy_id: str
    policy_version: str
    context_fingerprint: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.observation_id,
                self.policy_id,
                self.policy_version,
                self.context_fingerprint,
            )
        ):
            raise ValueError("observation reuse decision provenance is required")


@dataclass(frozen=True, slots=True)
class ReuseSelection:
    observations: tuple[GovernedObservation, ...]
    decisions: tuple[ObservationReuseDecision, ...]

    @property
    def observation_ids(self) -> frozenset[str]:
        return frozenset(item.record.observation_id for item in self.observations)


class ObservationReuseRejected(ValueError):
    def __init__(self, decision: ObservationReuseDecision) -> None:
        self.decision = decision
        super().__init__(f"{decision.observation_id}:{decision.reason.value}")


def _decision(
    observation: GovernedObservation,
    *,
    disposition: ReuseDisposition,
    reason: ReuseReason,
    context: ObservationReuseContext,
    policy: ObservationReusePolicy,
) -> ObservationReuseDecision:
    return ObservationReuseDecision(
        observation_id=observation.record.observation_id,
        disposition=disposition,
        reason=reason,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        context_fingerprint=context.fingerprint,
    )


def evaluate_observation_reuse(
    observation: GovernedObservation,
    *,
    context: ObservationReuseContext,
    policy: ObservationReusePolicy,
) -> ObservationReuseDecision:
    authority = observation.reuse_authority

    if observation.record.subject_id != context.subject_id:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.SUBJECT_MISMATCH,
            context=context,
            policy=policy,
        )
    if authority.rights_status is ObservationRightsStatus.PROHIBITED:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.RIGHTS_PROHIBITED,
            context=context,
            policy=policy,
        )
    if authority.rights_status is ObservationRightsStatus.UNKNOWN:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.RIGHTS_UNKNOWN,
            context=context,
            policy=policy,
        )
    if authority.access_status is ObservationAccessStatus.INACCESSIBLE:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.INACCESSIBLE,
            context=context,
            policy=policy,
        )
    if authority.provenance_ref is None:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.PROVENANCE_MISSING,
            context=context,
            policy=policy,
        )
    if authority.scope is ObservationReuseScope.RESTRICTED:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.RESTRICTED_SCOPE,
            context=context,
            policy=policy,
        )
    if authority.scope is ObservationReuseScope.TENANT_PRIVATE:
        if context.target_scope is ReuseTargetScope.GLOBAL_WORLD:
            return _decision(
                observation,
                disposition=ReuseDisposition.REJECT,
                reason=ReuseReason.PRIVATE_SCOPE_GLOBAL_LEAK,
                context=context,
                policy=policy,
            )
        if authority.scope_owner_id != context.tenant_id:
            return _decision(
                observation,
                disposition=ReuseDisposition.REJECT,
                reason=ReuseReason.PRIVATE_SCOPE_MISMATCH,
                context=context,
                policy=policy,
            )
    if context.subject_id not in authority.applicable_subject_ids:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.SUBJECT_NOT_APPLICABLE,
            context=context,
            policy=policy,
        )
    if context.purpose.value not in authority.applicable_purposes:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.PURPOSE_NOT_APPLICABLE,
            context=context,
            policy=policy,
        )
    if context.purpose is ReusePurpose.CURRENT_STATE:
        if authority.currentness is Currentness.STALE:
            return _decision(
                observation,
                disposition=ReuseDisposition.REJECT,
                reason=ReuseReason.STALE_FOR_CURRENT_USE,
                context=context,
                policy=policy,
            )
        if authority.currentness is Currentness.HISTORICAL:
            return _decision(
                observation,
                disposition=ReuseDisposition.REJECT,
                reason=ReuseReason.HISTORICAL_FOR_CURRENT_USE,
                context=context,
                policy=policy,
            )
        if authority.currentness is Currentness.UNKNOWN:
            return _decision(
                observation,
                disposition=ReuseDisposition.REJECT,
                reason=ReuseReason.CURRENTNESS_UNKNOWN,
                context=context,
                policy=policy,
            )
    elif authority.currentness is Currentness.UNKNOWN:
        return _decision(
            observation,
            disposition=ReuseDisposition.REJECT,
            reason=ReuseReason.CURRENTNESS_UNKNOWN,
            context=context,
            policy=policy,
        )

    return _decision(
        observation,
        disposition=ReuseDisposition.ALLOW,
        reason=ReuseReason.ALLOWED,
        context=context,
        policy=policy,
    )


def select_reusable_observations(
    memory: ObservationMemory,
    *,
    context: ObservationReuseContext,
    policy: ObservationReusePolicy,
) -> ReuseSelection:
    decisions: list[ObservationReuseDecision] = []
    allowed: list[GovernedObservation] = []
    for observation in memory.for_subject(context.subject_id):
        decision = evaluate_observation_reuse(observation, context=context, policy=policy)
        decisions.append(decision)
        if decision.disposition is ReuseDisposition.ALLOW:
            allowed.append(observation)
    return ReuseSelection(tuple(allowed), tuple(decisions))
