"""Potential buyers: organizations that could buy what this organization offers (ADR-0099).

A potential buyer is derived, never observed: an organization where independent public
signals point to plausible demand for this organization's activity. Each signal keeps its
own source, date and route, and the candidate is shown with all of them, separately:

* CUSTOMER_OF_COMPETITOR: it buys this activity from someone else. A public award to a
  competitor, or a client a same-activity organization shows on its own website.
* PUBLIC_BUYER_OF_CATEGORY: it keeps awarding contracts under this activity's codes.
* GROUP_OF_CUSTOMER: it is in the same corporate group (GLEIF) as a customer it already has.
* SIMILAR_TO_CUSTOMERS: Wikidata places it in the industry and country of its customers.
* SECTOR_BUYS_FROM_ITS_SECTOR: active nearby in a sector that usually buys from its own.

Candidates are organizations only, never people. They are POTENTIAL: not a customer, a
lead, a relationship nor a probability (MASTER §53.3). There is no score: candidates are
ordered by how many independent kinds of signal agree, then by the strongest kind.
Existing customers, partners, its own group and itself are never candidates.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from application.world_demand.awards import normalized_name

VERSION = "potential-buyers-v1"
MAX_CANDIDATES = 25
MAX_SIGNALS_SHOWN = 8
MAX_CUSTOMERS_LOOKED_UP = 8
MAX_GROUP_ENTITIES = 5
#: Strongest first: buying the activity already outranks resembling those who do.
SIGNAL_TYPES: tuple[str, ...] = (
    "CUSTOMER_OF_COMPETITOR",
    "PUBLIC_BUYER_OF_CATEGORY",
    "GROUP_OF_CUSTOMER",
    "SIMILAR_TO_CUSTOMERS",
    "SECTOR_BUYS_FROM_ITS_SECTOR",
)
POLICY = (
    "An organization where independent public signals point to plausible demand for this "
    "activity. Organizations only, never people. Not a customer, a lead, a relationship "
    "nor a probability: each signal is shown with its source and date."
)


@dataclass(frozen=True)
class Signal:
    candidate: str
    type: str
    basis: str
    source_url: str | None = None
    observed_at: str | None = None
    via: str | None = None
    identifiers: Mapping[str, str] = field(default_factory=dict)


def _items(value: object) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _detail(d: Mapping[str, Any]) -> Mapping[str, Any]:
    detail = d.get("detail")
    return detail if isinstance(detail, Mapping) else {}


def _discoveries(values: Iterable[object]) -> list[Mapping[str, Any]]:
    return [d for d in values if isinstance(d, Mapping)]


def customer_names(discoveries: Iterable[object]) -> list[str]:
    """Who already buys from it: the clients its own website shows, then its public buyers."""
    found = _discoveries(discoveries)
    declared = [str(d["statement"]) for d in found
                if d.get("code") == "CLIENT_DECLARED" and d.get("statement")]  # fmt: skip
    awarded = [str(d["statement"]) for d in found
               if d.get("code") == "PUBLIC_CONTRACTS_WON" and d.get("statement")]  # fmt: skip
    return list(dict.fromkeys([*declared, *awarded]))[:MAX_CUSTOMERS_LOOKED_UP]


def excluded_names(discoveries: Iterable[object], own_names: Iterable[str]) -> set[str]:
    """Itself, its group, its customers and partners: never a potential buyer."""
    out = {normalized_name(n) for n in own_names if n}
    for d in _discoveries(discoveries):
        code = str(d.get("code") or "")
        if code in {"CLIENT_DECLARED", "PARTNER_DECLARED", "PUBLIC_CONTRACTS_WON", "GROUP_PARENT",
                    "LEGAL_NAME_DECLARED"}:  # fmt: skip
            out.add(normalized_name(str(d.get("statement") or "")))
        if code == "GROUP_SUBSIDIARIES":
            for entity in _items(_detail(d).get("subsidiaries")):
                if isinstance(entity, Mapping):
                    out.add(normalized_name(str(entity.get("name") or "")))
        if code == "PUBLIC_CONTRACT_PARTNER":
            out.add(normalized_name(str(d.get("statement") or "")))
    out.discard("")
    return out


def view_signals(discoveries: Iterable[object]) -> list[Signal]:
    """Signals already in the observation: public awards and the value chain."""
    out: list[Signal] = []
    for d in _discoveries(discoveries):
        code, detail = d.get("code"), _detail(d)
        url, at = d.get("sourceUrl"), d.get("observedAt")
        if code == "RECURRING_PUBLIC_BUYER" and d.get("statement"):
            winners = [str(w) for w in _items(detail.get("topWinners"))]
            out.append(Signal(
                str(d["statement"]), "PUBLIC_BUYER_OF_CATEGORY",
                f"Awarded {detail.get('contracts', 0)} public contracts under this activity's "
                "codes, none to this organization in the awards held.",
                str(url) if url else None, str(at) if at else None,
                via=", ".join(winners[:3]) or None,
            ))  # fmt: skip
        elif code == "WINS_IN_SAME_CODES" and d.get("statement"):
            for buyer in _items(detail.get("buyers")):
                out.append(Signal(
                    str(buyer), "CUSTOMER_OF_COMPETITOR",
                    f"Awarded public contracts in this activity to {d['statement']}, which "
                    "wins under the same codes.",
                    str(url) if url else None, str(at) if at else None, via=str(d["statement"]),
                ))  # fmt: skip
        elif code == "POTENTIAL_PRIVATE_CUSTOMER" and d.get("statement"):
            out.append(Signal(
                str(d["statement"]), "SECTOR_BUYS_FROM_ITS_SECTOR",
                f"Active in its area in a sector ({detail.get('sectorLabel') or detail.get('sector')}) that usually buys "
                "from its own (Eurostat input-output).",
                str(url) if url else None, str(at) if at else None,
            ))  # fmt: skip
    return out


def peer_signals(peers: Sequence[Mapping[str, Any]]) -> list[Signal]:
    """Clients that same-activity organizations in the subscriber's portfolio show."""
    out: list[Signal] = []
    for peer in peers:
        name = str(peer.get("name") or "")
        for d in _discoveries(_items(peer.get("clients"))):
            if d.get("code") != "CLIENT_DECLARED" or not d.get("statement"):
                continue
            out.append(Signal(
                str(d["statement"]), "CUSTOMER_OF_COMPETITOR",
                f"Shown as a client on the website of {name}, which has the same activity "
                "reading. The client has not confirmed it.",
                str(d.get("sourceUrl") or "") or None, str(d.get("observedAt") or "") or None,
                via=name,
            ))  # fmt: skip
    return out


def group_signals(
    customer: str, group: Mapping[str, Any], *, countries: Sequence[str] = ()
) -> list[Signal]:
    """Entities in a customer's corporate group (GLEIF), the subscriber's countries first."""
    out: list[Signal] = []
    read_at = str(group.get("readAt") or "") or None
    parents = group.get("parents")
    entities: list[tuple[Mapping[str, Any], str]] = []
    if isinstance(parents, Mapping):
        for level in ("ultimate-parent", "direct-parent"):
            parent = parents.get(level)
            if isinstance(parent, Mapping) and parent.get("name"):
                entities.append((parent, "parent"))
    children = [c for c in _items(group.get("children")) if isinstance(c, Mapping)]
    wanted = {c.upper() for c in countries}
    children.sort(key=lambda c: (str(c.get("country") or "").upper() not in wanted,
                                 str(c.get("name") or "")))  # fmt: skip
    entities += [(c, "subsidiary") for c in children[:MAX_GROUP_ENTITIES]]
    for entity, role in entities:
        lei = str(entity.get("lei") or "")
        out.append(Signal(
            str(entity["name"]), "GROUP_OF_CUSTOMER",
            f"A {role} in the corporate group of {customer}, already a customer (GLEIF).",
            f"https://search.gleif.org/#/record/{lei}" if lei else None, read_at, via=customer,
            identifiers={k: str(v) for k, v in (("lei", lei), ("country", entity.get("country")))
                         if v},
        ))  # fmt: skip
    return out


def similar_signals(
    customers: Mapping[str, Mapping[str, Any]], peers: Sequence[Mapping[str, Any]]
) -> list[Signal]:
    """Organizations in the industry and country of its customers (Wikidata)."""
    out: list[Signal] = []
    for reading in peers:
        industry, country = reading.get("industry"), reading.get("country")
        via = [name for name, item in customers.items()
               if industry in _items(item.get("industries"))
               and country in _items(item.get("countries"))]  # fmt: skip
        if not via:
            continue
        sector = reading.get("industryLabel") or industry
        place = reading.get("countryLabel") or country
        for org in _discoveries(_items(reading.get("organizations"))):
            label = str(org.get("label") or "")
            if not label:
                continue
            out.append(Signal(
                label, "SIMILAR_TO_CUSTOMERS",
                f"Wikidata places it in {sector} in {place}, like {', '.join(via[:3])}, "
                "already customers. Resembling a customer is not buying.",
                f"https://www.wikidata.org/wiki/{org.get('item')}",
                str(reading.get("readAt") or "") or None, via=", ".join(via[:3]),
                identifiers={k: str(v) for k, v in (("wikidata", org.get("item")),
                             ("website", org.get("website")), ("lei", org.get("lei"))) if v},
            ))  # fmt: skip
    return out


def potential_buyers(
    signals: Iterable[Signal], *, exclude: set[str], observed_at: str
) -> list[dict[str, object]]:
    """One POTENTIAL_BUYER finding per organization, with every signal kept apart."""
    by_name: dict[str, list[Signal]] = {}
    for signal in signals:
        key = normalized_name(signal.candidate)
        if len(key) < 3 or key in exclude:
            continue
        by_name.setdefault(key, []).append(signal)
    rows = []
    for arrival, found in enumerate(by_name.values()):
        types = [t for t in SIGNAL_TYPES if any(s.type == t for s in found)]
        rows.append((-len(types), SIGNAL_TYPES.index(types[0]), arrival, types, found))
    # Ties keep the order each source gave (its relevance, the subscriber's countries first).
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out: list[dict[str, object]] = []
    for _n, _strength, _arrival, types, found in rows[:MAX_CANDIDATES]:
        name = found[0].candidate
        identifiers: dict[str, str] = {}
        for s in found:
            for k, v in s.identifiers.items():
                identifiers.setdefault(k, v)
        ordered = sorted(found, key=lambda s: SIGNAL_TYPES.index(s.type))
        seen: set[tuple[str, str | None]] = set()
        shown = []
        for s in ordered:
            if (s.type, s.via) in seen:
                continue  # the same route said once
            seen.add((s.type, s.via))
            shown.append({"type": s.type, "basis": s.basis, "via": s.via,
                          "sourceUrl": s.source_url, "observedAt": s.observed_at})  # fmt: skip
        out.append({
            "kind": "DEMAND", "code": "POTENTIAL_BUYER", "statement": name,
            "epistemicState": "POTENTIAL", "sourceUrl": shown[0]["sourceUrl"], "excerpt": None,
            "observedAt": observed_at,
            "detail": {
                "signalTypes": types, "independentSignals": len(types),
                "signals": shown[:MAX_SIGNALS_SHOWN], "identifiers": identifiers,
                "version": VERSION, "policy": POLICY,
            },
        })  # fmt: skip
    return out


def no_buyer_signals(*, has_customers: bool, observed_at: str) -> dict[str, object]:
    """Why no potential buyer is shown: an unknown, never 'nobody would buy'."""
    return {
        "kind": "SIGNIFICANT_UNKNOWN", "code": "NO_BUYER_SIGNALS",
        "statement": "No potential buyer can be derived yet.", "epistemicState": "UNKNOWN",
        "sourceUrl": None, "excerpt": None, "observedAt": observed_at,
        "detail": {
            "hasCustomerProfile": has_customers,
            "limitation": "Potential buyers are derived from who already buys: clients its "
            "website shows, public awards, competitors' clients and its sector's buyers. None "
            "is available yet; this is not an absence of demand.",
            "version": VERSION,
        },
    }  # fmt: skip
