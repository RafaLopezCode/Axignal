"""The research frontier: what AXIGNAL may look at next, and why.

A ResearchLead is a direction of attention, never evidence. Its identity is
content-addressed (Xeed, family, kind, target), so a lead rediscovered from a
different path merges its provenance instead of duplicating work, and a cyclic
expansion (buyer → project → buyer) lands on the lead that already exists.
Priority is an explicit tier plus a stable tie-break; there is no score.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import IntEnum, StrEnum

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode
from application.observation_runtime.families import (
    FAMILY_ORDER,
    LEAD_CAPABILITY,
    LeadKind,
    ObservationFamily,
)


class LeadTier(IntEnum):
    """Why a lead competes for budget now; lower runs first."""

    #: An entry point never observed: the family is UNKNOWN for this Xeed.
    FIRST_OBSERVATION = 0
    #: Opened by new evidence; it can reduce a named UNKNOWN.
    FOLLOW_UP = 1
    #: Evidence it produced aged out of CURRENT.
    STALE_EVIDENCE = 2
    #: Due by cadence; it yielded recently.
    SCHEDULED_REFRESH = 3
    #: Repeatedly produced nothing new; it waits behind everything else.
    LOW_YIELD = 4


class LeadStatus(StrEnum):
    ACTIVE = "ACTIVE"
    #: No adopted source (or no adapter) can answer it now: UNKNOWN stays UNKNOWN.
    BLOCKED = "BLOCKED"


class LeadOutcome(StrEnum):
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    UNCHANGED = "UNCHANGED"
    NO_EVIDENCE = "NO_EVIDENCE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


def lead_id(
    xeed_id: str, family: ObservationFamily, kind: LeadKind, target: str, geography: str | None
) -> str:
    payload = "|".join((xeed_id, family.value, kind.value, target, geography or ""))
    return "lead:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True, slots=True)
class ResearchLead:
    lead_id: str
    xeed_id: str
    family: ObservationFamily
    kind: LeadKind
    #: What is looked at: a URL, an organization name, a buyer, a jurisdiction.
    target: str
    geography: TaxonomyCode | None
    question: str
    #: The UNKNOWN this lead could reduce, in words.
    reduces_unknown: str
    depth: int
    parent_lead_id: str | None
    #: Evidence keys that opened this lead; empty for entry points.
    origin_evidence: tuple[str, ...]
    reasons: tuple[str, ...]
    next_due_at: datetime
    tier: LeadTier
    scheduling_reason: str
    status: LeadStatus = LeadStatus.ACTIVE
    attempts: int = 0
    failures: int = 0
    no_gain_streak: int = 0
    last_outcome: LeadOutcome | None = None
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_material_change_at: datetime | None = None
    blocked_reason: str | None = None
    evidence_keys: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.xeed_id.strip() or not self.target.strip() or not self.question.strip():
            raise ValueError("a research lead needs a Xeed, a target and a question")
        if self.depth < 0:
            raise ValueError("lead depth cannot be negative")
        if (self.depth == 0) != (self.parent_lead_id is None):
            raise ValueError("only entry leads (depth 0) have no parent")
        if self.depth > 0 and not self.origin_evidence:
            raise ValueError("a follow-up lead must name the evidence that opened it")
        if self.next_due_at.tzinfo is None:
            raise ValueError("lead due time must be timezone-aware")
        expected = lead_id(
            self.xeed_id,
            self.family,
            self.kind,
            self.target,
            None if self.geography is None else self.geography.code,
        )
        if self.lead_id != expected:
            raise ValueError("lead identity must be content-addressed")

    @property
    def capability(self) -> SourceCapability:
        return LEAD_CAPABILITY[self.kind]

    def due(self, now: datetime) -> bool:
        return self.next_due_at <= now

    def merged_with(self, other: ResearchLead) -> ResearchLead:
        """Same lead reached again: union of provenance; its schedule is never reset."""

        if other.lead_id != self.lead_id:
            raise ValueError("only the same lead can be merged")
        return replace(
            self,
            origin_evidence=tuple(sorted({*self.origin_evidence, *other.origin_evidence})),
            reasons=tuple(dict.fromkeys((*self.reasons, *other.reasons))),
        )


def lead_order(lead: ResearchLead) -> tuple[object, ...]:
    """Tier, then closer to the Xeed, then canonical family order, then identity."""

    return (lead.tier, lead.depth, FAMILY_ORDER[lead.family], lead.kind.value, lead.lead_id)


def explain(lead: ResearchLead) -> tuple[str, ...]:
    """Why AXIGNAL would spend budget on this lead, answerable without any model."""

    lines = [
        f"TIER:{lead.tier.name}:{lead.scheduling_reason}",
        f"FAMILY:{lead.family.value}",
        f"QUESTION:{lead.question}",
        f"REDUCES_UNKNOWN:{lead.reduces_unknown}",
        f"NEEDS:{lead.capability.value}",
        f"TARGET:{lead.target}",
        f"DEPTH:{lead.depth}",
    ]
    if lead.geography is not None:
        lines.append(f"GEOGRAPHY:{lead.geography.code}")
    if lead.origin_evidence:
        lines.append("FROM_EVIDENCE:" + ",".join(lead.origin_evidence))
    return (*lines, *lead.reasons)
