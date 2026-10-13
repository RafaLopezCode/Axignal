"""INXIGHTs: what crossing the observed families reveals, explainable down to its evidence.

MASTER §4.6 and §18: an INXIGHT is derived knowledge, never a FAXT. Each one here is a
deterministic, versioned rule over the discoveries an observation already holds — no
model call, no new source, no extra cost. It cites every discovery it crosses (kind,
code, statement, source, date), keeps its own date as the oldest of its evidence, and is
recomputed on every read, so it degrades and disappears when its evidence changes.
Always POTENTIAL: an inference that deserves attention, not an established fact, never a
score.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from typing import Any

RULES_VERSION = "inxights-v1"
Discovery = Mapping[str, Any]
_FORMS = {"sa", "sl", "slu", "sau", "ltd", "inc", "gmbh", "sas", "spa", "srl", "bv", "nv",
          "plc", "llc", "corp", "co", "group", "grupo", "the"}  # fmt: skip


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def _core(name: str) -> str:
    return " ".join(t for t in _fold(name).split() if t not in _FORMS)


def same_name(a: str, b: str) -> bool:
    x, y = _core(a), _core(b)
    return bool(x) and bool(y) and min(len(x), len(y)) >= 4 and (x == y or x in y or y in x)


def _all(view: Mapping[str, Any], kind: str, *codes: str) -> list[Discovery]:
    held = view.get("discoveries")
    return [
        d
        for d in (held if isinstance(held, list) else [])
        if isinstance(d, Mapping)
        and d.get("kind") == kind
        and (not codes or d.get("code") in codes)
    ]


def _detail(d: Discovery) -> Mapping[str, Any]:
    detail = d.get("detail")
    return detail if isinstance(detail, Mapping) else {}


def _cite(d: Discovery) -> dict[str, object]:
    return {
        "kind": d.get("kind"), "code": d.get("code"), "statement": d.get("statement"),
        "epistemicState": d.get("epistemicState"), "sourceUrl": d.get("sourceUrl"),
        "observedAt": d.get("observedAt"),
    }  # fmt: skip


def _inxight(
    family: str, rule: str, statement: str, evidence: Sequence[Discovery], *,
    why: str, values: Mapping[str, object] | None = None,
) -> dict[str, object]:  # fmt: skip
    dates = sorted(str(d.get("observedAt")) for d in evidence if d.get("observedAt"))
    return {
        "kind": "INXIGHT",
        "code": f"{family}:{rule}",
        "statement": statement,
        "epistemicState": "POTENTIAL",
        "sourceUrl": next((d.get("sourceUrl") for d in evidence if d.get("sourceUrl")), None),
        "excerpt": None,
        "observedAt": dates[0] if dates else None,
        "detail": {
            "rule": rule,
            "rulesVersion": RULES_VERSION,
            "family": family,
            "values": dict(values or {}),
            "evidence": [_cite(d) for d in evidence[:8]],
            "evidenceCount": len(evidence),
            "why": why,
            "limitation": "Derived by crossing observed findings; an inference that deserves "
            "attention, not a fact. It is recomputed when its evidence changes.",
        },
    }


def _area(view: Mapping[str, Any]) -> str:
    """AREA when attention covers a region, COUNTRY when a whole country."""
    scopes = [str(x.get("jurisdiction") or "") for x in view.get("attentionScopes") or []
              if isinstance(x, Mapping)]  # fmt: skip
    return "AREA" if max((len(c.split("/")) for c in scopes), default=2) > 2 else "COUNTRY"


# ---- rules ----------------------------------------------------------------------------
def local_buyers_never_awarded(view: Mapping[str, Any]) -> list[dict[str, object]]:
    buyers = [
        b for b in _all(view, "DEMAND", "RECURRING_PUBLIC_BUYER")
        if int(_detail(b).get("contractsInArea") or 0) > 0
    ]  # fmt: skip
    if len(buyers) < 2:
        return []
    contracts = sum(int(_detail(b).get("contractsInArea") or 0) for b in buyers)
    where = "its area" if _area(view) == "AREA" else "its country"
    return [_inxight(
        "demand", "LOCAL_BUYERS_NEVER_AWARDED",
        f"{len(buyers)} public bodies in {where} award what it does ({contracts} contracts in "
        "the period held) and none has awarded it a contract.",
        buyers, values={"buyers": len(buyers), "contracts": contracts, "where": _area(view)},
        why="Recurring demand close by that it is not capturing.",
    )]  # fmt: skip


def competitors_win_with_its_buyers(view: Mapping[str, Any]) -> list[dict[str, object]]:
    buyers = {str(b.get("statement")): b for b in _all(view, "DEMAND", "RECURRING_PUBLIC_BUYER")}
    rivals: list[Discovery] = []
    shared: dict[str, None] = {}
    for rival in _all(view, "COMPETITION"):
        where = [n for n in _detail(rival).get("buyers") or [] if n in buyers]
        if where:
            rivals.append(rival)
            shared.update(dict.fromkeys(where))
    if not rivals:
        return []
    names = [str(r.get("statement")) for r in rivals][:3]
    places = list(shared)[:3]
    return [_inxight(
        "relationships", "COMPETITORS_WIN_WITH_ITS_BUYERS",
        f"{', '.join(names)} already win contracts with {', '.join(places)}: buyers of its "
        "activity that have not awarded it.",
        [*rivals[:4], *(buyers[n] for n in places)],
        values={"competitors": names, "buyers": places},
        why="Where competitors are established, the buyer already buys this activity: the "
        "door is open, and who holds it is known.",
    )]  # fmt: skip


def demand_without_declared_offer(view: Mapping[str, Any]) -> list[dict[str, object]]:
    tenders = [
        d for d in _all(view, "DEMAND")
        if d.get("code") not in {"RECURRING_PUBLIC_BUYER", "VALUE_CHAIN_BUYERS",
                                 "POTENTIAL_PRIVATE_CUSTOMER"}
    ]  # fmt: skip
    gap = _all(view, "REPRESENTATION_GAP", "OFFER_NOT_MACHINE_READABLE")
    if not tenders or not gap:
        return []
    # The view lists a bounded sample; the demand reading carries the real total.
    demand = view.get("demand")
    total = demand.get("total") if isinstance(demand, Mapping) else None
    calls = total if isinstance(total, int) and total >= len(tenders) else len(tenders)
    return [_inxight(
        "demand", "OPEN_DEMAND_OFFER_NOT_DECLARED",
        f"{calls} open public call(s) match what it does, while its website does not "
        "declare that offer as structured data.",
        [*gap, *tenders[:5]], values={"openCalls": calls, "shown": len(tenders)},
        why="Buyers and search surfaces that rely on structured data may not connect it to "
        "demand that exists now.",
    )]  # fmt: skip


def ai_names_competitors(view: Mapping[str, Any]) -> list[dict[str, object]]:
    geo = _all(view, "GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY")
    rivals = _all(view, "COMPETITION")
    if not geo or not rivals:
        return []
    named = [str(n) for n in _detail(geo[0]).get("competitorsNamed") or []]
    both = [r for r in rivals if any(same_name(str(r.get("statement") or ""), n) for n in named)]
    if not both:
        return []
    names = [str(r.get("statement")) for r in both][:3]
    return [_inxight(
        "presence", "AI_NAMES_COMPETITORS_NOT_IT",
        f"Asked about its category, AI assistants name {', '.join(names)} — companies that "
        "win contracts in its codes — and not this organization.",
        [geo[0], *both], values={"competitors": names},
        why="Competitors are being recommended where buyers now ask; this organization is not.",
    )]  # fmt: skip


def public_revenue_share(view: Mapping[str, Any]) -> list[dict[str, object]]:
    revenue = next(
        (d for d in _all(view, "ECONOMIC_FACT")
         if _detail(d).get("fact") == "revenue" and _detail(d).get("unit") == "EUR"),
        None,
    )  # fmt: skip
    won = _all(view, "RELATIONSHIP", "PUBLIC_CONTRACTS_WON")
    if revenue is None or not won:
        return []
    annual = float(_detail(revenue).get("value") or 0)
    awarded = sum(float(_detail(w).get("amount") or 0) for w in won
                  if _detail(w).get("currency") in {"EUR", None})  # fmt: skip
    if annual <= 0 or awarded <= 0:
        return []
    share = awarded / annual
    if share < 0.2:
        return []
    statement = (
        "Public contracts awarded to it in the period held exceed its latest reported annual "
        "revenue (contracts often span several years)."
        if share >= 1
        else "Public contracts awarded to it in the period held add up to about "
        f"{round(share * 100)}% of its latest reported annual revenue."
    )
    return [_inxight(
        "economics", "PUBLIC_CONTRACTS_WEIGHT", statement, [revenue, *won],
        values={"share": round(share, 3), "awarded": round(awarded, 2), "revenue": annual},
        why="A high weight of public contracts means exposure to public budgets and tenders. "
        "Contract amounts may span several years: an order of magnitude, not a ratio of sales.",
    )]  # fmt: skip


def client_concentration(view: Mapping[str, Any]) -> list[dict[str, object]]:
    won = _all(view, "RELATIONSHIP", "PUBLIC_CONTRACTS_WON")
    amounts = [(w, float(_detail(w).get("amount") or 0)) for w in won]
    total = sum(a for _w, a in amounts)
    if len(won) < 3 or total <= 0:
        return []
    top, value = max(amounts, key=lambda x: x[1])
    if value / total < 0.5:
        return []
    return [_inxight(
        "relationships", "PUBLIC_CLIENT_CONCENTRATION",
        f"{top.get('statement')} accounts for {round(value / total * 100)}% of the public "
        "contract value awarded to it in the period held.",
        [top, *[w for w, _a in amounts if w is not top]],
        values={"client": top.get("statement"), "share": round(value / total, 3)},
        why="Dependence on one public client: a renewal or a budget change there weighs a lot.",
    )]  # fmt: skip


def sector_in_news_not_it(view: Mapping[str, Any]) -> list[dict[str, object]]:
    headlines = _all(view, "CONTEXT_SIGNAL", "SECTOR_HEADLINE")
    if len(headlines) < 3 or _all(view, "MENTION", "PRESS_MENTION"):
        return []
    return [_inxight(
        "reputation", "SECTOR_IN_NEWS_NOT_IT",
        f"Its sector is in the news ({len(headlines)} recent headlines in its country) and the "
        "indexed press does not name this organization.",
        headlines, values={"headlines": len(headlines)},
        why="A conversation about its market is happening without its voice.",
    )]  # fmt: skip


def group_countries_unwatched(view: Mapping[str, Any]) -> list[dict[str, object]]:
    group = _all(view, "DECLARED_LOCATION", "GROUP_ENTITIES_IN_COUNTRIES")
    if not group:
        return []
    countries = [str(c) for c in (_detail(group[0]).get("countries") or {})]
    watched = {str(x.get("jurisdiction") or "") for x in view.get("attentionScopes") or []
               if isinstance(x, Mapping)}  # fmt: skip
    markets = view.get("demandMarkets")
    directed = markets.get("directed") if isinstance(markets, Mapping) else None
    watched |= {str(c) for c in directed or []}
    missing = [c for c in countries if not any(c in w.split("/") for w in watched)]
    if not missing:
        return []
    return [_inxight(
        "markets", "GROUP_COUNTRIES_DEMAND_UNWATCHED",
        f"Its group has registered entities in {', '.join(missing[:6])}, where its demand is "
        "not being watched.",
        group, values={"countries": missing},
        why="Countries where it already has a legal presence are the cheapest markets to "
        "watch; direct demand there to see it.",
    )]  # fmt: skip


def inception_disagreement(view: Mapping[str, Any]) -> list[dict[str, object]]:
    years: dict[str, Discovery] = {}
    for d in _all(view, "ECONOMIC_FACT"):
        if (
            _detail(d).get("fact") == "inception"
            and str(_detail(d).get("value") or "")[:4].isdigit()
        ):
            years[str(_detail(d).get("sourceKind") or "OTHER")] = d
    official, community = years.get("OFFICIAL_REGISTER"), years.get("SECONDARY_COMMUNITY_EDITED")
    if official is None or community is None:
        return []
    a = int(str(_detail(official).get("value"))[:4])
    b = int(str(_detail(community).get("value"))[:4])
    if abs(a - b) < 3:
        return []
    return [_inxight(
        "organization", "FOUNDING_YEAR_SOURCES_DISAGREE",
        f"The official register dates it to {a}; Wikidata to {b}.",
        [official, community], values={"register": a, "wikidata": b},
        why="Often a predecessor company or a re-registration; worth knowing which entity "
        "carries its history.",
    )]  # fmt: skip


RULES: tuple[Callable[[Mapping[str, Any]], list[dict[str, object]]], ...] = (
    local_buyers_never_awarded,
    competitors_win_with_its_buyers,
    demand_without_declared_offer,
    ai_names_competitors,
    public_revenue_share,
    client_concentration,
    sector_in_news_not_it,
    group_countries_unwatched,
    inception_disagreement,
)


def apply_inxights(view: dict[str, Any]) -> dict[str, Any]:
    """Recompute every INXIGHT from the view's current discoveries (never stored)."""
    held = view.get("discoveries")
    discoveries = [d for d in (held if isinstance(held, list) else [])
                   if not (isinstance(d, Mapping) and d.get("kind") == "INXIGHT")]  # fmt: skip
    base = {**view, "discoveries": discoveries}
    found: list[dict[str, object]] = []
    for rule in RULES:
        try:
            found += rule(base)
        except (TypeError, ValueError, KeyError):  # malformed evidence: that rule stays silent
            continue
    view["discoveries"] = [*found, *discoveries]
    return view
