"""Open demand read live from the world index for a stored first observation.

A first observation records which capabilities were recognized (with the classification
codes buyers use for them) and where the organization's attention lies. Tenders open and
close daily, so the demand shown to a subscriber is matched again at read time against the
current index: only calls still open today, all of them (not a frozen top five), with the
ones published in the last days marked as new. The index answers only for slices that are
complete and fresh; otherwise the caller keeps what the observation stored.

Every match stays POTENTIAL: a capability code inside a published call is a plausible fit,
never a customer, a lead or an assessed commercial fit. A call whose main object is something
else, where the activity is only an additional code, is said so and shown after the others.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.observation_intelligence.catalog import with_current_codes
from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode
from application.observation_intelligence.findings import (
    ADDITIONAL,
    MAIN,
    ProcurementRecord,
    classified_as,
)
from application.world_demand.index import DemandIndexStore, DemandSlice, code_within, country_of

OPEN = SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
#: A call published within this period is shown as new.
NEW_FOR = timedelta(days=7)
#: Read-time freshness: one missed daily ingestion is tolerated, two are not.
FRESH_FOR = timedelta(hours=50)
MAX_SHOWN = 100


@dataclass(frozen=True, slots=True)
class LiveDemand:
    as_of: datetime
    #: The index ingestion the answer comes from (never fresher than observed).
    ingested_at: datetime
    candidates: tuple[dict[str, object], ...]
    total: int
    new: int
    sources: tuple[str, ...]
    #: Calls where the activity is only an additional code (main object: something else).
    additional: int = 0


def _words(title: object) -> str:
    """A title's own words: TED prefixes 'Country, en dash, Category, en dash' to it."""
    text = str(title or "").split(" \u2013 ")[-1].casefold()
    return " ".join(re.findall(r"\w+", text))[:60]


def _best_classification(*known: object) -> str | None:
    """MAIN when any reading says so, ADDITIONAL when one does, otherwise unknown."""
    return MAIN if MAIN in known else ADDITIONAL if ADDITIONAL in known else None


def _without_duplicates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    """One call published in several sources is shown once, from its national platform.

    Same buyer, same deadline day and the same opening words: the same call. So is one with
    the same deadline day and the same full list of three or more codes: sources title and
    name buyers differently, a detailed classification is the call's own. The national
    platform's entry is kept (its official link); otherwise the first one seen. What one
    source knows of the call's main object (TED publishes it) is kept on the merged entry.
    """
    kept: dict[tuple[str, str, str], dict[str, object]] = {}
    by_codes: dict[tuple[str, str], tuple[str, str, str]] = {}
    for candidate in candidates:
        key = (
            str(candidate.get("buyer") or "").casefold().strip(),
            str(candidate.get("deadline") or "")[:10],
            _words(candidate.get("title"))[:40],
        )
        signature = str(candidate.pop("_allCodes", "") or "")
        twin = by_codes.get((key[1], signature)) if signature and key[1] else None
        if twin is not None and key not in kept:
            key = twin
        if not key[0] or not key[1]:
            kept[(str(id(candidate)), "", "")] = candidate
            continue
        if signature:
            by_codes.setdefault((key[1], signature), key)
        current = kept.get(key)
        if current is None:
            kept[key] = candidate
            continue
        known = _best_classification(current.get("classifiedAs"), candidate.get("classifiedAs"))
        if current.get("source") != "es-placsp" and candidate.get("source") == "es-placsp":
            current = kept[key] = dict(candidate)
        current["classifiedAs"] = known
    return list(kept.values())


def _items(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else []


def _capabilities(
    raw: Iterable[Mapping[str, object]],
) -> list[tuple[str, tuple[TaxonomyCode, ...]]]:
    out = []
    for item in raw:
        codes = tuple(
            TaxonomyCode(str(pair[0]), str(pair[1]))
            for pair in _items(item.get("demandCodes"))
            if isinstance(pair, Sequence) and len(pair) == 2
        )
        if codes and item.get("capabilityId"):
            out.append((str(item["capabilityId"]), codes))
    return out


class LiveDemandReader:
    """Matches stored capabilities and attention against the current index."""

    def __init__(
        self,
        store: DemandIndexStore,
        *,
        sources: Sequence[str],
        clock: Callable[[], datetime],
        fresh_for: timedelta = FRESH_FOR,
    ) -> None:
        self._store = store
        self._sources = tuple(sources)
        self._clock = clock
        self._fresh_for = fresh_for
        # Decoded slice records, kept until the slice is ingested again.
        self._cache: dict[str, tuple[datetime, tuple[ProcurementRecord, ...]]] = {}

    def _records(self, item: DemandSlice) -> tuple[datetime, tuple[ProcurementRecord, ...]] | None:
        state = self._store.state(item)
        if state is None or not state.complete or state.ingested_at is None:
            if state is None or state.demanded_at is None:
                # Not prepared yet: demand it, so the ingestor prepares it for next time.
                self._store.demand(item, now=self._clock())
            return None
        if self._clock() - state.ingested_at > self._fresh_for:
            return None
        cached = self._cache.get(item.key)
        if cached is None or cached[0] != state.ingested_at:
            cached = (state.ingested_at, self._store.records(item))
            self._cache[item.key] = cached
        return cached

    def read(
        self,
        capabilities: Iterable[Mapping[str, object]],
        jurisdictions: Iterable[str],
    ) -> LiveDemand | None:
        """None when nothing can be answered from a complete, fresh slice."""
        wanted = _capabilities(capabilities)
        markets = [TaxonomyCode("GEO", j) for j in dict.fromkeys(jurisdictions) if j]
        if not wanted or not markets:
            return None
        now = self._clock()
        today = now.date().isoformat()
        found: dict[tuple[str, str], dict[str, object]] = {}
        ingested: list[datetime] = []
        answered: set[str] = set()
        for market in markets:
            country = country_of(market)
            if country is None:
                continue
            for source_id in self._sources:
                read = self._records(DemandSlice(source_id, country, OPEN))
                if read is None:
                    continue
                ingested.append(read[0])
                answered.add(source_id)
                for record in read[1]:
                    # A closed call is evidence of demand, not an open opportunity;
                    # an unknown deadline is not open either.
                    if record.deadline is None or record.deadline[:10] < today:
                        continue
                    if not any(place.within(market) for place in record.places):
                        continue
                    matched = {
                        capability_id: {
                            offered
                            for offered in record.demand_codes
                            if any(code_within(offered, code) for code in codes)
                        }
                        for capability_id, codes in wanted
                    }
                    matched = {k: v for k, v in matched.items() if v}
                    key = (record.source_id, record.record_id)
                    if not matched or key in found:
                        continue
                    classification = _best_classification(
                        *(classified_as(record, codes) for cid, codes in wanted if cid in matched)
                    )
                    found[key] = {
                        "title": record.title,
                        "buyer": record.buyer_name,
                        "url": record.source_url,
                        "deadline": record.deadline,
                        "publishedAt": record.published_at.isoformat(),
                        "market": market.code,
                        "capabilityIds": sorted(matched),
                        "codes": sorted(
                            f"{c.scheme}:{c.code}" for codes in matched.values() for c in codes
                        ),
                        "source": record.source_id,
                        "demandForm": "OPEN_CALL_FOR_TENDER",
                        "epistemicState": "POTENTIAL",
                        "isNew": now - record.published_at <= NEW_FOR,
                        "classifiedAs": classification,
                        # Read by the duplicate check only, then dropped.
                        "_allCodes": ",".join(sorted({c.code for c in record.demand_codes}))
                        if len(record.demand_codes) >= 3
                        else "",
                    }
        if not answered:
            return None
        ordered = sorted(
            _without_duplicates(list(found.values())),
            key=lambda c: (
                c.get("classifiedAs") == ADDITIONAL,
                not c["isNew"],
                str(c["deadline"]),
                str(c["title"]),
            ),
        )
        return LiveDemand(
            as_of=now,
            ingested_at=min(ingested),
            candidates=tuple(ordered[:MAX_SHOWN]),
            total=len(ordered),
            new=sum(1 for c in ordered if c["isNew"]),
            sources=tuple(sorted(answered)),
            additional=sum(1 for c in ordered if c.get("classifiedAs") == ADDITIONAL),
        )


def _expired(discovery: Mapping[str, object], today: str) -> bool:
    detail = discovery.get("detail")
    deadline = detail.get("deadline") if isinstance(detail, Mapping) else None
    return isinstance(deadline, str) and deadline[:10] < today


def apply_live_demand(
    view: dict[str, object],
    proof: Mapping[str, object],
    reader: LiveDemandReader | None,
    *,
    now: datetime,
    directed: Sequence[str] = (),
) -> dict[str, object]:
    """The subscriber view with demand matched now; stored demand when the index cannot say.

    Applies only where the observation itself looked for demand. Without a live answer,
    calls whose deadline has passed are still removed: a closed call is not open demand.
    """
    discoveries = [d for d in _items(view.get("discoveries")) if isinstance(d, Mapping)]
    looked = any(
        d.get("kind") == "DEMAND" or d.get("code") == "NO_RELEVANT_DEMAND_FOUND"
        for d in discoveries
    )
    # Markets the subscriber chose direct attention too: demand is looked for there even
    # when the observation found no place of its own (never a fact about the organization).
    looked = looked or bool(directed)
    if not looked:
        return view
    live = None
    if reader is not None:
        live = reader.read(
            [
                with_current_codes(c)
                for c in _items(proof.get("capabilities"))
                if isinstance(c, Mapping)
            ],
            [
                str(s.get("jurisdiction"))
                for s in _items(proof.get("attentionScopes"))
                if isinstance(s, Mapping)
            ]
            + list(directed),
        )
    today = now.date().isoformat()
    if live is None:
        kept = [d for d in discoveries if not (d.get("kind") == "DEMAND" and _expired(d, today))]
        shown = sum(1 for d in kept if d.get("kind") == "DEMAND")
        view["discoveries"] = kept
        view["demand"] = {
            "live": False,
            "asOf": now.isoformat(),
            "total": shown,
            "new": 0,
            "preparing": bool(directed) and reader is not None,
        }
        return view
    others = [
        d
        for d in discoveries
        if d.get("kind") != "DEMAND" and d.get("code") != "NO_RELEVANT_DEMAND_FOUND"
    ]
    matched = [
        {
            "kind": "DEMAND",
            "code": "POTENTIAL_DEMAND",
            "statement": str(c.get("title") or "Public demand"),
            "epistemicState": "POTENTIAL",
            "sourceUrl": c.get("url"),
            "excerpt": None,
            "observedAt": live.ingested_at.isoformat(),
            "detail": c,
        }
        for c in live.candidates
    ]
    if not matched:
        matched = [
            {
                "kind": "SIGNIFICANT_UNKNOWN",
                "code": "NO_RELEVANT_DEMAND_FOUND",
                "statement": "The governed sources searched have no open matching demand today. "
                "No result is not no opportunity.",
                "epistemicState": "UNKNOWN",
                "sourceUrl": None,
                "excerpt": None,
                "observedAt": live.ingested_at.isoformat(),
                "detail": {},
            }
        ]
    view["discoveries"] = others + matched
    view["demand"] = {
        "live": True,
        "asOf": live.as_of.isoformat(),
        "ingestedAt": live.ingested_at.isoformat(),
        "total": live.total,
        "shown": len(live.candidates),
        "new": live.new,
        "additional": live.additional,
        "sources": list(live.sources),
    }
    return view
