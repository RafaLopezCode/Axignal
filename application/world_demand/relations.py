"""Relationships and competition read from published public contract awards.

Two readings, kept apart:

* Contracts the organization won, grouped by buyer. The award itself is an official,
  OBSERVED publication. Attributing it to this organization is identity: by its tax
  identifier the relationship is OBSERVED; by exact legal name only it stays POTENTIAL
  and says so. A past award is not a current relationship nor future business.
* Who else wins contracts under the same classification codes in the same country.
  That they compete with this organization is an inference: POTENTIAL, with the awards
  that ground it. It is not a ranking of quality.

Coverage is always stated: the index holds the awards published since a given date, so
"no awards found" means none in that window, never that the organization has none.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Protocol

from application.observation_intelligence.contracts import TaxonomyCode
from application.world_demand.awards import (
    AwardRecord,
    is_company,
    normalized_name,
    normalized_tax_id,
)
from application.world_demand.index import code_within
from application.world_demand.opportunities import contract_partners, recurrent_buyers

#: Competition looks back this far (bounded by what the index actually holds).
COMPETITION_WINDOW = timedelta(days=365)
MAX_COMPETITORS = 8
MAX_BUYERS = 12
_SPANISH_TAX_ID = re.compile(r"\b(?:ES)?([A-HJ-NP-SUVW]\d{7}[0-9A-J]|\d{8}[A-Z])\b")


class AwardStore(Protocol):
    def awards_won_by(
        self, *, tax_ids: Sequence[str] = (), names: Sequence[str] = (), limit: int = 500
    ) -> tuple[AwardRecord, ...]: ...

    def awards_in(
        self, country: str, *, since: date, limit: int = 20000
    ) -> tuple[AwardRecord, ...]: ...

    def awards_coverage(self, country: str) -> tuple[date | None, int]: ...


def _items(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else []


def identity_keys(view: Mapping[str, object]) -> tuple[list[str], list[str]]:
    """Tax ids and legal names the observation itself published (never invented)."""
    tax_ids: list[str] = []
    names: list[str] = []
    for d in _items(view.get("discoveries")):
        if not isinstance(d, Mapping):
            continue
        code = str(d.get("code") or "")
        statement = str(d.get("statement") or "")
        tax = normalized_tax_id(statement.split(" ", 1)[-1])
        if d.get("kind") == "IDENTITY_HINT" and code.startswith("IDENTIFIER_DECLARED:") and tax:
            tax_ids.append(tax)
        if d.get("kind") == "IDENTITY_HINT" and code == "LEGAL_NAME_DECLARED" and statement:
            names.append(statement)
        detail = d.get("detail")
        if code == "COUNTRY_FROM_SITE_SIGNALS" and isinstance(detail, Mapping):
            for signal in _items(detail.get("signals")):
                if isinstance(signal, Mapping) and signal.get("kind") == "TAX_IDENTIFIER":
                    found = _SPANISH_TAX_ID.search(str(signal.get("value") or "").upper())
                    if found:
                        tax_ids.append(found.group(1))
    target = view.get("target")
    if isinstance(target, Mapping) and isinstance(target.get("name"), str) and target["name"]:
        names.append(str(target["name"]))
    return list(dict.fromkeys(tax_ids)), list(dict.fromkeys(names))


def _codes(proof: Mapping[str, object]) -> list[TaxonomyCode]:
    out: list[TaxonomyCode] = []
    for capability in _items(proof.get("capabilities")):
        if isinstance(capability, Mapping):
            for pair in _items(capability.get("demandCodes")):
                if isinstance(pair, list | tuple) and len(pair) == 2 and pair[0] == "CPV":
                    out.append(TaxonomyCode("CPV", str(pair[1])))
    return out


def _award_wire(award: AwardRecord) -> dict[str, object]:
    return {
        "title": award.title,
        "buyer": award.buyer_name,
        "winner": award.winner_name,
        "amount": award.amount,
        "currency": award.currency,
        "awardedOn": None if award.awarded_on is None else award.awarded_on.isoformat(),
        "offersReceived": award.offers_received,
        "url": award.source_url,
        "source": award.source_id,
    }


def _discovery(kind: str, code: str, statement: str, state: str, url: str | None,
               observed_at: str, detail: dict[str, object]) -> dict[str, object]:  # fmt: skip
    return {
        "kind": kind, "code": code, "statement": statement, "epistemicState": state,
        "sourceUrl": url, "excerpt": None, "observedAt": observed_at, "detail": detail,
    }  # fmt: skip


def public_award_discoveries(
    view: Mapping[str, object],
    proof: Mapping[str, object],
    store: AwardStore,
    *,
    now: datetime,
    country: str = "EU/ES",
) -> list[dict[str, object]]:
    tax_ids, names = identity_keys(view)
    since, held = store.awards_coverage(country)
    coverage = {
        "coverageSince": None if since is None else since.isoformat(),
        "awardsInIndex": held,
        "limitation": "Public contract awards published since this date only; "
        "absence here is not absence of contracts.",
    }
    # Stable across reads of the same observation: its own time, never the reading time.
    observed_at = str(view.get("observedAt") or now.isoformat())
    out: list[dict[str, object]] = []
    won = [
        a
        for a in store.awards_won_by(tax_ids=tax_ids, names=names)
        if a.places and any(p.code.startswith(country) for p in a.places)
    ]
    by_tax = {a.key for a in won if a.winner_id and a.winner_id in tax_ids}
    own_names = {normalized_name(n) for n in names}
    own_ids = set(tax_ids) | {a.winner_id for a in won if a.winner_id}
    by_buyer: dict[str, list[AwardRecord]] = defaultdict(list)
    for award in won:
        by_buyer[award.buyer_name or "—"].append(award)
    ranked = sorted(by_buyer.items(), key=lambda item: (-len(item[1]), item[0]))
    for buyer, awards in ranked[:MAX_BUYERS]:
        strong = all(a.key in by_tax for a in awards)
        out.append(
            _discovery(
                "RELATIONSHIP", "PUBLIC_CONTRACTS_WON", buyer,
                "OBSERVED" if strong else "POTENTIAL", awards[0].source_url, observed_at,
                {
                    "role": "PUBLIC_BUYER",
                    "matchedBy": "TAX_ID" if strong else "LEGAL_NAME",
                    "contracts": len(awards),
                    "amount": round(sum(a.amount or 0 for a in awards), 2),
                    "currency": next((a.currency for a in awards if a.currency), None),
                    "lastAwardedOn": max((a.awarded_on.isoformat() for a in awards if a.awarded_on), default=None),
                    "awards": [_award_wire(a) for a in awards[:10]],
                    **coverage,
                },
            )
        )  # fmt: skip
    codes = _codes(proof)
    matched: list[AwardRecord] = []
    window: tuple[AwardRecord, ...] = ()
    if codes:
        window_start = (now - COMPETITION_WINDOW).date()
        rivals: dict[str, list[AwardRecord]] = defaultdict(list)
        window = store.awards_in(country, since=window_start)
        for award in window:
            if not any(code_within(c, wanted) for c in award.demand_codes for wanted in codes):
                continue
            matched.append(award)
            if (award.winner_id and award.winner_id in own_ids) or normalized_name(
                award.winner_name
            ) in own_names:
                continue
            if not is_company(award.winner_name, award.winner_id):
                continue  # an individual's award is never shown as competition
            rivals[award.winner_id or normalized_name(award.winner_name)].append(award)
        top = sorted(rivals.values(), key=lambda a: (-len(a), -sum(x.amount or 0 for x in a)))
        for awards in top[:MAX_COMPETITORS]:
            out.append(
                _discovery(
                    "COMPETITION", "WINS_IN_SAME_CODES", awards[0].winner_name, "POTENTIAL",
                    awards[0].source_url, observed_at,
                    {
                        "winnerId": awards[0].winner_id,
                        "contracts": len(awards),
                        "amount": round(sum(a.amount or 0 for a in awards), 2),
                        "currency": next((a.currency for a in awards if a.currency), None),
                        "buyers": sorted({a.buyer_name for a in awards if a.buyer_name})[:6],
                        "medianOffers": _median([a.offers_received for a in awards if a.offers_received]),
                        "codes": sorted({f"CPV:{c.code}" for a in awards for c in a.demand_codes if any(code_within(c, w) for w in codes)})[:6],
                        "awards": [_award_wire(a) for a in awards[:5]],
                        "basis": "Wins public contracts under the classification codes of this "
                        "organization's activity. Competing with it is an inference.",
                        **coverage,
                    },
                )
            )  # fmt: skip
    if matched:
        # Who keeps buying what it does, and has not bought from it (POTENTIAL).
        scopes = [
            TaxonomyCode("GEO", str(s.get("jurisdiction")))
            for s in _items(proof.get("attentionScopes"))
            if isinstance(s, Mapping) and s.get("jurisdiction")
        ]
        out += recurrent_buyers(
            matched, own_buyers=set(by_buyer), scopes=scopes, observed_at=observed_at,
            coverage=coverage,
        )  # fmt: skip
    if window:
        # Companies active nearby in the sectors its sector buys from and sells to.
        from application.value_chain import chain_organizations, company_industry

        industry = company_industry(view, [c.code for c in codes])
        if industry is not None:
            area = [
                TaxonomyCode("GEO", str(s.get("jurisdiction")))
                for s in _items(proof.get("attentionScopes"))
                if isinstance(s, Mapping) and s.get("jurisdiction")
            ]
            out += chain_organizations(
                list(window), industry[0],
                in_area=lambda a: not area or any(p.within(z) for p in a.places for z in area),
                own_ids=own_ids, own_names=own_names, normalize=normalized_name,
                observed_at=observed_at,
            )  # fmt: skip
    lots_of = getattr(store, "awards_of_lots", None)
    utes_named = getattr(store, "joint_venture_awards", None)
    if won and callable(lots_of) and callable(utes_named):
        # Who it has been awarded contracts together with (same lot or joint venture).
        out += contract_partners(
            won,
            lots_of([(a.source_id, a.record_id, a.lot) for a in won[:200]]),
            utes_named([n for n in names if len(normalized_name(n)) >= 4]),
            own_ids=own_ids, own_names=own_names, observed_at=observed_at,
        )  # fmt: skip
    elif callable(utes_named) and names:
        out += contract_partners(
            (), (), utes_named([n for n in names if len(normalized_name(n)) >= 4]),
            own_ids=own_ids, own_names=own_names, observed_at=observed_at,
        )  # fmt: skip
    if not won and (tax_ids or names) and held:  # nothing held: nothing to say
        out.append(
            _discovery(
                "SIGNIFICANT_UNKNOWN", "NO_PUBLIC_AWARDS_FOUND",
                "No public contract award to this organization in the awards held.",
                "UNKNOWN", None, observed_at,
                {"matchedBy": ["TAX_ID"] * bool(tax_ids) + ["LEGAL_NAME"] * bool(names), **coverage},
            )
        )  # fmt: skip
    return out


def _median(values: Iterable[int]) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    return (
        float(ordered[middle]) if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    )


def apply_public_awards(
    view: dict[str, object],
    proof: Mapping[str, object],
    store: AwardStore | None,
    *,
    now: datetime,
    countries: Callable[[], Sequence[str]] | None = None,
) -> dict[str, object]:
    """Add award-based relationships and competition to an observation view (Spain first)."""
    if store is None:
        return view
    scopes = [
        str(s.get("jurisdiction"))
        for s in _items(proof.get("attentionScopes"))
        if isinstance(s, Mapping)
    ]
    directed = list(countries()) if countries is not None else []
    if not any(code.startswith("EU/ES") for code in (*scopes, *directed)):
        return view  # PLACSP covers Spain; other countries need their award sources
    found = public_award_discoveries(view, proof, store, now=now)
    if found:
        view["discoveries"] = [*_items(view.get("discoveries")), *found]
    return view
