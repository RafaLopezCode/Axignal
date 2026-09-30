"""Deterministic Research Value Gate for AXIGNAL Prime.

The gate decides whether an explicit knowledge gap deserves research now.
It does not determine truth, source rights, canonical admission, or provider choice.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ResearchValueDisposition(StrEnum):
    RETAIN_UNKNOWN = "RETAIN_UNKNOWN"
    RESEARCH_NOW = "RESEARCH_NOW"
    DEFER = "DEFER"
    BLOCKED_BY_BUDGET_OR_RIGHTS = "BLOCKED_BY_BUDGET_OR_RIGHTS"


class ResearchValueSignal(StrEnum):
    MATERIALITY = "MATERIALITY"
    DECISION_IMPACT = "DECISION_IMPACT"
    REUSE_POTENTIAL = "REUSE_POTENTIAL"
    FRESHNESS_NEED = "FRESHNESS_NEED"


class ResearchValueReason(StrEnum):
    RIGHTS_DENIED = "RIGHTS_DENIED"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    BUDGET_DENIED = "BUDGET_DENIED"
    BUDGET_UNKNOWN = "BUDGET_UNKNOWN"
    NO_PROGRESS = "NO_PROGRESS"
    NO_VALUE_SIGNAL = "NO_VALUE_SIGNAL"
    MATERIALITY = "MATERIALITY"
    DECISION_IMPACT = "DECISION_IMPACT"
    REUSE_POTENTIAL = "REUSE_POTENTIAL"
    FRESHNESS_NEED = "FRESHNESS_NEED"


@dataclass(frozen=True, slots=True)
class ResearchValueContext:
    subject_id: str
    state_fingerprint: str
    dimension_id: str
    missing_requirements: tuple[str, ...]
    value_signals: frozenset[ResearchValueSignal]
    rights_permit: bool
    capability_available: bool
    budget_permits: bool | None
    known_source_available: bool
    no_progress_observed: bool = False

    def __post_init__(self) -> None:
        if any(
            not item.strip()
            for item in (self.subject_id, self.state_fingerprint, self.dimension_id)
        ):
            raise ValueError("research-value context identity is required")
        if not self.missing_requirements:
            raise ValueError("research-value context requires explicit missing state")
        if len(set(self.missing_requirements)) != len(self.missing_requirements):
            raise ValueError("research-value missing requirements must be unique")
        if any(not item.strip() for item in self.missing_requirements):
            raise ValueError("research-value missing requirements cannot be empty")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "subject_id": self.subject_id,
                "state_fingerprint": self.state_fingerprint,
                "dimension_id": self.dimension_id,
                "missing_requirements": self.missing_requirements,
                "value_signals": sorted(signal.value for signal in self.value_signals),
                "rights_permit": self.rights_permit,
                "capability_available": self.capability_available,
                "budget_permits": self.budget_permits,
                "known_source_available": self.known_source_available,
                "no_progress_observed": self.no_progress_observed,
            }
        )


@dataclass(frozen=True, slots=True)
class ResearchValuePolicy:
    policy_id: str
    version: str
    research_signals: frozenset[ResearchValueSignal]
    defer_on_unknown_budget: bool = True
    defer_on_no_progress: bool = True

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("research-value policy identity is required")
        if not self.research_signals:
            raise ValueError("research-value policy requires explicit value signals")


@dataclass(frozen=True, slots=True)
class ResearchValueDecision:
    subject_id: str
    state_fingerprint: str
    dimension_id: str
    missing_requirements: tuple[str, ...]
    disposition: ResearchValueDisposition
    policy_id: str
    policy_version: str
    context_fingerprint: str
    reason_codes: tuple[ResearchValueReason, ...]

    def __post_init__(self) -> None:
        if any(
            not item.strip()
            for item in (
                self.subject_id,
                self.state_fingerprint,
                self.dimension_id,
                self.policy_id,
                self.policy_version,
                self.context_fingerprint,
            )
        ):
            raise ValueError("research-value decision identity is required")
        if not self.missing_requirements:
            raise ValueError("research-value decision requires explicit missing state")
        if not self.reason_codes:
            raise ValueError("research-value decision requires explicit reason codes")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("research-value reason codes must be unique")


def decide_research_value(
    *,
    context: ResearchValueContext,
    policy: ResearchValuePolicy,
) -> ResearchValueDecision:
    """Apply deterministic research-worth policy without producing an opaque score."""

    reasons: tuple[ResearchValueReason, ...]
    if not context.rights_permit:
        disposition = ResearchValueDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS
        reasons = (ResearchValueReason.RIGHTS_DENIED,)
    elif not context.capability_available:
        disposition = ResearchValueDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS
        reasons = (ResearchValueReason.CAPABILITY_UNAVAILABLE,)
    elif context.budget_permits is False:
        disposition = ResearchValueDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS
        reasons = (ResearchValueReason.BUDGET_DENIED,)
    elif context.budget_permits is None and policy.defer_on_unknown_budget:
        disposition = ResearchValueDisposition.DEFER
        reasons = (ResearchValueReason.BUDGET_UNKNOWN,)
    elif context.no_progress_observed and policy.defer_on_no_progress:
        disposition = ResearchValueDisposition.DEFER
        reasons = (ResearchValueReason.NO_PROGRESS,)
    else:
        matched = tuple(
            ResearchValueReason(signal.value)
            for signal in (
                ResearchValueSignal.MATERIALITY,
                ResearchValueSignal.DECISION_IMPACT,
                ResearchValueSignal.REUSE_POTENTIAL,
                ResearchValueSignal.FRESHNESS_NEED,
            )
            if signal in context.value_signals and signal in policy.research_signals
        )
        if matched:
            disposition = ResearchValueDisposition.RESEARCH_NOW
            reasons = matched
        else:
            disposition = ResearchValueDisposition.RETAIN_UNKNOWN
            reasons = (ResearchValueReason.NO_VALUE_SIGNAL,)

    return ResearchValueDecision(
        subject_id=context.subject_id,
        state_fingerprint=context.state_fingerprint,
        dimension_id=context.dimension_id,
        missing_requirements=context.missing_requirements,
        disposition=disposition,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        context_fingerprint=context.fingerprint,
        reason_codes=reasons,
    )
