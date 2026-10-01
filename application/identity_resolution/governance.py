"""Governed canonical-identity topology for FR-23.

Canonical identity changes are append-only decisions. A merge may redirect an
old OrganizationId to a retained canonical OrganizationId. A split never
chooses one child automatically: the old identity becomes ambiguous until a
new observation is resolved against a concrete canonical subject.

Subscriber/Xeed context is intentionally absent from every authority contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from domain.identity import OrganizationId


class IdentityDecisionKind(StrEnum):
    MERGE = "MERGE"
    SPLIT = "SPLIT"
    REVERSAL = "REVERSAL"


class IdentitySubjectState(StrEnum):
    ACTIVE = "ACTIVE"
    REDIRECTED = "REDIRECTED"
    AMBIGUOUS = "AMBIGUOUS"


class IdentityDecisionAuthority(StrEnum):
    GOVERNED_HUMAN = "GOVERNED_HUMAN"
    DETERMINISTIC_POLICY = "DETERMINISTIC_POLICY"


@dataclass(frozen=True, slots=True)
class IdentitySubjectPointer:
    organization_id: OrganizationId
    state: IdentitySubjectState
    redirect_to: OrganizationId | None = None
    last_decision_id: str | None = None
    requires_revalidation: bool = False

    def __post_init__(self) -> None:
        if not self.organization_id.strip():
            raise ValueError("identity subject pointer requires organization id")
        if self.state is IdentitySubjectState.REDIRECTED:
            if self.redirect_to is None or not self.redirect_to.strip():
                raise ValueError("redirected identity requires target")
            if self.redirect_to == self.organization_id:
                raise ValueError("identity cannot redirect to itself")
        elif self.redirect_to is not None:
            raise ValueError("non-redirected identity cannot carry redirect target")


@dataclass(frozen=True, slots=True)
class IdentityDecisionRecord:
    decision_id: str
    kind: IdentityDecisionKind
    from_organization_ids: tuple[OrganizationId, ...]
    to_organization_ids: tuple[OrganizationId, ...]
    evidence_refs: tuple[str, ...]
    reason_code: str
    authority: IdentityDecisionAuthority
    decided_by: str
    decided_at: datetime
    previous_decision_id: str | None = None
    reverses_decision_id: str | None = None
    requires_revalidation_ids: tuple[OrganizationId, ...] = ()

    def __post_init__(self) -> None:
        required = (self.decision_id, self.reason_code, self.decided_by)
        if any(not value.strip() for value in required):
            raise ValueError("identity decision provenance is required")
        if not isinstance(self.authority, IdentityDecisionAuthority):
            raise ValueError("identity decision authority must be governed")
        if self.decided_at.tzinfo is None:
            raise ValueError("identity decision time must be timezone-aware")
        if not self.from_organization_ids or not self.to_organization_ids:
            raise ValueError("identity decision requires from/to organizations")
        if len(set(self.from_organization_ids)) != len(self.from_organization_ids):
            raise ValueError("identity decision from organizations must be unique")
        if len(set(self.to_organization_ids)) != len(self.to_organization_ids):
            raise ValueError("identity decision to organizations must be unique")
        if any(not item.strip() for item in self.evidence_refs):
            raise ValueError("identity decision evidence refs must be non-empty")
        if not self.evidence_refs:
            raise ValueError("identity decision requires evidence")
        if self.kind is IdentityDecisionKind.MERGE:
            if len(self.to_organization_ids) != 1:
                raise ValueError("merge requires exactly one retained target")
            if set(self.from_organization_ids) & set(self.to_organization_ids):
                raise ValueError("merge source and retained target must be distinct")
            if self.reverses_decision_id is not None:
                raise ValueError("merge cannot be a reversal")
        elif self.kind is IdentityDecisionKind.SPLIT:
            if len(self.from_organization_ids) != 1 or len(self.to_organization_ids) < 2:
                raise ValueError("split requires one source and at least two targets")
            if set(self.from_organization_ids) & set(self.to_organization_ids):
                raise ValueError("split source and targets must be distinct")
            if self.reverses_decision_id is not None:
                raise ValueError("split cannot be a reversal")
        elif self.reverses_decision_id is None or not self.reverses_decision_id.strip():
            raise ValueError("reversal must target a prior identity decision")

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["authority"] = self.authority.value
        payload["decided_at"] = self.decided_at.astimezone(UTC).isoformat()
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class IdentityGovernanceConflict(RuntimeError):
    """Identity topology could not be changed without violating history."""


class IdentityGovernanceStore(Protocol):
    def seed_subject(self, organization_id: OrganizationId) -> bool: ...

    def current(self, organization_id: OrganizationId) -> IdentitySubjectPointer | None: ...

    def get_decision(self, decision_id: str) -> IdentityDecisionRecord | None: ...

    def latest_decision_id(self) -> str | None: ...

    def history(self) -> tuple[IdentityDecisionRecord, ...]: ...

    def append_and_apply(self, record: IdentityDecisionRecord) -> None: ...


def _require_active(
    store: IdentityGovernanceStore,
    organization_id: OrganizationId,
) -> IdentitySubjectPointer:
    pointer = store.current(organization_id)
    if pointer is None:
        raise IdentityGovernanceConflict("identity subject is not registered")
    if pointer.state is not IdentitySubjectState.ACTIVE:
        raise IdentityGovernanceConflict("identity subject is not active")
    return pointer


def merge_identities(
    *,
    absorbed_organization_ids: tuple[OrganizationId, ...],
    retained_organization_id: OrganizationId,
    evidence_refs: tuple[str, ...],
    reason_code: str,
    authority: IdentityDecisionAuthority,
    decided_by: str,
    decided_at: datetime,
    decision_id: str,
    store: IdentityGovernanceStore,
) -> IdentityDecisionRecord:
    if not absorbed_organization_ids:
        raise ValueError("merge requires at least one absorbed organization")
    for organization_id in absorbed_organization_ids:
        _require_active(store, organization_id)
    _require_active(store, retained_organization_id)

    record = IdentityDecisionRecord(
        decision_id=decision_id,
        kind=IdentityDecisionKind.MERGE,
        from_organization_ids=absorbed_organization_ids,
        to_organization_ids=(retained_organization_id,),
        evidence_refs=evidence_refs,
        reason_code=reason_code,
        authority=authority,
        decided_by=decided_by,
        decided_at=decided_at,
        previous_decision_id=store.latest_decision_id(),
    )
    store.append_and_apply(record)
    return record


def split_identity(
    *,
    source_organization_id: OrganizationId,
    target_organization_ids: tuple[OrganizationId, ...],
    evidence_refs: tuple[str, ...],
    reason_code: str,
    authority: IdentityDecisionAuthority,
    decided_by: str,
    decided_at: datetime,
    decision_id: str,
    store: IdentityGovernanceStore,
) -> IdentityDecisionRecord:
    _require_active(store, source_organization_id)
    for organization_id in target_organization_ids:
        _require_active(store, organization_id)

    record = IdentityDecisionRecord(
        decision_id=decision_id,
        kind=IdentityDecisionKind.SPLIT,
        from_organization_ids=(source_organization_id,),
        to_organization_ids=target_organization_ids,
        evidence_refs=evidence_refs,
        reason_code=reason_code,
        authority=authority,
        decided_by=decided_by,
        decided_at=decided_at,
        previous_decision_id=store.latest_decision_id(),
        requires_revalidation_ids=(
            source_organization_id,
            *target_organization_ids,
        ),
    )
    store.append_and_apply(record)
    return record


def reverse_identity_decision(
    *,
    target_decision_id: str,
    evidence_refs: tuple[str, ...],
    reason_code: str,
    authority: IdentityDecisionAuthority,
    decided_by: str,
    decided_at: datetime,
    decision_id: str,
    store: IdentityGovernanceStore,
) -> IdentityDecisionRecord:
    target = store.get_decision(target_decision_id)
    if target is None:
        raise IdentityGovernanceConflict("identity reversal target does not exist")
    if target.kind is IdentityDecisionKind.REVERSAL:
        raise IdentityGovernanceConflict("identity reversal cannot target another reversal")

    affected = tuple(
        sorted(
            set(target.from_organization_ids) | set(target.to_organization_ids),
            key=str,
        )
    )
    record = IdentityDecisionRecord(
        decision_id=decision_id,
        kind=IdentityDecisionKind.REVERSAL,
        from_organization_ids=target.to_organization_ids,
        to_organization_ids=target.from_organization_ids,
        evidence_refs=evidence_refs,
        reason_code=reason_code,
        authority=authority,
        decided_by=decided_by,
        decided_at=decided_at,
        previous_decision_id=store.latest_decision_id(),
        reverses_decision_id=target.decision_id,
        requires_revalidation_ids=affected,
    )
    store.append_and_apply(record)
    return record


def resolve_current_subject(
    store: IdentityGovernanceStore,
    organization_id: OrganizationId,
) -> IdentitySubjectPointer:
    """Resolve current canonical use without silently choosing after a split."""

    pointer = store.current(organization_id)
    if pointer is None:
        raise IdentityGovernanceConflict("identity subject is not registered")
    if pointer.state is IdentitySubjectState.AMBIGUOUS:
        raise IdentityGovernanceConflict("identity subject is ambiguous after split")
    if pointer.state is IdentitySubjectState.REDIRECTED:
        assert pointer.redirect_to is not None
        target = store.current(pointer.redirect_to)
        if target is None or target.state is not IdentitySubjectState.ACTIVE:
            raise IdentityGovernanceConflict("identity redirect target is not active")
        return target
    return pointer


def observation_matches_current_subject(
    *,
    observation_subject_id: OrganizationId,
    requested_subject_id: OrganizationId,
    store: IdentityGovernanceStore,
) -> bool:
    """Fail closed: historical observations are never silently rebound."""

    current = resolve_current_subject(store, requested_subject_id)
    return observation_subject_id == current.organization_id
