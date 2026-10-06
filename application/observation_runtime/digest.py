"""Subscriber-safe reading of what autonomous observation currently supports.

Opportunities stay POTENTIAL with their provenance and their missing context.
A family with no current evidence reads as UNKNOWN with the reason it could not
be observed, never as zero or absence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from application.observation_runtime.families import ObservationFamily
from application.observation_runtime.frontier import LeadStatus
from application.observation_runtime.ports import ObservationRuntimeStore
from domain.evidence.epistemics import Currentness


@dataclass(frozen=True, slots=True)
class DigestOpportunity:
    candidate_id: str
    title: str
    buyer: str | None
    deadline: str | None
    source_url: str
    epistemic_state: str
    open_on_as_of: bool
    why_looked: tuple[str, ...]
    missing_context: tuple[str, ...]
    observed_at: str


@dataclass(frozen=True, slots=True)
class FamilyReading:
    family: str
    #: CURRENT / STALE / HISTORICAL from evidence; UNKNOWN when nothing was observed.
    currentness: str
    evidence: int
    last_observed_at: str | None
    unknown_because: tuple[str, ...]
    next_due_at: str | None


@dataclass(frozen=True, slots=True)
class ObservationDigest:
    xeed_id: str
    as_of: str
    opportunities: tuple[DigestOpportunity, ...]
    families: tuple[FamilyReading, ...]

    @property
    def fingerprint(self) -> str:
        payload = {
            "opportunities": [(o.candidate_id, o.open_on_as_of) for o in self.opportunities],
            "families": [(f.family, f.currentness, f.evidence) for f in self.families],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


_WORST = (Currentness.HISTORICAL, Currentness.STALE, Currentness.CURRENT)


def observation_digest(
    store: ObservationRuntimeStore, xeed_id: str, *, as_of: datetime
) -> ObservationDigest:
    if as_of.tzinfo is None:
        raise ValueError("a digest needs a timezone-aware cut")
    evidence = [e for e in store.evidence() if e.xeed_id == xeed_id and e.observed_at <= as_of]
    leads = [lead for lead in store.leads() if lead.xeed_id == xeed_id]
    day = as_of.date().isoformat()
    opportunities = tuple(
        DigestOpportunity(
            candidate_id=c.candidate_id,
            title=c.record.title,
            buyer=c.record.buyer_name,
            deadline=c.record.deadline,
            source_url=c.record.source_url,
            epistemic_state=c.epistemic_state.value,
            open_on_as_of=c.record.deadline is not None and c.record.deadline[:10] >= day,
            why_looked=c.why_looked,
            missing_context=c.missing_context,
            observed_at=c.observed_at.isoformat(),
        )
        for c in (item.candidate for item in store.candidates(xeed_id))
        if c.observed_at <= as_of
    )
    families = []
    for family in ObservationFamily:
        rows = [e for e in evidence if e.family is family]
        own = [lead for lead in leads if lead.family is family]
        states = {row.currentness for row in rows}
        # The family is only as current as its oldest evidence.
        currentness = next((s for s in _WORST if s in states), Currentness.UNKNOWN)
        last = max((r.observed_at for r in rows), default=None)
        due = min((lead.next_due_at for lead in own), default=None)
        families.append(
            FamilyReading(
                family=family.value,
                currentness=currentness.value,
                evidence=len(rows),
                last_observed_at=None if last is None else last.isoformat(),
                unknown_because=tuple(
                    sorted(
                        lead.blocked_reason or ""
                        for lead in own
                        if lead.status is LeadStatus.BLOCKED
                    )
                ),
                next_due_at=None if due is None else due.isoformat(),
            )
        )
    return ObservationDigest(xeed_id, as_of.isoformat(), opportunities, tuple(families))
