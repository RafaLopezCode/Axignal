"""Semantic demand screen (spec 062): the first consumer of the semantic layer.

Deterministic code finds candidate demand (classification codes, places, deadlines)
and the Economic Relevance Gate (spec 059) decides reach. Between them, one System
One call per (tender, capability class) answers two questions that codes cannot:

* how closely the tender's object is the capability's work (Score), and
* where the work must be delivered (Choice), which feeds the gate's delivery-mode
  family instead of leaving it UNKNOWN.

The screen can only narrow and explain. A confidently UNRELATED tender is filtered
and counted, never deleted; an uncertain judgment changes nothing; the screen never
creates a candidate, widens reach or turns POTENTIAL into anything stronger.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.economic_reach.model import DeliveryMode
from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.observation_intelligence.loop import OpportunityCandidate
from application.semantic_layer.cascade import CascadeOutcome, Resolution, ResolvedJudgment
from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion, fingerprint
from application.semantic_layer.ledger import CostLedger

SCREEN_VERSION = "demand-screen:1"

FIT = SemanticQuestion(
    question_id="tender_capability_fit",
    version="1",
    primitive=SemanticPrimitive.SCORE,
    instructions=(
        "Judge only from `tender.title`, `tender.buyer` and `tender.classification`: how "
        "closely is the work this tender asks for the work described in `capability`?"
    ),
    criteria=(
        ("UNRELATED", "The tender asks for work the capability does not do."),
        ("ADJACENT", "Same sector or setting, but the main work requested is different."),
        ("PARTIAL", "Part of the requested work is the capability; other parts are not."),
        ("CORE", "The main work the tender asks for is the capability's work."),
    ),
)

DELIVERY = SemanticQuestion(
    question_id="tender_delivery_mode",
    version="1",
    primitive=SemanticPrimitive.CHOICE,
    instructions="According to `tender`, where must the requested work be delivered?",
    criteria=(
        ("CUSTOMER_SITE", "Works or services carried out at the buyer's premises or a site."),
        ("SHIPPED", "Goods supplied and delivered to the buyer."),
        ("REMOTE_OR_DIGITAL", "Services that can be delivered remotely or as software."),
        ("UNCLEAR", "The tender does not say where the work is delivered."),
    ),
)

_MODES: dict[str, frozenset[DeliveryMode]] = {
    "CUSTOMER_SITE": frozenset({DeliveryMode.CUSTOMER_SITE}),
    "SHIPPED": frozenset({DeliveryMode.SHIPPED}),
    "REMOTE_OR_DIGITAL": frozenset({DeliveryMode.REMOTE, DeliveryMode.DIGITAL}),
}
_LEXICON = {entry.capability_id: entry for entry in CAPABILITY_LEXICON}
_FIT_ORDER = {"CORE": 0, "PARTIAL": 1, "ADJACENT": 2}


def screen_batch(candidate: OpportunityCandidate, capability_id: str) -> SemanticBatch | None:
    """World-level state only: the public notice and the capability class, nothing private."""
    entry = _LEXICON.get(capability_id)
    if entry is None:
        return None
    record = candidate.record
    state: dict[str, object] = {
        "tender": {
            "title": record.title,
            "buyer": record.buyer_name,
            "classification": [f"{code.scheme}:{code.code}" for code in record.demand_codes],
        },
        "capability": {
            "label": entry.label,
            "described_as": list(entry.terms),
            "buyers_ask_for": list(entry.buyer_jobs),
        },
    }
    key = fingerprint([SCREEN_VERSION, record.source_id, record.record_id, capability_id])
    return SemanticBatch(f"demand-screen:{key[:24]}", state, (FIT, DELIVERY))


@dataclass(frozen=True, slots=True)
class DemandScreen:
    """What the semantic layer may tell the projection about one candidate."""

    candidate_id: str
    fits: Mapping[str, ResolvedJudgment]
    delivery: ResolvedJudgment | None

    @property
    def unrelated(self) -> bool:
        """Every matched capability was confidently judged UNRELATED (never on doubt)."""
        return bool(self.fits) and all(
            item.usable and item.answer is not None and item.answer.top == "UNRELATED"
            for item in self.fits.values()
        )

    @property
    def required_modes(self) -> frozenset[DeliveryMode]:
        if self.delivery is None or not self.delivery.usable or self.delivery.answer is None:
            return frozenset()
        return _MODES.get(self.delivery.answer.top, frozenset())

    @property
    def best_fit(self) -> str | None:
        levels = [
            item.answer.top
            for item in self.fits.values()
            if item.usable and item.answer is not None and item.answer.top in _FIT_ORDER
        ]
        return min(levels, key=_FIT_ORDER.__getitem__) if levels else None

    @property
    def rank(self) -> int:
        """Presentation order only: CORE, PARTIAL, ADJACENT, then not judged."""
        return _FIT_ORDER.get(self.best_fit or "", len(_FIT_ORDER))

    def explanation(self) -> dict[str, object]:
        return {
            "version": SCREEN_VERSION,
            "fit": self.best_fit,
            "fitByCapability": {cid: item.to_wire() for cid, item in self.fits.items()},
            "delivery": None if self.delivery is None else self.delivery.to_wire(),
            "requiredModes": sorted(mode.value for mode in self.required_modes),
            "nonAuthoritative": True,
        }


@dataclass(frozen=True, slots=True)
class ScreenRun:
    """One screening pass: per-candidate screens and what it cost."""

    screens: Mapping[str, DemandScreen]
    usage: Mapping[str, object]


class DemandScreenPort(Protocol):
    def screen(self, candidates: Sequence[OpportunityCandidate], *, now: datetime) -> ScreenRun: ...


class CascadeRunner(Protocol):
    ledger: CostLedger

    def run(
        self, batches: Sequence[SemanticBatch], *, now: datetime
    ) -> dict[str, CascadeOutcome]: ...


@dataclass(slots=True)
class SemanticDemandScreen:
    """``DemandScreenPort`` over a semantic cascade built fresh for each run, so the
    budget and the cost ledger are per run; judgment memory is shared across runs."""

    cascade_factory: Callable[[], CascadeRunner]

    def screen(self, candidates: Sequence[OpportunityCandidate], *, now: datetime) -> ScreenRun:
        cascade = self.cascade_factory()
        planned: list[tuple[OpportunityCandidate, str, SemanticBatch]] = []
        for candidate in candidates:
            for capability_id in candidate.capability_ids:
                batch = screen_batch(candidate, capability_id)
                if batch is not None:
                    planned.append((candidate, capability_id, batch))
        unique = {batch.batch_id: batch for _, _, batch in planned}
        outcomes = cascade.run(tuple(unique.values()), now=now)
        screens: dict[str, DemandScreen] = {}
        for candidate in candidates:
            fits: dict[str, ResolvedJudgment] = {}
            deliveries: list[ResolvedJudgment] = []
            for planned_candidate, capability_id, batch in planned:
                if planned_candidate is not candidate or batch.batch_id not in outcomes:
                    continue
                outcome = outcomes[batch.batch_id]
                fits[capability_id] = outcome.judgment(FIT.question_id)
                deliveries.append(outcome.judgment(DELIVERY.question_id))
            usable = [item for item in deliveries if item.usable]
            delivery = usable[0] if usable else (deliveries[0] if deliveries else None)
            if fits or delivery is not None:
                screens[candidate.candidate_id] = DemandScreen(
                    candidate.candidate_id, fits, delivery
                )
        return ScreenRun(screens, cascade.ledger.to_wire())


def screen_summary(screens: Mapping[str, DemandScreen]) -> dict[str, int]:
    """How many judgments were usable, uncertain or unavailable (for the trace)."""
    summary: dict[str, int] = {}
    for screen in screens.values():
        for item in (*screen.fits.values(), *((screen.delivery,) if screen.delivery else ())):
            key = item.resolution.value
            summary[key] = summary.get(key, 0) + 1
    return summary


__all__ = [
    "DELIVERY",
    "FIT",
    "SCREEN_VERSION",
    "DemandScreen",
    "DemandScreenPort",
    "Resolution",
    "ScreenRun",
    "SemanticDemandScreen",
    "screen_batch",
    "screen_summary",
]
