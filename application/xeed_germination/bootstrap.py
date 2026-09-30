"""Temporal Xeed bootstrap controller that hands off to AXIGNAL Prime quickly.

Bootstrap is deliberately short-lived: reuse governed memory, acquire only explicit
known sources when they can satisfy declared minimum state, otherwise request adaptive
research. Once minimum state exists, Prime owns all subsequent cognitive routing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery import (
    DimensionRoutingPolicy,
    PrimeControlPlan,
    TypingDimensionContract,
    build_prime_control_plan,
)
from application.economic_discovery.brain_contracts import StateChange
from application.source_representation import RichSubjectState, compile_rich_subject_state
from application.xeed_access.organization_reader import AuthorizedXeedOrganization


class BootstrapDisposition(StrEnum):
    ACQUIRE_KNOWN_SOURCES = "ACQUIRE_KNOWN_SOURCES"
    HANDOFF_TO_PRIME = "HANDOFF_TO_PRIME"
    ADAPTIVE_RESEARCH = "ADAPTIVE_RESEARCH"


@dataclass(frozen=True, slots=True)
class BootstrapPolicy:
    policy_id: str
    version: str
    initial_state_requirements: tuple[str, ...]
    max_known_sources: int = 3

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("bootstrap policy identity is required")
        if not self.initial_state_requirements:
            raise ValueError("bootstrap policy requires minimum initial state")
        if len(set(self.initial_state_requirements)) != len(self.initial_state_requirements):
            raise ValueError("bootstrap state requirements must be unique")
        if any(not field.strip() for field in self.initial_state_requirements):
            raise ValueError("bootstrap state requirements cannot be empty")
        if self.max_known_sources < 1:
            raise ValueError("bootstrap source budget must be positive")


@dataclass(frozen=True, slots=True)
class BootstrapSourceCandidate:
    candidate_id: str
    subject_id: str
    observation_slot: str
    source_ref: str
    source_type: str
    provides_fields: frozenset[str]
    priority: int = 100

    def __post_init__(self) -> None:
        required = (
            self.candidate_id,
            self.subject_id,
            self.observation_slot,
            self.source_ref,
            self.source_type,
        )
        if any(not value.strip() for value in required):
            raise ValueError("bootstrap source candidate identity is required")
        if not self.provides_fields or any(not field.strip() for field in self.provides_fields):
            raise ValueError("bootstrap source candidate must declare provided fields")
        if self.priority < 0:
            raise ValueError("bootstrap source priority cannot be negative")


@dataclass(frozen=True, slots=True)
class BootstrapPlan:
    xeed_id: str
    subject_id: str
    policy_id: str
    policy_version: str
    state_fingerprint: str
    disposition: BootstrapDisposition
    reused_observation_count: int
    available_state_fields: frozenset[str]
    missing_requirements: tuple[str, ...]
    source_candidates: tuple[BootstrapSourceCandidate, ...] = ()
    prime_plan: PrimeControlPlan | None = None
    plan_fingerprint: str = ""

    def __post_init__(self) -> None:
        required = (self.xeed_id, self.subject_id, self.policy_id, self.policy_version)
        if any(not value.strip() for value in required):
            raise ValueError("bootstrap plan identity is required")
        if self.reused_observation_count < 0:
            raise ValueError("reused observation count cannot be negative")
        if self.disposition is BootstrapDisposition.HANDOFF_TO_PRIME:
            if self.prime_plan is None or self.missing_requirements or self.source_candidates:
                raise ValueError("Prime handoff requires complete bootstrap state only")
        elif self.prime_plan is not None:
            raise ValueError("only Prime handoff may include a Prime control plan")

        if self.disposition is BootstrapDisposition.ACQUIRE_KNOWN_SOURCES and (
            not self.source_candidates or not self.missing_requirements
        ):
            raise ValueError("source acquisition requires candidates and missing state")
        if self.disposition is BootstrapDisposition.ADAPTIVE_RESEARCH and (
            self.source_candidates or not self.missing_requirements
        ):
            raise ValueError("adaptive research requires unresolved missing state")
        if not self.plan_fingerprint.strip():
            raise ValueError("bootstrap plan fingerprint is required")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _select_known_sources(
    *,
    subject_id: str,
    missing: tuple[str, ...],
    candidates: tuple[BootstrapSourceCandidate, ...],
    limit: int,
) -> tuple[BootstrapSourceCandidate, ...]:
    missing_set = set(missing)
    eligible = [
        candidate
        for candidate in candidates
        if candidate.subject_id == subject_id
        and bool(candidate.provides_fields.intersection(missing_set))
    ]
    selected: list[BootstrapSourceCandidate] = []
    uncovered = set(missing_set)
    remaining = list(eligible)
    while uncovered and remaining and len(selected) < limit:
        remaining.sort(
            key=lambda item: (
                -len(item.provides_fields.intersection(uncovered)),
                item.priority,
                item.candidate_id,
            )
        )
        chosen = remaining.pop(0)
        if not chosen.provides_fields.intersection(uncovered):
            break
        selected.append(chosen)
        uncovered.difference_update(chosen.provides_fields)
    return tuple(selected)


def _plan_fingerprint(
    *,
    xeed_id: str,
    subject_id: str,
    policy: BootstrapPolicy,
    state_fingerprint: str,
    disposition: BootstrapDisposition,
    missing: tuple[str, ...],
    sources: tuple[BootstrapSourceCandidate, ...],
    prime_plan: PrimeControlPlan | None,
) -> str:
    return _fingerprint(
        {
            "xeed_id": xeed_id,
            "subject_id": subject_id,
            "policy": (policy.policy_id, policy.version),
            "state_fingerprint": state_fingerprint,
            "disposition": disposition.value,
            "missing": missing,
            "sources": [item.candidate_id for item in sources],
            "prime_items": []
            if prime_plan is None
            else [
                (
                    item.dimension_id,
                    item.disposition.value,
                    item.route.value,
                    item.policy_version,
                )
                for item in prime_plan.items
            ],
        }
    )


def build_bootstrap_plan(
    *,
    seed: AuthorizedXeedOrganization,
    rich_state: RichSubjectState,
    reused_observation_count: int,
    policy: BootstrapPolicy,
    known_sources: tuple[BootstrapSourceCandidate, ...],
    contracts: tuple[TypingDimensionContract, ...],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
) -> BootstrapPlan:
    """Return the shortest governed path from planted Xeed to Prime."""

    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("bootstrap requires an AuthorizedXeedOrganization")

    xeed_id = seed.authorized_xeed.xeed.id
    subject_id = seed.organization.id
    if rich_state.subject_id != subject_id:
        raise ValueError("bootstrap rich state must belong to the Xeed organization")
    if reused_observation_count < 0:
        raise ValueError("reused observation count cannot be negative")
    candidate_ids = [candidate.candidate_id for candidate in known_sources]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("bootstrap source candidate identities must be unique")
    available = rich_state.available_fields
    missing = tuple(
        requirement
        for requirement in policy.initial_state_requirements
        if requirement not in available
    )

    if not missing:
        empty = compile_rich_subject_state(subject_id=subject_id, contributions=())
        change = StateChange(
            subject_id=subject_id,
            changed_fields=available,
            previous_fingerprint=empty.fingerprint,
            current_fingerprint=rich_state.fingerprint,
        )

        prime_plan = build_prime_control_plan(
            change=change,
            contracts=contracts,
            available_state_fields=available,
            routing_policies=routing_policies,
        )
        disposition = BootstrapDisposition.HANDOFF_TO_PRIME
        sources: tuple[BootstrapSourceCandidate, ...] = ()
    else:
        prime_plan = None
        sources = _select_known_sources(
            subject_id=subject_id,
            missing=missing,
            candidates=known_sources,
            limit=policy.max_known_sources,
        )
        disposition = (
            BootstrapDisposition.ACQUIRE_KNOWN_SOURCES
            if sources
            else BootstrapDisposition.ADAPTIVE_RESEARCH
        )

    fingerprint = _plan_fingerprint(
        xeed_id=xeed_id,
        subject_id=subject_id,
        policy=policy,
        state_fingerprint=rich_state.fingerprint,
        disposition=disposition,
        missing=missing,
        sources=sources,
        prime_plan=prime_plan,
    )
    return BootstrapPlan(
        xeed_id=xeed_id,
        subject_id=subject_id,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        state_fingerprint=rich_state.fingerprint,
        disposition=disposition,
        reused_observation_count=reused_observation_count,
        available_state_fields=available,
        missing_requirements=missing,
        source_candidates=sources,
        prime_plan=prime_plan,
        plan_fingerprint=fingerprint,
    )
