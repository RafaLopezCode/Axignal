"""Fit judgments of open demand, made off the read path (spec 075).

Codes say a call may concern a capability; an evaluator's narrow judgment (spec 062's
``tender_capability_fit``: CORE, PARTIAL, ADJACENT, UNRELATED) says how closely its work is
that capability's. Judgments are world-level (the public notice and the catalog
capability, nothing about any organization), stored in judgment memory and read by live
demand without any provider call. Newest calls first, within the run's budget; what is
not judged today stays unknown and is shown as before.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.findings import ProcurementRecord
from application.observation_intelligence.semantic_screen import (
    FIT,
    CascadeRunner,
    record_batch,
)
from application.semantic_layer.contracts import SemanticBatch
from application.world_demand.index import code_within


def catalog_capabilities(
    only: Iterable[str] = (),
) -> list[tuple[str, tuple[TaxonomyCode, ...]]]:
    """Catalog capabilities with their current codes; ``only`` (when given) first and alone."""
    wanted = list(dict.fromkeys(only))
    entries = {e.capability_id: e.demand_codes for e in CAPABILITY_LEXICON if e.demand_codes}
    ids = [c for c in wanted if c in entries] if wanted else list(entries)
    return [(c, entries[c]) for c in ids]


def open_pairs(
    records: Iterable[ProcurementRecord],
    capabilities: Sequence[tuple[str, tuple[TaxonomyCode, ...]]],
    *,
    today: str,
) -> list[tuple[ProcurementRecord, str]]:
    """(Open call, capability) pairs the code match produces, newest calls first."""
    pairs: list[tuple[ProcurementRecord, str]] = []
    for record in sorted(records, key=lambda r: r.published_at, reverse=True):
        if record.deadline is None or record.deadline[:10] < today:
            continue
        for capability_id, codes in capabilities:
            if any(code_within(c, w) for c in record.demand_codes for w in codes):
                pairs.append((record, capability_id))
    return pairs


@dataclass(frozen=True, slots=True)
class FitRun:
    pairs: int
    #: Resolution of each fit judgment (DECIDED, UNCERTAIN, ABSTAINED_BUDGET, FAILED...).
    resolutions: dict[str, int] = field(default_factory=dict)
    #: Usable labels (CORE, PARTIAL, ADJACENT, UNRELATED).
    labels: dict[str, int] = field(default_factory=dict)
    from_memory: int = 0
    usage: dict[str, object] = field(default_factory=dict)

    def to_wire(self) -> dict[str, object]:
        return {
            "pairs": self.pairs,
            "resolutions": self.resolutions,
            "labels": self.labels,
            "fromMemory": self.from_memory,
            "usage": self.usage,
            "question": f"{FIT.question_id}:{FIT.version}",
        }


def judge_pairs(
    pairs: Sequence[tuple[ProcurementRecord, str]], cascade: CascadeRunner, *, now: datetime
) -> FitRun:
    """One batch per (notice, capability) state: memory first, then System One in order."""
    batches: dict[str, SemanticBatch] = {}
    for record, capability_id in pairs:
        batch = record_batch(record, capability_id)
        if batch is not None:
            batches.setdefault(batch.batch_id, batch)
    outcomes = cascade.run(tuple(batches.values()), now=now)
    resolutions: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    from_memory = 0
    for outcome in outcomes.values():
        judgment = outcome.judgment(FIT.question_id)
        resolutions[judgment.resolution.value] += 1
        from_memory += judgment.from_memory
        if judgment.usable and judgment.answer is not None:
            labels[judgment.answer.top] += 1
    return FitRun(
        pairs=len(batches),
        resolutions=dict(resolutions),
        labels=dict(labels),
        from_memory=from_memory,
        usage=dict(cascade.ledger.to_wire()),
    )
